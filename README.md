# SwitchPilot

> **Intelligent Scene Switcher for OBS & vMix**  
> switchpilot automates your live stream by monitoring your screen, detecting specific scenes using advanced computer vision (Histogram + NCC + LBP), and triggering actions in OBS Studio or vMix.

[![Download](https://img.shields.io/badge/Download-Latest_Release-blue?style=for-the-badge&logo=windows)](https://github.com/Fabianob19/SwitchPilot/releases/latest)
[![Discord](https://img.shields.io/badge/Discord-Join_Community-5865F2?style=for-the-badge&logo=discord)](https://discord.gg/2MKdsQpMFt)

---

## 🚀 Quick Start

1. **Download**: Get the latest installer (`.exe`) from the [Releases Page](https://github.com/Fabianob19/SwitchPilot/releases/latest).
2. **Install**: Run the installer. It will set up everything in `C:\Program Files\SwitchPilot`.
3. **Run**: Open "SwitchPilot" from your Start Menu.
4. **Configure**:
    - **Reference Manager**: Select a region of your screen to monitor.
    - **Add Reference**: Capture a scene (e.g., "Map Screen" or "Lobby") and assign an action (e.g., "Switch to Scene: In-Game").
    - **Start**: Click "Iniciar Monitoramento".

## ✨ Features

- **👀 Real-Time Detection**: Uses a robust ensemble algorithm (Histogram + NCC + LBP) to detect scenes with ~95% accuracy.
- **🎥 Multi-Platform Support**: Native control for **OBS Studio** (WebSocket 5.0) and **vMix** (Web Controller).
- **🖱️ Flexible Capture**: Monitor specific windows or screen regions.
- **🎨 Modern UI**: Dark mode interface built with PyQt5, featuring a custom title bar and responsive layout.
- **⚡ Low Latency**: Optimized processing (~0.5s cycle) with minimal CPU usage (~5%).
- **🎯 Per-Reference PGM**: Each reference can have its own PGM Region, enabling monitoring of multiple areas or cameras simultaneously.

## 🛠️ Configuration

| Setting | Description | Recommended |
|---------|-------------|-------------|
| **Threshold** | Similarity score required to trigger action | `0.88` - `0.92` |
| **OBS Port** | WebSocket port for OBS connection | `4455` |
| **vMix Port** | Web Controller port for vMix | `8088` |

## 📚 Documentation

- **[User Guide](./docs/help/tutorial.md)**: Full tutorial and usage instructions.
- **[Developer Docs](./docs/developer/project_structure.md)**: Project structure and architecture for contributors.
- **[Changelog](./CHANGELOG.md)**: Version history.

## 🤝 Contributing

Contributions are welcome! Please check the [Developer Documentation](./docs/developer/project_structure.md) to understand the codebase structure.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Developed with ❤️ by <a href="https://github.com/Fabianob19">FabianoB</a>
</p>
