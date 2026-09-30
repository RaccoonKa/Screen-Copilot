import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

datas = [
    ('models', 'models'),
]

if os.path.exists('assets'):
    datas.append(('assets', 'assets'))

datas += collect_data_files('transformers')
datas += collect_data_files('torch')

hiddenimports = [
    'core',
    'core.ai_engine',
    'core.translator',
    'core.hotkey_listener',
    'core.process_watcher',
    'ui',
    'ui.styles',
    'ui.overlay_window',
    'ui.result_card',
    'ui.highlight_box',
    'pynput.keyboard._win32',
    'pynput.mouse._win32',
    'PIL._imagingtk',
    'PIL._tkinter_finder',
]
hiddenimports += collect_submodules('transformers')

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy'],
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
    name='ScreenCopilot',
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
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='ScreenCopilot',
)