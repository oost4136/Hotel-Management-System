# -*- mode: python ; coding: utf-8 -*-
# Hotel PMS - PyInstaller Build Spec
# Run with: pyinstaller hotel_pms.spec

import os

block_cipher = None

# Collect all Python source files in the project directory
a = Analysis(
    ['main.py'],                          # Entry point
    pathex=['.'],
    binaries=[],
    datas=[
        ('assets', 'assets'),             # Bundle the assets (room/inventory images)
    ],
    hiddenimports=[
        'customtkinter',
        'PIL',
        'PIL._tkinter_finder',
        'fpdf',
        'bcrypt',
        'sqlite3',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='HotelPMS',                      # Name of the final .exe
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,                        # <-- Hides the black terminal window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='HotelPMS',                      # Output folder name inside /dist
)
