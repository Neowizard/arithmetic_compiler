#! /bin/python

import compiler.compiler as compiler
import sys

if __name__ == '__main__':
    args = sys.argv
    if len(args) < 3:
        print(f'Usage: {sys.argv[0]} <input_file> <output_file>\n'
              f'Reads <input_file>, compiles it down to x86_64 assembly and writes it to <output_file> '
              f'(overriding <output_file>)')

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    compiler.compile_file(input_file, output_file)
