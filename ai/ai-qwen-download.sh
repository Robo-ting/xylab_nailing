set -e
export PATH="$HOME/.local/bin:$PATH"
export HF_ENDPOINT=https://hf-mirror.com
export HF_HOME=/home/weitingwang/ai/hf-home
export HF_HUB_DISABLE_XET=1
nohup /home/weitingwang/ai/qwen25vl/.venv/bin/python - << "PY" > /home/weitingwang/ai/qwen25vl/download.log 2>&1 &
from huggingface_hub import snapshot_download
path = snapshot_download(
    repo_id="Qwen/Qwen2.5-VL-7B-Instruct",
    local_dir="/home/weitingwang/ai/models/Qwen2.5-VL-7B-Instruct",
)
print("DOWNLOADED", path, flush=True)
PY
echo $! > /home/weitingwang/ai/qwen25vl/download.pid
echo STARTED $(cat /home/weitingwang/ai/qwen25vl/download.pid)