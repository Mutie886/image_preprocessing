import streamlit as st
import pandas as pd

st.set_page_config(page_title="Football Results CSV", page_icon="⚽", layout="centered")
st.title("⚽ Paste Football Results to CSV")

st.markdown("""
Paste your match data below using this 4-line pattern, repeated for each match:

""")

# Input area
raw_input = st.text_area(
    "Paste your match data here",
    height=300,
    placeholder="Home Team\nHome Score\nAway Score\nAway Team\n..."
)

# Options
col1, col2 = st.columns(2)
with col1:
    strict_numeric = st.checkbox(
        "Require numeric scores",
        value=True,
        help="Skip rows with non-numeric scores if enabled."
    )
with col2:
    include_incomplete = st.checkbox(
        "Include incomplete rows",
        value=False,
        help="Keep rows missing scores or teams with blanks."
    )

# Parse button
parse_clicked = st.button("Parse to table")

def parse_matches(text: str, strict: bool, keep_incomplete: bool):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    matches = []
    errors = []
    for i in range(0, len(lines), 4):
        chunk = lines[i:i+4]
        if len(chunk) < 4:
            if keep_incomplete:
                while len(chunk) < 4:
                    chunk.append("")
                home_team, home_score_raw, away_score_raw, away_team = chunk
                home_score = home_score_raw if home_score_raw.isdigit() else ""
                away_score = away_score_raw if away_score_raw.isdigit() else ""
                matches.append([home_team, home_score, away_score, away_team])
            else:
                errors.append(f"Incomplete group at lines {i+1}-{i+len(chunk)}: expected 4 lines, got {len(chunk)}")
            continue

        home_team, home_score_raw, away_score_raw, away_team = chunk

        hs_is_num = home_score_raw.isdigit()
        as_is_num = away_score_raw.isdigit()

        if strict and not (hs_is_num and as_is_num):
            errors.append(f"Non-numeric score at lines {i+2}-{i+3}: '{home_score_raw}' / '{away_score_raw}'")
            if keep_incomplete:
                matches.append([home_team, "", "", away_team])
            continue

        home_score = int(home_score_raw) if hs_is_num else (home_score_raw if not strict else "")
        away_score = int(away_score_raw) if as_is_num else (away_score_raw if not strict else "")

        matches.append([home_team, home_score, away_score, away_team])

    return matches, errors

if parse_clicked:
    if not raw_input.strip():
        st.warning("Please paste your match data first.")
    else:
        matches, errors = parse_matches(raw_input, strict=strict_numeric, keep_incomplete=include_incomplete)

        if errors:
            with st.expander("Parsing notes"):
                for e in errors:
                    st.write(f"- {e}")

        if matches:
            df = pd.DataFrame(matches, columns=["Home Team", "Home Score", "Away Score", "Away Team"])
            st.subheader("📊 Parsed match results")
            st.dataframe(df, use_container_width=True)

            csv_data = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name="football_results.csv",
                mime="text/csv"
            )

            st.success(f"Parsed {len(df)} matches.")
        else:
            st.warning("No complete matches found. Ensure your data follows the 4-line pattern for each match.")

