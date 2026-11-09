import torch
from PIL import Image
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration
from qwen_vl_utils import process_vision_info

model_path = "/home/weitingwang/ai/models/Qwen2.5-VL-7B-Instruct"
image_path = "/home/weitingwang/ai/qwen25vl/sample.png"
Image.new("RGB", (448, 448), (186, 140, 90)).save(image_path)

print("loading", flush=True)
model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    model_path,
    torch_dtype=torch.bfloat16,
    device_map="cuda:0",
)
processor = AutoProcessor.from_pretrained(
    model_path,
    min_pixels=128 * 28 * 28,
    max_pixels=512 * 28 * 28,
)
messages = [{
    "role": "user",
    "content": [
        {"type": "image", "image": image_path},
        {"type": "text", "text": "这张纯色图主要是什么颜色？只回答一个词。"},
    ],
}]
text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
image_inputs, video_inputs = process_vision_info(messages)
inputs = processor(text=[text], images=image_inputs, videos=video_inputs, padding=True, return_tensors="pt")
inputs = inputs.to("cuda")
out = model.generate(**inputs, max_new_tokens=16)
trimmed = out[:, inputs.input_ids.shape[1]:]
print("ANSWER", processor.batch_decode(trimmed, skip_special_tokens=True)[0], flush=True)
print("SMOKE_OK", flush=True)
