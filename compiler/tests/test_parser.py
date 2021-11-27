import compiler.parser as parser
import compiler.ast as arith_ast


def test_operand():
    subject = parser.nt_operand
    num_input = "123"
    var_input = "r11"

    actual_num = subject(num_input).match
    actual_var = subject(var_input).match
    assert actual_num.value == 123
    assert actual_var.name == "r11"


def test_muldiv_expr():
    subject = parser.nt_muldiv_expr
    input = "1 / r12 / r13/4*     5"

    actual = subject(input).match
    assert actual.type == arith_ast.NodeType.MulExpr
    assert actual.right_operand.value == 5

    left_operand = actual.left_operand
    assert left_operand.type == arith_ast.NodeType.DivExpr
    assert left_operand.right_operand.value == 4

    left_operand = left_operand.left_operand
    assert left_operand.type == arith_ast.NodeType.DivExpr
    assert left_operand.right_operand.name == 'r13'

    left_operand = left_operand.left_operand
    assert left_operand.type == arith_ast.NodeType.DivExpr
    assert left_operand.right_operand.name == 'r12'

    left_operand = left_operand.left_operand
    assert left_operand.type == arith_ast.NodeType.Num
    assert left_operand.value == 1


def test_addsub_expr():
    subject = parser.nt_addsub_expr
    input = '''5+5-
    5*r12'''

    actual = subject(input).match
    assert actual.type == arith_ast.NodeType.SubExpr
    assert actual.right_operand.type == arith_ast.NodeType.MulExpr
    assert actual.right_operand.right_operand.name == 'r12'
    assert actual.right_operand.left_operand.value == 5

    left_operand = actual.left_operand
    assert left_operand.type == arith_ast.NodeType.AddExpr
    assert left_operand.right_operand.value == 5


def test_loop():
    subject = parser.nt_loop_assignment
    input = '''loop r10 r10 = 1 r10=0;'''

    actual = subject(input).match
    assert actual.type == arith_ast.NodeType.LoopAssignment
