import sys
import logging
import json
from alu import ALU
from stack import Stack
from memory import Memory
from enum import Enum


class ReturnStackSignal(Enum):
    PUSH = 1
    POP = 2


class DataStackSignal(Enum):
    PUSH = 1
    POP = 2
    SWAP = 3


class DataMemorySignal(Enum):
    WRITE = 1
    READ = 2
    SET_ADDRESS = 3


class InstructionMemorySignal(Enum):
    READ = 1
    SET_ADDRESS = 2


class LatchSignal(Enum):
    IP = 1
    IR = 2


class IpMuxSignal(Enum):
    IP = 1
    DS = 2
    RS = 3
    ALU = 4


class DsMuxSignal(Enum):
    DS = 1
    DM = 2
    ALU = 3


class DmMuxSignal(Enum):
    DS = 1
    ALU = 2


class AluSignal(Enum):
    ADD = 1
    SUB = 2
    MUL = 3
    DIV = 4
    MOD = 5
    COMP = 6
    EQUALS = 7
    LESS = 8
    GREATER = 9
    SET_A = 10
    SET_B = 11
    NOT_A = 12
    NOT_B = 13


class AluMuxSignalA(Enum):
    DS = 1
    IM = 2
    ALU = 3
    ZERO = 4
    ONE = 5


class AluMuxSignalB(Enum):
    DS = 1
    IM = 2
    ALU = 3
    ZERO = 4
    ONE = 5


class ControlSignal(Enum):
    HALT = 1
    NOP = 2


class JumpSignal(Enum):
    JMP = 1
    JMZ = 2
    JNZ = 3


class MUX:
    def __init__(self):
        self.mux_value = None

    def choose(self, value):
        self.mux_value = value

    def get(self):
        return self.mux_value


