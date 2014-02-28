from unittest import TestCase

from sort_imports import main

class TestSortImports(TestCase):

    def test(self):
        input_ = """from __future__ import absolute_import
from spam import eggs
import sys
from wsgiref.handlers import CGIHandler, BaseCGIHandler, SimpleHandler
from ast import Expr, parse, Import, ImportFrom, NodeTransformer, NodeVisitor, Module
from ..base import spam, eggs, foobar
from .. import bla
"""
        expected_output = """from __future__ import absolute_import
import sys
from ast import (
    Expr,
    Import,
    ImportFrom,
    Module,
    NodeTransformer,
    NodeVisitor,
    parse
)
from wsgiref.handlers import BaseCGIHandler, CGIHandler, SimpleHandler
from spam import eggs
from ..base import eggs, foobar, spam
from .. import bla"""
        res = main(input_,
                   ["ast", "wsgiref", "spam"])
        self.assertEqual(expected_output, res)
