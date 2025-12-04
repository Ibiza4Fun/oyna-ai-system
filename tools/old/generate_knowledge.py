import os
import json
import base64
from pathlib import Path
from pypdf import PdfReader
import docx
from openai import OpenAI

# OpenAI client – API key provided via environment (OPENAI_API_KEY)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

RAW_DIR = Path("ai-input/raw")
OUT_DIR = Path("knowledge")
OUT_DIR.mkdir(exist_ok=True)

# --------------------------
# Extract TEXT from documents
# --------------------------

def extract_text_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text


def extract_text_docx(path: Path) -> str:
    doc = docx.Document(str(path))
    return "\n".join([p.text for p in doc.paragraphs])


def extract_text_generic(path: Path) -> str:
    try:
        return path.read_text(errors="ignore")
    except Exception:
        return ""


def extract_image_base64(path: Path) -> str:
    """
    Returns a data: URL with base64-encoded image content.
    This can be passed directly to OpenAI Vision.
    """
    with path.open("rb") as imgf:
        encoded = base64.b64encode(imgf.read()).decode("utf-8")

    ext = path.suffix.lower()
    if ext == ".png":
        mime = "image/png"
    else:
        mime = "image/jpeg"

    return f"data:{mime};base64,{encoded}"


def extract_content(path: Path) -> str:
    """
    Returns either plain text (for docs) or a data:image/... base64 string for images.
    """
    ext = path.suffix.lower()

    if ext == ".pdf":
        return extract_text_pdf(path)

    if ext == ".docx":
        return extract_text_docx(path)

    if ext in [".txt", ".md"]:
        return extract_text_generic(path)

    if ext in [".png", ".jpg", ".jpeg", ".webp"]:
        return extract_image_base64(path)

    # Fallback: mark as unsupported
    return f"[UNSUPPORTED FILE TYPE: {path.name}]"


# --------------------------
# AI CONVERSION
# --------------------------

def ai_convert_to_knowledge(content: str, filename: str) -> str:
    """
    Sends either text or image+text to OpenAI and expects STRICT JSON in response.
    Returns the JSON string (optionally normalized).
    """

    is_image = content.startswith("data:image")

    if is_image:
        user_content = [
            {
                "type": "image_url",
                "image_url": {
                    "url": content
                },
            },
            {
                "type": "text",
                "text": f"""
You are ØynaWaterworksDocAI.

The user has provided an ENGINEERING DIAGRAM / PHOTO as an image.

Task:
- Inspect the image carefully.
- Identify components, connections, flows, and relevant technical context.
- Convert this into a structured Øyna AI knowledge module.

Requirements:
- Be factual and concise.
- Do NOT mention that you saw an image; just describe the system.
- Output STRICT JSON ONLY. No explanation, no markdown.

Filename: {filename}
                """.strip(),
            },
        ]
    else:
        user_content = [
            {
                "type": "text",
                "text": f"""
You are ØynaWaterworksDocAI.

The user has provided an ENGINEERING DOCUMENT for Øyna Vassverk (waterworks).

Task:
- Convert the following document into a structured Øyna AI knowledge module.
- Capture the core facts, structure, and relationships.
- Use clear, factual, engineering-oriented descriptions.
- Output STRICT JSON ONLY. No explanation, no markdown.

Document filename: {filename}

Document content:
{content}
                """.strip(),
            }
        ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You convert Øyna waterworks engineering documents and diagrams into "
                    "structured JSON knowledge modules compatible with downstream AI agents."
                ),
            },
            {
                "role": "user",
                "content": user_content,
            },
        ],
    )

    raw_content = response.choices[0].message.content

    # Try to normalize to valid JSON
    try:
        parsed = json.loads(raw_content)
        return json.dumps(parsed, ensure_ascii=False, indent=2)
    except Exception:
        # If the model ever returns non-JSON, wrap it in a simple structure
        fallback = {
            "module_id": "raw_ai_output",
            "source_filename": filename,
            "error": "Model did not return valid JSON. Raw content preserved.",
            "raw_content": raw_content,
        }
        return json.dumps(fallback, ensure_ascii=False, indent=2)


# --------------------------
# MAIN
# --------------------------

def main():
    print("Scanning raw input files...\n")

    if not RAW_DIR.exists():
        print(f"No raw directory found at: {RAW_DIR}")
        return

    any_files = False

    for file in RAW_DIR.rglob("*"):
        if not file.is_file():
            continue

        any_files = True
        print(f"Processing: {file}")

        content = extract_content(file)
        json_output = ai_convert_to_knowledge(content, file.name)

        out_name = file.stem.lower().replace(" ", "_") + ".json"
        out_file = OUT_DIR / out_name

        with out_file.open("w", encoding="utf-8") as f:
            f.write(json_output)

        print(f" → Written knowledge file: {out_file}\n")

    if not any_files:
        print(f"No files found under {RAW_DIR}, nothing to do.")


if __name__ == "__main__":
    main()
