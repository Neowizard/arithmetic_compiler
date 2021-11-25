import infra.pc as pc
import compiler.arith_ast as arith_ast


def _spaced(parser):
    nt_space = pc.make_const(lambda c: ord(c) <= 32)
    nt_comment = pc.caten(pc.make_char('#'), pc.star(pc.make_const(lambda c: c != '\n')))
    nt_whitespaces = pc.star(pc.disj(nt_comment, nt_space))
    nt_spaced = pc.caten_list([nt_whitespaces, parser, nt_whitespaces])
    return pc.pack(nt_spaced, lambda l: l[1])


def _spaced_token(word):
    return _spaced(pc.make_word(word))


_token_assignment = _spaced_token('=')
_token_eos = _spaced_token(';')
_token_loop = _spaced_token('loop')
_token_open_curly = _spaced_token('{')
_token_close_curly = _spaced_token('}')
_token_muldiv = _spaced(pc.make_oneof("*/"))
_token_addsub = _spaced(pc.make_oneof("+-"))
_token_num = _spaced(pc.plus(pc.make_char_range('0', '9')))
_token_num = pc.pack(_token_num, lambda digits: int(''.join(digits)))

_var_token = pc.pack(_spaced(pc.disj_list([pc.make_word("r10"),
                                           pc.make_word("r11"),
                                           pc.make_word("r12"),
                                           pc.make_word("r13")])),
                     lambda var_chars: arith_ast.Var(''.join(var_chars)))


def make_int(sign_num):
    sign = sign_num[0]
    sign = -1 if sign == '-' else 1

    num = sign * sign_num[1]
    return arith_ast.Num(num)


nt_int = pc.pack(pc.caten(pc.disj(pc.make_oneof('+-'), pc.epsilon_parser), _token_num), make_int)

nt_operand = pc.disj(nt_int, _var_token)


def make_arith_node(parsed):
    left_operand = parsed[0]
    tail = parsed[1]
    if len(tail) == 0:
        return left_operand

    operation = tail[0][0]
    second_operand = tail[0][1]

    operation_to_node_type = {'+': arith_ast.NodeType.AddExpr,
                              '-': arith_ast.NodeType.SubExpr,
                              '*': arith_ast.NodeType.MulExpr,
                              '/': arith_ast.NodeType.DivExpr}
    node_type = operation_to_node_type[operation]
    first_operation = arith_ast.ArithExpr(node_type, left_operand, second_operand)

    return make_arith_node((first_operation, tail[1:]))


_nt_muldiv_expr = pc.pack(pc.caten(_token_muldiv, nt_operand),
                          lambda op_and_rhs: (op_and_rhs[0], op_and_rhs[1]))
_nt_muldiv_expr = pc.caten(nt_operand, pc.star(_nt_muldiv_expr))
nt_muldiv_expr = pc.pack(_nt_muldiv_expr, make_arith_node)

_nt_addsub_expr = pc.pack(pc.caten(_token_addsub, nt_muldiv_expr),
                          lambda op_and_rhs: (op_and_rhs[0], op_and_rhs[1]))
_nt_addsub_expr = pc.caten(nt_muldiv_expr, pc.star(_nt_addsub_expr))
nt_addsub_expr = pc.pack(_nt_addsub_expr, make_arith_node)

nt_arith_expr = nt_addsub_expr


def make_assignment_node(elements):
    var = elements[0]
    expr = elements[2]
    return arith_ast.Assignment(var, expr)


_nt_assignment = pc.caten_list([_var_token, _token_assignment, nt_arith_expr, _token_eos])
nt_assignment = pc.pack(_nt_assignment, make_assignment_node)


def make_loop_assignment_node(elements):
    counter = elements[1]
    assignment = elements[3]
    return arith_ast.LoopAssignment(counter, assignment)


_nt_loop_assignment = pc.caten_list([_token_loop, nt_operand,
                                     _token_open_curly,
                                     nt_assignment,
                                     _token_close_curly])
nt_loop_assignment = pc.pack(_nt_loop_assignment, make_loop_assignment_node)


def make_program(statements):
    return arith_ast.Program(statements)


nt_statements = pc.pack(pc.star(pc.disj(nt_assignment, nt_loop_assignment)), make_program)
