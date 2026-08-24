from __future__ import annotations

import json
import logging
import shutil
import webbrowser
from collections import Counter
from pathlib import Path

from flask import Flask, Response, jsonify, request
from lxml import html

from docs.adr.src.parser.models import FeatureBlock
from docs.adr.src.parser.utils.html_utils import normalize_html
from docs.adr.src.validation.validation import (
    _extract_gt_elements,
    _highlight_extraction_by_status,
    _highlight_gt_by_status,
)

logger = logging.getLogger(__name__)

_TEMPLATE_DIR = Path(__file__).parent / "templates"

_gt_dir: Path = Path()
_entries: list[dict] = []
_raw_html_cache: dict[str, str] = {}
_features_by_serp: dict[str, list[FeatureBlock]] = {}
_taxonomy: list[dict] = []
_problems_by_serp: dict[str, list[dict]] = {}
_matched_xpaths: dict[str, list[tuple[str, str]]] = {}


def _recompare_serp(serp_id: str) -> None:
    gt_path = _gt_dir / f"{serp_id}.html"
    if not gt_path.exists():
        return

    gt_html = gt_path.read_text(encoding="utf-8")
    gt_elements = _extract_gt_elements(gt_html)
    features = _features_by_serp.get(serp_id, [])

    gt_remaining: dict[str, list[str]] = {}
    for cat, norm in gt_elements:
        gt_remaining.setdefault(cat, []).append(norm)

    results: list[dict] = []

    for f in features:
        if not f.content:
            results.append({"feature_id": str(f.id), "serp_id": serp_id,
                            "category": f.category, "status": "extraction_failed",
                            "xpath": f.xpath})
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
        elif gt_cat_list:
            results.append({"feature_id": str(f.id), "serp_id": serp_id,
                            "category": f.category, "status": "mismatched",
                            "xpath": f.xpath})
        else:
            results.append({"feature_id": str(f.id), "serp_id": serp_id,
                            "category": f.category, "status": "extra",
                            "xpath": f.xpath})

    for cat, remaining in gt_remaining.items():
        for _ in remaining:
            results.append({"feature_id": None, "serp_id": serp_id,
                            "category": cat, "status": "missing",
                            "xpath": None})

    _problems_by_serp[serp_id] = [r for r in results if r["status"] != "matched"]

    for entry in _entries:
        if entry["serp_id"] == serp_id:
            all_statuses = Counter(r["status"] for r in results)
            entry["statuses"] = dict(all_statuses)
            entry["problems"] = _problems_by_serp[serp_id]
            break


