import compiler.parser as parser


def compile_file(_input, output):
    with open(_input, 'rt') as input_file:
        input_code = input_file.read()
    compile(input_code, output)


def compile(code, output):
    ast = parser.nt_statements(code).match
    output_code = ast.codegen()

    with open(output, 'wt') as output_file:
        output_file.write(output_code)
