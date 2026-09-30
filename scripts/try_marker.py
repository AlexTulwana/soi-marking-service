import io

from PIL import Image, ImageDraw

from app.markers.base import FilePayload, MarkingInput
from app.markers.gemini_marker import GeminiMarker
from app.schemas import RubricCriterion
from PIL import ImageFont


# Draws lines of text onto a white PNG image (fake handwriting).
def make_image(lines):
    img = Image.new("RGB", (900, 120 * max(len(lines), 1) + 40), "white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=50)
    for i, line in enumerate(lines):
        draw.text((30, 30 + i * 100), line, fill="black", font=font)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return FilePayload(data=buf.getvalue(), mime_type="image/png")


memo = make_image(["Solve 2x + 6 = 14", "2x = 14 - 6", "2x = 8", "x = 4"])
rubric = [
    RubricCriterion(id=1, criterion="Correct method shown", max_points=4),
    RubricCriterion(id=2, criterion="Correct answer x = 4", max_points=4),
    RubricCriterion(id=3, criterion="Clear final statement", max_points=2),
]
cases = {
    "A (correct)": make_image(["2x = 14 - 6", "2x = 8", "x = 4", "Answer: x = 4"]),
    "C (wrong answer)": make_image(["2x = 14 - 6", "2x = 8", "x = 10"]),
    "D (blank)": make_image([]),
}

marker = GeminiMarker()
for name, sub in cases.items():
    r = marker.mark(MarkingInput(10, sub, memo, rubric))
    print("----", name)
    print("score:", r.score, "| unreadable:", r.unreadable)
    print("criteria:", r.criterion_scores)
    print("feedback:", r.feedback)
