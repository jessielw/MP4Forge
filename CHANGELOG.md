# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0-rc4] - 2025-12-??

### Added

- Queue persistence between restarts
- Checkbox to optionally reset on job add (defaults to checked)

### Changed

- In output tab changed button text **Add Current to Queue** to **Add to Queue**

### Fixed

-

## [2.0.0-rc3] - 2025-12-13

### Added

- Ability to scroll through the tabs on the left hand side when the mouse is hovering in the nav panel

### Changed

- Adjusted the spacing in the nav panel
- Input box is now larger and wraps text to show more data
  - Adjusted input/delete buttons to stack on the right of the input widget
- Disabled scroll wheel for language combo box
- Improved the Output tab layout/visuals
- Update to PySide6 v6.10.1

### Fixed

- Chapter tab layout now pushes widgets to the top
- Layout issues with subtitles, video tab, chapters, and output tabs

## [2.0.0-rc2] - 2025-12-12

### Added

- Pop up for failure to load MediaInfo
- Multiple track import when opening a video on the **Video** tab:
  - New window to select which track(s) a user would like to import
    - This supports audio(s), subtitle(s) and chapters
- Error handling when a file is opened for video file without a video track
- Now detects language _(based off of MediaInfo)_ and applies it from input
- Now detects title and applies it from input
- Now detects default/forced flags where applicable and applies them from mediainfo if being imported from the video tab
- Default flags to audio/subtitles
  - Automatically unchecks other default flags if checked in another tab in the same category _(category: audio/subtitles)_
- Forced flags to subtitles
- Audio/subtitles are now importable from mp4/m4v files
- Button to see where log files are stored in the settings panel
- Now automatically cleans up log files over 50 log files ~1 seconds after UI initializes
- Added a **Details** column in the **Output** tab that will allow the user to click on it in the event of a failure and see the output from mp4box when a job fails
- Remembers last opened path in the context to open new file browsers at that same path
- Generates a default output name based on the input from the video tab _(file input_new.mp4)_
- Asks to overwrite if file already exists on adding new job to queue
- Now attempts to detects language from filename as a fallback if mediainfo doesn't have it
- Detects forced/foreign in subtitle filename and auto checks the track in the UI if input is not mp4/m4v

### Changed

- Subtitle tab now accepts **.mp4/.m4v**
- Improved logging (still some work to be done)
- All tabs contents are now wrapped in a scrolled area box - allowing the program to stay compact but also have larger default widget sizes if needed
- Changed to a slightly better icon for the program (still could use improvement)
- Error window pop can now be maximized

### Fixed

- Settings mp4box path was set to the wrong icon

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
