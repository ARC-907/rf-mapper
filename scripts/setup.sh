#!/bin/sh
# Fetch the optional MiDaS depth model into weights/model_small.onnx.
# The app runs without it; depth inference stays disabled until present.
set -e

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
dest="$repo_root/weights/model_small.onnx"
url="https://github.com/isl-org/MiDaS/releases/download/v2_1/model-small.onnx"

if [ -f "$dest" ]; then
    echo "Model already present at $dest"
    exit 0
fi

mkdir -p "$(dirname "$dest")"
echo "Downloading MiDaS small model (~64 MB) from $url ..."
curl -L -o "$dest" "$url"
echo "Saved to $dest"
