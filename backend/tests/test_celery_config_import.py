from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path


class CeleryConfigImportTests(unittest.TestCase):
    def test_celery_import_works_without_database_and_s3_env_vars(self) -> None:
        backend_dir = Path(__file__).resolve().parents[1]
        env = os.environ.copy()
        env.update(
            {
                "SECRET_KEY": "test-secret",
                "ENCRYPTION_KEY": "QhIFvEu7FFM7jv9Nlk5t4z4N4HiQf0yxvWvW9tZZxFc=",
                "OPENAI_API_KEY": "test-openai-key",
            }
        )
        for key in ("DATABASE_URL", "S3_BUCKET", "S3_ACCESS_KEY", "S3_SECRET_KEY"):
            env.pop(key, None)

        result = subprocess.run(
            [sys.executable, "-c", "from app.workers.celery_app import celery_app; print(celery_app.main)"],
            cwd=backend_dir,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(
            result.returncode,
            0,
            msg=f"Expected Celery app import to succeed, got stderr:\n{result.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
