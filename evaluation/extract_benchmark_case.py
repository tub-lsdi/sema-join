#!/usr/bin/env python3
"""
Extract benchmark case input tables from Semantic-join-Benchmark.

Usage:
    python evaluation/extract_benchmark_case.py 15
    python evaluation/extract_benchmark_case.py 3

This will extract case_15_table_r.json and case_15_table_s.json (or case_3_table_r.json, etc.)
from the corresponding Case{NUMBER}_input.txt file.
"""

import sys
import json
from pathlib import Path


def extract_benchmark_case(case_number: int, output_dir: Path = None):
    """
    Extract tables from a benchmark case input file.

    Args:
        case_number: The case number (e.g., 15)
        output_dir: Directory to save output files. If None, uses current directory.
    """
    # Paths
    project_root = Path(__file__).parent.parent
    benchmark_dir = (
        project_root
        / "evaluation"
        / "semantic-join-benchmark"
        / "Semantic-join-Benchmark"
    )
    input_file = benchmark_dir / f"Case{case_number}_input.txt"

    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)

    # Output directory
    if output_dir is None:
        output_dir = Path.cwd()
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    # Output files
    output_r = output_dir / f"case_{case_number}_table_r.json"
    output_s = output_dir / f"case_{case_number}_table_s.json"

    # Read input file
    print(f"Reading: {input_file}")
    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Split by empty line (two consecutive newlines)
    # The tables are separated by a blank line
    parts = content.split("\n\n")

    if len(parts) < 2:
        print(
            f"Error: Expected 2 tables separated by blank line, found {len(parts)} parts"
        )
        sys.exit(1)

    # Table R is the first part
    table_r_lines = [
        line.strip() for line in parts[0].strip().split("\n") if line.strip()
    ]

    # Table S is the second part
    table_s_lines = [
        line.strip() for line in parts[1].strip().split("\n") if line.strip()
    ]

    # Convert to list of dicts with "value" key
    table_r_data = [{"value": line} for line in table_r_lines]
    table_s_data = [{"value": line} for line in table_s_lines]

    # Write table R as JSON
    print(f"Writing table R ({len(table_r_data)} rows): {output_r}")
    with open(output_r, "w", encoding="utf-8") as f:
        json.dump(table_r_data, f, indent=2, ensure_ascii=False)

    # Write table S as JSON
    print(f"Writing table S ({len(table_s_data)} rows): {output_s}")
    with open(output_s, "w", encoding="utf-8") as f:
        json.dump(table_s_data, f, indent=2, ensure_ascii=False)

    print(f"\nSuccess! Extracted:")
    print(f"  - Table R: {len(table_r_lines)} rows → {output_r}")
    print(f"  - Table S: {len(table_s_lines)} rows → {output_s}")


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python evaluation/extract_benchmark_case.py <case_number> [output_dir]"
        )
        print("\nExamples:")
        print("  python evaluation/extract_benchmark_case.py 15")
        print("  python evaluation/extract_benchmark_case.py 15 output/")
        print("\nAvailable cases:")

        # List available cases
        project_root = Path(__file__).parent.parent
        benchmark_dir = (
            project_root
            / "evaluation"
            / "semantic-join-benchmark"
            / "Semantic-join-Benchmark"
        )
        if benchmark_dir.exists():
            case_files = sorted(benchmark_dir.glob("Case*_input.txt"))
            for case_file in case_files:
                case_num = case_file.stem.replace("Case", "").replace("_input", "")
                print(f"  - Case {case_num}")

        sys.exit(1)

    try:
        case_number = int(sys.argv[1])
    except ValueError:
        print(f"Error: Case number must be an integer, got: {sys.argv[1]}")
        sys.exit(1)

    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    extract_benchmark_case(case_number, output_dir)


if __name__ == "__main__":
    main()
