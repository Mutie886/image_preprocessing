import streamlit as st
import easyocr
import pandas as pd
import numpy as np
import re
from PIL import Image
import cv2

st.set_page_config(page_title="Football OCR CSV", page_icon="⚽", layout="centered")
st.title("⚽ Upload Multiple Screenshots to Build CSV")

# Initialize session state
if "matches" not in st.session_state:
    st.session_state.matches = []

# Upload multiple screenshots
uploaded_files = st.file_uploader("Upload one or more screenshots", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

# Preprocessing toggle
use_preprocessing = st.checkbox("Apply preprocessing (grayscale + threshold)", value=True)
threshold_value = st.slider("Threshold value", 120, 230, 180)

def preprocess_image(image, threshold):
    img_array = np.array(image.convert("RGB"))
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    _, th = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
    return th

def extract_matches(image_np):
    reader = easyocr.Reader(['en'], gpu=False)
    results = reader.readtext(image_np)

    lines = [res[1].strip() for res in results]
    matches = []

    for i in range(0, len(lines) - 2):
        team1 = lines[i]
        score_line = lines[i + 1]
        team2 = lines[i + 2]

        score_match = re.match(r"(\d+)\s*[-–—]\s*(\d+)", score_line)
        if score_match:
            home_score = int(score_match.group(1))
            away_score = int(score_match.group(2))
            matches.append([team1, home_score, away_score, team2])

    return matches

# Process uploaded files
if uploaded_files:
    new_matches = []
    for file in uploaded_files:
        image = Image.open(file)
        processed = preprocess_image(image, threshold_value) if use_preprocessing else np.array(image.convert("RGB"))
        extracted = extract_matches(processed)
        new_matches.extend(extracted)

    if new_matches:
        st.session_state.matches.extend(new_matches)
        st.success(f"Added {len(new_matches)} matches from {len(uploaded_files)} image(s).")

# Display full table
if st.session_state.matches:
    df = pd.DataFrame(st.session_state.matches, columns=["Home Team", "Home Score", "Away Score", "Away Team"])
    st.subheader("📊 Combined Match Results")
    st.dataframe(df, use_container_width=True)

    st.download_button(
        label="Download Full CSV",
        data=df.to_csv(index=False),
        file_name="football_results.csv",
        mime="text/csv"
    )

    if st.button("Clear all data"):
        st.session_state.matches = []
        st.experimental_rerun()
else:
    st.info("Upload screenshots to start building your match table.")
