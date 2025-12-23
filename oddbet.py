import streamlit as st
import pandas as pd
import numpy as np
import re
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats

# Allowed team names (case-sensitive)
VALID_TEAMS = {
    "Leeds", "Aston V", "Manchester Blue", "Liverpool", "London Blues", "Everton",
    "Brighton", "Sheffield U", "Tottenham", "Palace", "Newcastle", "West Ham",
    "Leicester", "West Brom", "Burnley", "London Reds", "Southampton", "Wolves",
    "Fulham", "Manchester Reds"
}

st.set_page_config(page_title="Football Results Dashboard", page_icon="⚽", layout="wide")
st.title("⚽ Football Results Dashboard & Analytics")

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

# Create tabs for different sections
tab1, tab2, tab3 = st.tabs(["📥 Data Input", "📊 Analytics Dashboard", "📈 Team Performance"])

with tab1:
    # Two equal columns for input
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
                st.rerun()

with tab2:
    st.header("📊 Analytics Dashboard")
    
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
        
        # Create metrics row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Matches", len(df))
        with col2:
            avg_goals = df["Total_Goals"].mean()
            st.metric("Average Goals per Match", f"{avg_goals:.2f}")
        with col3:
            home_wins = len(df[df["Match_Result"] == "Home Win"])
            st.metric("Home Wins", home_wins)
        with col4:
            draws = len(df[df["Match_Result"] == "Draw"])
            st.metric("Draws", draws)
        
        # Create two columns for analytics
        analytics_col1, analytics_col2 = st.columns(2)
        
        with analytics_col1:
            st.subheader("🏆 Current Longest Dry Spells")
            
            # Calculate current dry spells for each team
            current_dry_spells = []
            for team in VALID_TEAMS:
                # Get the most recent appearance of each team
                team_home_games = df[df["Home_Team"] == team]
                team_away_games = df[df["Away_Team"] == team]
                
                if not team_home_games.empty:
                    last_home_won = team_home_games.iloc[-1]["Games_Since_Last_Won_Combined_Home"]
                    last_home_3goals = team_home_games.iloc[-1]["Games_Since_Last_3Goals_Home"]
                else:
                    last_home_won = st.session_state.ha_counters[team]
                    last_home_3goals = st.session_state.status3_counters[team]
                
                if not team_away_games.empty:
                    last_away_won = team_away_games.iloc[-1]["Games_Since_Last_Won_Combined_Away"]
                    last_away_3goals = team_away_games.iloc[-1]["Games_Since_Last_3Goals_Away"]
                else:
                    last_away_won = st.session_state.ha_counters[team]
                    last_away_3goals = st.session_state.status3_counters[team]
                
                # Take the maximum between home and away appearances
                current_won_dry = max(last_home_won, last_away_won)
                current_3goals_dry = max(last_home_3goals, last_away_3goals)
                
                current_dry_spells.append({
                    "Team": team,
                    "Won_Dry_Spell": current_won_dry,
                    "3Goals_Dry_Spell": current_3goals_dry
                })
            
            dry_spells_df = pd.DataFrame(current_dry_spells)
            
            # Sort by Won Dry Spell (longest first)
            st.write("**Longest Without 'Won' (4 goals):**")
            top_won_dry = dry_spells_df.sort_values("Won_Dry_Spell", ascending=False).head(5)
            for _, row in top_won_dry.iterrows():
                st.progress(row["Won_Dry_Spell"] / max(dry_spells_df["Won_Dry_Spell"]), 
                           text=f"{row['Team']}: {int(row['Won_Dry_Spell'])} games")
            
            st.write("**Longest Without '3 ✔' (3 goals):**")
            top_3goals_dry = dry_spells_df.sort_values("3Goals_Dry_Spell", ascending=False).head(5)
            for _, row in top_3goals_dry.iterrows():
                st.progress(row["3Goals_Dry_Spell"] / max(dry_spells_df["3Goals_Dry_Spell"]), 
                           text=f"{row['Team']}: {int(row['3Goals_Dry_Spell'])} games")
        
        with analytics_col2:
            st.subheader("📈 Average Dry Spells by Team")
            
            # Calculate average dry spells for each team
            team_stats = []
            for team in VALID_TEAMS:
                team_home_games = df[df["Home_Team"] == team]
                team_away_games = df[df["Away_Team"] == team]
                
                all_won_dry = []
                all_3goals_dry = []
                
                # Collect home game counters
                if not team_home_games.empty:
                    all_won_dry.extend(team_home_games["Games_Since_Last_Won_Combined_Home"].tolist())
                    all_3goals_dry.extend(team_home_games["Games_Since_Last_3Goals_Home"].tolist())
                
                # Collect away game counters
                if not team_away_games.empty:
                    all_won_dry.extend(team_away_games["Games_Since_Last_Won_Combined_Away"].tolist())
                    all_3goals_dry.extend(team_away_games["Games_Since_Last_3Goals_Away"].tolist())
                
                if all_won_dry:
                    avg_won_dry = np.mean(all_won_dry)
                    avg_3goals_dry = np.mean(all_3goals_dry)
                    games_played = len(all_won_dry)
                    
                    team_stats.append({
                        "Team": team,
                        "Avg_Won_Dry_Spell": round(avg_won_dry, 1),
                        "Avg_3Goals_Dry_Spell": round(avg_3goals_dry, 1),
                        "Games_Played": games_played
                    })
            
            team_stats_df = pd.DataFrame(team_stats)
            
            # Display top teams with longest average dry spells
            st.write("**Highest Average 'Won' Dry Spells:**")
            top_avg_won = team_stats_df.sort_values("Avg_Won_Dry_Spell", ascending=False).head(5)
            st.dataframe(top_avg_won[["Team", "Avg_Won_Dry_Spell", "Games_Played"]])
            
            st.write("**Highest Average '3 Goals' Dry Spells:**")
            top_avg_3goals = team_stats_df.sort_values("Avg_3Goals_Dry_Spell", ascending=False).head(5)
            st.dataframe(top_avg_3goals[["Team", "Avg_3Goals_Dry_Spell", "Games_Played"]])
        
        # Correlation Analysis
        st.subheader("🔗 Correlation Analysis")
        
        # Prepare data for correlation analysis
        correlation_data = []
        for _, row in df.iterrows():
            correlation_data.append({
                "Won_Dry_Home": row["Games_Since_Last_Won_Combined_Home"],
                "Won_Dry_Away": row["Games_Since_Last_Won_Combined_Away"],
                "3Goals_Dry_Home": row["Games_Since_Last_3Goals_Home"],
                "3Goals_Dry_Away": row["Games_Since_Last_3Goals_Away"],
                "Home_Win": 1 if row["Match_Result"] == "Home Win" else 0,
                "Away_Win": 1 if row["Match_Result"] == "Away Win" else 0,
                "Draw": 1 if row["Match_Result"] == "Draw" else 0,
                "Total_Goals": row["Total_Goals"],
                "Goal_Difference": row["Goal_Difference"]
            })
        
        corr_df = pd.DataFrame(correlation_data)
        
        # Calculate correlations
        corr_matrix = corr_df.corr()
        
        # Display key correlations
        col1, col2, col3 = st.columns(3)
        
        with col1:
            corr_won_home_win = corr_matrix.loc["Won_Dry_Home", "Home_Win"]
            st.metric("Correlation: Won Dry Spell vs Home Win", f"{corr_won_home_win:.3f}")
        
        with col2:
            corr_3goals_home_win = corr_matrix.loc["3Goals_Dry_Home", "Home_Win"]
            st.metric("Correlation: 3 Goals Dry Spell vs Home Win", f"{corr_3goals_home_win:.3f}")
        
        with col3:
            corr_won_total_goals = corr_matrix.loc["Won_Dry_Home", "Total_Goals"]
            st.metric("Correlation: Won Dry Spell vs Total Goals", f"{corr_won_total_goals:.3f}")
        
        # Heatmap of correlations
        with st.expander("View Full Correlation Matrix"):
            fig = px.imshow(corr_matrix, 
                          text_auto='.2f',
                          aspect="auto",
                          color_continuous_scale='RdBu_r',
                          title="Correlation Matrix")
            st.plotly_chart(fig, use_container_width=True)
        
        # Distribution Analysis
        st.subheader("📊 Distribution of Dry Spells")
        
        dist_col1, dist_col2 = st.columns(2)
        
        with dist_col1:
            # Create histogram for Won Dry Spells
            fig1 = px.histogram(df, 
                               x=["Games_Since_Last_Won_Combined_Home", "Games_Since_Last_Won_Combined_Away"],
                               nbins=20,
                               title="Distribution of 'Won' Dry Spells",
                               labels={"value": "Games Since Last 'Won'", "variable": "Team Type"},
                               opacity=0.7)
            st.plotly_chart(fig1, use_container_width=True)
        
        with dist_col2:
            # Create histogram for 3 Goals Dry Spells
            fig2 = px.histogram(df, 
                               x=["Games_Since_Last_3Goals_Home", "Games_Since_Last_3Goals_Away"],
                               nbins=20,
                               title="Distribution of '3 Goals' Dry Spells",
                               labels={"value": "Games Since Last '3 ✔'", "variable": "Team Type"},
                               opacity=0.7)
            st.plotly_chart(fig2, use_container_width=True)
    
    else:
        st.info("No data available. Please add matches in the Data Input tab.")

