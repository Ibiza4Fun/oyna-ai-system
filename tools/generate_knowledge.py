import os
import json
import base64
from pathlib import Path
from pypdf import PdfReader
import docx
from openai import OpenAI

# ============================================================
# CONFIG
# ============================================================

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

RAW_DIR = Path("ai-input/raw")
PROCESSED_DIR = Path("ai-input/processed")
OUT_DIR = Path("knowledge")

PROCESSED_DIR.mkdir(exist_ok=True)
OUT_DIR.mkdir(exist_ok=True)


# ============================================================
# TEXT EXTRACTION
# ============================================================

def extract_text_pdf(path: Path):
    text = ""
    try:
        reader = PdfReader(str(path))
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception as e:
        text += f"[PDF extraction error: {e}]"
    return text


def extract_text_docx(path: Path):
    try:
        doc = docx.Document(str(path))
        return "\n".join([p.text for p in doc.paragraphs])
    except Exception as e:
        return f"[DOCX extraction error: {e}]"


def extract_text_generic(path: Path):
    try:
        return path.read_text(errors="ignore")
    except Exception as e:
        return f"[TEXT extraction error: {e}]"


def extract_image_base64(path: Path):
    try:
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        mime = "image/jpeg" if path.suffix.lower() in [".jpg", ".jpeg"] else "image/png"
        return f"data:{mime};base64,{b64}"
    except Exception as e:
        return f"[IMAGE extraction error: {e}]"


def extract_content(path: Path):
    s = path.suffix.lower()

    if s in [".png", ".jpg", ".jpeg"]:
        return {"type": "image", "data": extract_image_base64(path)}

    if s == ".pdf":
        return {"type": "text", "data": extract_text_pdf(path)}

    if s == ".docx":
        return {"type": "text", "data": extract_text_docx(path)}

    if s in [".txt", ".md"]:
        return {"type": "text", "data": extract_text_generic(path)}

    return {"type": "text", "data": f"[UNSUPPORTED FILE TYPE: {path.name}]"}


# ============================================================
# CLEAN AND VALIDATE JSON
# ============================================================

def clean_json_output(raw_text: str):
    """Remove ``` fences and validate JSON."""
    text = raw_text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    if text.endswith("```"):
        text = text[:-3].strip()

    try:
        parsed = json.loads(text)
        return json.dumps(parsed, indent=2, ensure_ascii=False)
    except json.JSONDecodeError:
        return None


# ============================================================
# AI CONVERSION
# ============================================================

def ai_convert_to_knowledge(content, filename):
    system_prompt = """
You are ØynaWaterworksDocAI.
Convert documents and images into structured JSON.
Rules:
- Output pure JSON only.
- No markdown.
- No code blocks.
- No commentary.
"""

    if content["type"] == "image":
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": content["data"]}},
                    {"type": "text", "text": f"Filename: {filename}\nConvert image to structured JSON."}
                ]
            }
        ]
    else:
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text",
                     "text": f"Filename: {filename}\nDocument:\n{content['data']}\nConvert to structured JSON."}
                ]
            }
        ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0
    )

    raw = response.choices[0].message.content
    cleaned = clean_json_output(raw)

    if cleaned is None:
        return json.dumps({
            "module_id": "raw_ai_output",
            "source_filename": filename,
            "error": "Model returned invalid JSON.",
            "raw_content": raw
        }, indent=2, ensure_ascii=False)

    return cleaned


# ============================================================
# SAFE MOVE
# ============================================================

def move_with_overwrite(src: Path, dst: Path):
    if dst.exists():
        dst.unlink()  # ensure overwrite
    src.rename(dst)


# ============================================================
# MAIN
# ============================================================

def main():
    print("Scanning ai-input/raw ...\n")

    paths = [p for p in RAW_DIR.rglob("*") if p.is_file()]

    if not paths:
        print("No files found.")
        return

    for file in paths:
        print(f"Processing: {file}")

        content = extract_content(file)
        json_output = ai_convert_to_knowledge(content, file.name)

        out_name = file.stem.lower().replace(" ", "_") + ".json"
        out_file = OUT_DIR / out_name

        with out_file.open("w", encoding="utf-8") as f:
            f.write(json_output)

        print(f" → Wrote knowledge: {out_file}")

        destination = PROCESSED_DIR / file.name
        move_with_overwrite(file, destination)

        print(f" → Moved to: {destination}\n")


if __name__ == "__main__":
    main()
