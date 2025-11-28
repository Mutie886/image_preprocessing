import streamlit as st
import easyocr
import pandas as pd
import re
import numpy as np
from PIL import Image
import cv2
from math import isfinite

st.title("⚽ Football Results OCR to CSV")

# --- Controls ---
uploaded_file = st.file_uploader("Upload a screenshot", type=["png", "jpg", "jpeg"])
use_preprocessing = st.checkbox("Apply preprocessing (grayscale + threshold + resize)", value=True)
threshold_value = st.slider("Threshold value", 120, 230, 180, help="Try 150–200 if digits are faint")
resize_factor = st.slider("Resize factor", 1.0, 3.0, 2.0, 0.1, help="Upscale to make thin digits more legible")
conf_min = st.slider("Min OCR confidence", 0.0, 1.0, 0.35, 0.05, help="Filter out low-confidence noise")
show_debug = st.checkbox("Show debug detections", value=False)

# --- Helpers ---
def preprocess(img: np.ndarray, threshold: int, scale: float) -> np.ndarray:
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    # Upscale to help digit recognition
    if scale != 1.0:
        h, w = gray.shape
        gray = cv2.resize(gray, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)
    # Adaptive cleanup: slight blur + binary threshold
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    _, th = cv2.threshold(blur, threshold, 255, cv2.THRESH_BINARY)
    # Light morphological closing to strengthen thin strokes
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, kernel, iterations=1)
    return th

def bbox_center_y(bbox):
    # bbox is 4 points: [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
    ys = [p[1] for p in bbox]
    return float(sum(ys) / len(ys))

def bbox_center_x(bbox):
    xs = [p[0] for p in bbox]
    return float(sum(xs) / len(xs))

def clean_score_text(s: str) -> str:
    # Normalize dashes and common misreads
    t = s.replace("—", "-").replace("–", "-")
    t = t.upper()
    # Replace common OCR confusions
    t = t.replace("O", "0").replace("S", "5")
    # Remove spaces around dash
    t = re.sub(r"\s*-\s*", "-", t)
    # Keep only digits and one dash
    t = re.sub(r"[^0-9-]", "", t)
    return t

def extract_score(s: str):
    s = clean_score_text(s)
    m = re.match(r"^(\d{1,3})-(\d{1,3})$", s)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None

def is_team_text(t: str) -> bool:
    # Accept letters, spaces, common abbreviations
    return bool(re.match(r"^[A-Za-z][A-Za-z &'.\-]*$", t.strip()))

def group_rows(detections, y_tol=18.0):
    """
    Cluster detections into rows based on Y centers.
    y_tol is delta in pixels; tune if rows merge/split.
    """
    dets = []
    for bbox, text, conf in detections:
        yc = bbox_center_y(bbox)
        xc = bbox_center_x(bbox)
        dets.append({"bbox": bbox, "y": yc, "x": xc, "text": text, "conf": conf})

    # Sort top-to-bottom
    dets.sort(key=lambda d: d["y"])
    rows = []
    for d in dets:
        placed = False
        for row in rows:
            # compare with row mean y
            row_y = np.mean([e["y"] for e in row])
            if abs(d["y"] - row_y) <= y_tol:
                row.append(d)
                placed = True
                break
        if not placed:
            rows.append([d])

    # Sort each row left-to-right
    for row in rows:
        row.sort(key=lambda e: e["x"])
    return rows

def parse_rows(rows):
    """
    For each row, try to find left team, centered score, right team
    If no centered score, fall back to pairing teams line-by-line (two per row).
    """
    matches = []
    for row in rows:
        # Filter by confidence
        row_keep = [e for e in row if e["conf"] is None or e["conf"] >= conf_min]
        if not row_keep:
            continue

        # Find score candidates and team candidates
        score_cands = []
        team_cands = []
        for e in row_keep:
            s = e["text"].strip()
            score = extract_score(s)
            if score:
                score_cands.append({"e": e, "score": score})
            elif is_team_text(s):
                team_cands.append(e)

        # Ideal case: left team, score, right team
        if score_cands and len(team_cands) >= 2:
            # Choose the score closest to row center
            row_center_x = np.mean([e["x"] for e in row_keep])
            score_cands.sort(key=lambda c: abs(c["e"]["x"] - row_center_x))
            sc = score_cands[0]["score"]

            # Left team = closest left of score; Right team = closest right of score
            score_x = score_cands[0]["e"]["x"]
            lefts = [e for e in team_cands if e["x"] <= score_x]
            rights = [e for e in team_cands if e["x"] >= score_x]
            if lefts and rights:
                lefts.sort(key=lambda e: abs(e["x"] - score_x))
                rights.sort(key=lambda e: abs(e["x"] - score_x))
                team1 = lefts[-1]["text"].strip() if lefts else team_cands[0]["text"].strip()
                team2 = rights[0]["text"].strip() if rights else team_cands[-1]["text"].strip()
                matches.append([team1, sc[0], sc[1], team2])
                continue

        # Fallback: two teams in the row, no score found
        if len(team_cands) >= 2:
            t1 = team_cands[0]["text"].strip()
            t2 = team_cands[1]["text"].strip()
            # Unknown score; skip or set None
            matches.append([t1, None, None, t2])

    return matches

if uploaded_file:
    # Load image
    image = Image.open(uploaded_file).convert("RGB")
    img_np = np.array(image)

    # Preprocess
    if use_preprocessing:
        processed = preprocess(img_np, threshold_value, resize_factor)
    else:
        processed = img_np

    # Reader
    reader = easyocr.Reader(['en'], gpu=False)

    # General detections (text)
    results_text = reader.readtext(processed, detail=1, paragraph=False)
    # Digit-focused detections for scores: run separately and merge
    results_digits = reader.readtext(processed, detail=1, paragraph=False, allowlist="0123456789-–—")

    # Merge detections: keep highest confidence per bbox proximity
    # Simple concat is often sufficient; we rely on row grouping and confidence filters
    detections = []
    for r in results_text:
        bbox, text, conf = r
        detections.append((bbox, text, conf))
    for r in results_digits:
        bbox, text, conf = r
        detections.append((bbox, text, conf))

    # Debug output
    if show_debug:
        st.subheader("🔍 Raw detections (text, conf)")
        dbg = [{"text": r[1], "conf": float(r[2]) if r[2] is not None and isfinite(r[2]) else None} for r in detections]
        st.write(dbg)

    # Group into rows by Y position
    rows = group_rows(detections, y_tol=18.0)

    # Parse rows into matches
    matches = parse_rows(rows)

    # Clean and finalize: drop rows with missing scores if you prefer strict output
    # Here we keep all rows and try a second pass to fill missing scores from score-only detections per row
    finalized = []
    for m in matches:
        t1, hs, as_, t2 = m
        # If missing scores, try to infer from any numeric-only detection on the same row
        if hs is None or as_ is None:
            finalized.append([t1, "", "", t2])
        else:
            finalized.append([t1, hs, as_, t2])

    # Show table
    if finalized:
        df = pd.DataFrame(finalized, columns=["Home Team", "Home Score", "Away Score", "Away Team"])
        st.subheader("📊 Extracted results")
        st.dataframe(df, use_container_width=True)

        st.download_button(
            label="Download CSV",
            data=df.to_csv(index=False),
            file_name="football_results.csv",
            mime="text/csv"
        )
    else:
        st.warning("No matches detected. Try adjusting threshold or resize, and ensure the screenshot has clear digits.")
