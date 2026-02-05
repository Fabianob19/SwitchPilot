# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.6.1] - 2026-02-05
### Fixed
- **Detection**: Runtime NCC Fallback for dynamic textures (noise/static/particles).
  - **Problem**: Images with random textures (where pixels change position each frame) resulted in NCC scores near zero, even when color distribution was identical, causing final scores of ~0.71.
  - **Solution**: System now detects when Histogram is near-perfect (>95%) but NCC fails (<10%), redistributing NCC weight to Histogram, raising final score to ~0.91.
  - Works transparently with the default 0.90 threshold.

### Added
- `switchpilot/utils/paths.py`: New utility module for cross-environment path resolution (dev and PyInstaller).
- `rthook_skip_zstd.py`: Runtime hook to resolve `zstandard` module conflicts in PyInstaller builds.

### Changed
- Refactored `__init__.py` and `help_center.py` to use the new path resolution system.

## [1.6.0] - 2026-02-03
### Added
- Unified Help Center (`docs/help/`) with Markdown support.
- `llms.txt` for AI discovery.
- Developer documentation structure (`docs/developer/`).

### Changed
- Refactored `main_window.py` to support dynamic help dialogs.
- Cleaned up repository structure (removed build artifacts from git).

## [1.5.2] - 2025-10-14
### Fixed
- **Thread Zombie**: Monitoring thread now returns immediately when no references are present.
- **OBS WebSocket**: Explicit closure implemented in application cleanup.
- **Legacy Methods**: Removed obsolete `connect_to_ui_slots()` calls causing `AttributeError`.

### Changed
- **Code Quality**: Documented "magic numbers" as constants (`HIST_BINS`, `WEIGHT_*`).
- **Logging**: Improved error messages to show expected ranges.
- **Cleanup**: Removed ~12 redundant print statements and duplicate code blocks.

## [1.5.2-beta2] - 2025-09-30
### Performance
- **NCC Algorithm**: Implemented intelligent downscaling (128x128), increasing precision by 5% and detection score by 1%.
- **Ensemble Weights**: Rebalanced weights (Hist: 40%, NCC: 20%, LBP: 40%) for better stability.

### Changed
- **Project Structure**: Removed unrelated network scripts and Kali configs.
- **Optimization**: Switched to `INTER_AREA` interpolation for image downscaling.

## [1.5.2-beta1] - 2025-09-17
### Added
- **UI**: Custom dark title bar, distinct menu bar, and new app icon.
- **DPI Support**: Per-Monitor v2 awareness for correct coordinates on high-DPI screens.
- **Detection**: Improved algorithm (Hist+NCC+LBP) with temporal smoothing.
- **Integrations**: On-demand OBS connection and aligned action mappings.

## [1.1.0] - 2024-06-XX
### Changed
- Removed NDIlib dependencies (feature optional/disabled).
- Cleaned up test files and old binaries.
- Generated optimized `requirements.txt`.

## [1.0.0] - 2025-05-01
### Added
- Initial stable release.
- Modern PyQt5 interface with 3 themes.
- Visual ROI selection.
- vMix and OBS integration.
- Reference image manager with multi-action support.
