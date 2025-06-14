import subprocess
import sys

import pytest


@pytest.mark.django_db
def test_all_models_have_migrations():
    """Fail if there are model changes without migrations."""
    result = subprocess.run(
        [sys.executable, "manage.py", "makemigrations", "--check", "--dry-run"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "There are model changes not reflected in migrations:\n"
        + result.stdout
        + result.stderr
    )
