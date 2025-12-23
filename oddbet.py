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
if "match_counter" not in st.session_state:
    st.session_state.match_counter = 1

# Two equal columns
col1, col2 = st.columns([1, 1])

with col1:
    raw_input = st.text_area("Paste match data (with dates/times - will be cleaned automatically)", 
                            height=200,
                            placeholder="Paste your messy data here, e.g.:\nAston V\n1\n2\nSheffield U\nEnglish League WEEK 17 - #2025122312\n3:58 pm\nSouthampton\n2\n0\nEverton\n...")
    
    parse_clicked = st.button("Parse and Add")
    
    # Show what the cleaner will do
    with st.expander("🔧 Data Cleaner Rules"):
        st.markdown("""
        The cleaner will automatically:
        - Remove lines containing: 'WEEK', 'pm', 'am', 'English League', '#'
        - Remove time patterns like '3:58 pm'
        - Remove date patterns like '2025122312'
        - Keep only team names and scores
        """)

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
    
    # Show cleaning summary
    if matches:
        st.info(f"✅ Cleaned {len(lines)} lines → {len(cleaned_lines)} valid items → {len(matches)} matches")
    
    return matches, errors, cleaned_lines

if parse_clicked and raw_input.strip():
    new_matches, errors, cleaned_lines = clean_and_parse_matches(raw_input)
    
    # Show what was cleaned
    with st.expander("🔍 Show Cleaning Process"):
        st.write("**Original lines:**")
        st.write([line.strip() for line in raw_input.splitlines() if line.strip()])
        st.write("**Cleaned lines:**")
        st.write(cleaned_lines)
        if new_matches:
            st.write("**Parsed matches:**")
            for m in new_matches:
                st.write(f"{m[0]} {m[1]}-{m[2]} {m[3]}")
    
    if errors:
        st.error(f"❌ Found {len(errors)} parsing errors:")
        with st.expander("Error Details"):
            for e in errors[:10]:  # Show first 10 errors
                st.write(f"- {e}")
        if new_matches:
            st.warning(f"But found {len(new_matches)} valid matches. Adding them...")
    else:
        st.success(f"✅ Successfully parsed {len(new_matches)} matches from cleaned data.")
    
    # Process the matches with new column structure
    for home_team, home_score, away_score, away_team in new_matches:
        match_id = st.session_state.match_counter
        st.session_state.match_counter += 1
        
        total_goals = home_score + away_score
        
        # Determine Total-G display
        if total_goals == 4:
            total_g_display = "Won"
        elif total_goals == 3:
            total_g_display = "3 ✔"
        else:
            total_g_display = total_goals
        
        # Update counters
        if total_goals == 4:
            st.session_state.home_counters[home_team] = 0
            st.session_state.away_counters[away_team] = 0
            st.session_state.ha_counters[home_team] = 0
            st.session_state.ha_counters[away_team] = 0
        else:
            st.session_state.home_counters[home_team] += 1
            st.session_state.away_counters[away_team] += 1
            st.session_state.ha_counters[home_team] += 1
            st.session_state.ha_counters[away_team] += 1

        if total_goals == 3:
            st.session_state.status3_counters[home_team] = 0
            st.session_state.status3_counters[away_team] = 0
        else:
            st.session_state.status3_counters[home_team] += 1
            st.session_state.status3_counters[away_team] += 1
        
        # Calculate derived statistics
        goal_difference = home_score - away_score
        
        # Determine match result
        if home_score > away_score:
            result = "Home Win"
        elif away_score > home_score:
            result = "Away Win"
        else:
            result = "Draw"
        
        # Both teams scored?
        both_teams_scored = "Yes" if home_score > 0 and away_score > 0 else "No"
        
        # Over/Under 2.5 goals
        over_under = "Over 2.5" if total_goals > 2.5 else "Under 2.5"
        
        # Add match data with new column names
        st.session_state.match_data.append([
            match_id,                      # Match_ID
            home_team,                     # Home_Team
            home_score,                    # Home_Score
            away_score,                    # Away_Score
            away_team,                     # Away_Team
            total_goals,                   # Total_Goals
            total_g_display,               # Total-G (Original display)
            result,                        # Match_Result
            goal_difference,               # Goal_Difference
            both_teams_scored,             # Both_Teams_Scored
            over_under,                    # Over_Under
            # Counters with descriptive names:
            st.session_state.home_counters[home_team],           # Games_Since_Last_Won_Home
            st.session_state.away_counters[away_team],           # Games_Since_Last_Won_Away
            st.session_state.ha_counters[home_team],             # Games_Since_Last_Won_Combined_Home
            st.session_state.ha_counters[away_team],             # Games_Since_Last_Won_Combined_Away
            st.session_state.status3_counters[home_team],        # Games_Since_Last_3Goals_Home
            st.session_state.status3_counters[away_team],        # Games_Since_Last_3Goals_Away
            # Legacy string format for backward compatibility:
            f"{home_team}: {st.session_state.ha_counters[home_team]} | {away_team}: {st.session_state.ha_counters[away_team]}",
            f"{home_team}: {st.session_state.status3_counters[home_team]} | {away_team}: {st.session_state.status3_counters[away_team]}"
        ])
    
    if new_matches:
        st.success(f"✅ Added {len(new_matches)} new matches to dashboard.")

