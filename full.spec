from pathlib import Path
import sys
from PyInstaller.utils.hooks import collect_submodules

BASE = Path(sys.argv[0]).resolve().parent

block_cipher = None

a = Analysis(
    [str(BASE / 'src/sim_rf_map/main.py')],
    pathex = [
        str(BASE),
        str(BASE / 'src'),
        str(BASE / 'src/sim_rf_map'),  # Added to ensure packaging stability
    ],
    binaries=[],
    datas=[
        (str(BASE / 'weights' / 'model_small.onnx'), 'weights/model_small.onnx'),
        (str(BASE / 'README.md'), '.'),
        (str(BASE / 'src/sim_rf_map'), 'sim_rf_map'),
        (str(BASE / 'whitebox_tools/whitebox_tools.exe'), 'whitebox_tools'),
        (str(BASE / 'whitebox_tools/plugins'), 'whitebox_tools/plugins'),
        (str(BASE / 'whitebox_tools/img'), 'whitebox_tools/img'),
        (str(BASE / 'whitebox_tools/settings.json'), 'whitebox_tools'),
    ],
    hiddenimports=collect_submodules('cv2') + [
        'skimage.measure',
        'onnxruntime',
        'numpy',
        'rasterio',
        'tkinter',
        'PIL',
        'numba',
        'skimage',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='rf-mapper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='rf-mapper',
)
