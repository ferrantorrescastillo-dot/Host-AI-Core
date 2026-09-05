from __future__ import annotations

import builtins
import hashlib
import io
import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Any, Callable

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
REAL_DATOS_ROOT = (REPO_ROOT / "DATOS").resolve()
_ORIGINALS: list[tuple[Any, str, Any]] = []
_BASELINE: tuple[int, str] | None = None


def _resolved(value: Any) -> Path | None:
    if isinstance(value, int) or value is None:
        return None
    try:
        return Path(os.fspath(value)).resolve(strict=False)
    except (TypeError, ValueError, OSError):
        return None


def _inside_real_datos(value: Any) -> bool:
    path = _resolved(value)
    if path is None:
        return False
    try:
        path.relative_to(REAL_DATOS_ROOT)
        return True
    except ValueError:
        return False


def _block(operation: str, *paths: Any) -> None:
    target = next((path for path in paths if _inside_real_datos(path)), None)
    if target is not None:
        raise AssertionError(
            "TEST_DATA_ISOLATION_GUARD: "
            f"{operation} intentó modificar DATOS real: {_resolved(target)}. "
            "Use tmp_path o .test-runs con una raíz inyectada."
        )


def _replace(owner: Any, name: str, replacement: Any) -> None:
    original = getattr(owner, name)
    _ORIGINALS.append((owner, name, original))
    setattr(owner, name, replacement(original))


def _single_path_guard(operation: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorate(original: Callable[..., Any]) -> Callable[..., Any]:
        def guarded(path: Any, *args: Any, **kwargs: Any) -> Any:
            _block(operation, path)
            return original(path, *args, **kwargs)

        return guarded

    return decorate


def _directory_guard(operation: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Permite el mkdir idempotente de un directorio real ya existente.

    Varios repositorios inicializan su ruta de lectura con mkdir(exist_ok=True).
    Eso no modifica bytes si DATOS ya existe; cualquier creación efectiva sigue
    bloqueada, igual que las aperturas de escritura posteriores.
    """
    def decorate(original: Callable[..., Any]) -> Callable[..., Any]:
        def guarded(path: Any, *args: Any, **kwargs: Any) -> Any:
            resolved = _resolved(path)
            if _inside_real_datos(path) and resolved is not None and resolved.is_dir():
                return original(path, *args, **kwargs)
            _block(operation, path)
            return original(path, *args, **kwargs)

        return guarded

    return decorate


def _two_path_guard(operation: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorate(original: Callable[..., Any]) -> Callable[..., Any]:
        def guarded(source: Any, destination: Any, *args: Any, **kwargs: Any) -> Any:
            _block(operation, source, destination)
            return original(source, destination, *args, **kwargs)

        return guarded

    return decorate


def _open_guard(original: Callable[..., Any]) -> Callable[..., Any]:
    def guarded(file: Any, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
        if any(flag in str(mode) for flag in ("w", "a", "x", "+")):
            _block(f"open({mode})", file)
        return original(file, mode, *args, **kwargs)

    return guarded


def _os_open_guard(original: Callable[..., Any]) -> Callable[..., Any]:
    write_flags = os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC

    def guarded(path: Any, flags: int, *args: Any, **kwargs: Any) -> Any:
        if int(flags) & write_flags:
            _block(f"os.open(flags={flags})", path)
        return original(path, flags, *args, **kwargs)

    return guarded


def _sqlite_guard(original: Callable[..., Any]) -> Callable[..., Any]:
    def guarded(database: Any, *args: Any, **kwargs: Any) -> Any:
        if database != ":memory:":
            _block("sqlite3.connect", database)
        return original(database, *args, **kwargs)

    return guarded


def _manifest() -> tuple[int, str]:
    rows = []
    for item in sorted((path for path in REAL_DATOS_ROOT.rglob("*") if path.is_file())):
        relative = item.relative_to(REAL_DATOS_ROOT).as_posix()
        rows.append(f"{relative}|{hashlib.sha256(item.read_bytes()).hexdigest().upper()}")
    digest = hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest().upper()
    return len(rows), digest


def pytest_configure(config: pytest.Config) -> None:
    global _BASELINE
    if not config.option.basetemp:
        isolated_root = Path(tempfile.gettempdir()) / "host-ai-test-runs"
        isolated_root.mkdir(parents=True, exist_ok=True)
        config.option.basetemp = str(isolated_root / f"pytest-{os.getpid()}")
    _BASELINE = _manifest()
    _replace(builtins, "open", _open_guard)
    _replace(io, "open", _open_guard)
    _replace(os, "open", _os_open_guard)
    for name in ("mkdir", "makedirs"):
        if hasattr(os, name):
            _replace(os, name, _directory_guard(f"os.{name}"))
    for name in ("remove", "unlink", "rmdir", "removedirs", "truncate", "chmod", "utime"):
        if hasattr(os, name):
            _replace(os, name, _single_path_guard(f"os.{name}"))
    for name in ("rename", "replace", "link", "symlink"):
        if hasattr(os, name):
            _replace(os, name, _two_path_guard(f"os.{name}"))
    _replace(sqlite3, "connect", _sqlite_guard)
    os.environ["HOST_AI_TEST_REAL_DATOS_GUARD"] = str(REAL_DATOS_ROOT)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    current = _manifest()
    if _BASELINE != current:
        reporter = session.config.pluginmanager.get_plugin("terminalreporter")
        if reporter is not None:
            reporter.write_sep(
                "!",
                f"TEST_DATA_ISOLATION_GUARD: DATOS real cambió: before={_BASELINE}, after={current}",
                red=True,
            )
        session.exitstatus = pytest.ExitCode.TESTS_FAILED


def pytest_unconfigure(config: pytest.Config) -> None:
    while _ORIGINALS:
        owner, name, original = _ORIGINALS.pop()
        setattr(owner, name, original)
    os.environ.pop("HOST_AI_TEST_REAL_DATOS_GUARD", None)
