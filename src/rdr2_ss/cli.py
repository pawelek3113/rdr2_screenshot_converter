"""Command-line interface for RDR2 photo to JPG conversion."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Sequence

from rdr2_ss.converter import (
    convert_all_photos,
    default_output_dir,
    default_source_dir,
)


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    default_src = default_source_dir()
    default_out = default_output_dir()

    parser = argparse.ArgumentParser(
        prog="rdr2-ss",
        description=(
            "Convert Red Dead Redemption 2 PRDR photo files into JPG images "
            "by stripping the 300-byte Rockstar header."
        ),
    )
    parser.add_argument(
        "-s",
        "--source-dir",
        type=Path,
        default=default_src,
        help=(
            "Source directory containing PRDR* files or profile folders "
            f"(default: {default_src}\\<Your_Profile_ID>\\)"
        ),
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=default_out,
        help=f"Output directory for converted JPG files (default: {default_out})",
    )
    parser.add_argument(
        "--no-overwrite",
        action="store_true",
        help="Skip files that have already been converted in the output directory.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    source_dir: Path = args.source_dir.expanduser().resolve()
    output_dir: Path = args.output_dir.expanduser().resolve()

    try:
        result = convert_all_photos(
            source_dir=source_dir,
            output_dir=output_dir,
            overwrite=not args.no_overwrite,
        )
    except (FileNotFoundError, NotADirectoryError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    total_found = len(result.converted) + len(result.skipped) + len(result.failed)
    if total_found == 0:
        print(f"No PRDR photo files found in: {source_dir}")
        return 0

    print(f"Source directory : {source_dir}")
    print(f"Output directory : {output_dir}")
    print(f"Converted        : {len(result.converted)} file(s)")
    if result.skipped:
        print(f"Skipped (exists) : {len(result.skipped)} file(s)")
    if result.failed:
        print(f"Failed           : {len(result.failed)} file(s)", file=sys.stderr)
        for failed_path, reason in result.failed:
            print(f"  - {failed_path.name}: {reason}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
