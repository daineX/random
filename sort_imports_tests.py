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
import os as os_mod
from bla import thisisareallylongimportedfunctionthatmightneedsomeindentationye
from aster import parse
from ast.blarg import foo
from ast import nop
"""
        expected_output = """from __future__ import absolute_import

from aster import parse
from bla import thisisareallylongimportedfunctionthatmightneedsomeindentationye
import os as os_mod
import sys

from ast import (
    Expr,
    Import,
    ImportFrom,
    Module,
    NodeTransformer,
    NodeVisitor,
    nop,
    parse
)
from ast.blarg import foo

from wsgiref.handlers import BaseCGIHandler, CGIHandler, SimpleHandler

from spam import eggs

from ..base import eggs, foobar, spam
from .. import bla"""
        res = main(input_,
                   ["ast", "wsgiref", "spam"])
        print res, expected_output
        self.assertEqual(expected_output, res)
