#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path


def add_repo_venv_to_path():
    """Allow `python manage.py` to use the repo's shared virtualenv."""
    backend_root = Path(__file__).resolve().parents[1]
    venv_root = backend_root / ".venv"

    candidate_paths = [venv_root / "Lib" / "site-packages"]
    candidate_paths.extend(sorted((venv_root / "lib").glob("python*/site-packages")))

    for site_packages in candidate_paths:
        if site_packages.exists():
            sys.path.insert(0, str(site_packages))
            return


def main():
    """Run administrative tasks."""
    project_dir = Path(__file__).resolve().parent
    if str(project_dir) not in sys.path:
        sys.path.insert(0, str(project_dir))

    add_repo_venv_to_path()

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TASK_MANAGEMENT.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
