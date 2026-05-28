# WhiteboxTools — install separately

RF Mapper optionally uses [WhiteboxTools](https://www.whiteboxgeo.com/) for
terrain analysis (DEM-derived metrics, slope/aspect, line-of-sight refinements).

WhiteboxTools is **MIT-licensed and free**, but its release binaries are ~99 MB
combined and we do not vendor them in this repo. Install them once per machine:

- Download the latest release for your OS from
  <https://www.whiteboxgeo.com/download-whiteboxtools/>
- Extract the contents into a `whitebox_tools/` directory at the repo root, OR
  set the `WBT_PATH` environment variable to point at your installation.

If WhiteboxTools is not installed, RF Mapper still runs — the WBT-dependent
features are gracefully skipped (the GUI marks them as "WBT required").
