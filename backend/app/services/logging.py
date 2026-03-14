import logging
import uuid
from contextvars import ContextVar

request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


def set_request_id(value: str | None) -> None:
    request_id_ctx.set(value)


def get_request_id() -> str | None:
    return request_id_ctx.get()


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "-"
        return True


def configure_logging() -> None:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] [request_id=%(request_id)s] %(message)s"
    )
    handler.setFormatter(formatter)
    handler.addFilter(RequestIdFilter())

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers = [handler]


def new_request_id() -> str:
    return str(uuid.uuid4())
