"""Validate the context holder used by identity-preserving scope rewrites."""
import ast


def is_docstring(node):
    return (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str))


def is_ctx_init(node):
    return (isinstance(node, ast.Assign) and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name) and node.targets[0].id == "ctx"
            and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "Ctx" and not node.value.args and not node.value.keywords)


def function_parameters(node):
    args = node.args
    return {arg.arg for arg in args.posonlyargs + args.args + args.kwonlyargs
            + [arg for arg in (args.vararg, args.kwarg) if arg]}


def ctx_copy_target(node):
    if (isinstance(node, ast.Assign) and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Attribute)
            and isinstance(node.targets[0].value, ast.Name) and node.targets[0].value.id == "ctx"):
        return node.targets[0].attr
    return None


def ctx_copy_name(node):
    name = ctx_copy_target(node)
    if name and isinstance(node.value, ast.Name) and name == node.value.id:
        return name
    return None


def ctx_prelude(node):
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or node.name not in {"evaluate", "simulate"}:
        return 0, 0
    start = int(bool(node.body and is_docstring(node.body[0])))
    if start == len(node.body) or not is_ctx_init(node.body[start]):
        return start, 0
    parameters = function_parameters(node)
    count = 1
    for item in node.body[start + 1:]:
        name = ctx_copy_name(item)
        if name is None or name not in parameters:
            break
        count += 1
    return start, count


def ctx_prelude_errors(node):
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or node.name not in {"evaluate", "simulate"}:
        return []
    start = int(bool(node.body and is_docstring(node.body[0])))
    inits = [item for item in ast.walk(node) if is_ctx_init(item)]
    first_init = start < len(node.body) and is_ctx_init(node.body[start])
    uses_ctx = any(isinstance(item, ast.Name) and item.id == "ctx" and isinstance(item.ctx, ast.Load)
                   for statement in node.body[start:] for item in ast.walk(statement))
    errors = []
    if (inits or uses_ctx) and not first_init:
        errors.append("ctx = Ctx() must be the first body statement after the optional docstring")
    if first_init and len(inits) != 1:
        errors.append("ctx = Ctx() must appear only once")
    if not first_init:
        return errors

    parameters = function_parameters(node)
    for item in node.body[start + 1:]:
        target = ctx_copy_target(item)
        if target is None or not isinstance(item.value, ast.Name):
            break
        source = item.value.id
        if target == source and target not in parameters:
            errors.append(f"ctx.{target} prelude copy must use a function parameter")
        elif target != source:
            break
    prelude_end = start + ctx_prelude(node)[1]
    copied = {ctx_copy_name(item) for item in node.body[start + 1:prelude_end]}
    used_parameters = {item.attr for statement in node.body[prelude_end:]
                       for item in ast.walk(statement)
                       if isinstance(item, ast.Attribute) and isinstance(item.value, ast.Name)
                       and item.value.id == "ctx" and item.attr in parameters}
    missing = sorted(used_parameters - copied)
    errors.extend(f"ctx.{name} parameter must be copied in the prelude" for name in missing)
    return errors


def top_level_bindings(tree):
    bindings = []

    class Collector(ast.NodeVisitor):
        def bind(self, name, node):
            if name:
                bindings.append((name, node))

        def visit_Name(self, node):
            if isinstance(node.ctx, (ast.Store, ast.Del)):
                self.bind(node.id, node)

        def visit_Import(self, node):
            for alias in node.names:
                self.bind(alias.asname or alias.name.split(".")[0], alias)

        def visit_ImportFrom(self, node):
            for alias in node.names:
                self.bind(alias.asname or alias.name, alias)

        def visit_FunctionDef(self, node):
            self.bind(node.name, node)
            for item in node.decorator_list:
                self.visit(item)
            self.visit(node.args)
            if node.returns:
                self.visit(node.returns)

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_ClassDef(self, node):
            self.bind(node.name, node)
            for item in node.decorator_list + node.bases:
                self.visit(item)
            for item in node.keywords:
                self.visit(item.value)

        def visit_Lambda(self, node):
            self.visit(node.args)

        def visit_ExceptHandler(self, node):
            self.bind(node.name, node)
            if node.type:
                self.visit(node.type)
            for item in node.body:
                self.visit(item)

        def visit_MatchAs(self, node):
            self.bind(node.name, node)
            if node.pattern:
                self.visit(node.pattern)

        def visit_MatchStar(self, node):
            self.bind(node.name, node)

        def visit_MatchMapping(self, node):
            self.bind(node.rest, node)
            self.generic_visit(node)

    collector = Collector()
    for statement in tree.body:
        collector.visit(statement)
    return bindings


