import sys
import json

terms_to_instructions: dict[str, list[str]] = {
    "=": ["eql"],
    "<": ["less"],
    ">": ["lrg"],
    "dup": ["dup"],
    "drop": ["pop"],
    "swap": ["swap"],
    "+": ["add"],
    "-": ["sub"],
    "*": ["mul"],
    "/": ["div"],
    "mod": ["mod"],
    "not": ["not"],
    "key": ["read INPUT"],
    "!": ["save"],
    "@": ["read"],
    "?": ["read", "save out_temp", "push 0", "jmp system_number_prepare", "jmp system_number_print"],
    ".": ["save out_temp", "jmp system_number_prepare", "jmp system_number_print"],
    "emit": ["save OUTPUT"],
    "cr": ["push 13", "save OUTPUT"],
}


def terms_to_assembly(terms: list[str]) -> tuple[dict[str, int], list[str], dict[str, list[str]]]:
    variables: dict[str, int] = {}  # name: size
    procedures: list[str] = []  # list of names
    conditions: list[str] = []  # list of names
    loops: list[str] = []  # list of names
    code: list[str] = []  # list of instructions
    labels_code: dict[str, list[str]] = {
        "system_number_prepare": ["system_number_prepare:", "read out_temp", "dup", "push 10", "read out_temp",
                                  "push 10", "div", "mul", "sub",
                                  "push 48", "add", "swap", "push 10", "div", "dup", "save out_temp",
                                  "push 0", "eql", "jmz system_number_prepare", "ret"],
        "system_number_print": ["system_number_print:", "dup", "save OUTPUT", "jnz system_number_print", "ret"],
    }  # name: list of instructions

    i: int = 0
    in_condition: bool = False
    in_function: bool = False
    in_loop: bool = False
    in_print: bool = False

    while i < len(terms):
        if in_print:
            for char in terms[i]:
                if char == "\"":
                    in_print = False
                    break

                if in_condition:
                    labels_code[conditions[-1]].extend([f"push {ord(char)}", "save OUTPUT"])
                elif in_loop:
                    labels_code[loops[-1]].extend([f"push {ord(char)}", "save OUTPUT"])
                elif in_function:
                    labels_code[procedures[-1]].extend([f"push {ord(char)}", "save OUTPUT"])
                else:
                    code.extend([f"push {ord(char)}", "save OUTPUT"])

            else:
                if in_condition:
                    labels_code[conditions[-1]].extend(["push 32", "save OUTPUT"])
                elif in_loop:
                    labels_code[loops[-1]].extend(["push 32", "save OUTPUT"])
                elif in_function:
                    labels_code[procedures[-1]].extend(["push 32", "save OUTPUT"])
                else:
                    code.extend(["push 32", "save OUTPUT"])

            i += 1

        elif (terms[i] == "variable") and (i + 4 < len(terms)) and (" ".join(terms[i + 3:i + 5]) == "cells allot"):
            assert not any([in_condition, in_function, in_loop]), f"variable definition is not allowed in word {i}"
            assert terms[i + 1] != "i", "name 'i' can't be redefined as it used by the system"
            assert terms[i + 1] != "end", "name 'end' can't be redefined as it used by the system"
            assert terms[i + 1] != "out_temp", "name 'out_temp' can't be redefined as it used by the system"
            assert terms[i + 1] != "system_number_print", \
                "name 'system_number_print' can't be redefined as it used by the system"

            variables[terms[i + 1]] = 1 + int(terms[i + 2])

            i += 5

        elif terms[i] == "variable":
            assert not any([in_condition, in_function, in_loop]), f"variable definition is not allowed in word {i}"
            assert terms[i + 1] != "i", "name 'i' can't be redefined as it used by the system"
            assert terms[i + 1] != "end", "name 'end' can't be redefined as it used by the system"
            assert terms[i + 1] != "out_temp", "name 'out_temp' can't be redefined as it used by the system"
            assert terms[i + 1] != "system_number_print", \
                "name 'system_number_print' can't be redefined as it used by the system"

            variables[terms[i + 1]] = 1

            i += 2

        elif terms[i] == ":":
            assert not in_function, "nested functions are not allowed in that implementation"
            assert not any([in_condition, in_loop]), f"function definition is not allowed in word {i}"
            assert terms[i + 1] != "system_number_print", \
                "name 'system_number_print' can't be redefined as it used by the system"

            in_function = True

            procedures.append(terms[i + 1])
            labels_code[terms[i + 1]] = [f"{terms[i + 1]}:"]

            i += 2

        elif terms[i] == ";":
            assert in_function, f"unexpected function ending was found in word {i}"

            in_function = False

            labels_code[procedures[-1]].append(f"ret")

            i += 1

        elif terms[i] == "if":
            assert not in_condition, "nested conditions are not allowed in that implementation"

            in_condition = True

            label_name = f"CONDITION_LABEL_IF_{hex(len(conditions))[2:]}"
            conditions.append(label_name)

            labels_code[label_name] = [f"{label_name}:"]

            if in_loop:
                labels_code[loops[-1]].append(f"jnz {label_name}")
            elif in_function:
                labels_code[procedures[-1]].append(f"jnz {label_name}")
            else:
                code.append(f"jnz {label_name}")

            i += 1

        elif terms[i] == "else":
            assert in_condition, f"unexpected else statement ending was found in word {i}"

            label_name = f"CONDITION_LABEL_ELSE_{conditions[-1][-1]}"
            conditions.append(label_name)

            labels_code[conditions[-2]].append("ret")

            labels_code[label_name] = [f"{label_name}:"]

            if in_loop:
                labels_code[loops[-1]].append(f"jmp {label_name}")
            elif in_function:
                labels_code[procedures[-1]].append(f"jmp {label_name}")
            else:
                code.append(f"jmp {label_name}")

            i += 1

        elif terms[i] == "then":
            assert in_condition, f"unexpected condition ending was found in word {i}"

            in_condition = False

            labels_code[conditions[-1]].append("ret")

            i += 1

        elif terms[i] == "begin":
            assert not in_loop, "nested loops are not allowed in that implementation"
            assert not in_condition, "loops inside a conditions are not allowed in that implementation"

            in_loop = True

            label_name = f"LOOP_LABEL_BEGIN_{len(loops)}"
            loops.append(label_name)

            labels_code[label_name] = [f"{label_name}:"]

            if in_function:
                labels_code[procedures[-1]].append(f"jmp {label_name}")
            else:
                code.append(f"jmp {label_name}")

            i += 1

        elif terms[i] == "until":
            assert in_loop, f"unexpected loop ending was found in word {i}"

            in_loop = False

            labels_code[loops[-1]].extend([f"jnz {loops[-1]}", "ret"])

            i += 1

        elif terms[i] == "do":
            assert not in_loop, "nested loops are not allowed in that implementation"
            assert not in_condition, "loops inside a conditions are not allowed in that implementation"

            in_loop = True

            label_name = f"LOOP_LABEL_DO_{len(loops)}"
            loops.append(label_name)

            labels_code[label_name] = [f"{label_name}:"]

            if in_function:
                labels_code[procedures[-1]].extend(["save i", "save end", f"jmp {label_name}"])
            else:
                code.extend(["save i", "save end", f"jmp {label_name}"])

            i += 1

        elif terms[i] == "loop":
            assert in_loop, f"unexpected loop ending was found in word {i}"

            in_loop = False

            labels_code[loops[-1]].extend(["push i", "read", "inc", "dup", "save i",
                                           "push end", "read", "less", f"jnz {loops[-1]}", "ret"])

            i += 1

        elif terms[i] == "leave":
            assert in_loop, f"unexpected leaving from loop was found in word {i}"

            if in_condition:
                labels_code[conditions[-1]].extend(["push end", "read", "push i", "save"])
            else:
                labels_code[loops[-1]].extend(["push end", "read", "push i", "save"])

            i += 1

        elif terms[i] == ".\"":
            assert not in_loop, "nested loops are not allowed in that implementation"
            assert not in_condition, "loops inside a conditions are not allowed in that implementation"

            in_print = True

            i += 1

        elif terms[i] in terms_to_instructions.keys():
            if in_condition:
                labels_code[conditions[-1]].extend(terms_to_instructions[terms[i]])
            elif in_loop:
                labels_code[loops[-1]].extend(terms_to_instructions[terms[i]])
            elif in_function:
                labels_code[procedures[-1]].extend(terms_to_instructions[terms[i]])
            else:
                code.extend(terms_to_instructions[terms[i]])

            i += 1

        elif terms[i] in procedures:
            if in_condition:
                labels_code[conditions[-1]].append(f"jmp {terms[i]}")
            elif in_loop:
                labels_code[loops[-1]].append(f"jmp {terms[i]}")
            elif in_function:
                labels_code[procedures[-1]].append(f"jmp {terms[i]}")
            else:
                code.append(f"jmp {terms[i]}")

            i += 1

        elif i + 1 < len(terms) and terms[i + 1] == "cells":
            if in_condition:
                labels_code[conditions[-1]].append(f"read {terms[i]}")
            elif in_loop:
                labels_code[loops[-1]].append(f"read {terms[i]}")
            elif in_function:
                labels_code[procedures[-1]].append(f"read {terms[i]}")
            else:
                code.append(f"read {terms[i]}")

            i += 2

        elif terms[i] in variables or terms[i].isnumeric() or (terms[i][0] == "-" and terms[i][1:].isnumeric()):
            if in_condition:
                labels_code[conditions[-1]].append(f"push {terms[i]}")
            elif in_loop:
                labels_code[loops[-1]].append(f"push {terms[i]}")
            elif in_function:
                labels_code[procedures[-1]].append(f"push {terms[i]}")
            else:
                code.append(f"push {terms[i]}")

            i += 1

        else:
            assert False, f"term {terms[i]} is undefined, you can't use it"

    code.append("hlt")
    return variables, code, labels_code


