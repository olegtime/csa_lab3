import os
import tempfile
import logging

import pytest

from translator import translate
from machine import simulate


@pytest.mark.golden_test("./golden/test/*.yml")
def test_translator_asm_and_machine(golden, caplog):
    caplog.set_level(logging.DEBUG)

    with tempfile.TemporaryDirectory() as directory:
        source = os.path.join(directory, "source.asm")
        input_stream = os.path.join(directory, "input.txt")
        target = os.path.join(directory, "target.o")
        output_stream = os.path.join(directory, "output.txt")

        with open(source, "w", encoding="utf-8") as file:
            file.write(golden["in_source"])
        with open(input_stream, "w", encoding="utf-8") as file:
            file.write(golden["in_stdin"])

        with caplog.at_level(logging.DEBUG):
            translate(source, target)
            simulate(target, input_stream, output_stream)

        with open(target, encoding="utf-8") as file:
            code = file.read()

        with open(output_stream, encoding="utf-8") as file:
            out_text = file.read()

        assert code == golden["out_code"]
        assert out_text == golden["out_stdout"]
        assert caplog.text == golden["out_log"]
