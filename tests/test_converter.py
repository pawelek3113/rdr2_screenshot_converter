"""Unit tests for rdr2_ss converter and CLI."""

from __future__ import annotations

from pathlib import Path

import pytest

from rdr2_ss.cli import main
from rdr2_ss.converter import (
    HEADER_SIZE,
    JPEG_SOI_MARKER,
    convert_all_photos,
    convert_photo,
    find_prdr_files,
)


def _make_fake_prdr(path: Path, payload: bytes = b"fake-jpeg-body") -> bytes:
    header = b"\x00" * HEADER_SIZE
    jpg_content = JPEG_SOI_MARKER + payload
    path.write_bytes(header + jpg_content)
    return jpg_content


def test_convert_photo_strips_300_byte_header(tmp_path: Path) -> None:
    src_file = tmp_path / "PRDR3106784205_1"
    expected_jpg = _make_fake_prdr(src_file, b"\xe0\x00\x10JFIF\x00\xff\xd9")
    out_dir = tmp_path / "out"

    out_path = convert_photo(src_file, out_dir)

    assert out_path is not None
    assert out_path == out_dir / "PRDR3106784205_1.jpg"
    assert out_path.read_bytes() == expected_jpg


def test_convert_photo_rejects_short_file(tmp_path: Path) -> None:
    src_file = tmp_path / "PRDR_SHORT"
    src_file.write_bytes(b"\x00" * 300)

    with pytest.raises(ValueError, match="too small"):
        convert_photo(src_file, tmp_path / "out")


def test_convert_photo_rejects_non_jpeg_payload(tmp_path: Path) -> None:
    src_file = tmp_path / "PRDR_BAD"
    src_file.write_bytes(b"\x00" * HEADER_SIZE + b"NOT_A_JPEG")

    with pytest.raises(ValueError, match="valid JPEG header"):
        convert_photo(src_file, tmp_path / "out")


def test_find_prdr_files_supports_direct_and_profile_subdirs(tmp_path: Path) -> None:
    profiles_dir = tmp_path / "Profiles"
    profile_a = profiles_dir / "A1B2C3D4"
    profile_a.mkdir(parents=True)

    f1 = profile_a / "PRDR111"
    f2 = profiles_dir / "PRDR222"
    ignored = profile_a / "OTHER123"
    _make_fake_prdr(f1)
    _make_fake_prdr(f2)
    ignored.write_bytes(b"ignore")

    found = find_prdr_files(profiles_dir)
    assert found == [f2.resolve(), f1.resolve()]


def test_cli_converts_directory(tmp_path: Path) -> None:
    src_dir = tmp_path / "Profiles" / "466F4FEF"
    src_dir.mkdir(parents=True)
    _make_fake_prdr(src_dir / "PRDR1001")
    _make_fake_prdr(src_dir / "PRDR1002")

    out_dir = tmp_path / "Downloads" / "rdr2_photos"
    exit_code = main(["-s", str(tmp_path / "Profiles"), "-o", str(out_dir)])

    assert exit_code == 0
    assert (out_dir / "PRDR1001.jpg").is_file()
    assert (out_dir / "PRDR1002.jpg").is_file()


@pytest.mark.skipif(
    not (Path(__file__).resolve().parents[1] / "example_photos").is_dir(),
    reason="Local example_photos directory not present",
)
def test_example_photos_conversion(tmp_path: Path) -> None:
    example_dir = Path(__file__).resolve().parents[1] / "example_photos"
    out_dir = tmp_path / "converted_examples"

    result = convert_all_photos(example_dir, out_dir)
    assert len(result.converted) == 3
    assert not result.failed
    for jpg_file in result.converted:
        data = jpg_file.read_bytes()
        assert data.startswith(JPEG_SOI_MARKER)
        assert len(data) == 1052488 - HEADER_SIZE
