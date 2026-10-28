from functools import cached_property
from dotenv import find_dotenv
from typing import Annotated
from pathlib import Path
from elasticsearch import Elasticsearch
from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict
# from warc_cache import WarcCacheStore
from warc_s3 import WarcS3Store
from sqlalchemy import create_engine, event, Engine


class EsConfig(BaseSettings):
    model_config = SettingsConfigDict(frozen=True)

    host: str = "localhost"
    port: int = 9200
    username: str | None = None
    password: str | None = None
    api_key: str | None = None
    index_serps: str = "serps"
    # index_organic_results: str = "organic_results"
    # index_features: str = "features"
    max_retries: int = 5
    # bulk_chunk_size: int = 500
    # bulk_max_chunk_bytes: int = 100 * 1024 * 1024
    # bulk_initial_backoff: int = 2
    # bulk_max_backoff: int = 60

    @cached_property
    def client(self) -> Elasticsearch:
        return Elasticsearch(
            hosts=f"https://{self.host}:{self.port}",
            api_key=self.api_key,
            http_auth=(self.username, self.password)
            if self.api_key is None
            and self.username is not None
            and self.password is not None
            else None,
            timeout=60,
            max_retries=self.max_retries,
            retry_on_status=(502, 503, 504),
            retry_on_timeout=True,
        )


class S3Config(BaseSettings):
    model_config = SettingsConfigDict(frozen=True)

    endpoint_url: str | None = None
    access_key: str | None = None
    secret_key: str | None = None
    bucket_name: str = "serps"

    @cached_property
    def warc_s3_store(self) -> WarcS3Store:
        return WarcS3Store(
            endpoint_url=self.endpoint_url,
            access_key=self.access_key,
            secret_key=self.secret_key,
            bucket_name=self.bucket_name,
            max_file_size=1_000_000_000,
            quiet=False,
        )

    # @cached_property
    # def warc_store(self) -> WarcStore:
    #     return WarcS3StoreWrapper(self.warc_s3_store)


# local data store
class PersistenceConfig(BaseSettings):
    model_config = SettingsConfigDict(frozen=True)
    data_path: Path = Path(__file__).resolve().parent.parent / "data"

    @cached_property
    def serp_path(self) -> Path:
        serp_path = self.data_path / "annotated_serps"
        serp_path.mkdir(parents=True, exist_ok=True)
        return serp_path

    @cached_property
    def sqlite_path(self) -> Path:
        self.data_path.mkdir(parents=True, exist_ok=True)
        return self.data_path / "annotator.db"

    @cached_property
    def sqlite_engine(self) -> Engine:
        engine = create_engine(url=f"sqlite:///{self.sqlite_path}")
        @event.listens_for(engine, "connect")
        def enable_foreign_keys(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        return engine


class ManifestConfig(BaseSettings):
    model_config = SettingsConfigDict(frozen=True)
    file_name: str = "serps_manifest.jsonl"


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        frozen=True,
        env_file=find_dotenv(),
        env_nested_delimiter="_",
        env_nested_max_split=1,
    )

    es: Annotated[
        EsConfig,
        Field(
            validation_alias=AliasChoices("es", "elasticsearch"),
        ),
    ] = EsConfig()
    s3: S3Config = S3Config()
    persistence: PersistenceConfig = PersistenceConfig()
    manifest: ManifestConfig = ManifestConfig()

    @cached_property
    def manifest_path(self) -> Path:
        return self.persistence.data_path / self.manifest.file_name

    # http: HttpConfig = HttpConfig()
    # warc_cache: WarcCacheConfig = WarcCacheConfig()


# the one shared instance: import this instead of calling Config() again, so
# cached clients (sqlite engine, ES, S3) are created once per process
config = Config()