def asm_to_machine(variables: dict[str, int],
                   instructions: list[str],
                   labels: dict[str, list[str]]) -> dict[str, list[dict[str | int, str | int]]]:
    variables_to_idx: dict[str, int] = {"INPUT": 0, "OUTPUT": 1, "out_temp": 2, "i": 3, "end": 4}
    processed_variables: list[dict[str | int, str | int]] = [
        {"idx": 0, "size": 1}, {"idx": 1, "size": 1},
        {"idx": 2, "size": 1}, {"idx": 3, "size": 1}, {"idx": 4, "size": 1}
    ]

    cell = 5
    for name, size in variables.items():
        variables_to_idx[name] = cell
        processed_variables.append({
            "idx": cell,
            "size": size,
        })
        cell += size

    idx = len(instructions)
    labels_to_idx: dict[str, int] = {}
    processed_code: list[dict[str | int, str | int]] = []
    processed_labels: list[dict[str | int, str | int]] = []

    for name, lines in labels.items():
        labels_to_idx[name] = idx
        idx += len(lines) - 1

    idx = 0

    for instruction in instructions:
        parts = instruction.split()
        if len(parts) == 2:
            if parts[1] in labels_to_idx.keys():
                processed_code.append({
                    "idx": idx,
                    "opcode": parts[0],
                    "operand": labels_to_idx[parts[1]]
                })
            elif parts[1] in variables_to_idx.keys():
                processed_code.append({
                    "idx": idx,
                    "opcode": parts[0],
                    "operand": variables_to_idx[parts[1]]
                })
            else:
                processed_code.append({
                    "idx": idx,
                    "opcode": parts[0],
                    "operand": int(parts[1])
                })
        else:
            processed_code.append({
                "idx": idx,
                "opcode": parts[0],
            })

        idx += 1

    for name, lines in labels.items():
        for line in lines[1:]:
            parts = line.split()
            if len(parts) == 2:
                if parts[1] in labels_to_idx.keys():
                    processed_labels.append({
                        "idx": idx,
                        "opcode": parts[0],
                        "operand": labels_to_idx[parts[1]]
                    })
                elif parts[1] in variables_to_idx.keys():
                    processed_labels.append({
                        "idx": idx,
                        "opcode": parts[0],
                        "operand": variables_to_idx[parts[1]]
                    })
                else:
                    processed_labels.append({
                        "idx": idx,
                        "opcode": parts[0],
                        "operand": int(parts[1])
                    })
            else:
                processed_labels.append({
                    "idx": idx,
                    "opcode": parts[0],
                })

            idx += 1

    result = {
        "memory": processed_variables,  # { idx: xx , size: xx }
        "instructions": processed_code + processed_labels  # { idx: xx , opcode: xx , operand: xx }
    }

    return result


def translate(source_path: str, dest_path: str) -> None:
    term_lst: list[str] = []

    with open(source_path, "r") as in_file:
        for line in in_file.readlines():
            term_lst.extend(line.strip().split())

    variables, instructions, procedures = terms_to_assembly(term_lst)

    # with open(dest_path, "w") as out_file:
    #     out_file.write(".data\n")
    #     for name, size in variables.items():
    #         out_file.write(f"{name} bf {size}\n")
    #
    #     out_file.write(".code\n")
    #     for instruction in instructions:
    #         out_file.write(f"{instruction}\n")
    #
    #     for procedure in procedures.values():
    #         for line in procedure:
    #             out_file.write(f"{line}\n")

    json_dict = asm_to_machine(variables, instructions, procedures)

    with open(dest_path, "w", encoding="utf-8") as out_file:
        json.dump(json_dict, out_file, indent=2)


if __name__ == "__main__":
    # assert len(sys.argv) == 3, "Usage: python translator.py <source> <target>"
    # translate(sys.argv[1], sys.argv[2])

    translate("golden/src/prob2.4th", "dest.o")
