"""Check baseline AST values across watchdog splits, with scoped ctx.X rewrites."""
import argparse
import ast
from collections import defaultdict
import copy
from pathlib import Path
import symtable
from identity_resolve import run_check

SCOPED_FUNCTIONS = {"evaluate", "simulate"}
SCOPE_NODES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda,
               ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)
COMP_NAMES = {ast.ListComp: "listcomp", ast.SetComp: "setcomp",
               ast.DictComp: "dictcomp", ast.GeneratorExp: "genexpr"}

def is_docstring(node): return isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)

def module_doc(tree): return tree.body[0].value.value if tree.body and is_docstring(tree.body[0]) else None

def binding_names(target): return sorted({n.id for n in ast.walk(target) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)})

def unit(node):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)): return node.name
    if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        names = sorted({name for target in targets for name in binding_names(target)})
        return "assignment " + (", ".join(names) if names else f"at line {node.lineno}")
    return type(node).__name__

class NormalizeCtx(ast.NodeTransformer):
    def __init__(self, locals_):
        self.locals = locals_
        self.outer = True

    def visit_Attribute(self, node):
        if (isinstance(node.value, ast.Name) and node.value.id == "ctx"
                and node.attr in self.locals):
            return ast.copy_location(ast.Name(id=node.attr, ctx=node.ctx), node)
        return self.generic_visit(node)

    def visit_arguments(self, node):
        if self.outer:
            self.outer = False
            for field in ("posonlyargs", "args", "kwonlyargs"):
                setattr(node, field, [arg for arg in getattr(node, field) if arg.arg != "ctx"])
            for field in ("vararg", "kwarg"):
                arg = getattr(node, field)
                if arg and arg.arg == "ctx": setattr(node, field, None)
        return self.generic_visit(node)

def canonical(node, locals_=()):
    clone = copy.deepcopy(node)
    return ast.dump(ast.fix_missing_locations(NormalizeCtx(set(locals_)).visit(clone) if locals_ else clone), include_attributes=False)

def scope_name(node):
    return node.name if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) else COMP_NAMES.get(type(node), "<lambda>")
def scope_type(node): return "class" if isinstance(node, ast.ClassDef) else "function"
def first_scope_descendants(node):
    for child in ast.iter_child_nodes(node):
        if isinstance(child, SCOPE_NODES):
            yield child
        else:
            yield from first_scope_descendants(child)

def scope_index(root, root_table):
    result = {id(root): root_table}

    def fill(node, table):
        unused = list(table.get_children())
        for child in first_scope_descendants(node):
            match = next((t for t in unused if t.get_name() == scope_name(child)
                          and t.get_type() == scope_type(child)
                          and t.get_lineno() == child.lineno), None)
            if match is None:
                if isinstance(child, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                    fill(child, table)
                continue
            unused.remove(match)
            result[id(child)] = match
            fill(child, match)

    fill(root, root_table)
    return result

def find_table(table, name, lineno, kind="function"):
    if table.get_name() == name and table.get_lineno() == lineno and table.get_type() == kind:
        return table
    for child in table.get_children():
        found = find_table(child, name, lineno, kind)
        if found: return found
    return None

def locals_of(table): return {s.get_name() for s in table.get_symbols() if s.is_local()}

def function_locals(node, table):
    names = {arg.arg for arg in node.args.posonlyargs + node.args.args + node.args.kwonlyargs}
    def visit(item):
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            if not isinstance(item, ast.Lambda):
                names.add(item.name)
            return
        if isinstance(item, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            visit(item.generators[0].iter)
            return
        if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Store):
            names.add(item.id)
        if isinstance(item, ast.ExceptHandler) and item.name:
            names.add(item.name)
        if isinstance(item, ast.Import):
            names.update(alias.asname or alias.name.split(".")[0] for alias in item.names)
        if isinstance(item, ast.ImportFrom):
            names.update(alias.asname or alias.name for alias in item.names if alias.name != "*")
        for child in ast.iter_child_nodes(item):
            visit(child)
    for statement in node.body:
        visit(statement)
    return locals_of(table) & names

def walk_without_inner_scopes(node):
    yield node
    for child in ast.iter_child_nodes(node):
        if isinstance(child, SCOPE_NODES):
            continue
        yield from walk_without_inner_scopes(child)

def shared_locals(table, top_locals, node):
    shared = set()

    def visit(scope):
        for symbol in scope.get_symbols():
            if symbol.get_name() in top_locals and symbol.is_free():
                shared.add(symbol.get_name())
        for child in scope.get_children():
            visit(child)

    for child in table.get_children():
        visit(child)
    for comp in (item for item in ast.walk(node)
                 if isinstance(item, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp))):
        comp_names = {name for generator in comp.generators for name in binding_names(generator.target)}
        expressions = [generator.iter for generator in comp.generators]
        if isinstance(comp, ast.DictComp):
            expressions.extend((comp.key, comp.value))
        else:
            expressions.append(comp.elt)
        expressions.extend(condition for generator in comp.generators for condition in generator.ifs)
        for expression in expressions:
            for item in walk_without_inner_scopes(expression):
                if (isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load)
                        and item.id in top_locals and item.id not in comp_names):
                    shared.add(item.id)
    return shared

