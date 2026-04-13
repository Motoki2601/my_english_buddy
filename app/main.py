import sys

from app.config import AppConfig
from app.utils.args import parse_args
from app.utils.env import load_dotenv


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    load_dotenv(args.env_file)

    try:
        config = AppConfig.from_env()
    except ValueError as e:
        print(f"Config error: {e}", file=sys.stderr)
        return 1

    if args.web:
        return _run_web(config, host=args.host, port=args.port)
    return _run_desktop(config)


def _run_web(config: AppConfig, *, host: str, port: int) -> int:
    try:
        import uvicorn
    except ImportError:
        print(
            "Web mode requires extra dependencies.\n"
            "Install with: uv pip install 'my-english-buddy[web]'",
            file=sys.stderr,
        )
        return 1

    from app.di_container import build_web_container
    from app.presentation.web_server import create_app

    try:
        container = build_web_container(config)
    except Exception as e:
        print(f"Failed to initialize web application: {e}", file=sys.stderr)
        return 2

    app = create_app(
        conversation_service=container.conversation_service,
        stt=container.stt,
        tts=container.tts,
        logger=container.logger,
    )

    print(f"\nStarting My English Buddy (web mode)")
    print(f"Open on your smartphone: http://<your-ip>:{port}\n")

    uvicorn.run(app, host=host, port=port)
    container.logger.save()
    return 0


def _run_desktop(config: AppConfig) -> int:
    from PySide6.QtWidgets import QApplication

    from app.di_container import build_container
    from app.presentation.conversation_worker import ConversationWorker
    from app.presentation.main_window import MainWindow

    try:
        container = build_container(config)
    except Exception as e:
        print(f"Failed to initialize application: {e}", file=sys.stderr)
        return 2

    conversation_worker = ConversationWorker(container.conversation_runner)

    app = QApplication(sys.argv)
    app.aboutToQuit.connect(container.logger.save)

    window = MainWindow(conversation_worker)
    window.show()

    conversation_worker.start()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
