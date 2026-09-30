import io

import docx
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw, ImageFont

import app.main as main


# Draws lines of text onto a white PNG (fake handwriting).
def make_png(lines):
    img = Image.new("RGB", (900, 120 * len(lines) + 40), "white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=50)
    for i, line in enumerate(lines):
        draw.text((30, 30 + i * 100), line, fill="black", font=font)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# Builds a typed Word file.
def make_docx(lines):
    d = docx.Document()
    for line in lines:
        d.add_paragraph(line)
    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()


ANSWER = ["2x = 14 - 6", "2x = 8", "x = 4", "Answer: x = 4"]
FILES = {
    "memo": make_png(["Solve 2x + 6 = 14", "2x = 14 - 6", "2x = 8", "x = 4"]),
    "good-photo": make_png(ANSWER),
    "good-word": make_docx(ANSWER),
    "bad-file": b"this is not a real file",
}
# A missing key raises an error, which fakes a failed download.
main.fetch_file = lambda url: FILES[url]

client = TestClient(main.app)
rubric = [
    {"id": 1, "criterion": "Correct method shown", "max_points": 4},
    {"id": 2, "criterion": "Correct answer x = 4", "max_points": 4},
    {"id": 3, "criterion": "Clear final statement", "max_points": 2},
]
for name, key in [("handwritten photo", "good-photo"), ("typed Word", "good-word"),
                  ("unsupported file", "bad-file"), ("download fails", "missing")]:
    body = {"submission_id": 1, "submission_url": key, "memo_url": "memo",
            "total_points": 10, "rubric_criteria": rubric}
    r = client.post("/mark", json=body)
    print("----", name, "-> HTTP", r.status_code)
    print(r.json())
