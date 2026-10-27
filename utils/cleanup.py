import logging
import os
import time
from pathlib import Path

import config

logger = logging.getLogger(__name__)


def cleanup_expired_files(max_age_hours: int = 24, dry_run: bool = False) -> dict:
    """
    Scans upload and report directories and removes files older than max_age_hours.
    Returns a summary dictionary of deleted files and reclaimed bytes.
    """
    cutoff_time = time.time() - (max_age_hours * 3600)
    directories = [Path(config.UPLOAD_FOLDER), Path(config.REPORT_FOLDER)]

    stats = {"files_scanned": 0, "files_removed": 0, "bytes_reclaimed": 0, "errors": []}

    for target_dir in directories:
        if not target_dir.exists():
            continue

        for file_path in target_dir.iterdir():
            if not file_path.is_file():
                continue

            stats["files_scanned"] += 1
            try:
                mtime = file_path.stat().st_mtime
                file_size = file_path.stat().st_size

                if mtime < cutoff_time:
                    if not dry_run:
                        file_path.unlink()
                        logger.info(f"Removed expired file: {file_path}")
                    stats["files_removed"] += 1
                    stats["bytes_reclaimed"] += file_size
            except Exception as e:
                err_msg = f"Failed to delete {file_path}: {e}"
                logger.error(err_msg)
                stats["errors"].append(err_msg)

    return stats


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Executing automated upload and report file cleanup...")
    results = cleanup_expired_files(max_age_hours=24)
    print(
        f"Cleanup finished: {results['files_removed']} files removed, {results['bytes_reclaimed']} bytes reclaimed."
    )
