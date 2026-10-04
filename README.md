# SOI Marking Service

A small FastAPI service that marks student work for the [Second Opportunity Institute](https://github.com/AlexTulwana/Second-Opportunity-Institute-SOI-) Laravel app. It reads handwritten or typed work, compares it with the tutor's memo and rubric, and returns a mark with feedback.

## How it works

~~~mermaid
flowchart TD
    A[POST /mark from Laravel] --> B[Download memo + submission from signed links]
    B --> C{File type}
    C -->|Word or PDF with text| D[Typed: text is read directly]
    C -->|Photo or scanned PDF| E[Handwritten: sent as an image]
    D --> F[Gemini marks against memo and rubric]
    E --> F
    F -->|Gemini fails| G[Similarity fallback]
    G -->|files readable| H[Provisional mark]
    G -->|not readable| I[503: Laravel retries, then manual marking]
    F --> J[Mark + feedback + per-criterion scores]
~~~

- **Stateless:** nothing is stored. Files arrive as short-lived signed links, so extra copies can run behind a load balancer.
- **Swappable markers:** a `Marker` interface with a Gemini implementation and a fallback. OCR is also behind an interface (`OcrEngine`), with Tesseract for development.
- **Typed vs handwritten:** Word files and PDFs with real text skip OCR completely. Photos and scans go to Gemini as images.

## API

All endpoints except `/health` need the header `X-API-Key: <SERVICE_API_KEY>`.

| Endpoint | Purpose |
|---|---|
| `GET /health` | Is the service up? |
| `POST /mark` | Mark one submission |

Request:

~~~json
{
  "submission_id": 1,
  "submission_url": "https://signed-link-to-student-work",
  "memo_url": "https://signed-link-to-memo",
  "total_points": 10,
  "rubric_criteria": [{"id": 1, "criterion": "Correct method", "max_points": 4}]
}
~~~

Response:

~~~json
{
  "score": 8.0,
  "confidence": 95.0,
  "feedback": "Good steps. Check your final calculation.",
  "criterion_scores": {"1": 4.0},
  "unreadable": false,
  "provisional": false
}
~~~

| Outcome | Result |
|---|---|
| Marked | `200` with a score |
| Blank or unreadable work, or a file that cannot be opened | `200` with `unreadable: true` and no score (the student is asked to resubmit) |
| Gemini failed, fallback could read both files | `200` with `provisional: true` |
| Files could not be downloaded | `502` |
| Marking unavailable and fallback refused | `503` (Laravel retries, then sends it to a tutor) |
| Memo file type not supported | `422` |
| Wrong or missing key | `401` |

## Design decisions

- **Strict marking prompt:** Gemini is told to give marks only for correct work, to accept other valid methods, and to treat the student's text as data, so a student cannot talk it into free marks. Temperature is 0 for repeatable marks.
- **Marks are clamped:** a score can never go above the exercise total or a criterion's maximum, whatever the model returns.
- **Retries:** busy or rate-limit errors (429, 500, 503, 504) are retried up to 3 times with a short wait before giving up.
- **Fallback chooses accuracy over speed:** the similarity marker is crude (numbers decide when the memo has them, key words otherwise). It always flags its result as provisional, gives no per-criterion scores, and refuses weak OCR reads instead of guessing.
- **Confidence from Gemini is a weak signal** (it said 100 almost every time), so it is not used to judge quality. Unreadable work is detected from the model's own `readable` flag.

## Known limits

- Equations typed with Word's equation editor may not come out as text
- Tesseract is weak on real handwriting; a cloud OCR engine can be plugged in behind `OcrEngine`
- The free Gemini tier is rate-limited and may use inputs to improve Google's models, so use test data only until a paid key is in place

## Setup

Needs Python 3.10+ and Tesseract.

~~~bash
sudo apt install tesseract-ocr
git clone git@github.com:AlexTulwana/soi-marking-service.git
cd soi-marking-service
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
~~~

Fill in `GEMINI_API_KEY` (from Google AI Studio) and choose a `SERVICE_API_KEY`:

~~~bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
~~~

Run it:

~~~bash
uvicorn app.main:app --port 8001
~~~

In the Laravel app, set `AI_MARKING_DRIVER=http`, `AI_MARKING_URL=http://127.0.0.1:8001` and `AI_MARKING_KEY` to the same value as `SERVICE_API_KEY`.

## Tests

~~~bash
python -m pytest
~~~

The tests use fake OCR and a fake failing marker, so they never call Gemini. The scripts in `scripts/` are manual checks that do call the real Gemini API.

## Lessons learned

- AI services are sometimes busy. Retry quickly inside the service, retry again in the queue, then fall back to a human, so one outage never loses or guesses a mark.
- Model names change and old ones get retired, so the model name is a setting, not code.