def _create_app(label: str) -> Flask:
    app = Flask(__name__, template_folder=str(_TEMPLATE_DIR))

    @app.route("/")
    def index():
        template = (_TEMPLATE_DIR / "comparison_multi_edit.html").read_text(encoding="utf-8")
        page = (template
                .replace("{{ENTRIES_JSON}}", json.dumps(_entries))
                .replace("{{TAXONOMY_JSON}}", json.dumps(_taxonomy))
                .replace("{{LABEL}}", label))
        return Response(page, mimetype="text/html")

    @app.route("/gt/<serp_id>")
    def serve_gt(serp_id: str):
        gt_path = _gt_dir / f"{serp_id}.html"
        if not gt_path.exists():
            return Response("<html><body><p>GT file not found</p></body></html>", mimetype="text/html")
        gt_html = gt_path.read_text(encoding="utf-8")
        problems = _problems_by_serp.get(serp_id, [])
        highlighted = _highlight_gt_by_status(gt_html, problems)
        highlighted = highlighted.replace(
            "</head>",
            "<style>"
            ".fb { outline: 3px solid #2196F3 !important; outline-offset: 2px;"
            " background-color: rgba(33, 150, 243, 0.1) !important; cursor: pointer; }"
            ".fb:hover { outline: 2px dashed #90caf9 !important; }"
            "</style></head>",
        )
        return Response(highlighted, mimetype="text/html")

    @app.route("/ext/<serp_id>")
    def serve_ext(serp_id: str):
        raw = _raw_html_cache.get(serp_id)
        if not raw:
            return Response("<html><body><p>Extraction HTML not available</p></body></html>", mimetype="text/html")
        features = _features_by_serp.get(serp_id, [])
        problems = _problems_by_serp.get(serp_id, [])
        highlighted = _highlight_extraction_by_status(raw, features, problems)

        extra_xpaths = _matched_xpaths.get(serp_id, [])
        if extra_xpaths:
            tree = html.fromstring(highlighted)
            for xpath_expr, cat in extra_xpaths:
                try:
                    elements = tree.xpath(xpath_expr)
                except Exception:
                    continue
                for el in elements:
                    el.set("style", "border:4px solid #4caf50!important; background:#e8f5e9!important; padding:8px!important; margin:4px!important;")
                    marker = html.Element("div")
                    marker.set("style", "background:#4caf50!important; color:white!important; padding:4px 10px!important; margin:0 0 5px 0!important; font-size:12px!important; font-weight:bold!important;")
                    marker.text = f"[MATCHED via XPath] {cat}"
                    el.insert(0, marker)
            highlighted = html.tostring(tree, encoding="unicode", method="html", doctype="<!DOCTYPE html>")

        return Response(highlighted, mimetype="text/html")

    @app.route("/taxonomy")
    def serve_taxonomy():
        return jsonify(_taxonomy)

    @app.route("/problems/<serp_id>")
    def get_problems(serp_id: str):
        return jsonify(_problems_by_serp.get(serp_id, []))

    @app.route("/accept-parsed/<serp_id>", methods=["POST"])
    def accept_parsed(serp_id: str):
        gt_path = _gt_dir / f"{serp_id}.html"
        if not gt_path.exists():
            return jsonify({"success": False, "message": "GT file not found"}), 404

        data = request.get_json()
        category = data["category"]
        parser_xpath = data["parser_xpath"]

        gt_raw = gt_path.read_text(encoding="utf-8")
        tree = html.fromstring(gt_raw)

        fb_elements = tree.xpath("//*[contains(@class, 'fb') and @data-fb-category]")
        mismatched_el = None
        for el in fb_elements:
            if el.get("data-fb-category") == category:
                mismatched_el = el
                break

        if mismatched_el is None:
            return jsonify({"success": False, "message": f"No GT element with category '{category}' found"}), 400

        classes = mismatched_el.get("class", "").split()
        classes = [c for c in classes if c != "fb"]
        if classes:
            mismatched_el.set("class", " ".join(classes))
        else:
            if "class" in mismatched_el.attrib:
                del mismatched_el.attrib["class"]
        for attr in ("data-fb-category", "data-fb-index"):
            if attr in mismatched_el.attrib:
                del mismatched_el.attrib[attr]

        try:
            targets = tree.xpath(parser_xpath)
        except Exception as e:
            return jsonify({"success": False, "message": f"XPath error: {e}"}), 400

        if not targets:
            return jsonify({"success": False, "message": "Parser XPath matched no elements in GT HTML"}), 400

        new_el = targets[0]
        new_classes = new_el.get("class", "").split()
        if "fb" not in new_classes:
            new_classes.append("fb")
        new_el.set("class", " ".join(new_classes))
        new_el.set("data-fb-category", category)

        all_fb = tree.xpath("//*[contains(@class, 'fb') and @data-fb-category]")
        for i, el in enumerate(all_fb, start=1):
            el.set("data-fb-index", str(i))

        shutil.copy2(gt_path, gt_path.with_suffix(".html.bak"))
        output = html.tostring(tree, encoding="unicode", method="html", doctype="<!DOCTYPE html>")
        gt_path.write_text(output, encoding="utf-8")

        _recompare_serp(serp_id)
        return jsonify({"success": True, "message": f"Accepted parsed for '{category}'"})

    @app.route("/accept-extra/<serp_id>", methods=["POST"])
    def accept_extra(serp_id: str):
        gt_path = _gt_dir / f"{serp_id}.html"
        if not gt_path.exists():
            return jsonify({"success": False, "message": "GT file not found"}), 404

        data = request.get_json()
        category = data["category"]
        parser_xpath = data["parser_xpath"]

        gt_raw = gt_path.read_text(encoding="utf-8")
        tree = html.fromstring(gt_raw)

        try:
            targets = tree.xpath(parser_xpath)
        except Exception as e:
            return jsonify({"success": False, "message": f"XPath error: {e}"}), 400

        if not targets:
            return jsonify({"success": False, "message": "XPath matched no elements in GT HTML"}), 400

        el = targets[0]
        classes = el.get("class", "").split()
        if "fb" not in classes:
            classes.append("fb")
        el.set("class", " ".join(classes))
        el.set("data-fb-category", category)

        all_fb = tree.xpath("//*[contains(@class, 'fb') and @data-fb-category]")
        for i, fb_el in enumerate(all_fb, start=1):
            fb_el.set("data-fb-index", str(i))

        shutil.copy2(gt_path, gt_path.with_suffix(".html.bak"))
        output = html.tostring(tree, encoding="unicode", method="html", doctype="<!DOCTYPE html>")
        gt_path.write_text(output, encoding="utf-8")

        _recompare_serp(serp_id)
        return jsonify({"success": True, "message": f"Accepted extra '{category}' into GT"})

    @app.route("/test-xpath/<serp_id>", methods=["POST"])
    def test_xpath(serp_id: str):
        raw = _raw_html_cache.get(serp_id)
        if not raw:
            return jsonify({"success": False, "matched": False, "message": "No raw HTML available"}), 400

        data = request.get_json()
        xpath_expr = data["xpath"]
        category = data["category"]

        try:
            tree = html.fromstring(raw)
            targets = tree.xpath(xpath_expr)
        except Exception as e:
            return jsonify({"success": False, "matched": False, "message": f"XPath error: {e}"}), 400

        if not targets:
            return jsonify({"success": True, "matched": False, "message": "XPath matched no elements"})

        extracted_html = html.tostring(targets[0], encoding="unicode", method="html")
        normalized_ext = normalize_html(extracted_html)

        gt_path = _gt_dir / f"{serp_id}.html"
        if not gt_path.exists():
            return jsonify({"success": True, "matched": False, "message": "GT file not found"})

        gt_html = gt_path.read_text(encoding="utf-8")
        gt_elements = _extract_gt_elements(gt_html)

        for gt_cat, gt_norm in gt_elements:
            if gt_cat == category and gt_norm == normalized_ext:
                if serp_id not in _matched_xpaths:
                    _matched_xpaths[serp_id] = []
                already = any(x == xpath_expr and c == category for x, c in _matched_xpaths[serp_id])
                if not already:
                    _matched_xpaths[serp_id].append((xpath_expr, category))

                problems = _problems_by_serp.get(serp_id, [])
                for p in problems:
                    if p["status"] == "missing" and p["category"] == category:
                        p["status"] = "matched"
                        break
                _problems_by_serp[serp_id] = [p for p in problems if p["status"] != "matched"]

                for entry in _entries:
                    if entry["serp_id"] == serp_id:
                        entry["problems"] = _problems_by_serp[serp_id]
                        all_statuses = Counter(p["status"] for p in _problems_by_serp[serp_id])
                        all_statuses["matched"] = all_statuses.get("matched", 0) + 1
                        entry["statuses"] = dict(all_statuses)
                        break

                return jsonify({"success": True, "matched": True, "message": f"XPath matches GT for '{category}'"})

        return jsonify({"success": True, "matched": False,
                        "message": "XPath found an element but content does not match GT"})

    @app.route("/save-gt/<serp_id>", methods=["POST"])
    def save_gt(serp_id: str):
        gt_path = _gt_dir / f"{serp_id}.html"
        if not gt_path.exists():
            return jsonify({"success": False, "message": f"GT file not found: {serp_id}"}), 404

        data = request.get_json()
        changes = data.get("changes", [])
        if not changes:
            return jsonify({"success": True, "message": "No changes to apply"})

        try:
            _apply_changes(gt_path, changes)
        except Exception as e:
            logger.error("Failed to save GT for %s: %s", serp_id, e)
            return jsonify({"success": False, "message": str(e)}), 500

        _recompare_serp(serp_id)
        return jsonify({"success": True, "message": f"Saved {len(changes)} change(s) to {serp_id}"})

    return app


