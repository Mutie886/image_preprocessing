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
    reader = easyocr.Reader(['en'])
    results = reader.readtext(processed_img)

    # Step 3: Extract text fragments
    lines = [res[1] for res in results]

    # Debug: show raw OCR output
    st.subheader("🔍 Raw OCR Output")
    st.write(lines)

    # Step 4: Reconstruct matches from 3-line chunks
    matches = []
    i = 0
    while i < len(lines) - 2:
        team1 = lines[i].strip()
        score_line = lines[i + 1].strip()
        team2 = lines[i + 2].strip()

        score_match = re.match(r"(\d+)\s*[-–—]\s*(\d+)", score_line)
        if score_match:
            home_score = int(score_match.group(1))
            away_score = int(score_match.group(2))
            matches.append([team1, home_score, away_score, team2])
            i += 3
        else:
            i += 1  # Skip forward if no score found

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
