# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0-rc2] - 2025-12-07

### Added

- Pop up for failure to load MediaInfo
- Multiple track import when opening a video on the **Video** tab:
  - New window to select which track(s) a user would like to import
    - This supports audio(s), subtitle(s) and chapters
- Error handling when a file is opened for video file without a video track
- Now detects language _(based off of MediaInfo)_ and applies it from input
- Now detects title and applies it from input
- Now detects default/forced flags where applicable and applies them from input
- Default flags to audio/subtitles
  - Automatically unchecks other default flags if checked in another tab in the same category _(category: audio/subtitles)_
- Forced flags to subtitles
- Audio/subtitles are now importable from mp4/m4v files

### Changed

- Subtitle tab now accepts **.mp4/.m4v**
- Improved logging (still some work to be done)

### Fixed

-

### Removed

-

## [2.0.0-rc1] - 2025-12-07

### Added

- Multi track support
- Dark mode
- Multi OS support

### Changed

- Complete re-write of the program in a modern framework covering a lot of issues
- Release no longer includes the binaries. Refer to the [readme](https://github.com/jessielw/MP4-Mux-Tool?tab=readme-ov-file#installation) to install mp4box
