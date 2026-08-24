from __future__ import annotations

import json
import logging
import tempfile
import webbrowser
from collections import Counter
from pathlib import Path

from lxml import etree, html

from docs.adr.src.parser.models import FeatureBlock
from docs.adr.src.parser.utils.html_utils import normalize_html, parse_with_xpath

logger = logging.getLogger(__name__)


def validate_xpath_syntax(xpath: str) -> dict[str, bool | str | None]:
    try:
        etree.XPath(xpath)
        return {"valid": True, "message": "Valid XPath syntax", "error": None}
    except etree.XPathSyntaxError as e:
        return {"valid": False, "message": "Invalid XPath syntax", "error": str(e)}
    except Exception as e:
        return {"valid": False, "message": "XPath validation failed", "error": str(e)}


def extract_by_xpath(html_str: str, xpath: str) -> list[str]:
    try:
        parser = etree.HTMLParser()
        tree = etree.fromstring(html_str.encode('utf-8'), parser)
        return [etree.tostring(elem, encoding='unicode', method='html') for elem in tree.xpath(xpath)]
    except Exception as e:
        logger.error("Error extracting by XPath: %s", e)
        return []


def count_xpath_matches(html_str: str, xpath: str) -> int:
    try:
        parser = etree.HTMLParser()
        tree = etree.fromstring(html_str.encode('utf-8'), parser)
        return len(tree.xpath(xpath))
    except Exception:
        return 0


def test_xpath_match(html_str: str, xpath: str, marked_element_html: str) -> dict[str, bool | str | None]:
    try:
        parser = etree.HTMLParser()
        tree = etree.fromstring(html_str.encode('utf-8'), parser)
        xpath_results = tree.xpath(xpath)

        if not xpath_results:
            return {"match": False, "xpath_html": None, "message": "XPath returned no results", "error": None}

        xpath_html = etree.tostring(xpath_results[0], encoding='unicode', method='html')
        match = normalize_html(marked_element_html) == normalize_html(xpath_html)
        return {
            "match": match,
            "xpath_html": xpath_html,
            "message": "XPath extracts same content" if match else "Content mismatch",
            "error": None,
        }
    except etree.XPathEvalError as e:
        return {"match": False, "xpath_html": None, "message": "Invalid XPath syntax", "error": str(e)}
    except Exception as e:
        return {"match": False, "xpath_html": None, "message": "Test failed", "error": str(e)}


_TEMPLATE_DIR = Path(__file__).parent / "templates"
_COMPARISON_HTML_TEMPLATE = (_TEMPLATE_DIR / "comparison_single.html").read_text(encoding="utf-8")
_GT_COMPARISON_MULTI_TEMPLATE = (_TEMPLATE_DIR / "comparison_multi.html").read_text(encoding="utf-8")


def compare_with_ground_truth(
    features: list[FeatureBlock],
    gt_dir: Path,
) -> dict[str, list | dict]:
    by_serp: dict[str, list[FeatureBlock]] = {}
    for f in features:
        by_serp.setdefault(str(f.serp_id), []).append(f)

    serp_ids = set(by_serp.keys())

    for gt_file in gt_dir.glob("*.html"):
        serp_ids.add(gt_file.stem)

    results: list[dict] = []
    summary = Counter()

    for serp_id in sorted(serp_ids):
        gt_path = gt_dir / f"{serp_id}.html"
        if not gt_path.exists():
            for f in by_serp.get(serp_id, []):
                results.append({"feature_id": str(f.id), "serp_id": serp_id,
                                "category": f.category, "status": "no_ground_truth",
                                "xpath": f.xpath})
                summary["no_ground_truth"] += 1
            continue

        gt_html = gt_path.read_text(encoding="utf-8")
        gt_elements = _extract_gt_elements(gt_html)

        gt_remaining: dict[str, list[str]] = {}
        for cat, norm in gt_elements:
            gt_remaining.setdefault(cat, []).append(norm)

        for f in by_serp.get(serp_id, []):
            if not f.content:
                results.append({"feature_id": str(f.id), "serp_id": serp_id,
                                "category": f.category, "status": "extraction_failed",
                                "xpath": f.xpath})
                summary["extraction_failed"] += 1
                continue

            normalized_ext = normalize_html(f.content)
            gt_cat_list = gt_remaining.get(f.category, [])

            matched_idx = None
            for i, gt_norm in enumerate(gt_cat_list):
                if gt_norm == normalized_ext:
                    matched_idx = i
                    break

            if matched_idx is not None:
                gt_cat_list.pop(matched_idx)
                results.append({"feature_id": str(f.id), "serp_id": serp_id,
                                "category": f.category, "status": "matched",
                                "xpath": f.xpath})
                summary["matched"] += 1
            elif gt_cat_list:
                results.append({"feature_id": str(f.id), "serp_id": serp_id,
                                "category": f.category, "status": "mismatched",
                                "xpath": f.xpath})
                summary["mismatched"] += 1
            else:
                results.append({"feature_id": str(f.id), "serp_id": serp_id,
                                "category": f.category, "status": "extra",
                                "xpath": f.xpath})
                summary["extra"] += 1

        for cat, remaining in gt_remaining.items():
            for _ in remaining:
                results.append({"feature_id": None, "serp_id": serp_id,
                                "category": cat, "status": "missing",
                                "xpath": None})
                summary["missing"] += 1

    return {"results": results, "summary": dict(summary)}


