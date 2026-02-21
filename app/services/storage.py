"""Supabase Storage operations for screenshots and PDFs."""

from __future__ import annotations

import os
import uuid

from app.services.supabase_client import get_supabase


def upload_file(
    bucket: str,
    local_path: str,
    remote_folder: str = "",
) -> str:
    """Upload a local file to Supabase Storage and return the public URL.

    Args:
        bucket: Storage bucket name ('screenshots' or 'reports').
        local_path: Path to the local file.
        remote_folder: Optional folder prefix in the bucket.

    Returns:
        Public URL of the uploaded file.
    """
    sb = get_supabase()
    filename = os.path.basename(local_path)
    ext = os.path.splitext(filename)[1]
    unique_name = f"{uuid.uuid4().hex}{ext}"
    remote_path = f"{remote_folder}/{unique_name}" if remote_folder else unique_name

    with open(local_path, "rb") as f:
        content_type = "image/png" if ext == ".png" else "application/pdf" if ext == ".pdf" else "application/octet-stream"
        sb.storage.from_(bucket).upload(
            path=remote_path,
            file=f.read(),
            file_options={"content-type": content_type},
        )

    public_url = sb.storage.from_(bucket).get_public_url(remote_path)
    return public_url


def upload_screenshot(local_path: str, project_id: str) -> str:
    """Upload a screenshot and return its public URL."""
    return upload_file("screenshots", local_path, remote_folder=project_id)


def upload_report_pdf(local_path: str, project_id: str) -> str:
    """Upload a PDF report and return its public URL."""
    return upload_file("reports", local_path, remote_folder=project_id)
