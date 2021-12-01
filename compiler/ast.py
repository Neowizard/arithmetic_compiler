import enum
import abc


class NodeType(enum.Enum):
    Num = 'num'
    Var = 'var'
    AddExpr = 'add_expr'
    SubExpr = 'sub_expr'
    MulExpr = 'mul_expr'
    DivExpr = 'div_expr'
    Assign = 'assignment'
    LoopAssignment = 'loop_assignment'
    Program = 'program'


class AstNode:
    @property
    @abc.abstractmethod
    def type(self):
        raise NotImplementedError

    @abc.abstractmethod
    def __repr__(self):
        raise NotImplementedError

    @abc.abstractmethod
    def codegen(self):
        raise NotImplementedError


class Num(AstNode):
    def __init__(self, value):
        self._value = value

    @property
    def value(self):
        return self._value

    @property
    def type(self):
        return NodeType.Num

    def codegen(self):
        if self._value >= (2 ** 64) - 1:
            raise ValueError(f'Cannot store {self._value} in a 64bit register')
        code = f'''; {self}: Codegen
mov rax, {self._value}'''
        return code

    def __str__(self):
        return f'{self._value}'

    def __repr__(self):
        return f'Num(value={self._value})'


class Var(AstNode):

    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return NodeType.Num

    def codegen(self):
        code = f'''; {self}: Codegen 
mov rax, {self._name}'''
        return code

    def __str__(self):
        return self._name

    def __repr__(self):
        return f'Var(name={self._name})'


class ArithExpr(AstNode):
    def __init__(self, node_type, left_operand, right_operand):
        self._type = node_type
        self._left_operand = left_operand
        self._right_operand = right_operand

    @property
    def left_operand(self):
        return self._left_operand

    @property
    def right_operand(self):
        return self._right_operand

    @property
    def type(self):
        return self._type

    def _addsub_op(self, op):
        code = f'''{op} rax, rbx'''
        return code

    def _muldiv_op(self, op):
        code = f'''{op} rbx'''
        return code

    def _op(self):
        node_types_to_ops = {NodeType.AddExpr: self._addsub_op('add'),
                             NodeType.SubExpr: self._addsub_op('sub'),
                             NodeType.MulExpr: self._muldiv_op('mul'),
                             NodeType.DivExpr: self._muldiv_op('div')}
        return node_types_to_ops[self.type]

    def codegen(self):
        left_operand_code = self._left_operand.codegen()
        right_operand_code = self._right_operand.codegen()
        op = self._op()
        code = f'''; {self}: Codegen for right operand
{right_operand_code}
; {self}: Pushing result of right operand evaluation
push rax
; {self}: Codegen for left operand
{left_operand_code}
; {self}: Applying op
pop rbx
{op}'''
        return code

    def __str__(self):
        op_str = {NodeType.AddExpr: '+',
                  NodeType.SubExpr: '-',
                  NodeType.MulExpr: '*',
                  NodeType.DivExpr: '/'}[self.type]
        return f'{self._left_operand} {op_str} {self._right_operand}'

    def __repr__(self):
        return f'ArithExpr(type={self._type.value}, ' \
               f'left_operand={self._left_operand}, ' \
               f'right_operand={self._right_operand})'


class Assignment(AstNode):
    def __init__(self, var, expr):
        self._var = var
        self._expr = expr

    @property
    def type(self):
        return NodeType.Assign

    def codegen(self):
        expr_code = self._expr.codegen()
        code = f'''; {self}: Codegen
{expr_code}
; {self}: Writing expression value to var 
mov {self._var.name}, rax'''
        return code

    def __str__(self):
        return f'{self._var} <- {self._expr}'

    def __repr__(self):
        return f'Assignment(var={self._var}, expr={self._expr})'


class LoopAssignment(AstNode):
    _label_counter = 0

    def __init__(self, counter, assignments):
        self._label = f'loop_{self._label_counter}'
        self._label_counter += 1

        self._counter = counter
        self._assignments = assignments

    @property
    def type(self):
        return NodeType.LoopAssignment

    def _assignments_code(self):
        return [assignment.codegen() for assignment in self._assignments]

    def codegen(self):
        assignments_code = "\n".join(self._assignments_code())
        counter_code = self._counter.codegen()
        code = f'''
; {self}: Evaluating counter
{counter_code}
; {self}: Storing counter in rcx
mov rcx, rax
{self._label}:
; {self}: Assignments code
{assignments_code}
loop {self._label}'''
        return code

    def __str__(self):
        return f"loop {self._counter}"

    def __repr__(self):
        return f'str LoopAssignment(counter={self._counter}, assignment={self._assignments})'


class Program(AstNode):
    def __init__(self, statements):
        self._statements = statements

    @property
    def type(self):
        return NodeType.Program

    def __repr__(self):
        statements = [f'{statement}' for statement in self._statements]
        statements = "\n".join(statements)
        return f'Program({statements})'

    def codegen(self):
        statements_code = [statement.codegen() for statement in self._statements]
        printed_statements = [f'{statement}\ncall print_rax\n' for statement in statements_code]
        statements = "".join(printed_statements)
        code = f'''
global main
main:
; Resetting r10, r11, r12, r13
mov r10, 0
mov r11, 0
mov r12, 0
mov r13, 0
{statements}

mov rax, 60
mov rdi, 0
syscall

section .data
format: db "%lld", 10

section .text
extern printf
print_rax:
    push rax
    push rcx
    push r10
    push r11
    push r12
    push r13
    mov rdi, format
    mov rsi, rax
    mov rax, 0
    call printf
    pop r13
    pop r12
    pop r11
    pop r10
    pop rcx
    pop rax
    ret'''
        return code