def _extract_gt_elements(gt_html: str) -> list[tuple[str, str]]:
    tree = html.fromstring(gt_html)
    elements = tree.xpath("//*[contains(@class, 'fb') and @data-fb-category]")
    out = []
    for el in elements:
        category = el.get("data-fb-category")
        el_html = html.tostring(el, encoding="unicode", method="html")
        out.append((category, normalize_html(el_html)))
    return out


def _sanitize_for_local_display(tree) -> None:
    for script in tree.xpath("//script"):
        script.getparent().remove(script)
    for meta in tree.xpath("//meta[@http-equiv]"):
        if (meta.get("http-equiv") or "").lower() in ("refresh", "location"):
            meta.getparent().remove(meta)
    for noscript in tree.xpath("//noscript"):
        noscript.getparent().remove(noscript)
    for base in tree.xpath("//base"):
        base.getparent().remove(base)


_STATUS_COLORS = {
    "matched": ("#4caf50", "#e8f5e9"),
    "mismatched": ("#e53935", "#ffebee"),
    "missing": ("#7b1fa2", "#f3e5f5"),
    "extra": ("#ff9800", "#fff3e0"),
    "extraction_failed": ("#795548", "#efebe9"),
}


def _highlight_gt_by_status(gt_html: str, problems_for_serp: list[dict]) -> str:
    tree = html.fromstring(gt_html)
    _sanitize_for_local_display(tree)
    gt_elements = tree.xpath("//*[contains(@class, 'fb') and @data-fb-category]")

    mismatched_counts: Counter = Counter()
    missing_counts: Counter = Counter()
    for p in problems_for_serp:
        if p["status"] == "mismatched":
            mismatched_counts[p["category"]] += 1
        elif p["status"] == "missing":
            missing_counts[p["category"]] += 1

    gt_cat_counts: Counter = Counter()
    for el in gt_elements:
        gt_cat_counts[el.get("data-fb-category")] += 1

    category_status_queue: dict[str, list[str]] = {}
    for cat in gt_cat_counts:
        statuses = (
            ["matched"] * max(0, gt_cat_counts[cat] - mismatched_counts[cat] - missing_counts[cat])
            + ["mismatched"] * mismatched_counts[cat]
            + ["missing"] * missing_counts[cat]
        )
        category_status_queue[cat] = statuses

    category_idx: Counter = Counter()
    for el in gt_elements:
        cat = el.get("data-fb-category")
        idx = category_idx[cat]
        category_idx[cat] += 1
        queue = category_status_queue.get(cat, [])
        status = queue[idx] if idx < len(queue) else "matched"
        border_color, bg_color = _STATUS_COLORS.get(status, _STATUS_COLORS["matched"])

        el.set("style", f"border:4px solid {border_color}!important; background:{bg_color}!important; padding:8px!important; margin:4px!important;")
        marker = html.Element("div")
        marker.set("style", f"background:{border_color}!important; color:white!important; padding:4px 10px!important; margin:0 0 5px 0!important; font-size:12px!important; font-weight:bold!important;")
        marker.text = f"[{status.upper()}] {cat}"
        el.insert(0, marker)

    return html.tostring(tree, encoding="unicode", method="html", doctype="<!DOCTYPE html>")


