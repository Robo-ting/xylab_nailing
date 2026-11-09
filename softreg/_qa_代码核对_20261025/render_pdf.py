from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image, ImageDraw

root = Path(r"D:\论文\软著申请\_qa_代码核对_20261025")
pdf = pdfium.PdfDocument(root / "rendered_09.pdf")
out = root / "pages_09"
out.mkdir(exist_ok=True)
thumbs = []

for i in range(len(pdf)):
    image = pdf[i].render(scale=1.8).to_pil()
    image.save(out / f"page_{i + 1:02}.png")
    thumbnail = image.copy()
    thumbnail.thumbnail((540, 760))
    thumbs.append(thumbnail)

cols = 3
rows = (len(thumbs) + cols - 1) // cols
sheet = Image.new("RGB", (cols * 560, rows * 800), "#dddddd")
draw = ImageDraw.Draw(sheet)
for i, image in enumerate(thumbs):
    x = (i % cols) * 560 + 10
    y = (i // cols) * 800 + 25
    sheet.paste(image, (x, y))
    draw.text((x, y - 20), f"Page {i + 1}", fill="black")
sheet.save(root / "contact_09.png")
print(f"Rendered {len(pdf)} pages")
