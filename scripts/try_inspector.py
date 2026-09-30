import io

import docx
import pymupdf
from PIL import Image, ImageDraw

from app.inspector import inspect_file

LONG = "Solve 2x + 6 = 14. Step one is 2x = 14 - 6, so 2x = 8 and x = 4."


# Builds one sample file of each kind, in memory.
def samples():
    d = docx.Document()
    d.add_paragraph(LONG)
    buf = io.BytesIO()
    d.save(buf)
    word = buf.getvalue()

    pdf = pymupdf.open()
    pdf.new_page().insert_text((72, 72), LONG, fontsize=12)
    text_pdf = pdf.tobytes()

    img = Image.new("RGB", (600, 200), "white")
    ImageDraw.Draw(img).text((20, 80), "x = 4", fill="black")
    png = io.BytesIO()
    img.save(png, format="PNG")
    jpg = io.BytesIO()
    img.save(jpg, format="JPEG")
    scanned = io.BytesIO()
    img.save(scanned, format="PDF")

    return {
        "word": word,
        "text pdf": text_pdf,
        "scanned pdf": scanned.getvalue(),
        "png photo": png.getvalue(),
        "jpeg photo": jpg.getvalue(),
        "random bytes": b"this is not a real file",
    }


for name, data in samples().items():
    try:
        p = inspect_file(data)
        kind = "TYPED" if p.text is not None else "HANDWRITTEN"
        print(f"{name:13} -> {kind:12} {p.mime_type}")
    except ValueError as e:
        print(f"{name:13} -> REJECTED     ({e})")