def _apply_changes(gt_path: Path, changes: list[dict]) -> None:
    raw = gt_path.read_text(encoding="utf-8")
    tree = html.fromstring(raw)

    fb_elements = tree.xpath("//*[contains(@class, 'fb') and @data-fb-index]")
    by_index: dict[str, html.HtmlElement] = {}
    for el in fb_elements:
        by_index[el.get("data-fb-index")] = el

    for change in changes:
        action = change["action"]

        if action == "update":
            el = by_index.get(change["fb_index"])
            if el is not None:
                el.set("data-fb-category", change["category"])

        elif action == "remove":
            el = by_index.get(change["fb_index"])
            if el is not None:
                classes = el.get("class", "").split()
                classes = [c for c in classes if c != "fb"]
                if classes:
                    el.set("class", " ".join(classes))
                else:
                    if "class" in el.attrib:
                        del el.attrib["class"]
                for attr in ("data-fb-category", "data-fb-index"):
                    if attr in el.attrib:
                        del el.attrib[attr]

        elif action == "add":
            xpath_expr = change.get("xpath")
            category = change.get("category")
            if xpath_expr and category:
                try:
                    targets = tree.xpath(xpath_expr)
                except Exception:
                    targets = []
                if targets:
                    el = targets[0]
                    classes = el.get("class", "").split()
                    if "fb" not in classes:
                        classes.append("fb")
                    el.set("class", " ".join(classes))
                    el.set("data-fb-category", category)

    all_fb = tree.xpath("//*[contains(@class, 'fb') and @data-fb-category]")
    for i, el in enumerate(all_fb, start=1):
        el.set("data-fb-index", str(i))

    shutil.copy2(gt_path, gt_path.with_suffix(".html.bak"))
    output = html.tostring(tree, encoding="unicode", method="html", doctype="<!DOCTYPE html>")
    gt_path.write_text(output, encoding="utf-8")
    logger.info("Saved GT: %s (%d fb elements)", gt_path.name, len(all_fb))


