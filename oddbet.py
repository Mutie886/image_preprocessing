import streamlit as st
import pandas as pd
import re

# Allowed team names (case-sensitive)
VALID_TEAMS = {
    "Leeds", "Aston V", "Manchester Blue", "Liverpool", "London Blues", "Everton",
    "Brighton", "Sheffield U", "Tottenham", "Palace", "Newcastle", "West Ham",
    "Leicester", "West Brom", "Burnley", "London Reds", "Southampton", "Wolves",
    "Fulham", "Manchester Reds"
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
if "clear_text" not in st.session_state:
    st.session_state.clear_text = False

# Two equal columns
col1, col2 = st.columns([1, 1])

with col1:
    # Check if we need to clear the text area
    if st.session_state.clear_text:
        default_text = ""
        st.session_state.clear_text = False
    else:
        default_text = ""
    
    raw_input = st.text_area("Paste match data (with dates/times - will be cleaned automatically)", 
                            height=200,
                            value=default_text,
                            key="match_input",
                            placeholder="Paste your messy data here, e.g.:\nAston V\n1\n2\nSheffield U\nEnglish League WEEK 17 - #2025122312\n3:58 pm\nSouthampton\n2\n0\nEverton\n...")
    
    parse_clicked = st.button("Parse and Add")

def clean_and_parse_matches(text: str):
    """
    Clean messy input data and parse matches
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    
    # Filter out unwanted lines
    cleaned_lines = []
    for line in lines:
        # Skip lines that match unwanted patterns
        skip_patterns = [
            r'WEEK \d+',  # WEEK 17, WEEK 18, etc.
            r'English League',
            r'\d{1,2}:\d{2}\s*(?:am|pm)',  # 3:58 pm, 2:30 am, etc.
            r'#\d+',  # #2025122312
            r'^\d{8,}$',  # Just numbers like 20251223
        ]
        
        # Check if line contains any team name (case-sensitive)
        is_team = line in VALID_TEAMS
        
        # Check if line is just digits (score)
        is_score = line.isdigit() and 0 <= int(line) <= 20  # Reasonable score range
        
        # Keep only team names and scores
        if is_team or is_score:
            cleaned_lines.append(line)
        else:
            # Check if it matches any skip pattern
            skip = False
            for pattern in skip_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    skip = True
                    break
            if not skip:
                # Could be a team name with extra text, try to extract
                for team in VALID_TEAMS:
                    if team in line:
                        cleaned_lines.append(team)
                        break
    
    # Now parse matches from cleaned lines
    matches, errors = [], []
    i = 0
    while i < len(cleaned_lines):
        # We need 4 consecutive items: team, score, score, team
        if i + 3 >= len(cleaned_lines):
            errors.append(f"Incomplete match at position {i+1}, need 4 items but got {len(cleaned_lines)-i}")
            break
            
        home_team = cleaned_lines[i]
        home_score_raw = cleaned_lines[i+1]
        away_score_raw = cleaned_lines[i+2]
        away_team = cleaned_lines[i+3]
        
        # Validate
        if home_team not in VALID_TEAMS:
            errors.append(f"Invalid home team at position {i+1}: {home_team}")
        if away_team not in VALID_TEAMS:
            errors.append(f"Invalid away team at position {i+4}: {away_team}")
        if not home_score_raw.isdigit():
            errors.append(f"Non-numeric home score at position {i+2}: {home_score_raw}")
        if not away_score_raw.isdigit():
            errors.append(f"Non-numeric away score at position {i+3}: {away_score_raw}")
        
        if errors and len(errors) > 5:  # Limit error messages
            errors.append("... more errors")
            break
            
        if home_team in VALID_TEAMS and away_team in VALID_TEAMS and home_score_raw.isdigit() and away_score_raw.isdigit():
            matches.append([home_team, int(home_score_raw), int(away_score_raw), away_team])
        
        i += 4
    
    # Reverse order so bottom match is processed first
    matches.reverse()
    
    return matches, errors, cleaned_lines

if parse_clicked and raw_input.strip():
    new_matches, errors, cleaned_lines = clean_and_parse_matches(raw_input)
    
    if errors:
        st.error(f"❌ Found {len(errors)} parsing errors:")
        with st.expander("Error Details"):
            for e in errors[:10]:  # Show first 10 errors
                st.write(f"- {e}")
        if new_matches:
            st.warning(f"But found {len(new_matches)} valid matches. Adding them...")
    else:
        st.success(f"✅ Successfully parsed {len(new_matches)} matches from cleaned data.")
    
    # Process the matches
    for home_team, home_score, away_score, away_team in new_matches:
        total_g_value = home_score + away_score
        if total_g_value == 4:
            total_g_display = "Won"
        elif total_g_value == 3:
            total_g_display = "3 ✔"
        else:
            total_g_display = total_g_value

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
    
    if new_matches:
        st.success(f"✅ Added {len(new_matches)} new matches to dashboard.")
    
    # Set flag to clear text area after processing
    st.session_state.clear_text = True
    # Use try-except to handle different Streamlit versions
    try:
        st.rerun()  # For newer Streamlit versions
    except:
        st.experimental_rerun()  # For older Streamlit versions

# Display summary in right column (same as before)
if st.session_state.match_data:
    df = pd.DataFrame(st.session_state.match_data,
                     columns=["Home Team", "Home Score", "Away Score", "Away Team", "Total-G", "F<4H", "F<4A", "F!=4HA", "Status3"])

    with col2:
        st.subheader("📌 Last 10 Match Summary")

        # Styled summary frame
        st.markdown("""
            <div style="background-color:black; color:white; padding:15px; border-radius:10px; border:2px solid #444;">
        """, unsafe_allow_html=True)

        for row in df.tail(10).itertuples(index=False):
            home, away = row[0], row[3]
            f_ha_home = int(row[7].split(":")[1].split("|")[0].strip())
            f_ha_away = int(row[7].split(":")[2].strip())
            status3_home = int(row[8].split(":")[1].split("|")[0].strip())
            status3_away = int(row[8].split(":")[2].strip())
            left = f"{home}, [{status3_home} : {f_ha_home}]"
            right = f"{away}, [{status3_away} : {f_ha_away}]"
            st.markdown(f"<div style='font-size:14px; margin-bottom:5px;'>{left} — {right}</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # Button styling with hover effects
        st.markdown("""
            <style>
            div[data-testid="stDownloadButton"] > button {
                background-color: #4CAF50 !important; /* Green */
                color: white !important;
                border-radius: 8px !important;
                margin-top: 10px !important;
                width: 100% !important;
                transition: 0.3s;
            }
            div[data-testid="stDownloadButton"] > button:hover {
                background-color: #45a049 !important;
            }
            div[data-testid="stButton"] > button {
                background-color: #f44336 !important; /* Red */
                color: white !important;
                border-radius: 8px !important;
                margin-top: 10px !important;
                width: 100% !important;
                transition: 0.3s;
            }
            div[data-testid="stButton"] > button:hover {
                background-color: #da190b !important;
            }
            </style>
        """, unsafe_allow_html=True)

        # Download button
        csv_data = df.to_csv(index=False)
        st.download_button("Download Full CSV", data=csv_data,
                          file_name="football_results.csv", mime="text/csv")

        # Clear button
        if st.button("Clear all data"):
            st.session_state.match_data = []
            st.session_state.home_counters = {team: 0 for team in VALID_TEAMS}
            st.session_state.away_counters = {team: 0 for team in VALID_TEAMS}
            st.session_state.ha_counters = {team: 0 for team in VALID_TEAMS}
            st.session_state.status3_counters = {team: 0 for team in VALID_TEAMS}
            # Use try-except to handle different Streamlit versions
            try:
                st.rerun()  # For newer Streamlit versions
            except:
                st.experimental_rerun()  # For older Streamlit versions
