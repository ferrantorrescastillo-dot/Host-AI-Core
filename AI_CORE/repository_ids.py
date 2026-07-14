from __future__ import annotations


def normalize_relative_path(path: str) -> str:
    return path.replace("\\", "/").strip("/")


def file_id(relative_path: str) -> str:
    return f"file:{normalize_relative_path(relative_path)}"


def module_name_from_path(relative_path: str) -> str:
    normalized = normalize_relative_path(relative_path)
    if normalized.lower().endswith(".py"):
        normalized = normalized[:-3]
    return normalized.replace("/", ".")


def module_id(relative_path: str) -> str:
    return f"module:{module_name_from_path(relative_path)}"


def class_id(module_name: str, qualified_name: str) -> str:
    return f"class:{module_name}.{qualified_name}"


def function_id(module_name: str, qualified_name: str) -> str:
    return f"function:{module_name}.{qualified_name}"