class NormalizeCtx(ast.NodeTransformer):
    def __init__(self, locals_):
        self.locals = locals_
        self.outer = True

    def visit_FunctionDef(self, node):
        if self.outer:
            start, count = ctx_prelude(node)
            del node.body[start:start + count]
        return self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Attribute(self, node):
        if (isinstance(node.value, ast.Name) and node.value.id == "ctx"
                and node.attr in self.locals):
            return ast.copy_location(ast.Name(id=node.attr, ctx=node.ctx), node)
        return self.generic_visit(node)

    def visit_AnnAssign(self, node):
        if (isinstance(node.target, ast.Attribute) and isinstance(node.target.value, ast.Name)
                and node.target.value.id == "ctx" and node.target.attr in self.locals):
            node.target = ast.copy_location(ast.Name(id=node.target.attr, ctx=node.target.ctx), node.target)
            node.simple = 1
        else:
            node.target = self.visit(node.target)
        node.annotation = self.visit(node.annotation)
        if node.value:
            node.value = self.visit(node.value)
        return node

    def visit_arguments(self, node):
        if self.outer:
            self.outer = False
            for field in ("posonlyargs", "args", "kwonlyargs"):
                setattr(node, field, [arg for arg in getattr(node, field) if arg.arg != "ctx"])
            for field in ("vararg", "kwarg"):
                arg = getattr(node, field)
                if arg and arg.arg == "ctx":
                    setattr(node, field, None)
        return self.generic_visit(node)


def validate_ctx_class(modules, scoped_names, extracted=()):
    functions = [node for _, tree in modules for node in tree.body
                 if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                 and node.name in scoped_names]
    functions.extend(extracted)
    fields = {node.attr for function in functions for node in ast.walk(function)
              if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
              and node.value.id == "ctx"}
    classes = [node for _, tree in modules for node in tree.body
               if isinstance(node, ast.ClassDef) and node.name == "Ctx"]
    has_init = any(is_ctx_init(node) for function in functions for node in ast.walk(function))
    if not fields:
        return None, (["Ctx: unexpected top-level class or initialization without ctx.X fields"]
                      if classes or has_init else [])
    if len(classes) != 1:
        return None, ["Ctx: exactly one top-level class is required for ctx.X fields"]

    node = classes[0]
    class_module = next(tree for _, tree in modules if node in tree.body)
    for _, tree in modules:
        for name, binding in top_level_bindings(tree):
            if (name == "Ctx" and binding is not node) or (name == "*" and tree is class_module):
                return None, ["Ctx: module name must not be rebound or imported"]
    owners = {id(item): tree for _, tree in modules for item in tree.body}
    for function in functions:
        if function.name not in scoped_names:
            continue
        uses_ctx = any(is_ctx_init(item) or
                       isinstance(item, ast.Attribute) and isinstance(item.value, ast.Name)
                       and item.value.id == "ctx" for item in ast.walk(function))
        if uses_ctx and owners.get(id(function)) is not class_module:
            return None, [f"Ctx: {function.name} must resolve Ctx in its defining module"]

    if node.bases or node.keywords or node.decorator_list:
        return None, ["Ctx: class must not have bases, keywords, or decorators"]
    body = node.body[1:] if node.body and is_docstring(node.body[0]) else node.body
    if (len(body) != 1 or not isinstance(body[0], ast.Assign)
            or len(body[0].targets) != 1 or not isinstance(body[0].targets[0], ast.Name)
            or body[0].targets[0].id != "__slots__" or not isinstance(body[0].value, ast.Tuple)
            or not all(isinstance(item, ast.Constant) and isinstance(item.value, str)
                       for item in body[0].value.elts)):
        return None, ["Ctx: body must contain only __slots__ = a tuple of string literals"]

    slots = [item.value for item in body[0].value.elts]
    if set(slots) != fields or len(slots) != len(fields):
        missing = sorted(fields - set(slots))
        extra = sorted(set(slots) - fields)
        return None, [f"Ctx: __slots__ must match ctx.X fields (missing={missing}, extra={extra})"]
    return node, []
