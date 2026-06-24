import logging
import re
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from compliance_register.models import (
    ESGComplianceEntry,
    ESGComplianceHistory,
    ESGComplianceMailLog,
    ESGComplianceStateLog,
    InsuranceRegisterDetail,
)

logger = logging.getLogger(__name__)

STATUS_ACTIVE = "active"
STATUS_RENEWAL_DUE = "renewal_due"
STATUS_EXPIRED = "expired"

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")


def normalize_status(status):
    """Return the internal lower-case status value used by reminder logic."""
    if not status:
        return STATUS_ACTIVE
    return str(status).strip().lower().replace(" ", "_")


def calculate_status(expiry_date, notify_days, today):
    """Calculate active, renewal_due, or expired from expiry and notify days."""
    notify_days = notify_days or 0
    trigger_date = expiry_date - timedelta(days=notify_days)

    if today > expiry_date:
        return STATUS_EXPIRED
    if trigger_date <= today <= expiry_date:
        return STATUS_RENEWAL_DUE
    return STATUS_ACTIVE


def split_recipients(value):
    """Parse one or more email recipients from strings, lists, or tuples."""
    if not value:
        return []
    if isinstance(value, (list, tuple, set)):
        values = value
    else:
        values = re.split(r"[,;\s]+", str(value))
    return [item.strip() for item in values if item and EMAIL_RE.fullmatch(item.strip())]


def extract_recipients(*values, fallback=None):
    """Find email addresses in model fields, then fall back to settings values."""
    recipients = []
    for value in values:
        if value:
            recipients.extend(EMAIL_RE.findall(str(value)))
    if not recipients:
        recipients.extend(split_recipients(fallback))
    return list(dict.fromkeys(recipients))


def build_esg_message(entry, history, status_value, today):
    """Build subject and body for ESG renewal or expiry notification."""
    remaining_days = max((history.expiry_date - today).days, 0)

    if status_value == STATUS_EXPIRED:
        subject = "ESG Compliance Expired"
        body = (
            "ESG Compliance Expired\n\n"
            f"Entry Number: {entry.unique_id}\n"
            f"Company: {entry.company_id}\n"
            f"Project: {entry.project_id}\n"
            f"Compliance Type: {entry.compliance_type_id}\n"
            f"Expiry Date: {history.expiry_date}\n"
            f"Responsible Person: {history.responsible_person}\n"
        )
        return subject, body

    subject = "ESG Compliance Renewal Due"
    body = (
        "ESG Compliance Renewal Due\n\n"
        f"Entry Number: {entry.unique_id}\n"
        f"Company: {entry.company_id}\n"
        f"Project: {entry.project_id}\n"
        f"Compliance Type: {entry.compliance_type_id}\n"
        f"Issue Date: {history.issue_date}\n"
        f"Expiry Date: {history.expiry_date}\n"
        f"Responsible Person: {history.responsible_person}\n"
        f"Remaining Days: {remaining_days}\n"
    )
    return subject, body


def build_insurance_message(detail, status_value, today):
    """Build subject and body for insurance renewal or expiry notification."""
    remaining_days = max((detail.validity - today).days, 0)

    if status_value == STATUS_EXPIRED:
        subject = "Insurance Policy Expired"
        body = (
            "Insurance Policy Expired\n\n"
            f"Policy Number: {detail.policy_no}\n"
            f"Asset Name: {detail.policy_asset}\n"
            f"Insurer: {detail.insurer}\n"
            f"Coverage: {detail.coverage}\n"
            f"Validity Date: {detail.validity}\n"
        )
        return subject, body

    subject = "Insurance Policy Renewal Due"
    body = (
        "Insurance Policy Renewal Due\n\n"
        f"Policy Number: {detail.policy_no}\n"
        f"Asset Name: {detail.policy_asset}\n"
        f"Insurer: {detail.insurer}\n"
        f"Coverage: {detail.coverage}\n"
        f"Validity Date: {detail.validity}\n"
        f"Remaining Days: {remaining_days}\n"
    )
    return subject, body


def send_reminder_email(subject, body, recipients):
    """Send an email through Django's configured SMTP backend."""
    if not recipients:
        return False
    send_mail(
        subject=subject,
        message=body,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        recipient_list=recipients,
        fail_silently=False,
    )
    return True


def create_state_log(history, old_status, new_status):
    """Create a state transition audit record when status changes."""
    if old_status == new_status:
        return None
    log = ESGComplianceStateLog.objects.create(
        compliance_history=history,
        from_status=old_status,
        to_status=new_status,
    )
    logger.info(
        "ESG status changed for history %s: %s -> %s",
        history.id,
        old_status,
        new_status,
    )
    return log


def create_mail_log(history, email_type, recipients, subject):
    """Persist ESG reminder email audit details."""
    return ESGComplianceMailLog.objects.create(
        compliance_history=history,
        email_type=email_type,
        sent_to=", ".join(recipients),
        subject=subject,
    )


class NotificationDispatcher:
    """Small dispatch point so SMS and WhatsApp can be added later."""

    def send_email(self, subject, body, recipients):
        return send_reminder_email(subject, body, recipients)

    def send_sms(self, *args, **kwargs):
        logger.debug("SMS notifications are not configured yet.")

    def send_whatsapp(self, *args, **kwargs):
        logger.debug("WhatsApp notifications are not configured yet.")


