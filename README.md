# Mp4Forge

A modern MP4 muxing tool with a desktop GUI interface, powered by MP4Box.

## Features

### Current Features (v2.0.0-rc)

- **Multi-track support**: Add multiple video, audio, subtitle, and chapter tracks to a single MP4 container
- **Multi-track MP4 audio selection**: Select specific audio tracks from MP4 files containing multiple audio streams
- **Language & metadata**: Set language codes, titles, default/forced flags for all tracks
- **Audio delay**: Support for audio delay values (automatically detected from filenames or MediaInfo)
- **Chapter support**: Import chapters from OGM/XML files or other MP4 containers
- **Queue system**: Build and manage multiple muxing jobs in a queue
- **Cross-platform**: Available for Windows (8+ x64), macOS, and Linux
- **Theme support**: Light, dark, and auto themes
- **Persistent configuration**: Settings stored in OS-appropriate locations (portable mode available)

### Supported Formats

**Video**: H.264/AVC, H.265/HEVC (as MP4/M4V input)  
**Audio**: AAC, AC3, E-AC3, MP2, MP3, Opus, OGG, MP4/M4A (with multi-track selection)  
**Subtitles**: SRT, SSA, ASS, VTT  
**Chapters**: OGM, XML, MP4 (extracted from existing files)  
**Output**: MP4 container only

## Requirements

**MP4Box** must be installed and available in your system PATH, or configured in the application settings.

- Download MP4Box: [GPAC Downloads](https://gpac.io/downloads/)
- Or install via package manager:
  - Windows: `winget install GPAC.GPAC` or `choco install gpac`
  - macOS: `brew install gpac`
  - Linux: `apt install gpac` or `yum install gpac`

## Installation

### Option 1: Download Pre-built Binaries (Recommended)

1. Go to the [Releases](https://github.com/jessielw/MP4-Mux-Tool/releases) page
2. Download the archive for your platform:
   - **Windows**: `Mp4Forge-Windows.zip`
   - **macOS**: `Mp4Forge-macOS.zip`
   - **Linux**: `Mp4Forge-Linux.tar.gz`
3. Extract the archive
4. Run the executable:
   - Windows: `Mp4Forge.exe`
   - macOS/Linux: `./Mp4Forge`

### Option 2: Run from Source

**Requirements**: Python 3.11 or 3.12, [uv](https://docs.astral.sh/uv/)

```bash
git clone https://github.com/jessielw/MP4-Mux-Tool.git
cd MP4-Mux-Tool
uv sync --all-extras
uv run python frontend_desktop/main.py
```

## Usage

1. **Add tracks**: Use the Video, Audio, Subtitles, and Chapters tabs to add input files
   - Drag & drop files directly onto tabs
   - Use the file browser button
   - For multi-track MP4 audio files, a track selector dialog will appear
2. **Configure metadata**: Set language, title, default/forced flags, and delay for each track

3. **Set output**: Go to the Output tab and specify your output file path

4. **Add to queue**: Click "Add Current Job" to add the muxing job to the queue

5. **Process**: Click "Process Queue" to start muxing all queued jobs

### Multi-track Audio

When adding an MP4 file with multiple audio tracks to an audio tab, Mp4Forge will display a track selector dialog showing:

- Track ID
- Format
- Channels
- Bitrate
- Sample rate
- Language
- Title
- Delay

Select the track you want to use and click OK.

### Portable Mode

By default, configuration is stored in your OS user config directory:

- **Windows**: `%APPDATA%\Mp4Forge\config.toml`
- **macOS**: `~/Library/Application Support/Mp4Forge/config.toml`
- **Linux**: `~/.config/Mp4Forge/config.toml`

For portable installations, the config is stored in the `runtime/` folder alongside the executable.

## Roadmap

### Planned Features

- **Docker/Web version**: Web-based interface with Docker deployment for headless servers (coming soon)
- **Batch processing**: Process multiple files with templates
- **Advanced MP4Box options**: Additional muxing flags and optimizations
- **Video format support**: Direct support for more video codecs

## Development

### Building from Source

```bash
# Install dependencies
uv sync --all-extras

# Run the application
uv run python frontend_desktop/main.py

# Build executables
uv run python build_desktop.py
```

### Tech Stack

- **Backend**: MP4Box (GPAC)
- **Frontend**: PySide6 (Qt6)
- **Build**: PyInstaller
- **Package Manager**: uv
- **MediaInfo**: pymediainfo for track inspection

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

See [LICENSE](LICENSE) for details.

## Credits

- Powered by [GPAC/MP4Box](https://gpac.io/)
- Built with [PySide6](https://wiki.qt.io/Qt_for_Python)
