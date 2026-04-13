import argparse


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audio-based OpenAI chat application")
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Path to .env file (default: .env). Use empty to disable.",
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Run as a web server (mobile-friendly browser UI).",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind the web server to (default: 0.0.0.0).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for the web server (default: 8000).",
    )
    return parser.parse_args(argv)