class Command(BaseCommand):
    help = "Check ESG and insurance expiry reminders, update statuses, and send emails."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Calculate changes without saving updates or sending emails.",
        )

    def handle(self, *args, **options):
        self.today = timezone.localdate()
        self.dry_run = options["dry_run"]
        self.dispatcher = NotificationDispatcher()

        logger.info("Expiry reminder command started for %s", self.today)

        esg_count = self.process_esg_entries()
        insurance_count = self.process_insurance_details()

        logger.info(
            "Expiry reminder command finished. ESG processed=%s, insurance processed=%s",
            esg_count,
            insurance_count,
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Processed ESG={esg_count}, Insurance={insurance_count}"
            )
        )

    def process_esg_entries(self):
        processed = 0
        queryset = ESGComplianceEntry.objects.filter(is_delete=False).prefetch_related("history")

        for entry in queryset.iterator(chunk_size=200):
            try:
                self.process_esg_entry(entry)
                processed += 1
            except Exception:
                logger.exception("Failed processing ESG entry %s", entry.id)

        return processed

    def get_latest_history(self, entry):
        """Return latest history, creating one from the entry if none exists."""
        history = entry.history.order_by("-id").first()
        if history:
            return history

        logger.info("Creating missing ESG history for entry %s", entry.id)
        if self.dry_run:
            return None

        return ESGComplianceHistory.objects.create(
            compliance_entry=entry,
            issue_date=entry.issue_date,
            expiry_date=entry.expiry_date,
            notify_days=entry.notify_days,
            status=normalize_status(entry.status),
            responsible_person=entry.responsible_person,
            reference_no=entry.reference_no,
            remarks=entry.remarks,
        )

    def process_esg_entry(self, entry):
        history = self.get_latest_history(entry)
        if history is None:
            return

        old_status = normalize_status(history.status)
        new_status = calculate_status(history.expiry_date, history.notify_days, self.today)

        with transaction.atomic():
            if old_status != new_status:
                logger.info(
                    "Updating ESG entry %s status: %s -> %s",
                    entry.id,
                    old_status,
                    new_status,
                )
                if not self.dry_run:
                    create_state_log(history, old_status, new_status)
                    history.status = new_status
                    history.save(update_fields=["status", "updated"])

            entry_status = normalize_status(entry.status)
            if entry_status != new_status and not self.dry_run:
                entry.status = new_status
                entry.save(update_fields=["status", "updated"])

            if new_status in (STATUS_RENEWAL_DUE, STATUS_EXPIRED):
                self.send_esg_email(entry, history, new_status)

    def send_esg_email(self, entry, history, status_value):
        if history.last_notified_on == self.today:
            logger.info("Skipping ESG history %s email; already sent today", history.id)
            return

        recipients = extract_recipients(
            history.responsible_person,
            entry.responsible_person,
            fallback=getattr(settings, "ESG_REMINDER_EMAIL_RECIPIENTS", ""),
        )
        if not recipients:
            logger.info("Skipping ESG history %s email; recipient email empty", history.id)
            return

        subject, body = build_esg_message(entry, history, status_value, self.today)
        email_type = "expired" if status_value == STATUS_EXPIRED else "renewal_due"

        if self.dry_run:
            logger.info("Dry run: would send ESG %s email to %s", email_type, recipients)
            return

        try:
            self.dispatcher.send_email(subject, body, recipients)
            history.last_notified_on = self.today
            history.save(update_fields=["last_notified_on", "updated"])
            create_mail_log(history, email_type, recipients, subject)
            logger.info("Sent ESG %s email for history %s to %s", email_type, history.id, recipients)
        except Exception:
            logger.exception("Failed sending ESG email for history %s", history.id)

    def process_insurance_details(self):
        processed = 0
        queryset = InsuranceRegisterDetail.objects.select_related("register").all()

        for detail in queryset.iterator():
            try:
                self.process_insurance_detail(detail)
                processed += 1
            except Exception:
                logger.exception("Failed processing insurance detail %s", detail.id)

        return processed

    def process_insurance_detail(self, detail):
        old_status = normalize_status(detail.status)
        new_status = calculate_status(detail.validity, detail.notify_days, self.today)

        if old_status != new_status:
            logger.info(
                "Updating insurance detail %s status: %s -> %s",
                detail.id,
                old_status,
                new_status,
            )
            if not self.dry_run:
                detail.status = new_status
                detail.save(update_fields=["status"])

        if new_status in (STATUS_RENEWAL_DUE, STATUS_EXPIRED):
            self.send_insurance_email(detail, new_status)

    def send_insurance_email(self, detail, status_value):
        if detail.last_notified_on == self.today:
            logger.info("Skipping insurance detail %s email; already sent today", detail.id)
            return

        recipients = extract_recipients(
            detail.register.remarks,
            detail.remarks,
            fallback=getattr(settings, "INSURANCE_REMINDER_EMAIL_RECIPIENTS", "")
            or getattr(settings, "ESG_REMINDER_EMAIL_RECIPIENTS", ""),
        )
        if not recipients:
            logger.info("Skipping insurance detail %s email; recipient email empty", detail.id)
            return

        subject, body = build_insurance_message(detail, status_value, self.today)
        email_type = "expired" if status_value == STATUS_EXPIRED else "renewal_due"

        if self.dry_run:
            logger.info("Dry run: would send insurance %s email to %s", email_type, recipients)
            return

        try:
            self.dispatcher.send_email(subject, body, recipients)
            detail.last_notified_on = self.today
            detail.save(update_fields=["last_notified_on"])
            logger.info(
                "Sent insurance %s email for detail %s to %s",
                email_type,
                detail.id,
                recipients,
            )
        except Exception:
            logger.exception("Failed sending insurance email for detail %s", detail.id)
