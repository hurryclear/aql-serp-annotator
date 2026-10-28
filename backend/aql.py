"""read SERPs from AQL: metadata from Elasticsearch, HTML from the S3 WARC store (ADR 0003)"""
from uuid import UUID

from warc_s3 import WarcS3Location

from config import Config
from orm import Serp
from exceptions import SerpNotFoundError, SerpHtmlUnavailableError

config = Config()


def _charset(record) -> str:
    content_type = record.http_headers.get_header("Content-Type") if record.http_headers else None
    if content_type and "charset=" in content_type.lower():
        return content_type.lower().split("charset=")[-1].split(";")[0].strip()
    return "utf-8"


def fetch_serp_html(serp_id: UUID) -> tuple[str, str]:
    """Return (html, capture_url) for one SERP.

    Raises SerpNotFoundError if the id isn't in the index, and
    SerpHtmlUnavailableError if the SERP was never archived to S3.
    S3/network failures propagate unchanged.
    """
    serp = Serp.get(
        id=str(serp_id),
        using=config.es.client,
        index=config.es.index_serps,
        ignore=404,
    )
    if serp is None:
        raise SerpNotFoundError(f"{serp_id} not found in AQL")
    if serp.warc_location is None:
        raise SerpHtmlUnavailableError(f"{serp_id} has no warc_location")

    location = WarcS3Location(
        key=serp.warc_location.file,
        offset=serp.warc_location.offset,
        length=serp.warc_location.length,
    )
    with config.s3.warc_s3_store.read(location) as record:
        body = record.content_stream().read()
        charset = _charset(record)

    try:
        html = body.decode(charset, errors="replace")
    except LookupError:  # unknown charset name in the header
        html = body.decode("utf-8", errors="replace")
    return html, str(serp.capture.url)