def has_ctx_arg(node): return any(arg.arg == "ctx" for arg in node.args.posonlyargs + node.args.args + node.args.kwonlyargs)

class CtxAudit(ast.NodeVisitor):
    def __init__(self, root, table, locals_, shared):
        self.scopes = [table]
        self.ast_scopes = []
        self.scope_map = scope_index(root, table)
        self.locals = locals_
        self.shared = shared
        self.errors = []
    def inner_local(self, name):
        return (any(name in locals_of(scope) for scope in self.scopes[1:])
                or any(name in scope for scope in self.ast_scopes))
    def visit_Name(self, node):
        if node.id in self.shared and not self.inner_local(node.id):
            self.errors.append(f"shared local {node.id!r} is not prefixed with ctx.")
    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name) and node.value.id == "ctx":
            if self.inner_local("ctx") and node.attr in self.locals: self.errors.append("ctx is shadowed in an inner scope.")
            elif self.inner_local(node.attr):
                self.errors.append(f"inner-scope name {node.attr!r} is prefixed with ctx.")
            elif node.attr not in self.locals:
                self.errors.append(f"ctx.{node.attr} is not a baseline top-scope local.")
        self.generic_visit(node)
    def _visit_outer_expressions(self, node):
        for item in getattr(node, "decorator_list", []):
            self.visit(item)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            for item in node.args.defaults + node.args.kw_defaults:
                if item is not None:
                    self.visit(item)
            for arg in node.args.posonlyargs + node.args.args + node.args.kwonlyargs:
                if arg.annotation:
                    self.visit(arg.annotation)
            if node.args.vararg and node.args.vararg.annotation:
                self.visit(node.args.vararg.annotation)
            if node.args.kwarg and node.args.kwarg.annotation:
                self.visit(node.args.kwarg.annotation)
            if getattr(node, "returns", None):
                self.visit(node.returns)
        elif isinstance(node, ast.ClassDef):
            for item in node.bases + node.keywords:
                self.visit(item)
    def _visit_scope_body(self, node, body):
        self._visit_outer_expressions(node)
        table = self.scope_map.get(id(node))
        if table is None:
            self.errors.append(f"cannot map inner scope at line {node.lineno} for ctx audit.")
            return
        self.scopes.append(table)
        for item in body:
            self.visit(item)
        self.scopes.pop()
    def visit_FunctionDef(self, node):
        self._visit_scope_body(node, node.body)
    visit_AsyncFunctionDef = visit_FunctionDef
    def visit_ClassDef(self, node):
        self._visit_scope_body(node, node.body)
    def visit_Lambda(self, node):
        self._visit_outer_expressions(node)
        table = self.scope_map.get(id(node))
        if table is None:
            self.errors.append(f"cannot map lambda scope at line {node.lineno} for ctx audit.")
            return
        self.scopes.append(table)
        self.visit(node.body)
        self.scopes.pop()
    def _visit_comprehension(self, node, value_nodes):
        self.visit(node.generators[0].iter)
        table = self.scope_map.get(id(node))
        local_names = {name for generator in node.generators for name in binding_names(generator.target)}
        self.ast_scopes.append(local_names)
        if table is not None:
            self.scopes.append(table)
        for index, gen in enumerate(node.generators):
            if index:
                self.visit(gen.iter)
            self.visit(gen.target)
            for condition in gen.ifs:
                self.visit(condition)
        for value in value_nodes:
            self.visit(value)
        if table is not None:
            self.scopes.pop()
        self.ast_scopes.pop()

    def visit_ListComp(self, node):
        self._visit_comprehension(node, [node.elt])

    visit_SetComp = visit_ListComp
    visit_GeneratorExp = visit_ListComp

    def visit_DictComp(self, node):
        self._visit_comprehension(node, [node.key, node.value])

