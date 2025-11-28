import streamlit as st
import easyocr
import pandas as pd
import re

st.title("⚽ Football Results OCR to CSV")

# Upload screenshot
uploaded_file = st.file_uploader("Upload a screenshot", type=["png", "jpg", "jpeg"])

if uploaded_file:
    # Step 1: OCR with EasyOCR
    reader = easyocr.Reader(['en'])
    results = reader.readtext(uploaded_file.read())

    # Step 2: Extract text lines
    lines = [res[1] for res in results]

    # Step 3: Parse matches
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

    # Step 4: Display and export
    if matches:
        df = pd.DataFrame(matches, columns=["Home Team", "Home Score", "Away Score", "Away Team"])
        st.subheader("📊 Extracted Results")
        st.dataframe(df)

        # Download button
        st.download_button(
            label="Download CSV",
            data=df.to_csv(index=False),
            file_name="football_results.csv",
            mime="text/csv"
        )
    else:
        st.warning("No matches detected. Try a clearer screenshot.")
#streamlit run oddbet.py