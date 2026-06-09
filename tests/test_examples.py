from pathlib import Path

from validators.rme_validator import validate

def test_all_examples():

    examples = Path("examples")

    for lua_file in examples.glob("*.lua"):

        content = lua_file.read_text(
            encoding="utf-8"
        )

        assert validate(content)