def function_node(tree, name):
    return next((n for n in reversed(tree.body) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                 and n.name == name), None)

def named_function(modules, name):
    for path, tree in modules:
        node = function_node(tree, name)
        if node is not None:
            return path, node
    return None, None

def ctx_check(node, source, filename, baseline_info):
    if node is None:
        return ["function is missing"]
    if not has_ctx_arg(node) and not any(isinstance(item, ast.Attribute) and isinstance(item.value, ast.Name)
                                         and item.value.id == "ctx" for item in ast.walk(node)):
        return []
    root_table = symtable.symtable(source, filename, "exec")
    table = find_table(root_table, node.name, node.lineno)
    if table is None:
        return ["cannot map function to symtable scope"]
    audit = CtxAudit(node, table, baseline_info["locals"], baseline_info["shared"])
    for item in node.body: audit.visit(item)
    return sorted(set(audit.errors))

def baseline_ctx_info(tree, source, filename):
    result = {}
    root_table = symtable.symtable(source, filename, "exec")
    for name in SCOPED_FUNCTIONS:
        node = function_node(tree, name)
        table = find_table(root_table, name, node.lineno) if node else None
        if node and table:
            top = function_locals(node, table)
            result[name] = {"locals": top, "shared": shared_locals(table, top, node)}
    return result

def ctx_audit_helpers(modules, infos):
    errors = []
    for path, tree in modules:
        source = path.read_text()
        path_hint = "simulate" if any("sim" in part.lower() for part in path.parts) else "evaluate"
        for node in ast.walk(tree):
            if (not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    or node.name in SCOPED_FUNCTIONS):
                continue
            has_ctx = has_ctx_arg(node) or any(
                isinstance(item, ast.Attribute) and isinstance(item.value, ast.Name)
                and item.value.id == "ctx" for item in ast.walk(node))
            if not has_ctx:
                continue
            fields = {item.attr for item in ast.walk(node) if isinstance(item, ast.Attribute)
                      and isinstance(item.value, ast.Name) and item.value.id == "ctx"}
            options = [(name, info) for name, info in infos.items()
                       if fields <= info["locals"]]
            selected = next((item for item in options if item[0] == path_hint), None)
            if selected is None and options:
                selected = max(options, key=lambda item: len(fields & item[1]["locals"]))
            if selected is None:
                selected = (path_hint, infos[path_hint]) if path_hint in infos else next(iter(infos.items()))
            name, info = selected
            errors.extend(f"{node.name}: {message}"
                          for message in ctx_check(node, source, str(path), info))
    return errors

BOOTSTRAP = ast.dump(ast.parse("sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))").body[0], include_attributes=False)
def is_bootstrap(node): return isinstance(node, ast.Expr) and ast.dump(node, include_attributes=False) == BOOTSTRAP
def is_hivewatch_import(node):
    return (isinstance(node, ast.Import) and any(a.name == "hivewatch" or a.name.startswith("hivewatch.") for a in node.names)
            or isinstance(node, ast.ImportFrom) and node.level == 0 and bool(node.module)
            and (node.module == "hivewatch" or node.module.startswith("hivewatch.")))
