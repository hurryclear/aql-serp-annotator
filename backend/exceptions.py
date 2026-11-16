class AnnotationExistsError(Exception):
    pass


class CartNotFoundError(Exception):
    """The cart_id an annotation points at doesn't exist."""
    pass


class SerpNotFoundError(Exception):
    """The serp_id doesn't exist in AQL's Elasticsearch index."""
    pass


class SerpHtmlUnavailableError(Exception):
    """The SERP exists, but has no warc_location (not archived to S3 yet)."""
    pass

class UnknownOptionError(Exception):
    """The user provided an unknown option (e.g. provider, language, year)."""
    pass