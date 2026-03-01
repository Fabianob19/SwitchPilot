# SwitchPilot

> **Intelligent Scene Switcher for OBS & vMix**  
> SwitchPilot automates your live stream by monitoring your screen, detecting specific scenes using advanced computer vision (Histogram + NCC + LBP), and triggering actions in OBS Studio or vMix —  with built-in **NSFW detection** to protect your broadcast.

[![Download](https://img.shields.io/badge/Download-Latest_Release-blue?style=for-the-badge&logo=windows)](https://github.com/Fabianob19/SwitchPilot/releases/latest)
[![Discord](https://img.shields.io/badge/Discord-Join_Community-5865F2?style=for-the-badge&logo=discord)](https://discord.gg/2MKdsQpMFt)

---

## 🚀 Quick Start

1. **Download**: Get the latest installer (`.exe`) from the [Releases Page](https://github.com/Fabianob19/SwitchPilot/releases/latest).
2. **Install**: Run the installer. It will set up everything automatically.
3. **Run**: Open "SwitchPilot" from your Start Menu.
4. **Configure**:
    - **Reference Manager**: Select a region of your screen to monitor.
    - **Add Reference**: Capture a scene (e.g., "Map Screen" or "Lobby") and assign an action.
    - **Start**: Click "Iniciar Monitoramento".

## ✨ Features

- **👀 Real-Time Scene Detection**: Robust ensemble algorithm (Histogram + NCC + LBP) with ~95% accuracy.
- **🛡️ NSFW Detection**: AI-powered content moderation using YOLOv8 + ONNX Runtime with GPU acceleration (DirectML).
  - Automatic scene switching when inappropriate content is detected.
  - Configurable thresholds per category (general, breasts, anus, genitalia).
  - CLAHE preprocessing for improved dark scene detection.
  - Fast scan at 416px + deep scan at 640px for optimal speed/accuracy.
- **🎥 Multi-Platform**: Native support for **OBS Studio** (WebSocket 5.0) and **vMix** (Web Controller).
- **🖱️ Flexible Capture**: Monitor specific windows or screen regions.
- **🎨 Modern UI**: Dark mode interface with PyQt5, custom title bar, and responsive layout.
- **⚡ Low Latency**: Optimized ~0.5s cycle with ~5% CPU usage. GPU-accelerated NSFW detection (~12ms/frame).
- **🎯 Per-Reference PGM**: Each reference can have its own PGM Region for multi-area monitoring.
- **⚙️ Configurable Thresholds**: All detection parameters adjustable via GUI with persistent settings.

## 🛠️ Configuration

| Setting | Description | Default |
|---------|-------------|---------|
| **Similarity Threshold** | Score required to trigger scene action | `0.90` |
| **NSFW General Sensitivity** | Minimum confidence for NSFW detection | `55%` |
| **NSFW Breast Confidence** | Minimum confidence for breast detection | `60%` |
| **OBS Port** | WebSocket port for OBS connection | `4455` |
| **vMix Port** | Web Controller port for vMix | `8088` |

Access all thresholds via **Settings → Configure Thresholds...** (`Ctrl+T`).

## 📚 Documentation

- **[User Guide](./docs/help/tutorial.md)**: Full tutorial and usage instructions.
- **[Developer Docs](./docs/developer/project_structure.md)**: Project structure and architecture.
- **[Changelog](./CHANGELOG.md)**: Version history.

## 🏗️ Building from Source

```bash
# Clone the repository
git clone https://github.com/Fabianob19/SwitchPilot.git
cd SwitchPilot

# Create virtual environment (Python 3.10)
python -m venv .venv310
.venv310\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run in development mode
python main.py

# Build installer (requires PyInstaller + Inno Setup 6)
pyinstaller SwitchPilot.spec --noconfirm
# Then compile SwitchPilot_Installer.iss with Inno Setup
```

## 🤝 Contributing

Contributions are welcome! Please check the [Developer Documentation](./docs/developer/project_structure.md) to understand the codebase structure.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Developed with ❤️ by <a href="https://github.com/Fabianob19">FabianoB</a>
</p>
