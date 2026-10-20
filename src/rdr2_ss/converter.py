"""Core logic for discovering and converting RDR2 PRDR photo files to JPG."""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path

HEADER_SIZE = 300
JPEG_SOI_MARKER = b"\xff\xd8\xff"


@dataclass
class ConversionResult:
    """Summary of a batch photo conversion run."""

    converted: list[Path] = field(default_factory=list)
    skipped: list[Path] = field(default_factory=list)
    failed: list[tuple[Path, str]] = field(default_factory=list)


def _user_profile_dir() -> Path:
    """Resolve %USERPROFILE% or fall back to Path.home()."""
    env_profile = os.environ.get("USERPROFILE")
    if env_profile:
        return Path(env_profile)
    return Path.home()


def default_source_dir() -> Path:
    """Return the default RDR2 Profiles directory path.

    Defaults to:
    %USERPROFILE%\\Documents\\Rockstar Games\\Red Dead Redemption 2\\Profiles
    """
    return (
        _user_profile_dir()
        / "Documents"
        / "Rockstar Games"
        / "Red Dead Redemption 2"
        / "Profiles"
    )


def default_output_dir() -> Path:
    """Return the default output directory path.

    Defaults to:
    %USERPROFILE%\\Downloads\\rdr2_photos
    """
    return _user_profile_dir() / "Downloads" / "rdr2_photos"


def find_prdr_files(source_dir: Path) -> list[Path]:
    """Find RDR2 PRDR* photo files in ``source_dir`` or its profile subdirectories.

    Supports both:
    - A direct directory containing ``PRDR*`` files (e.g. ``.../Profiles/<Profile_ID>`` or custom folder)
    - The parent ``.../Profiles`` directory containing ``<Profile_ID>/PRDR*`` subdirectories
    """
    source_path = source_dir.expanduser().resolve()
    if not source_path.exists():
        raise FileNotFoundError(f"Source directory does not exist: {source_path}")
    if not source_path.is_dir():
        raise NotADirectoryError(f"Source path is not a directory: {source_path}")

    candidates: dict[Path, None] = {}

    # 1. Direct PRDR* files in the given directory
    for item in sorted(source_path.glob("PRDR*")):
        if item.is_file() and item.suffix.lower() not in {".jpg", ".jpeg"}:
            candidates[item.resolve()] = None

    # 2. Profile subdirectories (<Your_Profile_ID>/PRDR*)
    for item in sorted(source_path.glob("*/PRDR*")):
        if item.is_file() and item.suffix.lower() not in {".jpg", ".jpeg"}:
            candidates[item.resolve()] = None

    return list(candidates.keys())


def convert_photo(
    source_file: Path,
    output_dir: Path,
    *,
    header_size: int = HEADER_SIZE,
    overwrite: bool = True,
) -> Path | None:
    """Strip the 300-byte Rockstar header from a PRDR file and save it as a .jpg.

    Returns the output ``Path`` if written, or ``None`` if skipped because ``overwrite=False``
    and the destination file already exists.
    """
    if not source_file.is_file():
        raise FileNotFoundError(f"Source file not found: {source_file}")

    raw_bytes = source_file.read_bytes()
    if len(raw_bytes) <= header_size:
        raise ValueError(
            f"File '{source_file.name}' is too small ({len(raw_bytes)} bytes <= {header_size}-byte header)."
        )

    jpg_bytes = raw_bytes[header_size:]
    if not jpg_bytes.startswith(JPEG_SOI_MARKER):
        raise ValueError(
            f"File '{source_file.name}' does not contain a valid JPEG header at byte offset {header_size}."
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{source_file.name}.jpg"

    if out_path.exists() and not overwrite:
        return None

    out_path.write_bytes(jpg_bytes)

    # Preserve original modification and access timestamps
    stat = source_file.stat()
    os.utime(out_path, (stat.st_atime, stat.st_mtime))

    return out_path


def convert_all_photos(
    source_dir: Path,
    output_dir: Path,
    *,
    header_size: int = HEADER_SIZE,
    overwrite: bool = True,
) -> ConversionResult:
    """Discover all PRDR* files in ``source_dir`` and convert them into ``output_dir``."""
    result = ConversionResult()
    prdr_files = find_prdr_files(source_dir)

    for file_path in prdr_files:
        try:
            out_path = convert_photo(
                file_path,
                output_dir,
                header_size=header_size,
                overwrite=overwrite,
            )
            if out_path is None:
                result.skipped.append(file_path)
            else:
                result.converted.append(out_path)
        except Exception as exc:  # noqa: BLE001
            result.failed.append((file_path, str(exc)))

    return result
