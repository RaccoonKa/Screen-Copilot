import os
import shutil
from huggingface_hub import snapshot_download
from config import MODEL_DIR

if os.path.exists(MODEL_DIR):
    shutil.rmtree(MODEL_DIR, ignore_errors=True)

os.makedirs(MODEL_DIR, exist_ok=True)

snapshot_download(
    repo_id="vikhyatk/moondream2",
    revision="2024-08-26",
    local_dir=MODEL_DIR,
    local_dir_use_symlinks=False,
    force_download=True
)

cache_hf = os.path.expanduser("~/.cache/huggingface/modules/transformers_modules/moondream2")
if os.path.exists(cache_hf):
    shutil.rmtree(cache_hf, ignore_errors=True)

print("The original pure Moondream2 weights have been restored.")