# Display summary in right column
if st.session_state.match_data:
    # Define column names for the DataFrame
    column_names = [
        "Match_ID", "Home_Team", "Home_Score", "Away_Score", "Away_Team",
        "Total_Goals", "Total-G", "Match_Result", "Goal_Difference", 
        "Both_Teams_Scored", "Over_Under",
        "Games_Since_Last_Won_Home", "Games_Since_Last_Won_Away",
        "Games_Since_Last_Won_Combined_Home", "Games_Since_Last_Won_Combined_Away",
        "Games_Since_Last_3Goals_Home", "Games_Since_Last_3Goals_Away",
        "F!=4HA", "Status3"  # Legacy columns for backward compatibility
    ]
    
    df = pd.DataFrame(st.session_state.match_data, columns=column_names)

    with col2:
        st.subheader("📌 Last 10 Match Summary")

        # Styled summary frame
        st.markdown("""
            <div style="background-color:black; color:white; padding:15px; border-radius:10px; border:2px solid #444;">
        """, unsafe_allow_html=True)

        for _, row in df.tail(10).iterrows():
            home = row["Home_Team"]
            away = row["Away_Team"]
            status3_home = row["Games_Since_Last_3Goals_Home"]
            status3_away = row["Games_Since_Last_3Goals_Away"]
            won_home = row["Games_Since_Last_Won_Combined_Home"]
            won_away = row["Games_Since_Last_Won_Combined_Away"]
            
            left = f"{home}, [{status3_home} : {won_home}]"
            right = f"{away}, [{status3_away} : {won_away}]"
            st.markdown(f"<div style='font-size:14px; margin-bottom:5px;'>{left} — {right}</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # Show data preview
        with st.expander("📊 Preview Data (First 5 rows)"):
            st.dataframe(df.head()[["Home_Team", "Home_Score", "Away_Score", "Away_Team", 
                                   "Total_Goals", "Match_Result", 
                                   "Games_Since_Last_Won_Combined_Home",
                                   "Games_Since_Last_3Goals_Home"]])
        
        # Download buttons for different formats
        st.subheader("📥 Download Options")
        
        # Option 1: Full dataset with all columns
        csv_full = df.to_csv(index=False)
        st.download_button("📋 Download Full CSV (All Columns)", 
                          data=csv_full,
                          file_name="football_results_full.csv", 
                          mime="text/csv",
                          help="Includes all columns with descriptive names")
        
        # Option 2: Analysis-ready dataset (without legacy string columns)
        df_analysis = df.drop(columns=["F!=4HA", "Status3"])
        csv_analysis = df_analysis.to_csv(index=False)
        st.download_button("📊 Download Analysis-Ready CSV", 
                          data=csv_analysis,
                          file_name="football_results_analysis.csv", 
                          mime="text/csv",
                          help="Clean dataset without legacy string columns")
        
        # Option 3: Original format (backward compatible)
        df_original = df[["Home_Team", "Home_Score", "Away_Score", "Away_Team", 
                         "Total-G", "Games_Since_Last_Won_Home", 
                         "Games_Since_Last_Won_Away", "F!=4HA", "Status3"]]
        df_original.columns = ["Home Team", "Home Score", "Away Score", "Away Team", 
                              "Total-G", "F<4H", "F<4A", "F!=4HA", "Status3"]
        csv_original = df_original.to_csv(index=False)
        st.download_button("🔄 Download Original Format CSV", 
                          data=csv_original,
                          file_name="football_results_original.csv", 
                          mime="text/csv",
                          help="Backward compatible with original column names")

        # Clear button
        if st.button("🗑️ Clear all data"):
            st.session_state.match_data = []
            st.session_state.home_counters = {team: 0 for team in VALID_TEAMS}
            st.session_state.away_counters = {team: 0 for team in VALID_TEAMS}
            st.session_state.ha_counters = {team: 0 for team in VALID_TEAMS}
            st.session_state.status3_counters = {team: 0 for team in VALID_TEAMS}
            st.session_state.match_counter = 1
            st.experimental_rerun()

# Add helper section
with st.sidebar:
    st.subheader("📋 Column Name Reference")
    st.markdown("""
    **New Descriptive Column Names:**
    
    **Match Info:**
    - `Match_ID`: Unique match identifier
    - `Home_Team` / `Away_Team`: Team names
    - `Home_Score` / `Away_Score`: Match scores
    - `Total_Goals`: Sum of home + away scores
    
    **Derived Statistics:**
    - `Match_Result`: Home Win / Away Win / Draw
    - `Goal_Difference`: Home score - Away score
    - `Both_Teams_Scored`: Yes/No
    - `Over_Under`: Over 2.5 / Under 2.5 goals
    
    **Counter Columns:**
    - `Games_Since_Last_Won_Home`: Matches since home team had 4 total goals
    - `Games_Since_Last_Won_Away`: Matches since away team had 4 total goals
    - `Games_Since_Last_Won_Combined_Home`: Combined counter for home team
    - `Games_Since_Last_Won_Combined_Away`: Combined counter for away team
    - `Games_Since_Last_3Goals_Home`: Matches since home team had 3 total goals
    - `Games_Since_Last_3Goals_Away`: Matches since away team had 3 total goals
    
    **Legacy Columns:**
    - `Total-G`: Original display (Won/3 ✔/number)
    - `F!=4HA`: Legacy string format
    - `Status3`: Legacy string format
    """)

# Button styling
st.markdown("""
    <style>
    /* Style for primary download button */
    div[data-testid="stDownloadButton"] button {
        background-color: #4CAF50 !important;
        color: white !important;
        border-radius: 8px !important;
        margin-top: 5px !important;
        width: 100% !important;
        transition: 0.3s;
        border: none !important;
    }
    div[data-testid="stDownloadButton"] button:hover {
        background-color: #45a049 !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Style for secondary buttons */
    div[data-testid="stButton"] button {
        background-color: #f44336 !important;
        color: white !important;
        border-radius: 8px !important;
        margin-top: 5px !important;
        width: 100% !important;
        transition: 0.3s;
        border: none !important;
    }
    div[data-testid="stButton"] button:hover {
        background-color: #da190b !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Style for expander headers */
    .streamlit-expanderHeader {
        background-color: #f0f2f6;
        border-radius: 5px;
        padding: 10px;
    }
    </style>
""", unsafe_allow_html=True)
