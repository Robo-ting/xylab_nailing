set -e
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv --version
rm -rf /home/weitingwang/xylab/backend/.venv
uv venv /home/weitingwang/xylab/backend/.venv
uv pip install -r /home/weitingwang/xylab/backend/requirements.txt --python /home/weitingwang/xylab/backend/.venv/bin/python
echo BACKEND_OK