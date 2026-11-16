import json
import random
from uuid import UUID

from config import config
from utils.html_utils import NODE_ATTR, clean_serp_html, number_elements
from utils.resource_json_loader import PROVIDERS, LANGUAGES

from src.database.core import SessionLocal
from src.serp.model import Serp, SerpSimple
from src.entities.annotation import Annotation

from exceptions import UnknownOptionError


def build_snapshot(raw_html: str, capture_url: str) -> str:
    """The snapshot of an archived SERP: cleaned for display, every element numbered."""
    return number_elements(clean_serp_html(raw_html, base_url=capture_url))


def save_serp_html(serp_id: UUID, html: str) -> None:
    serp_path = config.persistence.serp_path / f"{serp_id}.html"
    serp_path.write_text(html, encoding="utf-8")


def get_serp_html(serp_id: UUID) -> str | None:
    serp_path = config.persistence.serp_path / f"{serp_id}.html"
    if not serp_path.exists():
        return None
    html = serp_path.read_text(encoding="utf-8")
    # cached before elements were numbered: number it now, once, so it can be marked
    if NODE_ATTR not in html:
        html = number_elements(html)
        save_serp_html(serp_id, html)
    return html


def _to_serp(record: dict) -> Serp:
    """One line of the question file as a Serp. The file calls the id "serp", the model "serp_id"."""
    return Serp(
        serp_id=record["serp"],
        query=record["query"],
        provider=record["provider"],
        year=record["year"],
        language=record["language"],
        question_type=record["question_type"],
        matched=record["matched"],
    )


def get_question_serp_by_id(serp_id: UUID) -> Serp | None:
    with config.question_serps_path.open("r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            if UUID(record["serp"]) == serp_id:
                return _to_serp(record)
    return None


def _get_annotated_question_serps() -> set[UUID]:
    annotated_serps: set[UUID] = set()
    with SessionLocal() as session:
        annotations = session.query(Annotation).all()
        for annotation in annotations:
            annotated_serps.add(annotation.serp_id)
    return annotated_serps


def search_question_serps_by_ply(
    provider: str,
    language: str,
    year: int
) -> list[Serp]:
    serp_list: list[Serp] = []
    with config.question_serps_path.open("r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            if (
                record["provider"] == provider
                and record["language"] == language
                and record["year"] == year
            ):
                serp_list.append(_to_serp(record))
    return serp_list


def list_serps(
    provider_name: str,
    language_name: str,
    year: int,
    annotated: bool | None = None,
    limit: int = 25,
) -> list[SerpSimple]:

    provider = PROVIDERS.get(provider_name.lower())
    # the question file stores language names ("simplified_chinese"), not codes
    language = language_name.lower().replace(" ", "_")

    if provider is None:
        raise UnknownOptionError(f"unknown provider {provider_name!r}")
    if language not in LANGUAGES:
        raise UnknownOptionError(f"unknown language {language_name!r}")

    # 1. get all question SERPs for the given provider, language, and year
    serp_list = search_question_serps_by_ply(provider, language, year)

    # 2. filter by annotated if specified
    annotated_serps = _get_annotated_question_serps()
    if annotated is not None:
        if annotated:
            serp_list = [serp for serp in serp_list if serp.serp_id in annotated_serps]
        else:
            serp_list = [serp for serp in serp_list if serp.serp_id not in annotated_serps]

    # 3. pick at most `limit` at random, so two annotators with the same choices
    #    rarely get the same SERPs (the first lines of the file would always be the same)
    serp_list = random.sample(serp_list, min(limit, len(serp_list)))

    # 4. convert to SerpSimple objects
    serp_simple_list = [SerpSimple(
            serp_id=serp.serp_id,
            query=serp.query
        ) for serp in serp_list]

    return serp_simple_list
