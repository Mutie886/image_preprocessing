import streamlit as st
import pandas as pd

VALID_TEAMS = {
    "Leeds","Aston V","Manchester Blue","Liverpool","London Blues","Everton",
    "Brighton","Sheffield U","Tottenham","Palace","Newcastle","West Ham",
    "Leicester","West Brom","Burnley","London Reds","Southampton","Wolves",
    "Fulham","Manchester Reds"
}

st.set_page_config(page_title="Football Results CSV", page_icon="⚽", layout="wide")
st.title("⚽ Football Results Dashboard")

# Initialize session state
if "match_data" not in st.session_state:
    st.session_state.match_data = []
if "home_counters" not in st.session_state:
    st.session_state.home_counters = {team: 0 for team in VALID_TEAMS}
if "away_counters" not in st.session_state:
    st.session_state.away_counters = {team: 0 for team in VALID_TEAMS}
if "ha_counters" not in st.session_state:
    st.session_state.ha_counters = {team: 0 for team in VALID_TEAMS}
if "status3_counters" not in st.session_state:
    st.session_state.status3_counters = {team: 0 for team in VALID_TEAMS}

# Two equal columns
col1, col2 = st.columns([1,1])

with col1:
    raw_input = st.text_area("Paste match data", height=200,
                             placeholder="Home Team\nHome Score\nAway Score\nAway Team\n...")
    parse_clicked = st.button("Parse and Add")

def parse_matches(text: str):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    matches, errors = [], []
    for i in range(0, len(lines), 4):
        chunk = lines[i:i+4]
        if len(chunk) < 4:
            errors.append(f"Incomplete group at lines {i+1}-{i+len(chunk)}")
            continue
        home_team, home_score_raw, away_score_raw, away_team = chunk
        if home_team not in VALID_TEAMS: errors.append(f"Invalid home team: {home_team}")
        if away_team not in VALID_TEAMS: errors.append(f"Invalid away team: {away_team}")
        if not home_score_raw.isdigit() or not away_score_raw.isdigit():
            errors.append(f"Non-numeric score: {home_score_raw}/{away_score_raw}")
        if errors: continue
        matches.append([home_team,int(home_score_raw),int(away_score_raw),away_team])
    return matches, errors

if parse_clicked and raw_input.strip():
    new_matches, errors = parse_matches(raw_input)
    if errors:
        st.error("❌ Input errors detected. No new data added.")
        with st.expander("Details"):
            for e in errors: st.write(f"- {e}")
    else:
        for home_team, home_score, away_score, away_team in new_matches:
            total_g_value = home_score + away_score
            if total_g_value == 4: total_g_display = "Won"
            elif total_g_value == 3: total_g_display = "3 ✔"
            else: total_g_display = total_g_value

            if total_g_value == 4:
                st.session_state.home_counters[home_team] = 0
                st.session_state.away_counters[away_team] = 0
                st.session_state.ha_counters[home_team] = 0
                st.session_state.ha_counters[away_team] = 0
            else:
                st.session_state.home_counters[home_team] += 1
                st.session_state.away_counters[away_team] += 1
                st.session_state.ha_counters[home_team] += 1
                st.session_state.ha_counters[away_team] += 1

            if total_g_value == 3:
                st.session_state.status3_counters[home_team] = 0
                st.session_state.status3_counters[away_team] = 0
            else:
                st.session_state.status3_counters[home_team] += 1
                st.session_state.status3_counters[away_team] += 1

            f_ne_4_ha_str = f"{home_team}: {st.session_state.ha_counters[home_team]} | {away_team}: {st.session_state.ha_counters[away_team]}"
            status3_str = f"{home_team}: {st.session_state.status3_counters[home_team]} | {away_team}: {st.session_state.status3_counters[away_team]}"

            st.session_state.match_data.append([
                home_team, home_score, away_score, away_team,
                total_g_display,
                st.session_state.home_counters[home_team],
                st.session_state.away_counters[away_team],
                f_ne_4_ha_str, status3_str
            ])
        st.success(f"✅ Added {len(new_matches)} new matches.")

# Display summary in right column
if st.session_state.match_data:
    df = pd.DataFrame(st.session_state.match_data,
        columns=["Home Team","Home Score","Away Score","Away Team","Total-G","F<4H","F<4A","F!=4HA","Status3"])

    with col2:
        st.subheader("📌 Last 10 Match Summary")
        summary_box = st.container()
        with summary_box:
            for row in df.tail(10).itertuples(index=False):
                home, away = row[0], row[3]
                f_ha_home = int(row[7].split(":")[1].split("|")[0].strip())
                f_ha_away = int(row[7].split(":")[2].strip())
                status3_home = int(row[8].split(":")[1].split("|")[0].strip())
                status3_away = int(row[8].split(":")[2].strip())
                left = f"{home}, [{status3_home} : {f_ha_home}]"
                right = f"{away}, [{status3_away} : {f_ha_away}]"
                st.markdown(f"<div style='font-size:14px'>{left} — {right}</div>", unsafe_allow_html=True)

    # Buttons aligned bottom-left
    with col1:
        csv_data = df.to_csv(index=False)
        st.download_button("Download Full CSV", data=csv_data,
                           file_name="football_results.csv", mime="text/csv")
        if st.button("Clear all data"):
            st.session_state.match_data = []
            st.session_state.home_counters = {team: 0 for team in VALID_TEAMS}
            st.session_state.away_counters = {team: 0 for team in VALID_TEAMS}
            st.session_state.ha_counters = {team: 0 for team in VALID_TEAMS}
            st.session_state.status3_counters = {team: 0 for team in VALID_TEAMS}
            st.experimental_rerun()
