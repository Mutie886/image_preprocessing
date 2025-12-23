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

# ==================== NEW DASHBOARD LAYOUT ====================

# Create a main container
main_container = st.container()

with main_container:
    # Row 1: Input Section (Full width)
    st.header("📥 Data Input Section")
    
    input_col1, input_col2 = st.columns([2, 1])
    
    with input_col1:
        raw_input = st.text_area("Paste match data (with dates/times - will be cleaned automatically)", 
                                height=150,
                                placeholder="Paste your messy data here, e.g.:\nAston V\n1\n2\nSheffield U\nEnglish League WEEK 17 - #2025122312\n3:58 pm\nSouthampton\n2\n0\nEverton\n...")
        
        parse_clicked = st.button("🚀 Parse and Add Matches", type="primary", use_container_width=True)
    
    with input_col2:
        st.markdown("### ℹ️ Data Cleaner Info")
        with st.expander("🔧 Cleaning Rules", expanded=True):
            st.markdown("""
            The cleaner automatically removes:
            - Lines with 'WEEK', 'pm', 'am'
            - 'English League' and '#'
            - Time patterns like '3:58 pm'
            - Date patterns like '2025122312'
            - Keeps only team names and scores
            """)
        
        if st.button("🗑️ Clear All Data", type="secondary", use_container_width=True):
            st.session_state.match_data = []
            st.session_state.home_counters = {team: 0 for team in VALID_TEAMS}
            st.session_state.away_counters = {team: 0 for team in VALID_TEAMS}
            st.session_state.ha_counters = {team: 0 for team in VALID_TEAMS}
            st.session_state.status3_counters = {team: 0 for team in VALID_TEAMS}
            st.session_state.match_counter = 1
            st.rerun()

    # Divider
    st.divider()
    
    # Row 2: Processing and Results (Two columns)
    st.header("📊 Results & Analysis")
    
    if parse_clicked and raw_input.strip():
        new_matches, errors, cleaned_lines = clean_and_parse_matches(raw_input)
        
        # Show processing results
        with st.expander("🔍 Processing Details", expanded=True):
            proc_col1, proc_col2, proc_col3 = st.columns(3)
            
            with proc_col1:
                st.metric("Original Lines", len([line.strip() for line in raw_input.splitlines() if line.strip()]))
            
            with proc_col2:
                st.metric("Cleaned Items", len(cleaned_lines))
            
            with proc_col3:
                st.metric("Matches Found", len(new_matches))
            
            if errors:
                st.error(f"❌ Found {len(errors)} parsing errors")
                for e in errors[:3]:
                    st.write(f"- {e}")
                if len(errors) > 3:
                    st.write(f"... and {len(errors)-3} more errors")
            else:
                st.success("✅ All matches parsed successfully!")
        
        # Process the matches (same as before, kept for functionality)
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
                match_id, home_team, home_score, away_score, away_team,
                total_goals, total_g_display, result, goal_difference,
                both_teams_scored, over_under,
                st.session_state.home_counters[home_team],
                st.session_state.away_counters[away_team],
                st.session_state.ha_counters[home_team],
                st.session_state.ha_counters[away_team],
                st.session_state.status3_counters[home_team],
                st.session_state.status3_counters[away_team],
                f"{home_team}: {st.session_state.ha_counters[home_team]} | {away_team}: {st.session_state.ha_counters[away_team]}",
                f"{home_team}: {st.session_state.status3_counters[home_team]} | {away_team}: {st.session_state.status3_counters[away_team]}"
            ])
        
        if new_matches:
            st.success(f"✅ Successfully added {len(new_matches)} new matches!")

    # Row 3: Display Data (Only if we have data)
    if st.session_state.match_data:
        # Define column names for the DataFrame
        column_names = [
            "Match_ID", "Home_Team", "Home_Score", "Away_Score", "Away_Team",
            "Total_Goals", "Total-G", "Match_Result", "Goal_Difference", 
            "Both_Teams_Scored", "Over_Under",
            "Games_Since_Last_Won_Home", "Games_Since_Last_Won_Away",
            "Games_Since_Last_Won_Combined_Home", "Games_Since_Last_Won_Combined_Away",
            "Games_Since_Last_3Goals_Home", "Games_Since_Last_3Goals_Away",
            "F!=4HA", "Status3"
        ]
        
        df = pd.DataFrame(st.session_state.match_data, columns=column_names)
        
        # Create two columns for display
        display_col1, display_col2 = st.columns([1, 1])
        
        with display_col1:
            st.subheader("📋 Recent Matches Summary")
            
            # Create a better formatted table for last 10 matches
            summary_df = df.tail(10)[["Home_Team", "Home_Score", "Away_Score", "Away_Team", 
                                      "Total_Goals", "Match_Result",
                                      "Games_Since_Last_Won_Combined_Home",
                                      "Games_Since_Last_3Goals_Home"]].copy()
            
            # Rename columns for display
            summary_df_display = summary_df.rename(columns={
                "Home_Team": "Home",
                "Away_Team": "Away",
                "Total_Goals": "Total",
                "Match_Result": "Result",
                "Games_Since_Last_Won_Combined_Home": "Won_Cnt_H",
                "Games_Since_Last_3Goals_Home": "3Goals_Cnt_H"
            })
            
            # Display as a styled table
            st.dataframe(
                summary_df_display,
                column_config={
                    "Home": st.column_config.TextColumn("Home Team", width="medium"),
                    "Away": st.column_config.TextColumn("Away Team", width="medium"),
                    "Home_Score": st.column_config.NumberColumn("H Score", width="small"),
                    "Away_Score": st.column_config.NumberColumn("A Score", width="small"),
                    "Total": st.column_config.NumberColumn("Total G", width="small"),
                    "Result": st.column_config.TextColumn("Result", width="small"),
                    "Won_Cnt_H": st.column_config.NumberColumn("Won Cnt", width="small"),
                    "3Goals_Cnt_H": st.column_config.NumberColumn("3G Cnt", width="small")
                },
                hide_index=True,
                use_container_width=True
            )
            
            # Quick Stats
            st.subheader("📈 Quick Statistics")
            stats_col1, stats_col2, stats_col3 = st.columns(3)
            
            with stats_col1:
                total_matches = len(df)
                st.metric("Total Matches", total_matches)
            
            with stats_col2:
                home_wins = len(df[df["Match_Result"] == "Home Win"])
                st.metric("Home Wins", home_wins)
            
            with stats_col3:
                avg_goals = df["Total_Goals"].mean().round(2)
                st.metric("Avg Goals/Match", avg_goals)
        
        with display_col2:
            st.subheader("📥 Export Options")
            
            # Option 1: Full dataset
            csv_full = df.to_csv(index=False)
            st.download_button(
                "📋 Download Full CSV",
                data=csv_full,
                file_name="football_results_full.csv",
                mime="text/csv",
                use_container_width=True,
                help="All columns with descriptive names"
            )
            
            # Option 2: Analysis-ready dataset
            df_analysis = df.drop(columns=["F!=4HA", "Status3"])
            csv_analysis = df_analysis.to_csv(index=False)
            st.download_button(
                "📊 Download Analysis CSV",
                data=csv_analysis,
                file_name="football_results_analysis.csv",
                mime="text/csv",
                use_container_width=True,
                help="Clean dataset without legacy columns"
            )
            
            # Option 3: Original format
            df_original = df[["Home_Team", "Home_Score", "Away_Score", "Away_Team", 
                             "Total-G", "Games_Since_Last_Won_Home", 
                             "Games_Since_Last_Won_Away", "F!=4HA", "Status3"]]
            df_original.columns = ["Home Team", "Home Score", "Away Score", "Away Team", 
                                  "Total-G", "F<4H", "F<4A", "F!=4HA", "Status3"]
            csv_original = df_original.to_csv(index=False)
            st.download_button(
                "🔄 Download Original CSV",
                data=csv_original,
                file_name="football_results_original.csv",
                mime="text/csv",
                use_container_width=True,
                help="Backward compatible format"
            )
            
            # Data Preview
            st.subheader("🔍 Data Preview")
            with st.expander("View First 5 Rows", expanded=False):
                preview_cols = ["Home_Team", "Home_Score", "Away_Score", "Away_Team", 
                               "Total_Goals", "Match_Result"]
                st.dataframe(df.head()[preview_cols], hide_index=True, use_container_width=True)

    # If no data yet
    else:
        st.info("📝 No match data yet. Paste your data above and click 'Parse and Add Matches' to get started!")

