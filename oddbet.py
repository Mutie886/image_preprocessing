import streamlit as st
import easyocr
import pandas as pd
import re
import numpy as np
from PIL import Image
import cv2

st.title("⚽ Football Results OCR to CSV")

# Upload screenshot
uploaded_file = st.file_uploader("Upload a screenshot", type=["png", "jpg", "jpeg"])

# Toggle for preprocessing
use_preprocessing = st.checkbox("Apply image preprocessing (contrast/thresholding)", value=True)

def preprocess_image(uploaded_file):
    """Convert uploaded image to grayscale + threshold for better OCR."""
    image = Image.open(uploaded_file).convert("RGB")
    img_array = np.array(image)
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)[1]
    return thresh

if uploaded_file:
    # Step 1: Preprocess if selected
    if use_preprocessing:
        processed_img = preprocess_image(uploaded_file)
    else:
        processed_img = np.array(Image.open(uploaded_file).convert("RGB"))

    # Step 2: OCR with EasyOCR
    reader = easyocr.Reader(['en'], gpu=False)

    # General OCR (team names + text)
    results_text = reader.readtext(processed_img)

    # Digit-only OCR (scores)
    results_digits = reader.readtext(processed_img, allowlist='0123456789-–—')

    # Step 3: Extract fragments
    team_lines = [res[1].strip() for res in results_text if re.match(r"^[A-Za-z ]+$", res[1].strip())]
    score_lines = [res[1].strip() for res in results_digits if re.match(r"^\d+\s*[-–—]\s*\d+$", res[1].strip())]

    # Debug: show raw OCR output
    st.subheader("🔍 Raw OCR Output")
    st.write("Teams:", team_lines)
    st.write("Scores:", score_lines)

    # Step 4: Pair teams with scores
    matches = []
    for i in range(0, len(team_lines), 2):
        if i//2 < len(score_lines):
            team1 = team_lines[i]
            team2 = team_lines[i+1] if i+1 < len(team_lines) else "Unknown"
            score_line = score_lines[i//2]
            home_score, away_score = map(int, re.findall(r"\d+", score_line))
            matches.append([team1, home_score, away_score, team2])

    # Step 5: Display and export
    if matches:
        df = pd.DataFrame(matches, columns=["Home Team", "Home Score", "Away Score", "Away Team"])
        st.subheader("📊 Extracted Results")
        st.dataframe(df)

        st.download_button(
            label="Download CSV",
            data=df.to_csv(index=False),
            file_name="football_results.csv",
            mime="text/csv"
        )
    else:
        st.warning("No matches detected. Try toggling preprocessing or check OCR output above.")
