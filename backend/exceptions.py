class AnnotationExistsError(Exception):
    pass


class SerpNotFoundError(Exception):
    """The serp_id doesn't exist in AQL's Elasticsearch index."""
    pass


class SerpHtmlUnavailableError(Exception):
    """The SERP exists, but has no warc_location (not archived to S3 yet)."""
    pass