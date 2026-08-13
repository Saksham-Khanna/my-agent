import pytest
from dataclasses import FrozenInstanceError
from app.core.models import Attachment, AttachmentStorage
from app.core.attachments import (
    filter_attachments_by_mime_prefix,
    filter_attachments_by_exact_mime,
    get_first_attachment_by_mime_prefix,
)

def test_attachment_inline_validation():
    # Valid INLINE with data_b64
    att1 = Attachment(id="1", mime_type="image/png", storage=AttachmentStorage.INLINE, data_b64="abc")
    assert att1.data_b64 == "abc"

    # Valid INLINE with content
    att2 = Attachment(id="2", mime_type="text/plain", storage=AttachmentStorage.INLINE, content="hello")
    assert att2.content == "hello"

    # Invalid INLINE without data_b64 or content
    with pytest.raises(ValueError, match="requires 'data_b64' or 'content'"):
        Attachment(id="3", mime_type="image/png", storage=AttachmentStorage.INLINE)

def test_attachment_path_validation():
    # Valid PATH
    att = Attachment(id="1", mime_type="application/pdf", storage=AttachmentStorage.PATH, path="/path/to/doc.pdf")
    assert att.path == "/path/to/doc.pdf"

    # Invalid PATH without path
    with pytest.raises(ValueError, match="requires 'path'"):
        Attachment(id="2", mime_type="application/pdf", storage=AttachmentStorage.PATH)

def test_attachment_url_validation():
    # Valid URL
    att = Attachment(id="1", mime_type="image/jpeg", storage=AttachmentStorage.URL, url="https://example.com/img.jpg")
    assert att.url == "https://example.com/img.jpg"

    # Invalid URL without url
    with pytest.raises(ValueError, match="requires 'url'"):
        Attachment(id="2", mime_type="image/jpeg", storage=AttachmentStorage.URL)

def test_attachment_immutability():
    att = Attachment(id="1", mime_type="text/plain", storage=AttachmentStorage.INLINE, content="text")
    with pytest.raises(Exception):  # FrozenInstanceError
        att.content = "new text"  # type: ignore

def test_mime_helpers():
    img1 = Attachment(id="1", mime_type="image/png", storage=AttachmentStorage.INLINE, data_b64="img1")
    img2 = Attachment(id="2", mime_type="image/jpeg", storage=AttachmentStorage.INLINE, data_b64="img2")
    doc = Attachment(id="3", mime_type="application/pdf", storage=AttachmentStorage.PATH, path="/doc.pdf")
    txt = Attachment(id="4", mime_type="text/plain", storage=AttachmentStorage.INLINE, content="hello")

    attachments = [img1, img2, doc, txt]

    images = filter_attachments_by_mime_prefix(attachments, "image/")
    assert len(images) == 2
    assert images == [img1, img2]

    pdfs = filter_attachments_by_exact_mime(attachments, "application/pdf")
    assert len(pdfs) == 1
    assert pdfs[0] == doc

    first_image = get_first_attachment_by_mime_prefix(attachments, "image/")
    assert first_image == img1

    first_audio = get_first_attachment_by_mime_prefix(attachments, "audio/")
    assert first_audio is None
