from __future__ import annotations

import logging
from flask import Flask, Response

logger = logging.getLogger(__name__)

session = None      # AnnotationSession
config = None       # archive_query_log Config
warc_store = None   # WarcS3Store


def create_app() -> Flask:
    global config, warc_store

    from dotenv import load_dotenv
    load_dotenv()

    from archive_query_log.config import Config

    config = Config()
    warc_store = config.s3.warc_store

    app = Flask(__name__)

    from docs.adr.src.annotation.core.routes import bp
    app.register_blueprint(bp)

    @app.after_request
    def add_cors_headers(response: Response) -> Response:
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        return response

    @app.route("/", defaults={"path": ""}, methods=["OPTIONS"])
    @app.route("/<path:path>", methods=["OPTIONS"])
    def handle_options(path):
        return "", 204

    @app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
    def catch_all(path):
        return "", 404

    return app
