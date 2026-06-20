from django.db import migrations, models


def mark_product_owned_lookups(apps, schema_editor):
    ItemGroup = apps.get_model("purchase_master", "ItemGroup")
    SubGroup = apps.get_model("purchase_master", "SubGroup")
    ProductGroup = apps.get_model("purchase_master", "ProductGroup")
    ProductSubGroup = apps.get_model("purchase_master", "ProductSubGroup")

    item_group_keys = {
        (
            (group.group_name or "").strip().casefold(),
            (group.code or "").strip().casefold(),
        )
        for group in ItemGroup.objects.all()
    }
    item_group_ids = set(ItemGroup.objects.values_list("id", flat=True))

    product_group_ids = []
    for group in ProductGroup.objects.all():
        key = (
            (group.group_name or "").strip().casefold(),
            (group.code or "").strip().casefold(),
        )
        is_copied_from_item_group = group.id in item_group_ids or key in item_group_keys
        group.created_in_product_creation = not is_copied_from_item_group
        group.save(update_fields=["created_in_product_creation"])
        if group.created_in_product_creation:
            product_group_ids.append(group.id)

    item_sub_group_keys = {
        (
            sub_group.group_id,
            (sub_group.sub_group_name or "").strip().casefold(),
            (sub_group.sub_group_code or "").strip().casefold(),
        )
        for sub_group in SubGroup.objects.all()
    }
    item_sub_group_ids = set(SubGroup.objects.values_list("id", flat=True))

    for sub_group in ProductSubGroup.objects.all():
        key = (
            sub_group.group_id,
            (sub_group.sub_group_name or "").strip().casefold(),
            (sub_group.sub_group_code or "").strip().casefold(),
        )
        is_copied_from_item_sub_group = sub_group.id in item_sub_group_ids or key in item_sub_group_keys
        sub_group.created_in_product_creation = (
            sub_group.group_id in product_group_ids and not is_copied_from_item_sub_group
        )
        sub_group.save(update_fields=["created_in_product_creation"])


class Migration(migrations.Migration):

    dependencies = [
        ("purchase_master", "0004_product_group_sub_group"),
    ]

    operations = [
        migrations.AddField(
            model_name="productgroup",
            name="created_in_product_creation",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="productsubgroup",
            name="created_in_product_creation",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(mark_product_owned_lookups, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="productgroup",
            name="created_in_product_creation",
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name="productsubgroup",
            name="created_in_product_creation",
            field=models.BooleanField(default=True),
        ),
    ]
