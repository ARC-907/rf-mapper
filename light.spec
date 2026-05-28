block_cipher = None

a = Analysis(
    ['src/sim_rf_map/__main__.py'],
    pathex=['src'],
    binaries=[],
    datas=[],
    hiddenimports=[],
    excludes=['onnxruntime', 'whitebox_tools', 'rasterio', 'torch'],
    runtime_hooks=['set_onyx_mode_lite.py'],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz, a.scripts, a.binaries, a.zipfiles, a.datas,
          name='rf-mapper',
          console=True)
coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas,
               strip=False, upx=True, name='rf-mapper',
               distpath='dist')
