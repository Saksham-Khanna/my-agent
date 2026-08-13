from typing import List, Optional
from app.core.models import Attachment

def filter_attachments_by_mime_prefix(attachments: List[Attachment], prefix: str) -> List[Attachment]:
    """Returns attachments whose MIME type starts with the given prefix (e.g. 'image/', 'text/')."""
    return [att for att in attachments if att.mime_type.startswith(prefix)]

def filter_attachments_by_exact_mime(attachments: List[Attachment], mime_type: str) -> List[Attachment]:
    """Returns attachments matching the exact MIME type."""
    return [att for att in attachments if att.mime_type == mime_type]

def get_first_attachment_by_mime_prefix(attachments: List[Attachment], prefix: str) -> Optional[Attachment]:
    """Returns the first attachment whose MIME type starts with the given prefix, or None."""
    for att in attachments:
        if att.mime_type.startswith(prefix):
            return att
    return None
