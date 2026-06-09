from typing import Dict, List

from .rme_validator import validate as rme_validate, RMEValidationError
from .asset_validator import validate_asset
from .monster_validator import validate_monster
from .tile_validator import validate_tile


class QAPipeline:
    """
    Orchestrates the full validation pipeline:

    Lua
     ↓
    RME Validator  (forbidden APIs)
     ↓
    Asset Validator (item IDs)
     ↓
    Monster Validator (monster names)
     ↓
    Tile Validator  (coordinates)
     ↓
    QA Report
    """

    def run(self, lua_code: str) -> Dict:
        report = {
            "status": "success",
            "errors": [],
            "warnings": [],
            "stages": {},
        }

        # Stage 1: RME Validator
        try:
            rme_validate(lua_code)
            report["stages"]["rme_validator"] = "passed"
        except RMEValidationError as e:
            report["status"] = "failure"
            report["stages"]["rme_validator"] = "failed"
            report["errors"].append(f"RME: {str(e)}")
            # Stop pipeline if forbidden APIs detected
            return report

        # Stage 2: Asset Validator
        valid, asset_errors = validate_asset(lua_code)
        if not valid:
            report["stages"]["asset_validator"] = "failed"
            report["errors"].extend(f"Asset: {e}" for e in asset_errors)
            if not report["status"] == "failure":
                report["status"] = "failure"
        else:
            report["stages"]["asset_validator"] = "passed"

        # Stage 3: Monster Validator
        valid, monster_errors = validate_monster(lua_code)
        if not valid:
            report["stages"]["monster_validator"] = "failed"
            report["errors"].extend(f"Monster: {e}" for e in monster_errors)
            if not report["status"] == "failure":
                report["status"] = "failure"
        else:
            report["stages"]["monster_validator"] = "passed"

        # Stage 4: Tile Validator
        valid, tile_errors = validate_tile(lua_code)
        if not valid:
            report["stages"]["tile_validator"] = "failed"
            report["errors"].extend(f"Tile: {e}" for e in tile_errors)
            if not report["status"] == "failure":
                report["status"] = "failure"
        else:
            report["stages"]["tile_validator"] = "passed"

        return report