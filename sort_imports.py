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
from itertools import groupby
import sys


def is_magic_import(node):
    return hasattr(node, "module") and node.module == "__future__"

def sort_names(names):
    def sort_key(alias_obj):
        return (alias_obj.name.lower(), alias_obj.asname)
    sorted_names = sorted(names, key=sort_key)
    res = []
    for key, group in groupby(sorted_names, sort_key):
        res.append(group.next())
    return res

class ImportWriter(NodeVisitor):

    def format_name(self, name):
        if name.asname:
            return "{} as {}".format(name.name, name.asname)
        else:
            return name.name

    def format_names_single_line(self, formatted_names):
        return ', '.join(formatted_names)

    def format_names_multiple_lines(self, formatted_names):
        names_lines = ",\n".join("    {}".format(name) for name in formatted_names)
        return "(\n{}\n)".format(names_lines)

    def format_names(self, initial_length, names):
        formatted_names = [self.format_name(name) for name in names]
        if (initial_length + sum(
                len(formatted_name) + 2
                for formatted_name in formatted_names) > 81):
            return self.format_names_multiple_lines(formatted_names)
        else:
            return self.format_names_single_line(formatted_names)

    def visit_ImportFrom(self, node):
        imports = 'from {level}{module} import '.format(level=node.level * ".",
                                                        module=node.module or '')
        names = self.format_names(len(imports), node.names)
        return "{}{}".format(imports, names)

    def visit_Import(self, node):
        return "import {}".format(self.format_names(7, node.names))

    def visit_Module(self, node):
        current_sort_key = (True, 0, 0)
        res = []
        for subnode in node.body:
            is_magic, level, defer_level, _ = subnode.sort_key
            if (is_magic, level, defer_level) != current_sort_key:
                if res:
                    res.append("")
                current_sort_key = (is_magic, level, defer_level)
            res.append(self.visit(subnode))
        return '\n'.join(res)


class RemoveDuplicates(NodeTransformer):

    def __init__(self):
        self.last_node = None

    def visit_ImportFrom(self, node):
        if self.last_node is not None:
            if (node.module == self.last_node.module and
                node.level == self.last_node.level):
                    self.last_node.names = sort_names(self.last_node.names +
                                                      node.names)
                    return None
            else:
                res = self.last_node
                self.last_node = node
                return [res]
        else:
            self.last_node = node

    def visit_Import(self, node):
        if self.last_node:
            res = [self.last_node, node]
            self.last_node = None
            return res
        return [node]

    def visit_Module(self, node):
        new_body = []
        for subnode in node.body:
            res = self.visit(subnode)
            if res is not None:
                new_body.extend(res)
        if self.last_node is not None:
            new_body.append(self.last_node)
        return Module(body=new_body)


class SortImports(NodeTransformer):

    def __init__(self, deferred=None):
        self.deferred = deferred or []

    def sort_names_for_node(self, node):
        node.names = sort_names(node.names)
        return node

    visit_Import = sort_names_for_node
    visit_ImportFrom = sort_names_for_node

    def sort_imports(self, imports):
        def sort_key(node):
            defer_level = 0
            if hasattr(node, "module") and node.module:
                for index, module_name in enumerate(self.deferred):
                    if (node.module == module_name or
                        node.module.startswith(module_name + ".")):
                        defer_level = index + 1
                        break
                name = node.module.lower()
            else:
                name = sort_names(node.names)[0].name
            if hasattr(node, "level"):
                level = node.level
            else:
                level = 0
            return not is_magic_import(node), level, defer_level, name
        for node in imports:
            node.sort_key = sort_key(node)
        return sorted(imports, key=lambda node: node.sort_key)

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
    changed = RemoveDuplicates().visit(changed)
    return ImportWriter().visit(changed)


if __name__ == "__main__":
    print(main(sys.stdin.read(), sys.argv[1:]))
