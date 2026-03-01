# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.7.0] - 2026-03-01
### Added
- **NSFW Detection v11**: Motor de detecção NSFW customizado baseado em YOLOv8 (640m) com Engine ONNX própria.
- **GPU Acceleration**: Suporte a aceleração por GPU via DirectML (compatível com NVIDIA, AMD e Intel).
  - Fallback automático para CPU quando GPU não disponível.
- **Fase 2 Assíncrona**: Detecção profunda em background thread com análise por quadrantes.
- **Limiares NSFW Configuráveis**: Interface para ajustar sensibilidade geral e confiança mínima por categoria (seios, ânus, genitálias) via menu Configurações → Configurar Limiares (Ctrl+T).
- **Persistência NSFW**: Configurações de limiares NSFW salvas em `switchpilot_config.json`.

### Changed
- **ONNX Session Optimization**: Graph optimization (`ORT_ENABLE_ALL`) + configuração DirectML para máxima performance.
- **Resolução Adaptativa**: Fase 1 (rápida) usa 416px, Fase 2 (profunda) usa 640px — ~2x mais rápido sem perder precisão.
- **CLAHE Preprocessing**: Equalização adaptativa de contraste melhora detecção em cenas escuras (+10-24%).
- **YOLO Score Filter**: Reduzido de 0.20 para 0.15, melhor recall sem falsos positivos.
- **Dependências**: Adicionadas `nudenet` e `onnxruntime-directml` ao `requirements.txt`.
- **Build**: `SwitchPilot.spec` atualizado para o novo sistema de detecção.
- **UI**: Menu "Limiar de Similaridade..." renomeado para "Configurar Limiares..." com seção NSFW integrada.

### Removed
- Modelo ViT ONNX antigo (`nsfw.onnx`) e classificador de 5 categorias genéricas.
- Pacote `Pillow` como dependência (não é mais necessário).
- Scripts de teste avulsos da raiz do projeto (`test_nsfw_speed.py`, `test_onnx.py`).

## [1.6.2] - 2026-02-10
### Fixed
- **Persistence**: Fixed an issue where PGM Region details were lost after application restart.
- **UI Overlay**: Capture Area Overlay (F11) now correctly updates its position when selecting different references.
- **Auto-Save**: References, PGM details, **OBS, and vMix settings** are now saved immediately upon modification.
- **Installer**: Fixed missing `markdown` dependency preventing Help Center from loading.
- **Installer**: Fixed version metadata (now correctly shows 1.6.2 instead of 0.0.0.0).

### Changed
- **Cleanup**: Removed unused `tools/` and `tests/` directories and legacy config files from the repository.
- **Build**: Improved build process to ensure a clean environment (no stale config files).

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
