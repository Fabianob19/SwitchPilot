# -*- mode: python ; coding: utf-8 -*-
import os
import sys

import importlib
_nudenet_dir = os.path.dirname(importlib.import_module('nudenet').__file__)

from PyInstaller.utils.hooks import collect_all

datas = [
    (os.path.abspath('ICONE.ico'), '.'),
    (os.path.abspath('switchpilot/ui/themes'), 'switchpilot/ui/themes'),
    (os.path.abspath('switchpilot/references'), 'switchpilot/references'),
    (os.path.abspath('docs/help'), 'docs/help'),
    (os.path.abspath('VERSION'), '.'),
    (os.path.join(_nudenet_dir, '640m.onnx'), 'nudenet'),
]

binaries = [
    ('C:\\Windows\\System32\\vcomp140.dll', '.'),
    ('C:\\Windows\\System32\\msvcp140.dll', '.'),
    ('C:\\Windows\\System32\\vcruntime140.dll', '.'),
    ('C:\\Windows\\System32\\vcruntime140_1.dll', '.'),
]

hiddenimports = ['PyQt5', 'cv2', 'mss', 'numpy', 'websocket', 'markdown']

tmp_ret = collect_all('onnxruntime')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

tmp_ret = collect_all('nudenet')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['rthook_skip_zstd.py', 'rthook_onnx_preload.py'],
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
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[os.path.abspath('ICONE.ico')],
    version=os.path.abspath('version_info.txt'),
    manifest=os.path.abspath('switchpilot.manifest'),
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