# ==================== SIDEBAR ====================

with st.sidebar:
    st.header("ℹ️ Dashboard Guide")
    
    st.markdown("""
    ### How to Use:
    1. **Paste** your match data in the input box
    2. **Click** "Parse and Add Matches"
    3. **View** results and statistics
    4. **Download** data in your preferred format
    
    ### Column Abbreviations:
    - **Won_Cnt**: Games since last 4-goal match
    - **3G_Cnt**: Games since last 3-goal match
    - **H/A**: Home/Away team indicators
    
    ### Valid Team Names:
    """)
    
    # Display teams in two columns
    teams_list = list(VALID_TEAMS)
    mid = len(teams_list) // 2
    
    team_col1, team_col2 = st.columns(2)
    with team_col1:
        for team in teams_list[:mid]:
            st.write(f"• {team}")
    with team_col2:
        for team in teams_list[mid:]:
            st.write(f"• {team}")

# ==================== KEEP ORIGINAL FUNCTIONS ====================

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
            r'WEEK \d+',
            r'English League',
            r'\d{1,2}:\d{2}\s*(?:am|pm)',
            r'#\d+',
            r'^\d{8,}$',
        ]
        
        # Check if line contains any team name (case-sensitive)
        is_team = line in VALID_TEAMS
        
        # Check if line is just digits (score)
        is_score = line.isdigit() and 0 <= int(line) <= 20
        
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
        if i + 3 >= len(cleaned_lines):
            errors.append(f"Incomplete match at position {i+1}")
            break
            
        home_team = cleaned_lines[i]
        home_score_raw = cleaned_lines[i+1]
        away_score_raw = cleaned_lines[i+2]
        away_team = cleaned_lines[i+3]
        
        # Validate
        if home_team not in VALID_TEAMS:
            errors.append(f"Invalid home team: {home_team}")
        if away_team not in VALID_TEAMS:
            errors.append(f"Invalid away team: {away_team}")
        if not home_score_raw.isdigit():
            errors.append(f"Non-numeric home score: {home_score_raw}")
        if not away_score_raw.isdigit():
            errors.append(f"Non-numeric away score: {away_score_raw}")
        
        if errors and len(errors) > 5:
            errors.append("... more errors")
            break
            
        if home_team in VALID_TEAMS and away_team in VALID_TEAMS and home_score_raw.isdigit() and away_score_raw.isdigit():
            matches.append([home_team, int(home_score_raw), int(away_score_raw), away_team])
        
        i += 4
    
    # Reverse order so bottom match is processed first
    matches.reverse()
    
    return matches, errors, cleaned_lines

# ==================== STYLING ====================

st.markdown("""
<style>
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Metric cards */
    [data-testid="metric-container"] {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #dee2e6;
    }
    
    /* Button styling */
    .stButton button {
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        font-weight: 600;
        background-color: #f0f2f6;
        border-radius: 5px;
    }
    
    /* Dataframe styling */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Divider */
    hr {
        margin: 2rem 0;
        border: none;
        height: 1px;
        background-color: #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)
