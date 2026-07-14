from __future__ import annotations

import ast
from pathlib import Path

from .repository_fingerprints import hash_file_content
from .repository_ids import class_id, function_id, module_id, module_name_from_path
from .repository_models import (
    ImportRecord,
    ParseStatus,
    PythonClassRecord,
    PythonFunctionRecord,
    PythonModuleRecord,
)


def _expr_to_text(node: ast.AST | None, max_len: int = 160) -> str | None:
    if node is None:
        return None
    try:
        text = ast.unparse(node)
    except Exception:
        text = node.__class__.__name__
    if len(text) > max_len:
        return text[: max_len - 3] + "..."
    return text


def _read_python_source(path: Path) -> tuple[str | None, str | None, list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []
    try:
        raw = path.read_bytes()
    except Exception as exc:
        return None, None, warnings, [f"read_error:{exc}"]

    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            text = raw.decode(enc)
            if enc == "latin-1":
                warnings.append("encoding_fallback:latin-1")
            return text, enc, warnings, errors
        except UnicodeDecodeError:
            continue
    return None, None, warnings, ["decode_error:no_supported_encoding"]


def _function_kind(decorators: tuple[str, ...]) -> str | None:
    deco_set = set(decorators)
    if "classmethod" in deco_set:
        return "classmethod"
    if "staticmethod" in deco_set:
        return "staticmethod"
    if "property" in deco_set:
        return "property"
    return "method"


def _collect_imports(tree: ast.AST) -> tuple[ImportRecord, ...]:
    imports: list[ImportRecord] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = tuple(alias.name for alias in node.names)
            aliases = tuple(alias.asname for alias in node.names)
            imports.append(
                ImportRecord(
                    import_type="import",
                    module=None,
                    imported_names=names,
                    aliases=aliases,
                    level=0,
                    start_line=getattr(node, "lineno", 1),
                    raw_representation=f"import {', '.join(names)}",
                )
            )
        elif isinstance(node, ast.ImportFrom):
            names = tuple(alias.name for alias in node.names)
            aliases = tuple(alias.asname for alias in node.names)
            imports.append(
                ImportRecord(
                    import_type="from-import",
                    module=node.module,
                    imported_names=names,
                    aliases=aliases,
                    level=int(node.level or 0),
                    start_line=getattr(node, "lineno", 1),
                    raw_representation=(
                        f"from {'.' * int(node.level or 0)}{node.module or ''} import {', '.join(names)}"
                    ),
                )
            )
    imports.sort(key=lambda i: (i.start_line, i.import_type, i.module or "", ",".join(i.imported_names)))
    return tuple(imports)


def _collect_parameters(fn_node: ast.AST) -> tuple[tuple[dict[str, str | None], ...], tuple[dict[str, str | None], ...]]:
    if not isinstance(fn_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return (), ()

    params: list[dict[str, str | None]] = []
    annotations: list[dict[str, str | None]] = []
    args = fn_node.args

    positional = list(args.posonlyargs) + list(args.args)
    defaults = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)

    for arg, default in zip(positional, defaults):
        params.append(
            {
                "name": arg.arg,
                "kind": "positional",
                "annotation": _expr_to_text(arg.annotation),
                "default": _expr_to_text(default),
            }
        )
        annotations.append({"name": arg.arg, "annotation": _expr_to_text(arg.annotation)})

    if args.vararg is not None:
        params.append(
            {
                "name": args.vararg.arg,
                "kind": "vararg",
                "annotation": _expr_to_text(args.vararg.annotation),
                "default": None,
            }
        )
        annotations.append({"name": args.vararg.arg, "annotation": _expr_to_text(args.vararg.annotation)})

    kw_defaults = list(args.kw_defaults)
    for arg, default in zip(args.kwonlyargs, kw_defaults):
        params.append(
            {
                "name": arg.arg,
                "kind": "keyword_only",
                "annotation": _expr_to_text(arg.annotation),
                "default": _expr_to_text(default),
            }
        )
        annotations.append({"name": arg.arg, "annotation": _expr_to_text(arg.annotation)})

    if args.kwarg is not None:
        params.append(
            {
                "name": args.kwarg.arg,
                "kind": "kwarg",
                "annotation": _expr_to_text(args.kwarg.annotation),
                "default": None,
            }
        )
        annotations.append({"name": args.kwarg.arg, "annotation": _expr_to_text(args.kwarg.annotation)})

    return tuple(params), tuple(annotations)


def _collect_function(
    node: ast.AST,
    module_name: str,
    module_id_value: str,
    class_id_value: str | None,
    scope_prefix: str,
    function_type: str,
) -> PythonFunctionRecord:
    assert isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    decorators = tuple(_expr_to_text(d) or "" for d in node.decorator_list)
    qn = f"{scope_prefix}.{node.name}" if scope_prefix else node.name
    params, annotations = _collect_parameters(node)
    return PythonFunctionRecord(
        id=function_id(module_name, qn),
        module_id=module_id_value,
        class_id=class_id_value,
        qualified_name=qn,
        name=node.name,
        function_type=function_type,
        parameters=params,
        decorators=decorators,
        docstring=ast.get_docstring(node),
        start_line=getattr(node, "lineno", 1),
        end_line=getattr(node, "end_lineno", getattr(node, "lineno", 1)),
        async_status=isinstance(node, ast.AsyncFunctionDef),
        return_annotation=_expr_to_text(node.returns),
        parameter_annotations=annotations,
        method_kind=_function_kind(decorators) if function_type == "method" else None,
    )


def _collect_class(
    node: ast.ClassDef,
    module_name: str,
    module_id_value: str,
    scope_prefix: str,
) -> PythonClassRecord:
    qn = f"{scope_prefix}.{node.name}" if scope_prefix else node.name
    cid = class_id(module_name, qn)
    methods: list[PythonFunctionRecord] = []
    nested_classes: list[PythonClassRecord] = []
    for child in node.body:
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods.append(
                _collect_function(
                    node=child,
                    module_name=module_name,
                    module_id_value=module_id_value,
                    class_id_value=cid,
                    scope_prefix=qn,
                    function_type="method",
                )
            )
        elif isinstance(child, ast.ClassDef):
            nested_classes.append(_collect_class(child, module_name, module_id_value, qn))

    methods.sort(key=lambda m: (m.start_line, m.name))
    nested_classes.sort(key=lambda c: (c.start_line, c.name))
    return PythonClassRecord(
        id=cid,
        module_id=module_id_value,
        qualified_name=qn,
        name=node.name,
        bases=tuple(_expr_to_text(b) or "" for b in node.bases),
        decorators=tuple(_expr_to_text(d) or "" for d in node.decorator_list),
        docstring=ast.get_docstring(node),
        methods=tuple(methods),
        start_line=getattr(node, "lineno", 1),
        end_line=getattr(node, "end_lineno", getattr(node, "lineno", 1)),
        async_status=False,
        nested_classes=tuple(nested_classes),
    )


def analyze_python_file(file_path: Path, relative_path: str) -> PythonModuleRecord:
    mid = module_id(relative_path)
    mod_name = module_name_from_path(relative_path)
    pkg = mod_name.rsplit(".", 1)[0] if "." in mod_name else None

    text, encoding, warnings, errors = _read_python_source(file_path)
    file_fp = hash_file_content(file_path)
    if text is None:
        return PythonModuleRecord(
            id=mid,
            file_id=f"file:{relative_path}",
            relative_path=relative_path,
            module_name=mod_name,
            package_name=pkg,
            docstring=None,
            imports=(),
            classes=(),
            functions=(),
            warnings=tuple(warnings),
            parse_status=ParseStatus.READ_ERROR,
            fingerprint=file_fp,
            errors=tuple(errors),
        )

    if text.strip() == "":
        return PythonModuleRecord(
            id=mid,
            file_id=f"file:{relative_path}",
            relative_path=relative_path,
            module_name=mod_name,
            package_name=pkg,
            docstring=None,
            imports=(),
            classes=(),
            functions=(),
            warnings=tuple(warnings + ([f"encoding:{encoding}"] if encoding else [])),
            parse_status=ParseStatus.EMPTY,
            fingerprint=file_fp,
            errors=(),
        )

    try:
        tree = ast.parse(text, filename=relative_path)
    except SyntaxError as exc:
        return PythonModuleRecord(
            id=mid,
            file_id=f"file:{relative_path}",
            relative_path=relative_path,
            module_name=mod_name,
            package_name=pkg,
            docstring=None,
            imports=(),
            classes=(),
            functions=(),
            warnings=tuple(warnings + ([f"encoding:{encoding}"] if encoding else [])),
            parse_status=ParseStatus.PARSE_ERROR,
            fingerprint=file_fp,
            errors=(
                f"syntax_error:line={exc.lineno}:col={exc.offset}:msg={exc.msg}",
            ),
        )

    imports = _collect_imports(tree)
    classes: list[PythonClassRecord] = []
    functions: list[PythonFunctionRecord] = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            classes.append(_collect_class(node, mod_name, mid, ""))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(
                _collect_function(
                    node=node,
                    module_name=mod_name,
                    module_id_value=mid,
                    class_id_value=None,
                    scope_prefix="",
                    function_type="function",
                )
            )

    # Funciones anidadas para evitar colisiones de ids.
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    functions.append(
                        _collect_function(
                            node=child,
                            module_name=mod_name,
                            module_id_value=mid,
                            class_id_value=None,
                            scope_prefix=node.name,
                            function_type="nested_function",
                        )
                    )

    classes.sort(key=lambda c: (c.start_line, c.name))
    functions.sort(key=lambda f: (f.start_line, f.qualified_name))
    if encoding:
        warnings.append(f"encoding:{encoding}")

    return PythonModuleRecord(
        id=mid,
        file_id=f"file:{relative_path}",
        relative_path=relative_path,
        module_name=mod_name,
        package_name=pkg,
        docstring=ast.get_docstring(tree),
        imports=imports,
        classes=tuple(classes),
        functions=tuple(functions),
        warnings=tuple(warnings),
        parse_status=ParseStatus.OK,
        fingerprint=file_fp,
        errors=tuple(errors),
    )
