set -e
export PATH="$HOME/.local/bin:$PATH"
mkdir -p /home/weitingwang/ai/qwen25vl
uv venv /home/weitingwang/ai/qwen25vl/.venv --python 3.12
uv pip install --python /home/weitingwang/ai/qwen25vl/.venv/bin/python torch torchvision --index-url https://download.pytorch.org/whl/cu124
uv pip install --python /home/weitingwang/ai/qwen25vl/.venv/bin/python "transformers>=4.49" accelerate pillow qwen-vl-utils huggingface_hub
/home/weitingwang/ai/qwen25vl/.venv/bin/python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
echo ENV_OK