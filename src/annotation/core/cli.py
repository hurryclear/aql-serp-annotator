import argparse


def parse_cli_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Feature Block Annotation Server",
    )
    parser.add_argument("--provider", required=True)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--lang", required=True)
    parser.add_argument("--batch", type=int, default=20)
    parser.add_argument("--port", type=int, default=2626)
    return parser.parse_args()
