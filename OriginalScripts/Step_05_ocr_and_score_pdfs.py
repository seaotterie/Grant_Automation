
import os
import pandas as pd
import json
from pdf2image import convert_from_path
import pytesseract
from tqdm import tqdm

INPUT_CSV = "/data/output/scored_nonprofits.csv"
PDF_DIR = "/data/output/pdfs"
OCR_DIR = "/data/output/ocr"
PROGRESS_JSON = "/data/output/ocr_progress.json"

os.makedirs(OCR_DIR, exist_ok=True)

try:
    df = pd.read_csv(INPUT_CSV)
    df = df[df["COMPOSITE_SCORE"] >= 0.70].head(1)  # limit to first 1 EINs
except Exception as e:
    with open(PROGRESS_JSON, "w") as f:
        json.dump({"status": "error", "message": str(e)}, f)
    exit(1)

progress = {
    "status": "running",
    "processed_eins": 0,
    "total_eins": len(df),  # ← dynamic value now
    "current_ein": None,
    "current_page": 0,
    "total_pages": 0,
    "errors": []
}

with open(PROGRESS_JSON, "w") as f:
    json.dump(progress, f)

for idx, row in tqdm(df.iterrows(), total=len(df), desc="OCR Progress"):
    ein = str(row["EIN"]).zfill(9)
    pdf_path = os.path.join(PDF_DIR, f"{ein}.pdf")
    txt_path = os.path.join(OCR_DIR, f"{ein}.txt")

    progress["current_ein"] = ein
    progress["current_page"] = 0
    progress["total_pages"] = 0

    if not os.path.exists(pdf_path):
        progress["errors"].append(f"PDF not found: {ein}")
        with open(PROGRESS_JSON, "w") as f:
            json.dump(progress, f)
        continue

    try:
        images = convert_from_path(pdf_path, dpi=300)
        progress["total_pages"] = len(images)
        text = ""
        for i, img in enumerate(images, start=1):
            text += pytesseract.image_to_string(img)
            progress["current_page"] = i
            with open(PROGRESS_JSON, "w") as f:
                json.dump(progress, f)

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)

        progress["processed_eins"] += 1

    except Exception as e:
        progress["errors"].append(f"Error processing {ein}: {str(e)}")

    with open(PROGRESS_JSON, "w") as f:
        json.dump(progress, f)

progress["status"] = "complete"
with open(PROGRESS_JSON, "w") as f:
    json.dump(progress, f)
