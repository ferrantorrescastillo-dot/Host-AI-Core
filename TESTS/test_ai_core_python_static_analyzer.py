from __future__ import annotations

from pathlib import Path

from AI_CORE.python_static_analyzer import analyze_python_file
from AI_CORE.repository_models import ParseStatus


def _write(path: Path, content: str, encoding: str = "utf-8") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding=encoding)


def test_ast_extracts_module_class_functions_methods_imports(tmp_path: Path) -> None:
    file_path = tmp_path / "pkg" / "mod.py"
    _write(
        file_path,
        '"""doc modulo"""\n'
        "import os as operating_system\n"
        "from .a import b as bee\n"
        "def outer(x:int=1,*args,flag=True,**kwargs)->str:\n"
        "    def inner(y):\n"
        "        return y\n"
        "    return str(x)\n"
        "class C(Base):\n"
        "    @classmethod\n"
        "    def cm(cls, a:int):\n"
        "        return a\n"
        "    @staticmethod\n"
        "    def sm(v):\n"
        "        return v\n"
        "    @property\n"
        "    def prop(self):\n"
        "        return 1\n"
        "    async def am(self):\n"
        "        return 1\n"
        "    class Inner:\n"
        "        def z(self):\n"
        "            return 0\n",
    )
    module = analyze_python_file(file_path, "pkg/mod.py")
    assert module.parse_status == ParseStatus.OK
    assert module.docstring == "doc modulo"
    assert len(module.imports) >= 2
    assert any(i.import_type == "import" for i in module.imports)
    assert any(i.import_type == "from-import" and i.level == 1 for i in module.imports)
    assert any(f.qualified_name == "outer" for f in module.functions)
    assert any(f.qualified_name == "outer.inner" for f in module.functions)
    cls = next(c for c in module.classes if c.name == "C")
    assert cls.qualified_name == "C"
    kinds = {m.method_kind for m in cls.methods}
    assert "classmethod" in kinds
    assert "staticmethod" in kinds
    assert "property" in kinds
    assert any(m.async_status for m in cls.methods)
    assert len(cls.nested_classes) == 1


def test_ast_empty_bom_and_syntax_error(tmp_path: Path) -> None:
    empty = tmp_path / "empty.py"
    empty.write_text("", encoding="utf-8")
    mod_empty = analyze_python_file(empty, "empty.py")
    assert mod_empty.parse_status == ParseStatus.EMPTY

    bom = tmp_path / "bom.py"
    bom.write_bytes("\ufeffx = 1\n".encode("utf-8"))
    mod_bom = analyze_python_file(bom, "bom.py")
    assert mod_bom.parse_status == ParseStatus.OK

    bad = tmp_path / "bad.py"
    bad.write_text("def oops(:\n", encoding="utf-8")
    mod_bad = analyze_python_file(bad, "bad.py")
    assert mod_bad.parse_status == ParseStatus.PARSE_ERROR
    assert any("syntax_error" in e for e in mod_bad.errors)


def test_ast_problematic_encoding_and_no_execution(tmp_path: Path) -> None:
    file_path = tmp_path / "latin.py"
    file_path.write_bytes("def f():\n    return 'olá'\n".encode("latin-1"))
    mod = analyze_python_file(file_path, "latin.py")
    assert mod.parse_status == ParseStatus.OK
    assert any("encoding" in w for w in mod.warnings)

    danger = tmp_path / "danger.py"
    _write(
        danger,
        "def f(x=open('NEVER_CREATE_THIS_FILE.txt','w')):\n"
        "    return x\n",
    )
    mod_danger = analyze_python_file(danger, "danger.py")
    assert mod_danger.parse_status == ParseStatus.OK
    assert not (tmp_path / "NEVER_CREATE_THIS_FILE.txt").exists()


def test_stable_ids_for_duplicate_names_in_scopes(tmp_path: Path) -> None:
    file_path = tmp_path / "dup.py"
    _write(
        file_path,
        "def same():\n"
        "    def same():\n"
        "        return 1\n"
        "    return same()\n"
        "class K:\n"
        "    def same(self):\n"
        "        return 2\n",
    )
    mod = analyze_python_file(file_path, "dup.py")
    ids = {f.id for f in mod.functions}
    assert len(ids) == len(mod.functions)
    cls = mod.classes[0]
    method_ids = {m.id for m in cls.methods}
    assert len(method_ids) == len(cls.methods)
