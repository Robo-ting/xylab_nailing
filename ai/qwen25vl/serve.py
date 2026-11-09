import base64
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import torch
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration
from qwen_vl_utils import process_vision_info

MODEL_PATH = "/home/weitingwang/ai/models/Qwen2.5-VL-7B-Instruct"
print("loading", flush=True)
model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.bfloat16,
    device_map="cuda:0",
)
processor = AutoProcessor.from_pretrained(
    MODEL_PATH,
    min_pixels=128 * 28 * 28,
    max_pixels=512 * 28 * 28,
)
print("READY", flush=True)


def answer(image_path: str, prompt: str) -> str:
    messages = [{
        "role": "user",
        "content": [
            {"type": "image", "image": image_path},
            {"type": "text", "text": prompt},
        ],
    }]
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = processor(text=[text], images=image_inputs, videos=video_inputs, padding=True, return_tensors="pt")
    inputs = inputs.to("cuda")
    out = model.generate(**inputs, max_new_tokens=512)
    trimmed = out[:, inputs.input_ids.shape[1]:]
    return processor.batch_decode(trimmed, skip_special_tokens=True)[0]


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/health":
            self.send_error(404)
            return
        body = json.dumps({"status": "ok", "model": "Qwen2.5-VL-7B-Instruct"}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/analyze":
            self.send_error(404)
            return
        size = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(size))
        prompt = payload.get("prompt") or "描述这张图。"
        if payload.get("image_base64"):
            image_path = "/tmp/qwen-analyze.jpg"
            with open(image_path, "wb") as handle:
                handle.write(base64.b64decode(payload["image_base64"]))
        else:
            image_path = payload["image_path"]
        text = answer(image_path, prompt)
        body = json.dumps({"text": text}, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print(fmt % args, flush=True)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 8011), Handler)
    print("LISTEN 8011", flush=True)
    server.serve_forever()