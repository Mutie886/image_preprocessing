import streamlit as st
import easyocr
import pandas as pd
import re
import cv2
import numpy as np
from PIL import Image
import tempfile

st.title("⚽ Football Results OCR to CSV")

# Upload screenshot
uploaded_file = st.file_uploader("Upload a screenshot", type=["png", "jpg", "jpeg"])

def preprocess_image(uploaded_file):
    # Convert uploaded image to OpenCV format
    image = Image.open(uploaded_file).convert("RGB")
    img_array = np.array(image)
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)[1]
    return thresh

if uploaded_file:
    # Step 1: Preprocess image
    processed_img = preprocess_image(uploaded_file)

    # Step 2: OCR with EasyOCR
    reader = easyocr.Reader(['en'])
    results = reader.readtext(processed_img)

    # Step 3: Extract text lines
    lines = [res[1] for res in results]

    # Step 4: Parse matches
    matches = []
    for line in lines:
        match = re.match(r"(.+?)\s+(\d+)\s*[-–—]\s*(\d+)\s+(.+)", line)
        if match:
            matches.append([
                match.group(1).strip(),
                int(match.group(2)),
                int(match.group(3)),
                match.group(4).strip()
            ])

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
        st.warning("No matches detected. Try a clearer screenshot or adjust formatting.")
