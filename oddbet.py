import streamlit as st
import pandas as pd

# Allowed team names (case-sensitive)
VALID_TEAMS = {
    "Leeds", "Aston V", "Manchester Blue", "Liverpool", "London Blues", "Everton",
    "Brighton", "Sheffield U", "Tottenham", "Palace", "Newcastle", "West Ham",
    "Leicester", "West Brom", "Burnley", "London Reds", "Southampton", "Wolves",
    "Fulham", "Manchester Reds"
}

# Page setup
st.set_page_config(page_title="Football Results CSV", page_icon="⚽", layout="centered")
st.title("⚽ Paste Football Results to CSV")

st.markdown("""
Paste your match data below using this 4-line pattern, repeated for each match:


Only matches between these teams are accepted:
""" + ", ".join(sorted(VALID_TEAMS)))

# Initialize persistent match list and counters
if "match_data" not in st.session_state:
    st.session_state.match_data = []
if "home_counters" not in st.session_state:
    st.session_state.home_counters = {team: 0 for team in VALID_TEAMS}
if "away_counters" not in st.session_state:
    st.session_state.away_counters = {team: 0 for team in VALID_TEAMS}

# Input area
raw_input = st.text_area(
    "Paste your match data here",
    height=300,
    placeholder="Home Team\nHome Score\nAway Score\nAway Team\n..."
)

# Parse button
parse_clicked = st.button("Parse and Add")

def parse_matches(text: str):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    matches = []
    errors = []
    for i in range(0, len(lines), 4):
        chunk = lines[i:i+4]
        if len(chunk) < 4:
            errors.append(f"Incomplete group at lines {i+1}-{i+len(chunk)}: expected 4 lines, got {len(chunk)}")
            continue

        home_team, home_score_raw, away_score_raw, away_team = chunk

        # Validate team names
        if home_team not in VALID_TEAMS:
            errors.append(f"Invalid home team at line {i+1}: '{home_team}' not in allowed list")
        if away_team not in VALID_TEAMS:
            errors.append(f"Invalid away team at line {i+4}: '{away_team}' not in allowed list")

        # Validate scores
        if not home_score_raw.isdigit() or not away_score_raw.isdigit():
            errors.append(f"Non-numeric score at lines {i+2}-{i+3}: '{home_score_raw}' / '{away_score_raw}'")

        if errors:
            continue

        home_score = int(home_score_raw)
        away_score = int(away_score_raw)
        matches.append([home_team, home_score, away_score, away_team])

    return matches, errors

if parse_clicked:
    if not raw_input.strip():
        st.warning("Please paste your match data first.")
    else:
        new_matches, errors = parse_matches(raw_input)

        if errors:
            st.error("❌ Input errors detected. No new data added.")
            with st.expander("Details"):
                for e in errors:
                    st.write(f"- {e}")
        elif new_matches:
            # Update counters and add matches
            for home_team, home_score, away_score, away_team in new_matches:
                total_g = home_score + away_score

                if total_g == 4:
                    # Reset counters for both teams
                    st.session_state.home_counters[home_team] = 0
                    st.session_state.away_counters[away_team] = 0
                else:
                    if total_g < 4:
                        st.session_state.home_counters[home_team] += 1
                        st.session_state.away_counters[away_team] += 1

                # Append match with computed values
                st.session_state.match_data.append([
                    home_team,
                    home_score,
                    away_score,
                    away_team,
                    "Won" if total_g == 4 else total_g,
                    st.session_state.home_counters[home_team],
                    st.session_state.away_counters[away_team]
                ])

            st.success(f"✅ Added {len(new_matches)} new matches.")

# Display full table
if st.session_state.match_data:
    df = pd.DataFrame(
        st.session_state.match_data,
        columns=["Home Team", "Home Score", "Away Score", "Away Team", "Total-G", "F<4H", "F<4A"]
    )

    st.subheader("📊 Latest 9 Match Results")
    st.dataframe(df.tail(9), use_container_width=True)

    csv_data = df.to_csv(index=False)
    st.download_button(
        label="Download Full CSV",
        data=csv_data,
        file_name="football_results.csv",
        mime="text/csv"
    )

    if st.button("Clear all data"):
        st.session_state.match_data = []
        st.session_state.home_counters = {team: 0 for team in VALID_TEAMS}
        st.session_state.away_counters = {team: 0 for team in VALID_TEAMS}
        st.experimental_rerun()
else:
    st.info("Paste match data to begin building your CSV.")
