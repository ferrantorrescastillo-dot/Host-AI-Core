from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator


_INITIALIZE_PERSISTENTLY: ContextVar[bool] = ContextVar(
    "hostai_initialize_repositories_persistently", default=True,
)


def should_initialize_persistently() -> bool:
    return _INITIALIZE_PERSISTENTLY.get()


@contextmanager
def non_persistent_repository_initialization() -> Iterator[None]:
    """Evita mkdir/default JSON durante la construcción de repositorios READ."""
    token = _INITIALIZE_PERSISTENTLY.set(False)
    try:
        yield
    finally:
        _INITIALIZE_PERSISTENTLY.reset(token)