class DataPath:
    def __init__(self):
        self.data_memory: Memory = Memory()
        self.instruction_memory: Memory = Memory()

        self.return_stack: Stack = Stack()
        self.data_stack: Stack = Stack()

        self.alu = ALU()

        self.ip_mux = MUX()
        self.ds_mux = MUX()
        self.dm_mux = MUX()
        self.alu_mux_a = MUX()
        self.alu_mux_b = MUX()

        self.input_buffer: list[int] = []
        self.output_buffer: list[int] = []

        self.instruction_pointer: int = 0
        self.instruction_register: int = 0

        self.operand_flag: int = 0

        self.exit_flag: int = 0

        self.handle_signal = {
            ReturnStackSignal: self.return_stack_signal,
            DataStackSignal: self.data_stack_signal,
            DataMemorySignal: self.data_memory_signal,
            InstructionMemorySignal: self.instruction_memory_signal,
            LatchSignal: self.latch,
            IpMuxSignal: self.ip_mux_choice,
            DsMuxSignal: self.ds_mux_choice,
            DmMuxSignal: self.dm_mux_choice,
            AluSignal: self.alu_signal,
            AluMuxSignalA: self.alu_mux_a_choice,
            AluMuxSignalB: self.alu_mux_b_choice,
            JumpSignal: self.jump_signal,
            ControlSignal: self.control_signal,
        }

    def return_stack_signal(self, signal: ReturnStackSignal):
        match signal:
            case ReturnStackSignal.PUSH:
                self.return_stack.push(self.instruction_pointer)
            case ReturnStackSignal.POP:
                self.return_stack.pop()

    def data_stack_signal(self, signal: DataStackSignal):
        match signal:
            case DataStackSignal.PUSH:
                self.data_stack.push(self.ds_mux.get())
            case DataStackSignal.POP:
                self.data_stack.pop()
            case DataStackSignal.SWAP:
                self.data_stack.swap()

    def data_memory_signal(self, signal: DataMemorySignal):
        match signal:
            case DataMemorySignal.WRITE:
                assert self.data_memory.address_register != 0, "can't write to input device"
                if self.data_memory.address_register == 1:
                    self.output_buffer.append(self.dm_mux.get())
                else:
                    self.data_memory.write(self.dm_mux.get())
            case DataMemorySignal.READ:
                assert self.data_memory.address_register != 1, "can't read from output device"
                if self.data_memory.address_register == 0:
                    self.data_memory.data_register = self.input_buffer.pop(0)
                else:
                    self.data_memory.read()
            case DataMemorySignal.SET_ADDRESS:
                self.data_memory.address_register = self.dm_mux.get()

    def instruction_memory_signal(self, signal: InstructionMemorySignal):
        match signal:
            case InstructionMemorySignal.READ:
                self.instruction_memory.read()
            case InstructionMemorySignal.SET_ADDRESS:
                self.instruction_memory.address_register = self.instruction_pointer

    def ip_mux_choice(self, signal: IpMuxSignal):
        match signal:
            case IpMuxSignal.IP:
                self.ip_mux.choose(self.instruction_pointer + 1)
            case IpMuxSignal.DS:
                self.ip_mux.choose(self.data_stack.peek())
            case IpMuxSignal.RS:
                self.ip_mux.choose(self.return_stack.peek())
            case IpMuxSignal.ALU:
                self.ip_mux.choose(self.alu.result)

    def ds_mux_choice(self, signal: DsMuxSignal):
        match signal:
            case DsMuxSignal.DS:
                self.ds_mux.choose(self.data_stack.peek())
            case DsMuxSignal.DM:
                self.ds_mux.choose(self.data_memory.data_register)
            case DsMuxSignal.ALU:
                self.ds_mux.choose(self.alu.result)

    def dm_mux_choice(self, signal: DmMuxSignal):
        match signal:
            case DmMuxSignal.DS:
                self.dm_mux.choose(self.data_stack.peek())
            case DmMuxSignal.ALU:
                self.dm_mux.choose(self.alu.result)

    def alu_mux_a_choice(self, signal: AluMuxSignalA):
        match signal:
            case AluMuxSignalA.DS:
                self.alu_mux_a.choose(self.data_stack.peek())
            case AluMuxSignalA.ZERO:
                self.alu_mux_a.choose(0)
            case AluMuxSignalA.ONE:
                self.alu_mux_a.choose(1)
            case AluMuxSignalA.ALU:
                self.alu_mux_a.choose(self.alu.result)
            case AluMuxSignalA.IM:
                if "operand" in self.instruction_memory.data_register.keys():
                    self.alu_mux_a.choose(self.instruction_memory.data_register["operand"])
                    self.operand_flag = 1
                else:
                    self.alu_mux_a.choose(0)
                    self.operand_flag = 0

    def alu_mux_b_choice(self, signal: AluMuxSignalB):
        match signal:
            case AluMuxSignalB.DS:
                self.alu_mux_b.choose(self.data_stack.peek())
            case AluMuxSignalB.ZERO:
                self.alu_mux_b.choose(0)
            case  AluMuxSignalB.ONE:
                self.alu_mux_b.choose(1)
            case AluMuxSignalB.ALU:
                self.alu_mux_b.choose(self.alu.result)
            case AluMuxSignalB.IM:
                if "operand" in self.instruction_memory.data_register.keys():
                    self.alu_mux_b.choose(self.instruction_memory.data_register["operand"])
                    self.operand_flag = 1
                else:
                    self.alu_mux_b.choose(0)
                    self.operand_flag = 0

    def latch(self, signal: LatchSignal):
        match signal:
            case LatchSignal.IP:
                self.instruction_pointer = self.ip_mux.get()
            case LatchSignal.IR:
                self.instruction_register = self.instruction_memory.data_register["opcode"]

    def alu_signal(self, signal: AluSignal):
        match signal:
            case AluSignal.ADD:
                self.alu.add()
            case AluSignal.SUB:
                self.alu.sub()
            case AluSignal.MUL:
                self.alu.mul()
            case AluSignal.DIV:
                self.alu.div()
            case AluSignal.MOD:
                self.alu.mod()
            case AluSignal.COMP:
                self.alu.compare()
            case AluSignal.EQUALS:
                self.alu.equals()
            case AluSignal.LESS:
                self.alu.less()
            case AluSignal.GREATER:
                self.alu.greater()
            case AluSignal.SET_A:
                self.alu.a = self.alu_mux_a.get()
            case AluSignal.SET_B:
                self.alu.b = self.alu_mux_b.get()
            case AluSignal.NOT_A:
                self.alu.not_a()
            case AluSignal.NOT_B:
                self.alu.not_b()

    def jump_signal(self, signal: JumpSignal):
        match signal:
            case JumpSignal.JMP:
                self.return_stack.push(self.instruction_pointer)
                self.instruction_pointer = self.ip_mux.get()
            case JumpSignal.JMZ:
                if self.data_stack.peek() == 0:
                    self.return_stack.push(self.instruction_pointer)
                    self.instruction_pointer = self.ip_mux.get()
            case JumpSignal.JNZ:
                if self.data_stack.peek() != 0:
                    self.return_stack.push(self.instruction_pointer)
                    self.instruction_pointer = self.ip_mux.get()

    def control_signal(self, signal: ControlSignal):
        match signal:
            case ControlSignal.HALT:
                self.exit_flag = 1
            case ControlSignal.NOP:
                pass


