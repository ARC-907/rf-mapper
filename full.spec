from pathlib import Path
import sys
from PyInstaller.utils.hooks import collect_submodules

BASE = Path(sys.argv[0]).resolve().parent

block_cipher = None

# Optional payloads: bundle only what actually exists so a checkout without
# the ONNX model or a local WhiteboxTools install still builds. The app
# detects missing optional resources at runtime (sim_rf_map.capabilities).
datas = [
    (str(BASE / 'README.md'), '.'),
    (str(BASE / 'src/sim_rf_map'), 'sim_rf_map'),
]
_model = BASE / 'weights' / 'model_small.onnx'
if _model.exists():
    datas.append((str(_model), 'weights'))
else:
    print('full.spec: weights/model_small.onnx not found - building without depth model')
_wbt = BASE / 'whitebox_tools'
if _wbt.exists():
    for entry, target in (
        ('whitebox_tools.exe', 'whitebox_tools'),
        ('plugins', 'whitebox_tools/plugins'),
        ('img', 'whitebox_tools/img'),
        ('settings.json', 'whitebox_tools'),
    ):
        candidate = _wbt / entry
        if candidate.exists():
            datas.append((str(candidate), target))
else:
    print('full.spec: whitebox_tools/ not found - building without WhiteboxTools payload')

# Optional heavy imports: include only those installed in the build env.
hiddenimports = ['skimage.measure', 'numpy', 'tkinter', 'PIL', 'skimage']
for optional in ('onnxruntime', 'rasterio', 'numba'):
    try:
        __import__(optional)
        hiddenimports.append(optional)
    except ImportError:
        print(f'full.spec: {optional} not installed - excluded from bundle')
try:
    import cv2  # noqa: F401
    hiddenimports += collect_submodules('cv2')
except ImportError:
    print('full.spec: cv2 not installed - excluded from bundle')

a = Analysis(
    [str(BASE / 'src/sim_rf_map/main.py')],
    pathex = [
        str(BASE),
        str(BASE / 'src'),
        str(BASE / 'src/sim_rf_map'),  # Added to ensure packaging stability
    ],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[str(BASE / 'set_onyx_mode_full.py')],
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
