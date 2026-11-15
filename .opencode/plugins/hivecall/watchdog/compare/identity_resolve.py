"""Compare the runtime bindings used by baseline scopes."""
import ast
import builtins
import importlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types


SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda,
          ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)
SCOPE_NAMES = {ast.ListComp: "listcomp", ast.SetComp: "setcomp",
               ast.DictComp: "dictcomp", ast.GeneratorExp: "genexpr"}


def scope_name(node):
    return node.name if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) else SCOPE_NAMES.get(type(node), "lambda")


def scope_kind(node):
    return "class" if isinstance(node, ast.ClassDef) else "function"


def scope_tables(root, table):
    result = {id(root): table}

    def fill(node, parent):
        unused = list(parent.get_children())
        def direct_scopes(item):
            for child in ast.iter_child_nodes(item):
                if isinstance(child, SCOPES):
                    yield child
                else:
                    yield from direct_scopes(child)
        for child in direct_scopes(node):
            match = next((item for item in unused if item.get_name() == scope_name(child)
                          and item.get_type() == scope_kind(child)
                          and item.get_lineno() == child.lineno), None)
            if match is not None:
                unused.remove(match)
                result[id(child)] = match
                fill(child, match)

    fill(root, table)
    return result


def load_file(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_candidate(path):
    path = Path(path)
    module = load_file(path, "watch")
    package = path.parent / "hivewatch"
    if package.is_dir():
        importlib.import_module("hivewatch")
        for source in sorted(package.rglob("*.py")):
            relative = source.relative_to(package)
            if relative.name == "__init__.py":
                continue
            name = "hivewatch." + ".".join(relative.with_suffix("").parts)
            importlib.import_module(name)
    modules = {Path(value.__file__).resolve(): value for value in list(sys.modules.values())
               if isinstance(value, types.ModuleType) and getattr(value, "__file__", None)}
    modules[path.resolve()] = module
    return modules


def run_check(old_path, new_path, mappings):
    if not mappings:
        return []
    helper = Path(__file__).resolve()
    with tempfile.TemporaryDirectory(prefix="identity-") as temp:
        root = Path(temp)
        home, repo, cwd = (root / name for name in ("home", "repo", "cwd"))
        for path in (home, repo, cwd):
            path.mkdir()
        env = {"PATH": os.environ.get("PATH", os.defpath), "TZ": os.environ.get("TZ", "UTC"),
               "PYTHONHASHSEED": os.environ.get("PYTHONHASHSEED", "0"),
               "HOME": str(home), "REPO": str(repo)}
        try:
            proc = subprocess.run([sys.executable, str(helper), str(Path(old_path).resolve()), str(Path(new_path).resolve())],
                                  input=json.dumps(mappings), capture_output=True, text=True,
                                  cwd=cwd, env=env, timeout=10)
        except subprocess.TimeoutExpired:
            return ["runtime name resolution timed out after 10 seconds"]
    try:
        result = json.loads(proc.stdout.splitlines()[-1])
        return result.get("errors", [result.get("error", "runtime name resolution failed")])
    except (IndexError, json.JSONDecodeError):
        detail = (proc.stderr or proc.stdout).strip().splitlines()
        return ["runtime name resolution failed" + (f": {detail[-1]}" if detail else "")]


def own_module(name):
    return name == "watch" or name.startswith("hivewatch.")


def same_value(old, new, seen=None):
    if old is new:
        return True
    if type(old) is not type(new):
        old_type, new_type = type(old), type(new)
        if not (old_type.__qualname__ == new_type.__qualname__ and
                ((own_module(old_type.__module__) and own_module(new_type.__module__)) or
                 old_type.__module__ == new_type.__module__)):
            return False
    if isinstance(old, types.ModuleType):
        return old.__name__ == new.__name__
    if inspect.isfunction(old) or inspect.isclass(old):
        old_module, new_module = old.__module__, new.__module__
        return (old.__qualname__ == new.__qualname__ and
                ((own_module(old_module) and own_module(new_module)) or old_module == new_module))
    if inspect.isbuiltin(old):
        return old is new if old.__module__ == "builtins" else (
            old.__module__ == new.__module__ and old.__qualname__ == new.__qualname__)
    if isinstance(old, dict):
        return (old.keys() == new.keys() and all(same_value(old[key], new[key], seen) for key in old))
    if isinstance(old, (list, tuple)):
        return len(old) == len(new) and all(same_value(a, b, seen) for a, b in zip(old, new))
    if isinstance(old, (set, frozenset)):
        return old == new
    try:
        equal = old == new
        if isinstance(equal, bool) and equal:
            return True
    except Exception:
        pass
    if hasattr(old, "__dict__"):
        seen = seen or set()
        pair = (id(old), id(new))
        if pair in seen:
            return True
        seen.add(pair)
        return (same_value(type(old), type(new), seen) and
                same_value(vars(old), vars(new), seen))
    return False


def check(old_path, new_path, mappings):
    old_source = Path(old_path).read_text()
    old_tree = ast.parse(old_source, filename=str(old_path))
    old_module = load_file(old_path, "watch")
    candidate_modules = load_candidate(new_path)
    root_table = __import__("symtable").symtable(old_source, str(old_path), "exec")
    candidate = candidate_modules[Path(new_path).resolve()]
    errors = []
    _MISSING = object()
    for symbol in root_table.get_symbols():
        if not symbol.is_referenced():
            continue
        name = symbol.get_name()
        old_value = old_module.__dict__.get(name, builtins.__dict__.get(name, _MISSING))
        new_value = candidate.__dict__.get(name, builtins.__dict__.get(name, _MISSING))
        if old_value is _MISSING or new_value is _MISSING:
            same = old_value is new_value
        else:
            same = same_value(old_value, new_value)
        if not same:
            errors.append(f"module: global name {name!r} resolves differently")
    paths = {}
    by_key = {(node.lineno, node.name, type(node).__name__): node for node in ast.walk(old_tree)
              if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
    for item in mappings:
        node = by_key.get((item["line"], item["name"], item["kind"]))
        if node is not None:
            paths[id(node)] = Path(item["module"]).resolve()
    def visit(node, current_path, current_tables):
        current_path = paths.get(id(node), current_path)
        table = current_tables.get(id(node))
        if isinstance(node, SCOPES) and table is not None:
            names = sorted(symbol.get_name() for symbol in table.get_symbols() if symbol.is_global())
            module = candidate_modules.get(current_path)
            label = getattr(node, "name", SCOPE_NAMES.get(type(node), "<lambda>"))
            for name in names:
                old_value = old_module.__dict__.get(name, builtins.__dict__.get(name, _MISSING))
                new_value = (module.__dict__.get(name, builtins.__dict__.get(name, _MISSING))
                             if module is not None else _MISSING)
                if old_value is _MISSING or new_value is _MISSING:
                    same = old_value is new_value
                else:
                    same = same_value(old_value, new_value)
                if not same:
                    errors.append(f"{label}: global name {name!r} resolves differently")
        for child in ast.iter_child_nodes(node):
            visit(child, current_path, current_tables)

    for node in ast.iter_child_nodes(old_tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            table = next((item for item in root_table.get_children()
                          if item.get_name() == scope_name(node) and item.get_type() == scope_kind(node)
                          and item.get_lineno() == node.lineno), None)
            if table is None:
                continue
            current_path = paths.get(id(node), Path(new_path).resolve())
            visit(node, current_path, scope_tables(node, table))
    return sorted(set(errors))


def main():
    try:
        mappings = json.loads(sys.stdin.read())
        errors = check(sys.argv[1], sys.argv[2], mappings)
        print(json.dumps({"errors": errors}))
        return int(bool(errors))
    except Exception as error:
        print(json.dumps({"errors": [f"runtime resolution could not load modules: {error}"]}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