class ControlUnit:
    def __init__(self, data_path: DataPath):
        self.data_path = data_path

        self.instruction_counter: int = 0
        self.ticks = 0

        self.no_operand_mcode = {
            "fetch": [InstructionMemorySignal.SET_ADDRESS, InstructionMemorySignal.READ, LatchSignal.IR, AluMuxSignalA.IM, AluSignal.SET_A, AluMuxSignalB.ZERO, AluSignal.SET_B, AluSignal.ADD, IpMuxSignal.IP, LatchSignal.IP],
            "add": [AluMuxSignalB.DS, AluSignal.SET_B, DataStackSignal.POP, AluMuxSignalA.DS, AluSignal.SET_A, DataStackSignal.POP, AluSignal.ADD, DsMuxSignal.ALU, DataStackSignal.PUSH],
            "sub": [AluMuxSignalB.DS, AluSignal.SET_B, DataStackSignal.POP, AluMuxSignalA.DS, AluSignal.SET_A, DataStackSignal.POP, AluSignal.SUB, DsMuxSignal.ALU, DataStackSignal.PUSH],
            "mul": [AluMuxSignalB.DS, AluSignal.SET_B, DataStackSignal.POP, AluMuxSignalA.DS, AluSignal.SET_A, DataStackSignal.POP, AluSignal.MUL, DsMuxSignal.ALU, DataStackSignal.PUSH],
            "div": [AluMuxSignalB.DS, AluSignal.SET_B, DataStackSignal.POP, AluMuxSignalA.DS, AluSignal.SET_A, DataStackSignal.POP, AluSignal.DIV, DsMuxSignal.ALU, DataStackSignal.PUSH],
            "mod": [AluMuxSignalB.DS, AluSignal.SET_B, DataStackSignal.POP, AluMuxSignalA.DS, AluSignal.SET_A, DataStackSignal.POP, AluSignal.MOD, DsMuxSignal.ALU, DataStackSignal.PUSH],
            "inc": [AluMuxSignalB.ONE, AluSignal.SET_B, AluMuxSignalA.DS, AluSignal.SET_A, DataStackSignal.POP, AluSignal.ADD, DsMuxSignal.ALU, DataStackSignal.PUSH],
            "dec": [AluMuxSignalB.ONE, AluSignal.SET_B, AluMuxSignalA.DS, AluSignal.SET_A, DataStackSignal.POP, AluSignal.SUB, DsMuxSignal.ALU, DataStackSignal.PUSH],
            "not": [AluMuxSignalB.ZERO, AluSignal.SET_B, AluMuxSignalA.DS, AluSignal.SET_A, DataStackSignal.POP, AluSignal.NOT_A, DsMuxSignal.ALU, DataStackSignal.PUSH],
            "eql": [AluMuxSignalB.DS, AluSignal.SET_B, DataStackSignal.POP, AluMuxSignalA.DS, AluSignal.SET_A, DataStackSignal.POP, AluSignal.EQUALS, DsMuxSignal.ALU, DataStackSignal.PUSH],
            "less": [AluMuxSignalB.DS, AluSignal.SET_B, DataStackSignal.POP, AluMuxSignalA.DS, AluSignal.SET_A, DataStackSignal.POP, AluSignal.LESS, DsMuxSignal.ALU, DataStackSignal.PUSH],
            "lrg": [AluMuxSignalB.DS, AluSignal.SET_B, DataStackSignal.POP, AluMuxSignalA.DS, AluSignal.SET_A, DataStackSignal.POP, AluSignal.GREATER, DsMuxSignal.ALU, DataStackSignal.PUSH],
            "pop": [DataStackSignal.POP],
            "comp": [AluMuxSignalB.DS, AluSignal.SET_B, DataStackSignal.POP, AluMuxSignalA.DS, AluSignal.SET_A, DataStackSignal.POP, AluSignal.COMP, DsMuxSignal.ALU, DataStackSignal.PUSH],
            "dup": [DsMuxSignal.DS, DataStackSignal.PUSH],
            "ret": [IpMuxSignal.RS, ReturnStackSignal.POP, LatchSignal.IP],
            "read": [DmMuxSignal.DS, DataMemorySignal.SET_ADDRESS, DataStackSignal.POP, DataMemorySignal.READ, DsMuxSignal.DM, DataStackSignal.PUSH],
            "save": [DmMuxSignal.DS, DataMemorySignal.SET_ADDRESS, DataStackSignal.POP, DmMuxSignal.DS, DataMemorySignal.WRITE, DataStackSignal.POP],
            "swap": [DataStackSignal.SWAP],
            "hlt": [ControlSignal.HALT],
            "nop": [ControlSignal.NOP]
        }

        self.one_operand_mcode = {
            "push": [DsMuxSignal.ALU, DataStackSignal.PUSH],
            "read": [DmMuxSignal.ALU, DataMemorySignal.SET_ADDRESS, DataMemorySignal.READ, DsMuxSignal.DM, DataStackSignal.PUSH],
            "save": [DmMuxSignal.ALU, DataMemorySignal.SET_ADDRESS, DmMuxSignal.DS, DataMemorySignal.WRITE, DataStackSignal.POP],
            "jmp": [IpMuxSignal.ALU, JumpSignal.JMP],
            "jmz": [IpMuxSignal.ALU, JumpSignal.JMZ, DataStackSignal.POP],
            "jnz": [IpMuxSignal.ALU, JumpSignal.JNZ, DataStackSignal.POP],
        }

    def tick(self):
        self.ticks += 1

    def handle_command(self):
        logging.debug(f"Fetching instruction id = {self.data_path.instruction_pointer}")
        for mc in self.no_operand_mcode["fetch"]:
            logging.debug(f"Processing mcode instruction {mc}")
            self.data_path.handle_signal[type(mc)](mc)
            self.tick()

        logging.debug(f"Instruction n = {self.instruction_counter}: {self.data_path.instruction_register}")

        if self.data_path.operand_flag:
            logging.debug(f"Has operand {self.data_path.alu.result}")
            for mc in self.one_operand_mcode[self.data_path.instruction_register]:
                logging.debug(f"Processing mcode instruction {mc}")
                self.data_path.handle_signal[type(mc)](mc)
                self.tick()
                logging.debug(f"DS: {self.data_path.data_stack} RS: {self.data_path.return_stack} OutBuffer: {self.data_path.output_buffer} ALU: res = {self.data_path.alu.result}, a = {self.data_path.alu.a}, b = {self.data_path.alu.b}")
        else:
            logging.debug("Has no operand")
            for mc in self.no_operand_mcode[self.data_path.instruction_register]:
                logging.debug(f"Processing mcode instruction {mc}")
                self.data_path.handle_signal[type(mc)](mc)
                self.tick()
                logging.debug(f"DS: {self.data_path.data_stack} RS: {self.data_path.return_stack} OutBuffer: {self.data_path.output_buffer} ALU: res = {self.data_path.alu.result}, a = {self.data_path.alu.a}, b = {self.data_path.alu.b}")