def main_import_errors(modules):
    return [f"{path}: imports of __main__ are not allowed" for path, tree in modules
            for node in ast.walk(tree)
            if (isinstance(node, ast.Import) and any(alias.name == "__main__" for alias in node.names))
            or isinstance(node, ast.ImportFrom) and node.module == "__main__"]
def facade_header_errors(modules):
    facade = modules[0][1]
    if len(modules) == 1 and not any(is_bootstrap(node) or is_hivewatch_import(node) for node in ast.walk(facade)): return []
    body = facade.body
    if not body or not is_docstring(body[0]):
        return ["watch.py: facade header must start with its module docstring"]
    allowed = {id(body[0])}
    index = 1
    while index < len(body) and isinstance(body[index], (ast.Import, ast.ImportFrom)) and not is_hivewatch_import(body[index]):
        allowed.add(id(body[index])); index += 1
    has_bootstrap = index < len(body) and is_bootstrap(body[index])
    if has_bootstrap:
        allowed.add(id(body[index])); index += 1
    hive_imports = 0
    while index < len(body) and is_hivewatch_import(body[index]):
        allowed.add(id(body[index])); hive_imports += 1; index += 1
    errors = ([] if has_bootstrap else ["watch.py: facade header needs one path bootstrap after stdlib imports"])
    if not hive_imports: errors.append("watch.py: facade header needs hivewatch imports after the path bootstrap")
    if any(is_hivewatch_import(node) and id(node) not in allowed for node in ast.walk(facade)):
        errors.append("watch.py: hivewatch imports must stay in the facade header")
    bootstraps = [node for _, tree in modules for node in ast.walk(tree) if is_bootstrap(node)]
    if len(bootstraps) != 1 or id(bootstraps[0]) not in allowed:
        errors.append("watch.py: exactly one path bootstrap must appear in the facade header")
    return errors
def top_units(tree):
    return [(unit(node), node) for node in tree.body if not isinstance(node, (ast.Import, ast.ImportFrom)) and not is_docstring(node) and not is_bootstrap(node)]
def source_modules(new_path):
    modules = [(new_path, ast.parse(new_path.read_text(), filename=str(new_path)))]
    package = new_path.parent / "hivewatch"
    if package.is_dir():
        modules.extend((path, ast.parse(path.read_text(), filename=str(path)))
                       for path in sorted(package.rglob("*.py")) if path.is_file())
    return modules

def nested_functions(node):
    return [n for n in ast.walk(node) if n is not node and isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]

def node_key(node): return type(node), node.name, node.lineno, node.end_lineno

def remove_extracted(node, extracted):
    targets = {node_key(item) for item in extracted}
    clone = copy.deepcopy(node)
    def visit(parent):
        for field, value in ast.iter_fields(parent):
            if isinstance(value, list):
                value[:] = [item for item in value if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) or node_key(item) not in targets]
                for item in value:
                    if isinstance(item, ast.AST): visit(item)
            elif isinstance(value, ast.AST): visit(value)
    visit(clone)
    return clone

