from __future__ import annotations

import json
import logging
from pathlib import Path

from flask import Blueprint, request, jsonify, send_from_directory, Response
from lxml import etree

from docs.adr.src.annotation.utils.html_cleaning import clean_serp_html
from docs.adr.src.parser.utils.html_utils import normalize_html
from docs.adr.src.annotation.utils.jsonl_io import save_serp_id
from archive_query_log.orm import Serp

logger = logging.getLogger(__name__)

bp = Blueprint("annotation", __name__)

_FRONTEND_DIR = str(Path(__file__).resolve().parent.parent / "frontend")


def _server():
    from docs.adr.src.annotation.core import server
    return server


@bp.route("/serp-id/<serp_id>", methods=["GET"])
def serve_serp_by_id(serp_id: str):
    state = _server()
    try:
        serp_doc = Serp.get(
            id=serp_id,
            using=state.config.es.client,
            index=state.config.es.index_serps,
            ignore=404,
        )
    except Exception as e:
        return jsonify({"error": f"ES lookup failed: {e}"}), 500

    if serp_doc is None:
        return jsonify({"error": f"serp_id '{serp_id}' not found"}), 404

    warc_loc = getattr(serp_doc, "warc_location", None)
    if warc_loc is None or not getattr(warc_loc, "file", None):
        return jsonify({"error": f"serp_id '{serp_id}' has no warc_location"}), 400

    try:
        with state.warc_store.read(warc_loc) as record:
            html_bytes = record.content_stream().read()
    except Exception as e:
        return jsonify({"error": f"failed to read warc: {e}"}), 500

    if request.args.get("raw") == "true":
        return Response(html_bytes, status=200, mimetype="text/html; charset=utf-8")

    serp_url = getattr(serp_doc, "url", None)
    html_bytes = clean_serp_html(html_bytes, base_url=serp_url)
    return Response(html_bytes, status=200, mimetype="text/html; charset=utf-8")


@bp.route("/serp-ids", methods=["GET"])
def list_serp_ids():
    state = _server()
    s = state.session
    if not s:
        return jsonify({"serp_ids": []})
    return jsonify({
        "serp_ids": s.serp_ids,
        "total": len(s.serp_ids),
        "provider": s.provider,
        "year": s.year,
        "language": s.language,
    })


@bp.route("/annotation", methods=["GET"])
def serve_annotation_ui():
    return send_from_directory(_FRONTEND_DIR, "annotation.html")


@bp.route("/save-annotation/<serp_id>", methods=["POST"])
def save_annotation(serp_id: str):
    state = _server()
    s = state.session
    if not s:
        return jsonify({"error": "No active annotation session"}), 400

    try:
        content_type = request.headers.get("Content-Type", "")
        if "application/json" in content_type:
            data = request.json
            annotated_html = data.get("html", "")
            fbs = data.get("fbs", [])
            fb_num = data.get("fb_num", 0)
        else:
            annotated_html = request.data.decode("utf-8")
            fbs = []
            fb_num = 0

        if not annotated_html:
            return jsonify({"error": "No HTML content provided"}), 400

        html_saved = False

        if fb_num > 0:
            s.output_dir.mkdir(parents=True, exist_ok=True)
            annotated_file = s.output_dir / f"{serp_id}.html"
            annotated_file.write_text(annotated_html, encoding="utf-8")
            logger.info("Saved annotated SERP: %s", annotated_file)
            html_saved = True

        save_serp_id(
            annotation_dir=s.output_dir,
            serp_id=serp_id,
            provider=s.provider, year=s.year, language=s.language,
        )

        return jsonify({
            "success": True,
            "serp_id": serp_id,
            "fb_num": fb_num,
            "html_saved": html_saved,
        })
    except Exception as e:
        return jsonify({"error": f"Failed to save: {e}"}), 500


@bp.route("/test-xpath", methods=["POST"])
def test_xpath():
    try:
        data = request.json
        html = data.get("html")
        xpath = data.get("xpath")

        if not html or not xpath:
            return jsonify({"success": False, "message": "Missing html or xpath"}), 400

        parser = etree.HTMLParser()
        tree = etree.fromstring(html.encode("utf-8"), parser)

        marked_elements = tree.xpath("//*[contains(@class, 'fb-testing')]")
        if not marked_elements:
            return jsonify({
                "success": False,
                "message": "No element with 'fb-testing' class found",
            }), 400

        human_element = marked_elements[0]
        human_html = etree.tostring(human_element, encoding="unicode", method="html")

        parsed_results = tree.xpath(xpath)
        if not parsed_results:
            return jsonify({
                "success": True,
                "match": False,
                "human_html": human_html,
                "xpath_html": None,
                "message": "XPath returned no results",
            })

        parsed_element = parsed_results[0]
        parsed_html = etree.tostring(parsed_element, encoding="unicode", method="html")

        human_normalized = normalize_html(human_html)
        xpath_normalized = normalize_html(parsed_html)
        match = human_normalized == xpath_normalized

        return jsonify({
            "success": True,
            "match": match,
            "human_html": human_html,
            "xpath_html": parsed_html,
            "message": "XPath extracts same content" if match else "Content mismatch",
        })

    except etree.XPathEvalError as e:
        return jsonify({"success": False, "message": f"XPath syntax error: {e}"}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {e}"}), 500


@bp.route("/get-categories", methods=["GET"])
def get_categories():
    categories_file = Path(_FRONTEND_DIR) / "serp_features_taxonomy.json"
    try:
        with categories_file.open("r", encoding="utf-8") as f:
            data = json.load(f)

        provider = request.args.get("provider", "all")
        return jsonify({
            "provider": provider,
            "name": f"{provider.upper()} Feature Block Categories",
            "categories": data["categories"],
            "version": data.get("version"),
            "last_updated": data.get("last_updated"),
        })
    except FileNotFoundError:
        return jsonify({"error": "Categories file not found"}), 500
    except Exception as e:
        return jsonify({"error": f"Failed to load categories: {e}"}), 500