def simulate(source_path: str, input_path: str, result_path: str):
    data_path = DataPath()
    control_unit = ControlUnit(data_path)

    with open(source_path, "r") as source_file:
        source = json.load(source_file)

    with open(input_path, "r") as input_file:
        data_path.input_buffer = list(map(ord, list(input_file.read()))) + [0]

    for variable in source["memory"]:
        data_path.data_memory.allocate(variable["size"])
        data_path.data_memory.address_register = variable["idx"]
        data_path.data_memory.write(0)

    for instruction in source["instructions"]:
        data_path.instruction_memory.allocate(1)
        data_path.instruction_memory.address_register = instruction["idx"]
        data_path.instruction_memory.write(instruction)

    while data_path.exit_flag != 1:
        control_unit.handle_command()
        control_unit.instruction_counter += 1

    logging.info(f"System time: {control_unit.ticks}, instructions: {control_unit.instruction_counter}, output buffer: {data_path.output_buffer}")

    with open(result_path, "w") as result_file:
        for c in data_path.output_buffer:
            if c != 0:
                result_file.write(chr(c))


if __name__ == "__main__":
    assert len(sys.argv) == 3, "Usage: python machine.py <source> <input> <target>"
    logging.basicConfig(level=logging.DEBUG, handlers=[logging.StreamHandler()], encoding="utf-8")
    simulate(sys.argv[1], sys.argv[2], sys.argv[3])
    # simulate("dest.o", "input.txt", "result.txt")
