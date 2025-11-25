#!/usr/bin/env python3
import re
from rich import print
from rich.panel import Panel

class Test:

    def preprocess(data, name):
        pattern = r'#BEGINTEST\s+void\s+(\w+)\s*\((.*?)\)'
        replacement = r'__RICHTEST \1(\2)'
        data = re.sub(pattern, replacement, data)

        for pattern, replacement in [(r'#SETUP', '__PHASE SETUP;'),
                                    (r'#EXERCISE', '__PHASE EXERCISE;'),
                                    (r'#VERIFY', '__PHASE VERIFY;'),
                                    (r'#TEARDOWN', '__PHASE TEARDOWN;'),
                                    # TODO: this must be more clever?
                                    (r'_;', 'nondet_int();'),
                                    (r'#ENDTEST', '')]:
            data = data.replace(pattern, replacement)

        assume_counter = 1

        def replace_match(match):
            nonlocal assume_counter
            replacement = f'__ASSUME assume{assume_counter} = "{match.group(1)}";'
            assume_counter += 1
            return replacement

        pattern = r'#ASSUME\s+(.*)'
        data = re.sub(pattern, replace_match, data)

        def replace_match(match):
            nonlocal assert_counter
            replacement = f'\n__ASSERT assert{assert_counter} = "{match.group(1)}";'
            assert_counter += 1
            return replacement
        pattern = r'\n\s*#ASSERT\s+(.*)'
        # pattern = r'#ASSERT\s+(.*)'
        assert_counter = 1
        data = re.sub(pattern, replace_match, data)

        data = """typedef char* __ASSUME;
typedef char* __ASSERT;
int nondet_int();
""" + "void " + name + "() {\n" + data + "\n}\n"
        # includes = [line for line in data.split('\n') if line.startswith("#include")]
        # defines = [line for line in data.split('\n') if line.startswith("#define")]
        return data

    def __init__(self, lines, input_file, input_begin, input_length):
        head = lines[0]
        end = lines[-1]
        head_p = r'void (.*)\(\) {'
        end_p = r'}'
        rhead = re.match(head_p, head)
        rend = re.match(end_p, end)
        assert(rhead and rend)
        self.name = rhead.groups(0)[0]
        self.code = Test.preprocess('\n'.join(lines[1:-1]), self.name)
        self.input_file = input_file
        self.input_begin = input_begin + 5 # TODO: This is because we add typedfs, nondet_int, etc.
        self.input_length = input_length

    def print(self):
        print(Panel.fit(self.code, title=self.name))



    def from_lines(lines, dirpath):
        newlines = []
        input_begin = None
        input_length = None
        input_file = None

        for idx, l in enumerate(lines):
            p_input = r'\s*#INPUT (.*)'
            if re.match(p_input, l):
                assert(not input_begin) # Only allow one input block
                input_begin = idx
                input_file = re.match(p_input, l).groups()[0]
                input_lines = open(dirpath + "/" + input_file, 'r').readlines()
                numbered_lines = [""] # TODO: Remove this and fix coverage parsing accordingy
                for n, l in enumerate(input_lines):
                    numbered_lines.append(l.strip())
                input_length = len(numbered_lines) - 1
                newlines = newlines + numbered_lines
            else:
                newlines.append(l)
        return Test(newlines, input_file, input_begin, input_length)
