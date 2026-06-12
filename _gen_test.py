import os

os.makedirs("tests/blueprint_intelligence", exist_ok=True)
with open(
    "tests/blueprint_intelligence/test_similarity_engine.py", "w", encoding="utf-8"
) as f:
    f.write('"""Tests for BlueprintSimilarityEngine."""\n')
    f.write("\nimport pytest\n")
    f.write(
        "from core.blueprints.blueprint import Blueprint, BlueprintTile, BlueprintMetadata\n"
    )