def start_gt_editor(
    problems: list[dict],
    features,
    raw_html_cache: dict[str, str],
    gt_dir: Path,
    label: str,
) -> None:
    global _gt_dir, _entries, _raw_html_cache, _features_by_serp, _taxonomy, _problems_by_serp, _matched_xpaths

    taxonomy_path = Path(__file__).parent.parent / "new_scripts" / "taxonomy_mapping" / "serp_features_taxonomy.json"
    with taxonomy_path.open(encoding="utf-8") as f:
        _taxonomy = json.load(f).get("categories", [])

    _gt_dir = gt_dir
    _raw_html_cache = dict(raw_html_cache)
    _matched_xpaths = {}

    _problems_by_serp = {}
    for p in problems:
        _problems_by_serp.setdefault(p["serp_id"], []).append(p)

    _features_by_serp = {}
    for f in features:
        _features_by_serp.setdefault(str(f.serp_id), []).append(f)

    problem_serp_ids = sorted(_problems_by_serp.keys())

    _entries = []
    for serp_id in problem_serp_ids:
        gt_path = gt_dir / f"{serp_id}.html"
        if not gt_path.exists():
            continue

        serp_problems = _problems_by_serp[serp_id]
        statuses = Counter(p["status"] for p in serp_problems)
        _entries.append({
            "serp_id": serp_id,
            "statuses": dict(statuses),
            "problems": serp_problems,
        })

    if not _entries:
        print("No problems to edit.")
        return

    app = _create_app(label)
    print(f"\n  GT Editor: http://localhost:5050/  ({len(_entries)} SERPs with problems)")
    print("  Press Ctrl+C to stop.\n")
    webbrowser.open("http://localhost:5050/")
    app.run(host="127.0.0.1", port=5050, debug=False)