def _highlight_extraction_by_status(
    raw_html: str, features_for_serp: list[FeatureBlock], problems_for_serp: list[dict],
) -> str:
    tree = html.fromstring(raw_html)
    _sanitize_for_local_display(tree)

    feature_status: dict[str, str] = {}
    for p in problems_for_serp:
        if p["feature_id"]:
            feature_status[p["feature_id"]] = p["status"]

    highlighted_els: set[int] = set()

    for feat in features_for_serp:
        if not feat.xpath:
            continue
        status = feature_status.get(str(feat.id), "matched")
        try:
            elements = tree.xpath(feat.xpath)
        except Exception:
            continue

        normalized_feat = normalize_html(feat.content) if feat.content else None

        for el in elements:
            el_id = id(el)
            if el_id in highlighted_els:
                continue

            if normalized_feat and len(elements) > 1:
                el_html = html.tostring(el, encoding="unicode", method="html")
                if normalize_html(el_html) != normalized_feat:
                    continue

            highlighted_els.add(el_id)
            border_color, bg_color = _STATUS_COLORS.get(status, _STATUS_COLORS["matched"])
            el.set("style", f"border:4px solid {border_color}!important; background:{bg_color}!important; padding:8px!important; margin:4px!important;")
            marker = html.Element("div")
            marker.set("style", f"background:{border_color}!important; color:white!important; padding:4px 10px!important; margin:0 0 5px 0!important; font-size:12px!important; font-weight:bold!important;")
            marker.text = f"[{status.upper()}] {feat.category}"
            el.insert(0, marker)

    return html.tostring(tree, encoding="unicode", method="html", doctype="<!DOCTYPE html>")


def open_gt_comparison_view(
    problems: list[dict],
    features: list[FeatureBlock],
    raw_html_cache: dict[str, str],
    gt_dir: Path,
    label: str,
) -> None:
    problems_by_serp: dict[str, list[dict]] = {}
    for p in problems:
        problems_by_serp.setdefault(p["serp_id"], []).append(p)

    features_by_serp: dict[str, list[FeatureBlock]] = {}
    for f in features:
        features_by_serp.setdefault(str(f.serp_id), []).append(f)

    problem_serp_ids = sorted(problems_by_serp.keys())

    temp_dir = Path(tempfile.mkdtemp(prefix="gt_comparison_"))
    entries = []

    for serp_id in problem_serp_ids:
        gt_path = gt_dir / f"{serp_id}.html"
        if not gt_path.exists():
            continue

        gt_html_src = gt_path.read_text(encoding="utf-8")
        serp_problems = problems_by_serp[serp_id]
        serp_features = features_by_serp.get(serp_id, [])

        highlighted_gt = _highlight_gt_by_status(gt_html_src, serp_problems)
        gt_file = temp_dir / f"{serp_id}_gt.html"
        gt_file.write_text(highlighted_gt, encoding="utf-8")

        raw = raw_html_cache.get(serp_id)
        if raw:
            highlighted_ext = _highlight_extraction_by_status(raw, serp_features, serp_problems)
        else:
            highlighted_ext = "<html><body><p>Could not fetch raw SERP HTML</p></body></html>"
        ext_file = temp_dir / f"{serp_id}_ext.html"
        ext_file.write_text(highlighted_ext, encoding="utf-8")

        statuses = Counter(p["status"] for p in serp_problems)
        entries.append({
            "serp_id": serp_id,
            "gt_path": str(gt_file),
            "ext_path": str(ext_file),
            "statuses": dict(statuses),
            "problems": serp_problems,
        })

    if not entries:
        return

    page_html = (_GT_COMPARISON_MULTI_TEMPLATE
                 .replace("{{ENTRIES_JSON}}", json.dumps(entries))
                 .replace("{{LABEL}}", label))
    page_file = temp_dir / "comparison.html"
    page_file.write_text(page_html, encoding="utf-8")

    logger.info("Opening GT comparison view: file://%s", page_file)
    webbrowser.open(f"file://{page_file}")



__all__ = [
    "validate_xpath_syntax",
    "extract_by_xpath",
    "count_xpath_matches",
    "test_xpath_match",
    "compare_with_ground_truth",
    "open_gt_comparison_view",
]
