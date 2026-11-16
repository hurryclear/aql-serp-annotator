class AnnotationExistsError(Exception):
    pass


class InvalidMarkError(Exception):
    """A feature's marked element can't be written into the SERP's snapshot."""
    pass


class SerpNotQuestionSerpError(Exception):
    """The serp_id isn't in the question SERPs file, so it can't be annotated."""
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