def check(old_path, new_path):
    old_source = old_path.read_text()
    old_tree = ast.parse(old_source, filename=str(old_path))
    modules = source_modules(new_path)
    facade = modules[0][1]
    errors = []
    if module_doc(old_tree) != module_doc(facade) or module_doc(facade) is None:
        errors.append("watch.py: baseline module docstring must remain the facade's first statement")

    infos = baseline_ctx_info(old_tree, old_source, str(old_path))
    errors.extend(facade_header_errors(modules))
    errors.extend(main_import_errors(modules))
    actual = [(path, label, node) for path, tree in modules for label, node in top_units(tree)]
    used = set()
    resolution_modules = {}
    expected = top_units(old_tree)
    scoped = {node.name: node for _, node in expected
              if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in SCOPED_FUNCTIONS}

    for label, old_node in expected:
        if old_node in scoped.values():
            continue
        candidates = [i for i, (_, new_label, node) in enumerate(actual)
                      if i not in used and new_label == label and type(node) is type(old_node)]
        exact = next((i for i in candidates
                      if canonical(old_node) == canonical(actual[i][2])), None)
        if exact is None:
            errors.append(f"{label}: {'value changed' if candidates else 'missing'}")
        else:
            used.add(exact)
            if isinstance(old_node, SCOPE_NODES):
                resolution_modules[id(old_node)] = actual[exact][0]

    extracted = defaultdict(list)
    claimed_nested = set()
    for i, (path, label, node) in enumerate(actual):
        if i in used or not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for parent_name, parent in scoped.items():
            info = infos.get(parent_name)
            if not info:
                continue
            original = next((item for item in nested_functions(parent)
                             if id(item) not in claimed_nested
                             and canonical(item, info["locals"]) == canonical(node, info["locals"])), None)
            if original is None:
                continue
            ctx_errors = ctx_check(node, path.read_text(), str(path), info)
            if ctx_errors:
                errors.extend(f"{node.name}: {message}" for message in ctx_errors)
                break
            extracted[parent_name].append(original)
            claimed_nested.add(id(original))
            used.add(i)
            resolution_modules[id(original)] = path
            break

    for name, old_node in scoped.items():
        info = infos.get(name)
        new_module, new_node = named_function(modules, name)
        if not info or not new_node:
            errors.append(f"{name}: missing")
            continue
        used.update(i for i, (path, _, node) in enumerate(actual)
                    if path == new_module and node is new_node)
        resolution_modules[id(old_node)] = new_module
        ctx_errors = ctx_check(new_node, new_module.read_text(), str(new_module), info)
        expected_node = remove_extracted(old_node, extracted[name])
        if ctx_errors:
            errors.extend(f"{name}: {message}" for message in ctx_errors)
        elif canonical(expected_node, info["locals"]) != canonical(new_node, info["locals"]):
            errors.append(f"{name}: function value changed")

    errors.extend(f"{label}: unexpected top-level definition" for i, (_, label, _) in enumerate(actual) if i not in used)
    errors.extend(ctx_audit_helpers(modules, infos))
    if errors:
        return sorted(set(errors))
    mappings = [{"line": node.lineno, "name": node.name,
                 "kind": type(node).__name__, "module": str(module)}
                for node in ast.walk(old_tree)
                if (module := resolution_modules.get(id(node))) is not None]
    errors.extend(run_check(old_path, new_path, mappings))
    return sorted(set(errors))
def selftest():
    old = '''def evaluate():\n    shared = 3\n    def trigger(key):\n        return shared + key\n    return trigger(2)\n'''
    correct = '''def evaluate(ctx):\n    ctx.shared = 3\n    def trigger(key):\n        return ctx.shared + key\n    return trigger(2)\n'''
    unprefixed = correct.replace("return ctx.shared + key", "return shared + key")
    inner_prefixed = correct.replace("shared + key", "shared + ctx.key")
    cases = [("correct closure rewrite", correct, True),
             ("unprefixed shared read", unprefixed, False),
             ("prefixed inner parameter", inner_prefixed, False)]
    old_tree = ast.parse(old)
    info = baseline_ctx_info(old_tree, old, "<selftest>")["evaluate"]
    for label, source, expected in cases:
        tree = ast.parse(source)
        errors = ctx_check(function_node(tree, "evaluate"), source, "<selftest>", info)
        passed = not errors and canonical(function_node(tree, "evaluate"), info["locals"]) == canonical(
            function_node(old_tree, "evaluate"))
        if passed != expected:
            print(f"selftest FAIL: {label}: {errors or 'AST mismatch'}")
            return 1
        print(f"selftest PASS: {label}")
    return 0
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old", type=Path)
    parser.add_argument("--new", type=Path)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        return selftest()
    if not args.old or not args.new:
        parser.error("--old and --new are required unless --selftest is used")
    errors = check(args.old, args.new.resolve())
    if errors:
        for error in errors:
            print(error)
        return 1
    print("AST identity: all baseline values are present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
