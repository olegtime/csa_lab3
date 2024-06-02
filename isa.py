from enum import Enum


class OpCode(Enum):
    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"
    MOD = "mod"

    INC = "inc"
    DEC = "dec"

    READ = "read"
    SAVE = "save"

    POP = "pop"
    PUSH = "push"

    SWAP = "swap"
    DUP = "dup"
    EQL = "eql"
    LESS = "less"
    LRG = "lrg"

    JMP = "jmp"
    JUZ = "juz"
    JNZ = "jnz"

    RET = "ret"

    HLT = "hlt"

    NOP = "nop"

    def __str__(self):
        return self.name.lower()

    def __repr__(self):
        return str(self)


class Instruction:
    def __init__(self, opcode: OpCode, operand: int | None = None):
        self.opcode = opcode
        self.operand = operand

    def __str__(self):
        return f"{self.opcode.name} {self.operand}"

    def __repr__(self):
        return str(self)


def get_opcode_by_name(name: str) -> OpCode:
    for op in OpCode:
        if op.name.lower() == name.lower():
            return op
    return OpCode.NOP


class Term(Enum):
    EQUALS = "="
    LESS = "<"
    GREATER = ">"
    DUP = "dup"
    DROP = "drop"
    ADD = "+"
    SUB = "-"
    MUL = "*"
    DIV = "/"
    MOD = "mod"
    NOT = "not"
    KEY = "key"
    SWAP = "swap"
    SAVE = "!"
    READ = "@"
    READ_OUTPUT = "?"
    PRINT = "."
    PRINT_CHAR = "emit"
    PRINT_STR = ".\""
    END_STR = "\""
    PRINT_CR = "cr"
    DEF_FUNC = ":"
    END_FUNC = ";"
    IF = "if"
    ELSE = "else"
    THEN = "then"
    BEGIN = "begin"
    UNTIL = "until"
    DO = "do"
    LOOP = "loop"
    LEAVE = "leave"
    NOP = "nop"

    def __str__(self):
        return self.name.lower()

    def __repr__(self):
        return str(self)


def get_term_by_name(name: str) -> Term:
    for term in Term:
        if term.name.lower() == name.lower():
            return term
    return Term.NOP
