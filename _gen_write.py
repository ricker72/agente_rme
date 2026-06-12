import os

os.makedirs("tests/blueprint_intelligence", exist_ok=True)

with open(
    "tests/blueprint_intelligence/test_similarity_engine.py", "w", encoding="utf-8"
) as f:
    f.write("test")
