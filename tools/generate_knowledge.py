import os
import json
import base64
from pathlib import Path
from pypdf import PdfReader
import docx
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

RAW_DIR = Path("ai-input/raw")
OUT_DIR = Path("knowledge")
OUT_DIR.mkdir(exist_ok=True)

# --------------------------
# Extract TEXT from documents
# --------------------------

def extract_text_pdf(path):
    reader = PdfReader(str(path))
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

def extract_text_docx(path):
    doc = docx.Document(str(path))
    return "\n".join([p.text for p in doc.paragraphs])

def extract_text_generic(path):
    try:
        return path.read_text(errors="ignore")
    except:
        return ""

def extract_text(path: Path):
    if path.suffix.lower() == ".pdf":
        return extract_text_pdf(path)
    if path.suffix.lower() == ".docx":
        return extract_text_docx(path)
    if path.suffix.lower() in [".txt", ".md"]:
        return extract_text_generic(path)
    # For images/unsupported types: use placeholder
    return f"[UNSUPPORTED FILE TYPE: {path.name}]"

# --------------------------
# AI CONVERSION
# --------------------------

def ai_convert_to_knowledge(text, filename):
    prompt = f"""
You are ØynaWaterworksDocAI.

Your task:
- Convert the following document into a structured Øyna AI knowledge module.
- Use clear, factual, engineering-oriented descriptions.
- Output STRICT JSON ONLY, no explanation.

Document filename: {filename}

Document content:
{text}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You convert engineering documents into structured JSON knowledge modules."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    # FIXED: Use .content instead of ["content"]
    return response.choices[0].message.content

# --------------------------
# MAIN
# --------------------------

def main():
    print("Scanning raw input files...\n")

    for file in RAW_DIR.rglob("*"):
        if not file.is_file():
            continue

        print(f"Processing: {file}")

        text = extract_text(file)
        json_output = ai_convert_to_knowledge(text, file.name)

        out_name = file.stem.lower().replace(" ", "_") + ".json"
        out_file = OUT_DIR / out_name

        with out_file.open("w", encoding="utf-8") as f:
            f.write(json_output)

        print(f" → Written knowledge file: {out_file}\n")

if __name__ == "__main__":
    main()
