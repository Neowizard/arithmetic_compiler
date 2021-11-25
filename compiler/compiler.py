import compiler.parser as parser


def compile_file(_input, output):
    with open(_input, 'rt') as input_file:
        input_code = input_file.read()
    compile(input_code, output)


def compile(code, output):
    ast = parser.nt_statements(code)
    if ast.next_token_index < len(code):
        raise Exception(f'Failed to parse code at {ast.next_token_index}')
    output_code = ast.match.codegen()

    with open(output, 'wt') as output_file:
        output_file.write(output_code)
