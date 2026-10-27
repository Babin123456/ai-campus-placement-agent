import os
import sys
import tempfile
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from utils.cleanup import cleanup_expired_files


def test_cleanup_expired_files(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp_upload, tempfile.TemporaryDirectory() as tmp_report:
        upload_path = Path(tmp_upload)
        report_path = Path(tmp_report)

        monkeypatch.setattr(config, "UPLOAD_FOLDER", upload_path)
        monkeypatch.setattr(config, "REPORT_FOLDER", report_path)

        # Create fresh file (mtime = now)
        fresh_file = upload_path / "fresh_resume.pdf"
        fresh_file.write_text("fresh content")

        # Create expired file (mtime = 48 hours ago)
        expired_file = report_path / "old_report.pdf"
        expired_file.write_text("old report content")
        past_time = time.time() - (48 * 3600)
        os.utime(expired_file, (past_time, past_time))

        stats = cleanup_expired_files(max_age_hours=24)

        assert stats["files_scanned"] == 2
        assert stats["files_removed"] == 1
        assert not expired_file.exists()
        assert fresh_file.exists()
