# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

from django.test import TestCase

from dataops import formula_evaluation


class HasVariableTest(TestCase):

    formula1 = {u'not': False, u'rules': [
        {u'value': u'df', u'field': u'UOS_Code_a', u'operator': u'equal',
         u'input': u'text', u'type': u'string', u'id': u'UOS_Code_a'},
        {u'value': u'v2', u'field': u'ANOTHER', u'operator': u'equal',
         u'input': u'text', u'type': u'string', u'id': u'ANOTHER'}],
                u'valid': True, u'condition': u'AND'}

    formula2 = {u'not': False, u'rules': [
        {u'value': u'df', u'field': u'UOS_Code_a', u'operator': u'equal',
         u'input': u'text', u'type': u'string', u'id': u'UOS_Code_a'},
        {u'value': u'v2', u'field': u'ANOTHER', u'operator': u'equal',
         u'input': u'text', u'type': u'string', u'id': u'ANOTHER'}],
                u'valid': True, u'condition': u'AND'}

    formula3 = {u'not': False, u'rules': [
        {u'value': u'df', u'field': u'UOS_Code_b', u'operator': u'equal',
         u'input': u'text', u'type': u'string', u'id': u'UOS_Code_b'},
        {u'value': u'v2', u'field': u'ANOTHER', u'operator': u'equal',
         u'input': u'text', u'type': u'string', u'id': u'ANOTHER'}],
                u'valid': True, u'condition': u'AND'}

    def compare(self, f1, f2):

        if 'condition' in f1 and 'condition' not in f2:
            return False

        if 'condition' not in f1 and 'condition' in f2:
            return False

        if 'condition' in f1 and 'condition' in f2:

            # Assumes that the literals are in the same order
            return all([self.compare(a, b)
                        for a, b in zip(f1['rules'], f2['rules'])])

        # Dictionaries should have the same items (identically)
        return f1 == f2

    def test_rename_variable_true(self):

        self.assertTrue(self.compare(self.formula1, self.formula2))

        f3 = formula_evaluation.rename_variable(self.formula1,
                                                'UOS_Code_a',
                                                'UOS_Code_b')

        self.assertTrue(self.compare(self.formula3, f3))

    def test_evaluate_formula(self):

        self.assertTrue(
            formula_evaluation.evaluate_top_node(
                self.formula1, {'UOS_Code_a': 'df', 'ANOTHER': 'v2'}
            )
        )
