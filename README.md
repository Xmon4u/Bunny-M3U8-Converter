# Bunny Stream to M3U8 Converter

<div align="center">

[![Latest Release](https://img.shields.io/github/v/release/Xmon4u/Bunny-M3U8-Converter?color=brightgreen&label=Release&logo=github)](https://github.com/Xmon4u/Bunny-M3U8-Converter/releases/latest)
[![Direct Download](https://img.shields.io/badge/Download-BunnyM3U8.exe-success?style=flat&logo=windows)](https://github.com/Xmon4u/Bunny-M3U8-Converter/releases/latest/download/BunnyM3U8.exe)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com/Xmon4u/Bunny-M3U8-Converter)
[![GUI](https://img.shields.io/badge/GUI-CustomTkinter-orange.svg)](https://github.com/TomSchimansky/CustomTkinter)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](test_bunny.py)

A desktop and CLI utility that extracts direct HLS `playlist.m3u8` stream URLs from Bunny Stream play links, embed pages, iframe snippets, and token-signed links.

[Key Features](#key-features) •
[Accepted Formats](#accepted-input-formats) •
[Installation & Usage](#quick-start) •
[CLI Mode](#cli-usage) •
[Build Executable](#build-standalone-windows-exe) •
[Testing](#running-tests)

</div>

---

## Key Features

- **Dual Mode Operation**:
  - **GUI**: Built with CustomTkinter featuring a dark theme, batch queue management, and one-click clipboard copy.
  - **CLI / Headless**: Streamlined CLI for scripts, piping, automated pipelines, or server environments.
- **Smart Batch Processing**: Paste hundreds of mixed links or raw iframe code snippets at once. Processes links asynchronously with real-time status updates.
- **Robust Extraction Pipeline**:
  - Queries both modern player pages (`player.mediadelivery.net`) and legacy iframe embeds (`iframe.mediadelivery.net`).
  - Fallback CDN address resolver: constructs direct CDN endpoints even when web pages only expose video thumbnails.
  - Preserves token and expiry queries (`?token=...&expires=...`) seamlessly.
- **Zero-Failure Tolerance**: If a single URL in a batch is invalid, only that row is flagged — all valid links continue processing without interruption.
- **Export Options**: One-click copy for individual links or batch-export all converted playlist links.

---

## Accepted Input Formats

The converter accepts flexible and mixed inputs directly from the clipboard:

| Format / Type | Example Input |
| :--- | :--- |
| **Direct Play Link** | `https://player.mediadelivery.net/play/780046/61e4f637-dbd1-4dc1-b68a-9acdec0e6988` |
| **Embed URL** | `https://player.mediadelivery.net/embed/780046/61e4f637-dbd1-4dc1-b68a-9acdec0e6988` |
| **Legacy Iframe URL** | `https://iframe.mediadelivery.net/embed/780046/61e4f637-dbd1-4dc1-b68a-9acdec0e6988` |
| **Token-Signed Link** | `https://player.mediadelivery.net/play/780046/UUID?token=abc123&expires=1700000000` |
| **Raw HTML Embed Code**| `<iframe src="https://player.mediadelivery.net/embed/780046/UUID" loading="lazy" ...></iframe>` |
| **Direct Playlist URL**| `https://vz-abc123.b-cdn.net/UUID/playlist.m3u8` |
| **Multi-line Batch** | Any mixture of the above, one per line or mixed within raw HTML text |

---

## Quick Start

### 1. Download & Run Executable (Windows)

No Python setup or installation required:

1. [Download the latest BunnyM3U8.exe](https://github.com/Xmon4u/Bunny-M3U8-Converter/releases/latest/download/BunnyM3U8.exe) from the releases page.
2. Double-click `BunnyM3U8.exe` (or run `run.bat`) to launch the application.

---

### 2. Run From Source

Clone the repository and install dependencies:

```bash
git clone https://github.com/Xmon4u/Bunny-M3U8-Converter.git
cd Bunny-M3U8-Converter

pip install -r requirements.txt

# Launch GUI
python bunny_m3u8.py
```

> **Note for Linux / macOS users:** You can also run `./run.sh` to launch the application.

---

## CLI Usage

You can use the tool directly from terminal or in shell scripts.

### Basic Extraction:
```bash
python bunny_m3u8.py "https://player.mediadelivery.net/play/LIBRARY_ID/VIDEO_ID"
```

### Force CLI Interactive Mode:
```bash
python bunny_m3u8.py --cli
```

### Force GUI Mode:
```bash
python bunny_m3u8.py --gui
```

### CLI Command Options:
```text
usage: bunny_m3u8.py [-h] [--cli] [--gui] [urls ...]

Convert Bunny play URL to HLS m3u8

positional arguments:
  urls        Bunny play/embed URL(s)

options:
  -h, --help  show this help message and exit
  --cli       Force interactive CLI mode
  --gui       Force GUI mode
```

---

## Build Standalone Windows EXE

To generate a standalone, single-file `.exe` with icon and CustomTkinter assets bundled:

```bat
build.bat
```

The compiled binary will be placed at:
```text
dist\BunnyM3U8.exe
```

---

## Running Tests

The test suite validates parsing, query preservation, token handling, and fallback URL extraction:

```bash
python -m unittest test_bunny.py
```

All 13 unit test cases run against mocked HTTP endpoints and edge-case inputs.

---

## Project Structure

```text
Bunny-M3U8-Converter/
├── assets/
│   ├── app.ico            # Windows application icon
│   └── app.png            # PNG application graphic
├── bunny_m3u8.py          # Core extractor logic, regex patterns, & CLI handler
├── gui_app.py             # CustomTkinter dark-themed desktop interface
├── make_icon.py           # Procedural icon generator
├── test_bunny.py          # Unit tests suite
├── build.bat              # One-click Windows build script
├── run.bat                # Windows launch script
├── run.sh                 # Linux / macOS launch script
├── requirements.txt       # Project dependencies
├── LICENSE                # MIT License
└── README.md              # Project documentation
```

---

## License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

Built by **[XMON4U](https://github.com/Xmon4u)**

</div>
