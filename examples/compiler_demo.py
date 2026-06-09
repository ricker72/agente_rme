from pathlib import Path

from core.compiler import LuaCompiler


def main() -> None:
    source_path = Path(__file__).resolve().parent / "issavi_roshamuul_hybrid.lua"
    if not source_path.exists():
        raise FileNotFoundError(f"Example source not found: {source_path}")

    source = source_path.read_text(encoding="utf-8")
    compiler = LuaCompiler()
    report = compiler.compile(source)

    print("COMPILATION REPORT")
    print(report.to_dict())
    if report.script:
        output_path = source_path.with_name("issavi_roshamuul_hybrid.optimized.lua")
        output_path.write_text(report.script, encoding="utf-8")
        print(f"Optimized script written to: {output_path}")


if __name__ == "__main__":
    main()
