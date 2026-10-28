from typing import Annotated, TypeAlias
from datetime import datetime, UTC
from uuid import UUID
from annotated_types import Ge

from pydantic import Field, AliasChoices, AnyHttpUrl
from elasticsearch_pydantic import (
    BaseDocument,
    BaseInnerDocument,
    KeywordField as Keyword,
    IntegerField as Integer,
    LongField as Long,
)
from elasticsearch_dsl import (
    Date as _Date,
    RankFeature as _RankFeature,
    Keyword as _Keyword,
    Text as _Text,
    Completion as _Completion,
)

Date: TypeAlias = Annotated[
    datetime,
    _Date(
        default_timezone="UTC",
        format="strict_date_time_no_millis",
    ),
]
DefaultDate: TypeAlias = Annotated[
    Date,
    Field(default_factory=lambda: datetime.now(UTC)),
]
TextWithSuggestAndKeyword: TypeAlias = Annotated[
    str,
    _Text(
        fields={
            "suggest": _Completion(),
            "keyword": _Keyword(),
        }
    ),
]
RankFeature: TypeAlias = Annotated[
    float,
    Ge(0),
    _RankFeature(positive_score_impact=True),
]


class UuidBaseDocument(BaseDocument):
    id: UUID = Field(  # type: ignore[override]
        default_factory=UUID,
        validation_alias=AliasChoices("_id", "id"),
        serialization_alias="_id",
    )


class InnerProvider(BaseInnerDocument):
    id: UUID
    domain: Keyword
    url_path_prefix: Keyword
    priority: RankFeature | None = None


class InnerCapture(BaseInnerDocument):
    id: UUID
    url: AnyHttpUrl
    timestamp: Date
    status_code: Integer | None = None
    digest: Keyword
    mimetype: Keyword | None = None


class WarcLocation(BaseInnerDocument):
    file: Keyword
    offset: Long
    length: Long


class Serp(UuidBaseDocument):
    last_modified: DefaultDate
    # archive: InnerArchive
    provider: InnerProvider
    capture: InnerCapture
    url_query: TextWithSuggestAndKeyword
    # url_query_parser: InnerParser | None = None
    # url_page: Integer | None = None
    # url_page_parser: InnerParser | None = None
    # url_offset: Integer | None = None
    # url_offset_parser: InnerParser | None = None
    # url_language: LanguageAlpha2Keyword | None = None
    # url_language_parser: InnerParser | None = None
    warc_location: WarcLocation | None = None
    # warc_downloader: InnerDownloader | None = None
    warc_query: TextWithSuggestAndKeyword | None = None
    # warc_query_parser: InnerParser | None = None
    # warc_organic_results: Sequence[OrganicResultId] | None = None
    # warc_organic_results_parser: InnerParser | None = None
    # warc_features: Sequence[FeatureId] | None = None
    # warc_features_parser: InnerParser | None = None

    # @computed_field  # type: ignore[prop-decorator]
    # @property
    # def memento_url(self) -> AnyHttpUrl:
    #     return AnyHttpUrl(
    #         f"{self.archive.memento_api_url}/"
    #         f"{self.capture.timestamp.astimezone(UTC).strftime('%Y%m%d%H%M%S')}/"
    #         f"{self.capture.url}"
    #     )

    # class Index:
    #     settings = {
    #         "number_of_shards": 40,
    #         "number_of_replicas": 2,
    #     }
