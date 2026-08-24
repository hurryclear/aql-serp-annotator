import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=False)
load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env.project", override=False)

PROJECT_ROOT = Path(__file__).parent.parent.parent
# user can set data output dir, and it is $PROJECT_ROOT by default
DATA_OUTPUT_BASE = Path(os.getenv('AQLQA_DATA_OUTPUT', str(PROJECT_ROOT)))

# TODO Add ceph as base

def detect_environment() -> str:
    env = os.getenv('AQLQA_ENVIRONMENT', 'dev').lower()
    return env if env in ('test', 'dev', 'prod') else 'dev'


def make_pyl(provider: str, year: int, language: str) -> str:
    return f"{provider}-{year}-{language}"


def make_pl(provider: str, language: str) -> str:
    return f"{provider}-{language}"


class DataPaths:
    @classmethod
    def get_base(cls, env: str | None = None) -> Path:
        e = env or detect_environment()
        return DATA_OUTPUT_BASE / "data" / f"data-{e}"

    @classmethod
    def get_annotation_dir(
        cls, env: str | None = None,
    ) -> Path:
        return cls.get_base(env) / "annotation" / "qserp"

    @classmethod
    def get_extraction_dir(
        cls,
        mode: str,  # "gt" or "prod"
        env: str | None = None,
    ) -> Path:
        return cls.get_base(env) / "extraction" / mode

    @classmethod
    def get_ground_truth_serp_dir(
        cls, env: str | None = None,
    ) -> Path:
        return cls.get_base(env) / "ground-truth-serp"

    @classmethod
    def get_qserp_ids_dir(
        cls,
        mode: str,  # "gt" or "prod"
        env: str | None = None,
    ) -> Path:
        return cls.get_base(env) / "qserp-ids" / mode

    @classmethod
    def get_ground_truth_dir(
        cls, env: str | None = None,
    ) -> Path:
        return cls.get_base(env) / "ground-truth-serp"

    @classmethod
    def get_extraction_pyl_dir(
        cls, mode: str,
        provider: str, year: int, language: str,
        env: str | None = None,
    ) -> Path:
        pyl = make_pyl(provider, year, language)
        return cls.get_extraction_dir(mode, env) / pyl

    @classmethod
    def get_qserp_ids_file(
        cls, mode: str,
        provider: str, year: int, language: str,
        env: str | None = None,
    ) -> Path:
        pyl = make_pyl(provider, year, language)
        return cls.get_qserp_ids_dir(mode, env) / f"{pyl}.json"

    @classmethod
    def get_ground_truth_pyl_dir(
        cls,
        provider: str, year: int, language: str,
        env: str | None = None,
    ) -> Path:
        pyl = make_pyl(provider, year, language)
        return cls.get_ground_truth_dir(env) / f"{pyl}"

    @classmethod
    def get_extraction_pl_dir(
        cls, mode: str,
        provider: str, language: str,
        env: str | None = None,
    ) -> Path:
        pl = make_pl(provider, language)
        return cls.get_extraction_dir(mode, env) / pl

    @classmethod
    def discover_serp_id_files(
        cls, mode: str, provider: str,
        year: int | None = None,
        language: str | None = None,
        env: str | None = None,
    ) -> list[tuple[int, str, Path]]:
        ids_dir = cls.get_qserp_ids_dir(mode, env)
        results = []
        for f in sorted(ids_dir.glob(f"{provider}-*-*.json")):
            parts = f.stem.split("-")
            if len(parts) < 3:
                continue
            f_year, f_lang = int(parts[1]), parts[2]
            if year and f_year != year:
                continue
            if language and f_lang != language:
                continue
            results.append((f_year, f_lang, f))
        return sorted(results)

    @classmethod
    def get_ground_truth_jsonl(
        cls,
        provider: str, year: int, language: str,
        env: str | None = None,
    ) -> Path:
        pyl = make_pyl(provider, year, language)
        return cls.get_ground_truth_dir(env) / f"{pyl}-qphrase.jsonl"
