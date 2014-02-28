#!/usr/bin/env python
from __future__ import unicode_literals, print_function

from ast import (
    Import,
    ImportFrom,
    Module,
    NodeTransformer,
    NodeVisitor,
    parse
)
import sys


class ImportWriter(NodeVisitor):

    def format_name(self, name):
        if name.asname:
            return "{} as {}".format(name.name, name.asname)
        else:
            return name.name

    def format_names_single_line(self, formatted_names):
        return ', '.join(formatted_names)

    def format_names_multiple_lines(self, formatted_names):
        res = "(\n"
        res += ",\n".join("    {}".format(name) for name in formatted_names)
        res += "\n)"
        return res

    def format_names(self, initial_length, names):
        formatted_names = [self.format_name(name) for name in names]
        if (initial_length + sum(
                len(formatted_name) + 2
                for formatted_name in formatted_names) > 80):
            return self.format_names_multiple_lines(formatted_names)
        else:
            return self.format_names_single_line(formatted_names)

    def visit_ImportFrom(self, node):
        if node.module:
            res = 'from {}{} import '.format(node.level * ".", node.module)
        else:
            res = 'form {} import '.format(node.level * ".")
        res += self.format_names(len(res), node.names)
        print(res)

    def visit_Import(self, node):
        print("import {}".format(self.format_names(7, node.names)))


class SortImports(NodeTransformer):

    def __init__(self, deferred=None):
        self.deferred = deferred or []

    def sort_names(self, names):
        return sorted(names, key=lambda x: x.name.lower())

    def visit_ImportFrom(self, node):
        node.names = self.sort_names(node.names)
        return node

    def visit_Import(self, node):
        node.names = self.sort_names(node.names)
        return node

    def sort_imports(self, imports):
        def sort_key(node):
            defer_level = 0
            if hasattr(node, "module"):
                for index, module_name in enumerate(self.deferred):
                    if node.module.startswith(module_name):
                        defer_level = index + 1
                        break
                name = node.module.lower()
            else:
                name = self.sort_names(node.names)[0].name
            if hasattr(node, "level"):
                level = node.level
            else:
                level = 0
            return level, defer_level, name
        return sorted(imports, key=sort_key)

    def visit_Module(self, node):
        imports = []
        for subnode in node.body:
            if isinstance(subnode, (Import, ImportFrom)):
                imports.append(self.visit(subnode))
        sorted_imports = self.sort_imports(imports)
        return Module(body=sorted_imports)


def main(source, deferred):
    parsed = parse(source)
    changed = SortImports(deferred=deferred).visit(parsed)
    ImportWriter().visit(changed)


if __name__ == "__main__":
    main(sys.stdin.read(), sys.argv[1:])
