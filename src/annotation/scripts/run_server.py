import logging

from docs.adr.src.utils.logging_config import configure_logging
from docs.adr.src.annotation.core.cli import parse_cli_args
from docs.adr.src.annotation.core.session import init_session
from docs.adr.src.annotation.core import server

logger = logging.getLogger(__name__)


def main():
    configure_logging()

    args = parse_cli_args()

    app = server.create_app()

    session = init_session(args.provider, args.year, args.lang, args.batch)
    server.session = session

    print(f"\nFeature Block Annotation Server")
    print(f"{'=' * 40}")
    print(f"Provider:        {session.provider}")
    print(f"Year:            {session.year}")
    print(f"Language:        {session.language}")
    print(f"Output dir:      {session.output_dir}")
    print(f"\nCached IDs:      {session.total_cached}")
    print(f"Already done:    {session.already_annotated}")
    print(f"Remaining:       {session.remaining}")
    print(f"Current batch:   {len(session.serp_ids)}")
    print(f"\nUI: http://localhost:{args.port}/annotation")
    print(f"{'=' * 40}\n")

    app.run(host="127.0.0.1", port=args.port, debug=True, use_reloader=False)


if __name__ == "__main__":
    main()
