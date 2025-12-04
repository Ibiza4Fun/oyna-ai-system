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
    except:
        return ""


def extract_text_generic(path: Path):
    try:
        return path.read_text(errors="ignore")
    except:
        return ""


def extract_image_base64(path: Path):
    try:
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        mime = "image/jpeg" if path.suffix.lower() in [".jpg", ".jpeg"] else "image/png"
        return f"data:{mime};base64,{b64}"
    except:
        return None


def extract_content(path: Path):
    s = path.suffix.lower()

    # Image handling
    if s in [".png", ".jpg", ".jpeg"]:
        return {"type": "image", "data": extract_image_base64(path)}

    # PDF
    if s == ".pdf":
        return {"type": "text", "data": extract_text_pdf(path)}

    # DOCX
    if s == ".docx":
        return {"type": "text", "data": extract_text_docx(path)}

    # TXT / MD
    if s in [".txt", ".md"]:
        return {"type": "text", "data": extract_text_generic(path)}

    # Fallback
    return {"type": "text", "data": f"[UNSUPPORTED FILE TYPE: {path.name}]"}


# ============================================================
# CLEAN AND VALIDATE JSON
# ============================================================

def clean_json_output(raw_text: str):
    """
    Remove ```json fences and validate JSON.
    """
    text = raw_text.strip()

    # Remove leading ```json or ```
    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    # Remove trailing ```
    if text.endswith("```"):
        text = text[:-3].strip()

    # Try parse JSON
    try:
        parsed = json.loads(text)
        return json.dumps(parsed, indent=2, ensure_ascii=False)
    except json.JSONDecodeError:
        return None  # Invalid JSON


# ============================================================
# AI CONVERSION
# ============================================================

def ai_convert_to_knowledge(content, filename):
    """
    Uses OpenAI to convert document/image into structured JSON.
    Ensures AI outputs VALID JSON ONLY.
    """

    system_prompt = """
You are ØynaWaterworksDocAI.
You convert engineering documents, photos, diagrams, and PDF files
into structured JSON knowledge modules for an AI agent.

RULES:
- ALWAYS output pure JSON.
- NO markdown.
- NO code blocks.
- NO commentary.
- No backticks.
- No explanations.
"""

    # Select message content depending on type
    if content["type"] == "image":
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": content["data"]}
                    },
                    {
                        "type": "text",
                        "text": (
                            f"You are given an engineering-related image.\n"
                            f"Convert it into a structured knowledge module.\n"
                            f"Filename: {filename}\n"
                        )
                    }
                ]
            }
        ]
    else:
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            f"Filename: {filename}\n"
                            f"Document content:\n{content['data']}\n"
                            f"Convert this into a structured knowledge module."
                        )
                    }
                ]
            }
        ]

    # Call OpenAI
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0
    )

    raw = response.choices[0].message.content
    cleaned = clean_json_output(raw)

    if cleaned is None:
        # Return wrapper with raw output for debugging
        return json.dumps({
            "module_id": "raw_ai_output",
            "source_filename": filename,
            "error": "Model returned non-JSON content.",
            "raw_content": raw
        }, indent=2, ensure_ascii=False)

    return cleaned


# ============================================================
# MAIN
# ============================================================

def main():
    print("Scanning raw input files...\n")

    # If batch workflow provides a specific file, process only that
    single_file = os.getenv("RAW_SINGLE_FILE")

    if single_file:
        paths = [Path(single_file)]
    else:
        paths = [p for p in RAW_DIR.rglob("*") if p.is_file()]

    if not paths:
        print("No files to process.")
        return

    for file in paths:

        print(f"Processing: {file}")

        content = extract_content(file)
        json_output = ai_convert_to_knowledge(content, file.name)

        out_name = file.stem.lower().replace(" ", "_") + ".json"
        out_file = OUT_DIR / out_name

        with out_file.open("w", encoding="utf-8") as f:
            f.write(json_output)

        print(f" → Written knowledge file: {out_file}")

        # MOVE RAW FILE TO /processed/
        destination = PROCESSED_DIR / file.name
        file.rename(destination)

        print(f" → Moved raw file to: {destination}\n")

        # Process only 1 file unless batch workflow controls runs
        if not single_file:
            break


if __name__ == "__main__":
    main()
