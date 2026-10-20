# rdr2-ss

Convert Red Dead Redemption 2 (`PRDR*`) photo captures into standard `.jpg` files by stripping the 300-byte Rockstar metadata header.

## Requirements

- Python 3.10+
- [Poetry](https://python-poetry.org/)

## Installation

```powershell
poetry install
```

## Usage

Run with default directories:
- **Default source directory:** `%USERPROFILE%\Documents\Rockstar Games\Red Dead Redemption 2\Profiles\<Your_Profile_ID>\`
- **Default output directory:** `%USERPROFILE%\Downloads\rdr2_photos`

```powershell
poetry run rdr2-ss
```

Provide custom source and/or output directories:

```powershell
poetry run rdr2-ss --source-dir "C:\path\to\photos" --output-dir "C:\path\to\output"
# or short flags:
poetry run rdr2-ss -s ./example_photos -o ./output_jpgs
```

### CLI Options

| Flag | Description | Default |
| --- | --- | --- |
| `-s`, `--source-dir` | Directory containing `PRDR*` files (or the `Profiles` parent directory) | `%USERPROFILE%\Documents\Rockstar Games\Red Dead Redemption 2\Profiles` |
| `-o`, `--output-dir` | Destination directory for extracted `.jpg` files | `%USERPROFILE%\Downloads\rdr2_photos` |
| `--no-overwrite` | Skip converting photos whose target `.jpg` already exists | `False` |
