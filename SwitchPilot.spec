# -*- mode: python ; coding: utf-8 -*-
import os


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('ICONE.ico', '.'), ('switchpilot/ui/themes', 'switchpilot/ui/themes'), ('switchpilot/references', 'switchpilot/references'), ('docs/help', 'docs/help'), ('VERSION', '.')],
    hiddenimports=['PyQt5', 'cv2', 'mss', 'numpy', 'websocket', 'markdown'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['rthook_skip_zstd.py'],
    excludes=['zstandard'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SwitchPilot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Desativar UPX reduz falsos positivos
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['ICONE.ico'],
    version='version_info.txt',  # Adicionar informações de versão
    manifest=os.path.abspath('switchpilot.manifest'),  # Adicionar manifest do Windows
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,  # Desativar UPX reduz falsos positivos
    upx_exclude=[],
    name='SwitchPilot',
)