with tab3:
    st.header("📈 Team Performance Dashboard")
    
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
        
        # Team selector
        selected_team = st.selectbox("Select Team", sorted(list(VALID_TEAMS)))
        
        if selected_team:
            # Filter data for selected team
            team_home_games = df[df["Home_Team"] == selected_team]
            team_away_games = df[df["Away_Team"] == selected_team]
            
            # Combine home and away games
            team_games = pd.concat([team_home_games, team_away_games])
            team_games = team_games.sort_values("Match_ID", ascending=True)
            
            if not team_games.empty:
                # Team metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    total_games = len(team_games)
                    st.metric("Total Games", total_games)
                
                with col2:
                    wins = len(team_games[(team_games["Home_Team"] == selected_team) & (team_games["Match_Result"] == "Home Win")]) + \
                           len(team_games[(team_games["Away_Team"] == selected_team) & (team_games["Match_Result"] == "Away Win")])
                    st.metric("Wins", wins)
                
                with col3:
                    # Current dry spells
                    if not team_home_games.empty:
                        current_won_dry = team_home_games.iloc[-1]["Games_Since_Last_Won_Combined_Home"]
                        current_3goals_dry = team_home_games.iloc[-1]["Games_Since_Last_3Goals_Home"]
                    elif not team_away_games.empty:
                        current_won_dry = team_away_games.iloc[-1]["Games_Since_Last_Won_Combined_Away"]
                        current_3goals_dry = team_away_games.iloc[-1]["Games_Since_Last_3Goals_Away"]
                    else:
                        current_won_dry = st.session_state.ha_counters[selected_team]
                        current_3goals_dry = st.session_state.status3_counters[selected_team]
                    
                    st.metric("Current 'Won' Dry Spell", int(current_won_dry))
                
                with col4:
                    st.metric("Current '3 Goals' Dry Spell", int(current_3goals_dry))
                
                # Create two columns for team analysis
                team_col1, team_col2 = st.columns(2)
                
                with team_col1:
                    st.subheader(f"📅 {selected_team} - Recent Matches")
                    
                    # Display recent matches
                    recent_matches = team_games.tail(10).sort_values("Match_ID", ascending=False)
                    
                    for _, match in recent_matches.iterrows():
                        if match["Home_Team"] == selected_team:
                            opponent = match["Away_Team"]
                            score = f"{match['Home_Score']}-{match['Away_Score']}"
                            result = "W" if match["Match_Result"] == "Home Win" else ("L" if match["Match_Result"] == "Away Win" else "D")
                            location = "Home"
                        else:
                            opponent = match["Home_Team"]
                            score = f"{match['Away_Score']}-{match['Home_Score']}"
                            result = "W" if match["Match_Result"] == "Away Win" else ("L" if match["Match_Result"] == "Home Win" else "D")
                            location = "Away"
                        
                        st.write(f"**{result}** {location} vs {opponent} ({score}) - Total: {match['Total_Goals']}")
                
                with team_col2:
                    st.subheader(f"📊 {selected_team} - Performance Trends")
                    
                    # Prepare trend data
                    trend_data = []
                    for _, match in team_games.iterrows():
                        if match["Home_Team"] == selected_team:
                            won_dry = match["Games_Since_Last_Won_Combined_Home"]
                            goals_3_dry = match["Games_Since_Last_3Goals_Home"]
                        else:
                            won_dry = match["Games_Since_Last_Won_Combined_Away"]
                            goals_3_dry = match["Games_Since_Last_3Goals_Away"]
                        
                        trend_data.append({
                            "Match_ID": match["Match_ID"],
                            "Won_Dry_Spell": won_dry,
                            "3Goals_Dry_Spell": goals_3_dry,
                            "Total_Goals": match["Total_Goals"]
                        })
                    
                    trend_df = pd.DataFrame(trend_data)
                    
                    # Create trend chart
                    if len(trend_df) > 1:
                        fig = go.Figure()
                        
                        fig.add_trace(go.Scatter(
                            x=trend_df["Match_ID"],
                            y=trend_df["Won_Dry_Spell"],
                            mode='lines+markers',
                            name="Won Dry Spell",
                            line=dict(color='red', width=2)
                        ))
                        
                        fig.add_trace(go.Scatter(
                            x=trend_df["Match_ID"],
                            y=trend_df["3Goals_Dry_Spell"],
                            mode='lines+markers',
                            name="3 Goals Dry Spell",
                            line=dict(color='blue', width=2)
                        ))
                        
                        fig.update_layout(
                            title="Dry Spell Trends Over Time",
                            xaxis_title="Match Sequence",
                            yaxis_title="Dry Spell Length",
                            hovermode='x unified'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                
                # Team statistics summary
                st.subheader(f"📋 {selected_team} - Statistics Summary")
                
                # Calculate various statistics
                summary_stats = {
                    "Games Played": len(team_games),
                    "Home Games": len(team_home_games),
                    "Away Games": len(team_away_games),
                    "Wins": wins,
                    "Win Rate": f"{(wins/len(team_games)*100):.1f}%" if len(team_games) > 0 else "0%",
                    "Average Goals Scored": f"{team_games.apply(lambda x: x['Home_Score'] if x['Home_Team'] == selected_team else x['Away_Score'], axis=1).mean():.2f}",
                    "Average Goals Conceded": f"{team_games.apply(lambda x: x['Away_Score'] if x['Home_Team'] == selected_team else x['Home_Score'], axis=1).mean():.2f}",
                    "Average Total Goals": f"{team_games['Total_Goals'].mean():.2f}",
                    "Both Teams Scored Rate": f"{(team_games['Both_Teams_Scored'].value_counts().get('Yes', 0) / len(team_games) * 100):.1f}%" if len(team_games) > 0 else "0%",
                    "Over 2.5 Goals Rate": f"{(team_games['Over_Under'].value_counts().get('Over 2.5', 0) / len(team_games) * 100):.1f}%" if len(team_games) > 0 else "0%"
                }
                
                # Display summary stats in a nice format
                stats_cols = st.columns(4)
                for idx, (key, value) in enumerate(summary_stats.items()):
                    with stats_cols[idx % 4]:
                        st.metric(key, value)
            
            else:
                st.info(f"No games found for {selected_team}. Add more matches in the Data Input tab.")
    
    else:
        st.info("No data available. Please add matches in the Data Input tab.")

# Add helper section in sidebar
with st.sidebar:
    st.subheader("📋 Analytics Guide")
    st.markdown("""
    **📥 Data Input Tab:**
    - Paste your match data
    - Parse and clean data
    - Download CSV files
    
    **📊 Analytics Dashboard:**
    - **Dry Spell Analysis**: See which teams have longest streaks
    - **Average Calculations**: Team performance averages
    - **Correlation Analysis**: Relationships between dry spells and results
    
    **📈 Team Performance:**
    - Select any team
    - View detailed statistics
    - Track performance trends
    - Analyze match history
    """)
    
    st.subheader("📈 Key Metrics Explained")
    st.markdown("""
    **Won Dry Spell**: Games since team had 4 total goals
    
    **3 Goals Dry Spell**: Games since team had 3 total goals
    
    **Average Dry Spell**: Mean value for team's dry spells
    
    **Correlation**: Relationship between dry spells and match outcomes
    - Positive: Longer dry spells associated with better outcomes
    - Negative: Longer dry spells associated with worse outcomes
    - Near 0: Little to no relationship
    """)

# Global styling
st.markdown("""
    <style>
    /* Metric card styling */
    [data-testid="stMetric"] {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #ddd;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #4CAF50;
        color: white;
    }
    
    /* Progress bar styling */
    .stProgress > div > div > div > div {
        background-color: #4CAF50;
    }
    </style>
""", unsafe_allow_html=True)
