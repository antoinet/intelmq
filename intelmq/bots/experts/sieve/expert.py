# -*- coding: utf-8 -*-
"""
SieveExpertBot filters and modifies events based on a specification language similar to mail sieve.

TODO: Document possible necessary configurations.
Parameters:
    file: string
"""
from __future__ import unicode_literals

# imports for additional libraries and intelmq
import os
import intelmq.lib.exceptions as exceptions
import re
from intelmq.lib.bot import Bot
from textx.metamodel import metamodel_from_file
from textx.exceptions import TextXError


class SieveExpertBot(Bot):

    def init(self):
        # read the sieve grammar
        try:
            filename = os.path.join(os.path.dirname(__file__), 'sieve.tx')
            self.metamodel = metamodel_from_file(filename)
        except TextXError as e:
            self.logger.error('Could not process sieve grammar file. Error in (%d, %d)', e.line, e.col)
            self.logger.error(str(e)) # TODO: output textx exception message properly
            self.stop()

        # validate parameters
        if not os.path.exists(self.parameters.file):
            raise exceptions.InvalidArgument('file', got=self.parameters.file, expected='existing file')

        # parse sieve file
        try:
            self.sieve = self.metamodel.model_from_file(self.parameters.file)
        except TextXError as e:
            self.logger.error('Could not parse sieve file \'%r\', error in (%d, %d)', self.parameters.file, e.line, e.col)
            self.logger.error(str(e)) # TODO: output textx exception message properly
            self.stop()

    def process(self):
        event = self.receive_message()

        keep = False
        for rule in self.sieve.rules:
            keep = self.process_rule(rule, event)
            if not keep:
                break

        if keep:
            self.send_message(event)

        self.acknowledge_message()

    def process_rule(self, rule, event):
        match = self.match_expression(rule.expr, event)
        keep = True
        if match:
            for action in rule.actions:
                keep = self.process_action(action, event)
                if not keep:
                    break
        return keep


    def match_expression(self, expr, event):
        for conj in expr.conj:
            if self.process_conjunction(conj, event):
                return True
        return False

    def process_conjunction(self, conj, event):
        for cond in conj.cond:
            if not self.process_condition(cond, event):
                return False
        return True

    def process_condition(self, cond, event):
        match = cond.match
        if match.__class__.__name__ == 'ExistMatch':
            return self.process_exist_match(match.key, event)
        elif match.__class__.__name__ == 'StringMatch':
            return self.process_string_match(match.key, match.op, match.value, event)
        elif match.__class__.__name__ == 'NumericMatch':
            return self.process_numeric_match(match.key, match.op, match.value, event)
        elif match.__class__.__name__ == 'Expression':
            return self.match_expression(match, event)
        pass

    def process_exist_match(self, key, event):
        return key in event

    def process_string_match(self, key, op, value, event):
        if key not in event:
            return False

        if value.__class__.__name__ == 'SingleStringValue':
            return self.process_string_operator(event[key], op, value.value)
        elif value.__class__.__name__ == 'StringValueList':
            for val in value.values:
                if self.process_string_operator(event[key], op, val):
                    return True
            return False

    def process_string_operator(self, lhs, op, rhs):
        if op is '==':
            return lhs == rhs
        elif op is '!=':
            return lhs != rhs
        elif op is ':contains':
            return lhs.find(rhs) >= 0
        elif op is '=~':
            return re.fullmatch(rhs, lhs) is not None
        elif op is '!~':
            return re.fullmatch(rhs, lhs) is None

    def process_numeric_match(self, key, op, value, event):
        if key not in event:
            return False

        if value.__class__.__name__ == 'SingleNumericValue':
            return self.process_numeric_operator(event[key], op, value.value)
        elif value.__class__.__name__ == 'NumericValueList':
            for val in value.values:
                if self.process_numeric_operator(event[key], op, val):
                    return True
            return False

    def process_numeric_operator(self, lhs, op, rhs):
        return eval(lhs + op + rhs)


    def process_action(self, action, event):
        # TODO: Implement
        return True


BOT = SieveExpertBot