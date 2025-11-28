import streamlit as st
import easyocr
import pandas as pd
import re
from PIL import Image

st.title("⚽ Football Results OCR to CSV")

uploaded_file = st.file_uploader("Upload a screenshot", type=["png", "jpg", "jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    reader = easyocr.Reader(['en'])
    results = reader.readtext(np.array(image))

    lines = [res[1] for res in results]
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

    if matches:
        df = pd.DataFrame(matches, columns=["Home Team", "Home Score", "Away Score", "Away Team"])
        st.dataframe(df)
        st.download_button("Download CSV", df.to_csv(index=False), "football_results.csv")
    else:
        st.warning("No matches detected. Try a clearer screenshot.")
