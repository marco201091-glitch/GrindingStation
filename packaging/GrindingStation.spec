# Build from the repository root:
# python -m PyInstaller --noconfirm packaging/GrindingStation.spec
from pathlib import Path

root = Path(SPECPATH).parent
a = Analysis(
    [str(root / 'ui.py')],
    pathex=[str(root)],
    binaries=[],
    datas=[(str(root / name), name) for name in ('images', 'Buttons', 'assets', 'data')],
    hiddenimports=['pynput.keyboard._win32', 'pynput.mouse._win32'],
    hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[],
    noarchive=False, optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name='GrindingStation', debug=False, bootloader_ignore_signals=False,
    strip=False, upx=True, upx_exclude=[], runtime_tmpdir=None,
    console=False, disable_windowed_traceback=False, argv_emulation=False,
    target_arch=None, codesign_identity=None, entitlements_file=None,
    icon=[str(root / 'images' / 'grinding_station.ico')],
)
