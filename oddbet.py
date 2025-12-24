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

# Initialize ALL session state variables first
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
if "team_stats" not in st.session_state:
    st.session_state.team_stats = {
        team: {
            "P": 0,      # Played
            "W": 0,      # Wins
            "D": 0,      # Draws
            "L": 0,      # Losses
            "GF": 0,     # Goals For
            "GA": 0,     # Goals Against
            "GD": 0,     # Goal Difference
            "Pts": 0,    # Points
            "Form": []   # Last 5 results (W/D/L)
        }
        for team in VALID_TEAMS
    }
if "match_counter" not in st.session_state:
    st.session_state.match_counter = 1

# ============ HELPER FUNCTIONS ============
def calculate_rankings():
    """Calculate team rankings based on current stats"""
    sorted_teams = sorted(
        st.session_state.team_stats.items(),
        key=lambda x: (x[1]["Pts"], x[1]["GD"], x[1]["GF"]),
        reverse=True
    )
    return sorted_teams

def get_team_position(team_name):
    """Get current ranking position for a team"""
    rankings = calculate_rankings()
    for pos, (team, _) in enumerate(rankings, 1):
        if team == team_name:
            return pos
    return None

def calculate_team_metrics():
    """Calculate detailed metrics for each team"""
    metrics = {}
    
    for team in VALID_TEAMS:
        stats = st.session_state.team_stats[team]
        
        total_matches = stats["P"]
        win_rate = (stats["W"] / total_matches * 100) if total_matches > 0 else 0
        draw_rate = (stats["D"] / total_matches * 100) if total_matches > 0 else 0
        loss_rate = (stats["L"] / total_matches * 100) if total_matches > 0 else 0
        
        avg_gf = stats["GF"] / total_matches if total_matches > 0 else 0
        avg_ga = stats["GA"] / total_matches if total_matches > 0 else 0
        
        metrics[team] = {
            "win_rate": round(win_rate, 1),
            "draw_rate": round(draw_rate, 1),
            "loss_rate": round(loss_rate, 1),
            "avg_gf": round(avg_gf, 2),
            "avg_ga": round(avg_ga, 2),
            "form": stats["Form"][-5:] if len(stats["Form"]) >= 5 else stats["Form"],
            "points_per_game": round(stats["Pts"] / total_matches, 2) if total_matches > 0 else 0,
        }
    
    return metrics

def predict_match_outcome(home_team, away_team, team_metrics):
    """Predict match outcome probabilities"""
    
    home_metrics = team_metrics[home_team]
    away_metrics = team_metrics[away_team]
    
    # Base probabilities from win rates
    home_win_prob = home_metrics["win_rate"] * (1 - away_metrics["win_rate"] / 100)
    away_win_prob = away_metrics["win_rate"] * (1 - home_metrics["win_rate"] / 100)
    draw_prob = (home_metrics["draw_rate"] + away_metrics["draw_rate"]) / 2
    
    # Normalize to 100%
    total = home_win_prob + away_win_prob + draw_prob
    home_win_prob = (home_win_prob / total * 100) if total > 0 else 33.3
    away_win_prob = (away_win_prob / total * 100) if total > 0 else 33.3
    draw_prob = (draw_prob / total * 100) if total > 0 else 33.3
    
    # Calculate over/under probabilities
    total_goals_expected = home_metrics["avg_gf"] + away_metrics["avg_gf"]
    
    over_2_5_prob = min(90, max(10, (total_goals_expected - 1.5) * 30))
    over_3_5_prob = min(70, max(5, (total_goals_expected - 2.5) * 25))
    over_4_5_prob = min(50, max(2, (total_goals_expected - 3.5) * 20))
    
    both_teams_score_prob = 50  # Default
    
    return {
        "home_win": round(home_win_prob, 1),
        "away_win": round(away_win_prob, 1),
        "draw": round(draw_prob, 1),
        "over_2_5": round(over_2_5_prob, 1),
        "over_3_5": round(over_3_5_prob, 1),
        "over_4_5": round(over_4_5_prob, 1),
        "both_teams_score": round(both_teams_score_prob, 1),
        "expected_goals": round(total_goals_expected, 2),
        "predicted_score": f"{round(home_metrics['avg_gf'], 1)}-{round(away_metrics['avg_gf'], 1)}"
    }

def create_head_to_head_stats(home_team, away_team):
    """Calculate head-to-head statistics"""
    # Filter matches between these two teams
    h2h_matches = []
    for match in st.session_state.match_data:
        if (match[1] == home_team and match[4] == away_team) or \
           (match[1] == away_team and match[4] == home_team):
            h2h_matches.append(match)
    
    if not h2h_matches:
        return None
    
    stats = {
        "total_matches": len(h2h_matches),
        "home_wins": 0,
        "away_wins": 0,
        "draws": 0,
        "avg_goals": 0,
        "over_2_5": 0,
        "over_3_5": 0,
        "both_teams_score": 0
    }
    
    total_goals = 0
    for match in h2h_matches:
        home_score = match[2]
        away_score = match[3]
        total_goals += home_score + away_score
        
        if match[1] == home_team:  # Home team is actually home
            if home_score > away_score:
                stats["home_wins"] += 1
            elif away_score > home_score:
                stats["away_wins"] += 1
            else:
                stats["draws"] += 1
        else:  # Home team is away in this match
            if away_score > home_score:
                stats["home_wins"] += 1
            elif home_score > away_score:
                stats["away_wins"] += 1
            else:
                stats["draws"] += 1
        
        if home_score + away_score > 2.5:
            stats["over_2_5"] += 1
        if home_score + away_score > 3.5:
            stats["over_3_5"] += 1
        if home_score > 0 and away_score > 0:
            stats["both_teams_score"] += 1
    
    stats["avg_goals"] = round(total_goals / len(h2h_matches), 2)
    stats["over_2_5_pct"] = round(stats["over_2_5"] / len(h2h_matches) * 100, 1)
    stats["over_3_5_pct"] = round(stats["over_3_5"] / len(h2h_matches) * 100, 1)
    stats["both_teams_score_pct"] = round(stats["both_teams_score"] / len(h2h_matches) * 100, 1)
    
    return stats

# ============ MAIN APP LAYOUT ============
# Two equal columns
col1, col2 = st.columns([1, 1])

with col1:
    raw_input = st.text_area("Paste match data (with dates/times - will be cleaned automatically)", 
                            height=200,
                            placeholder="Paste your messy data here, e.g.:\nAston V\n1\n2\nSheffield U\nEnglish League WEEK 17 - #2025122312\n3:58 pm\nSouthampton\n2\n0\nEverton\n...")
    
    parse_clicked = st.button("Parse and Add")

def clean_and_parse_matches(text: str):
    """Clean messy input data and parse matches"""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    
    cleaned_lines = []
    for line in lines:
        skip_patterns = [
            r'WEEK \d+',
            r'English League',
            r'\d{1,2}:\d{2}\s*(?:am|pm)',
            r'#\d+',
            r'^\d{8,}$',
        ]
        
        is_team = line in VALID_TEAMS
        is_score = line.isdigit() and 0 <= int(line) <= 20
        
        if is_team or is_score:
            cleaned_lines.append(line)
        else:
            skip = False
            for pattern in skip_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    skip = True
                    break
            if not skip:
                for team in VALID_TEAMS:
                    if team in line:
                        cleaned_lines.append(team)
                        break
    
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
        
        if home_team not in VALID_TEAMS:
            errors.append(f"Invalid home team: {home_team}")
        if away_team not in VALID_TEAMS:
            errors.append(f"Invalid away team: {away_team}")
        if not home_score_raw.isdigit():
            errors.append(f"Non-numeric home score: {home_score_raw}")
        if not away_score_raw.isdigit():
            errors.append(f"Non-numeric away score: {away_score_raw}")
        
        if home_team in VALID_TEAMS and away_team in VALID_TEAMS and home_score_raw.isdigit() and away_score_raw.isdigit():
            matches.append([home_team, int(home_score_raw), int(away_score_raw), away_team])
        
        i += 4
    
    matches.reverse()
    return matches, errors, cleaned_lines

if parse_clicked and raw_input.strip():
    new_matches, errors, cleaned_lines = clean_and_parse_matches(raw_input)
    
    if new_matches:
        st.info(f"✅ Parsed {len(new_matches)} matches")
    
    if errors:
        st.error(f"❌ {len(errors)} errors")
        if new_matches:
            st.warning(f"Adding {len(new_matches)} valid matches")
    
    # Process matches
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
        
        # Update team stats for ranking
        # Home team
        st.session_state.team_stats[home_team]["P"] += 1
        st.session_state.team_stats[home_team]["GF"] += home_score
        st.session_state.team_stats[home_team]["GA"] += away_score
        st.session_state.team_stats[home_team]["GD"] = st.session_state.team_stats[home_team]["GF"] - st.session_state.team_stats[home_team]["GA"]
        
        # Away team
        st.session_state.team_stats[away_team]["P"] += 1
        st.session_state.team_stats[away_team]["GF"] += away_score
        st.session_state.team_stats[away_team]["GA"] += home_score
        st.session_state.team_stats[away_team]["GD"] = st.session_state.team_stats[away_team]["GF"] - st.session_state.team_stats[away_team]["GA"]
        
        # Update points and results
        if home_score > away_score:  # Home win
            st.session_state.team_stats[home_team]["W"] += 1
            st.session_state.team_stats[home_team]["Pts"] += 3
            st.session_state.team_stats[home_team]["Form"].append("W")
            
            st.session_state.team_stats[away_team]["L"] += 1
            st.session_state.team_stats[away_team]["Form"].append("L")
            
            result = "Home Win"
        elif away_score > home_score:  # Away win
            st.session_state.team_stats[away_team]["W"] += 1
            st.session_state.team_stats[away_team]["Pts"] += 3
            st.session_state.team_stats[away_team]["Form"].append("W")
            
            st.session_state.team_stats[home_team]["L"] += 1
            st.session_state.team_stats[home_team]["Form"].append("L")
            
            result = "Away Win"
        else:  # Draw
            st.session_state.team_stats[home_team]["D"] += 1
            st.session_state.team_stats[home_team]["Pts"] += 1
            st.session_state.team_stats[home_team]["Form"].append("D")
            
            st.session_state.team_stats[away_team]["D"] += 1
            st.session_state.team_stats[away_team]["Pts"] += 1
            st.session_state.team_stats[away_team]["Form"].append("D")
            
            result = "Draw"
        
        # Keep only last 5 form results
        if len(st.session_state.team_stats[home_team]["Form"]) > 5:
            st.session_state.team_stats[home_team]["Form"].pop(0)
        if len(st.session_state.team_stats[away_team]["Form"]) > 5:
            st.session_state.team_stats[away_team]["Form"].pop(0)
        
        # Get current rankings
        home_rank = get_team_position(home_team)
        away_rank = get_team_position(away_team)
        
        # Calculate derived statistics
        goal_difference = home_score - away_score
        both_teams_scored = "Yes" if home_score > 0 and away_score > 0 else "No"
        over_under = "Over 2.5" if total_goals > 2.5 else "Under 2.5"
        
        # Add match data
        st.session_state.match_data.append([
            match_id,                      # Match_ID
            home_team,                     # Home_Team
            home_score,                    # Home_Score
            away_score,                    # Away_Score
            away_team,                     # Away_Team
            total_goals,                   # Total_Goals
            total_g_display,               # Total-G
            result,                        # Match_Result
            goal_difference,               # Goal_Difference
            both_teams_scored,             # Both_Teams_Scored
            over_under,                    # Over_Under
            home_rank,                     # Home_Rank
            away_rank,                     # Away_Rank
            st.session_state.home_counters[home_team],           # Games_Since_Last_Won_Home
            st.session_state.away_counters[away_team],           # Games_Since_Last_Won_Away
            st.session_state.ha_counters[home_team],             # Games_Since_Last_Won_Combined_Home
            st.session_state.ha_counters[away_team],             # Games_Since_Last_Won_Combined_Away
            st.session_state.status3_counters[home_team],        # Games_Since_Last_3Goals_Home
            st.session_state.status3_counters[away_team],        # Games_Since_Last_3Goals_Away
            f"{home_team}: {st.session_state.ha_counters[home_team]} | {away_team}: {st.session_state.ha_counters[away_team]}",
            f"{home_team}: {st.session_state.status3_counters[home_team]} | {away_team}: {st.session_state.status3_counters[away_team]}"
        ])
    
    if new_matches:
        st.success(f"✅ Added {len(new_matches)} matches")

# ============ DISPLAY SECTION ============
# Display summary in right column - Only if match_data exists
if "match_data" in st.session_state and st.session_state.match_data:
    # Define column names
    column_names = [
        "Match_ID", "Home_Team", "Home_Score", "Away_Score", "Away_Team",
        "Total_Goals", "Total-G", "Match_Result", "Goal_Difference", 
        "Both_Teams_Scored", "Over_Under", "Home_Rank", "Away_Rank",
        "Games_Since_Last_Won_Home", "Games_Since_Last_Won_Away",
        "Games_Since_Last_Won_Combined_Home", "Games_Since_Last_Won_Combined_Away",
        "Games_Since_Last_3Goals_Home", "Games_Since_Last_3Goals_Away",
        "F!=4HA", "Status3"
    ]
    
    df = pd.DataFrame(st.session_state.match_data, columns=column_names)

    with col2:
        st.subheader("📌 Last 10 Match Summary")
        
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
            home_rank = row["Home_Rank"]
            away_rank = row["Away_Rank"]
            
            left = f"{home_rank}. {home} [{status3_home}:{won_home}]"
            right = f"{away_rank}. {away} [{status3_away}:{won_away}]"
            st.markdown(f"<div style='font-size:14px; margin-bottom:5px;'>{left} — {right}</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # Display League Table
        st.subheader("🏆 Current League Table")
        
        # Calculate rankings
        rankings = calculate_rankings()
        
        # Create league table DataFrame
        table_data = []
        for pos, (team, stats) in enumerate(rankings, 1):
            table_data.append([
                pos,
                team,
                stats["P"],
                stats["W"],
                stats["D"],
                stats["L"],
                stats["GF"],
                stats["GA"],
                stats["GD"],
                stats["Pts"],
                " ".join(stats["Form"][-5:])  # Last 5 form
            ])
        
        league_df = pd.DataFrame(
            table_data,
            columns=["Pos", "Team", "P", "W", "D", "L", "GF", "GA", "GD", "Pts", "Form"]
        )
        
        # Display the table
        st.dataframe(league_df, use_container_width=True, height=400)
        
        # Download options
        st.subheader("📥 Download Options")
        
        # Option 1: Full match data with rankings
        csv_full = df.to_csv(index=False)
        st.download_button(
            "📋 Download Full CSV (with Rankings)",
            data=csv_full,
            file_name="football_results_with_rankings.csv",
            mime="text/csv"
        )
        
        # Option 2: League table only
        csv_league = league_df.to_csv(index=False)
        st.download_button(
            "🏆 Download League Table",
            data=csv_league,
            file_name="league_table.csv",
            mime="text/csv"
        )
        
        # Option 3: Original format
        df_original = df[["Home_Team", "Home_Score", "Away_Score", "Away_Team", 
                         "Total-G", "Games_Since_Last_Won_Home", 
                         "Games_Since_Last_Won_Away", "F!=4HA", "Status3"]]
        df_original.columns = ["Home Team", "Home Score", "Away Score", "Away Team", 
                              "Total-G", "F<4H", "F<4A", "F!=4HA", "Status3"]
        csv_original = df_original.to_csv(index=False)
        st.download_button(
            "🔄 Download Original Format",
            data=csv_original,
            file_name="football_results_original.csv",
            mime="text/csv"
        )

        # Clear button
        if st.button("🗑️ Clear all data"):
            st.session_state.match_data = []
            st.session_state.home_counters = {team: 0 for team in VALID_TEAMS}
            st.session_state.away_counters = {team: 0 for team in VALID_TEAMS}
            st.session_state.ha_counters = {team: 0 for team in VALID_TEAMS}
            st.session_state.status3_counters = {team: 0 for team in VALID_TEAMS}
            st.session_state.team_stats = {
                team: {"P": 0, "W": 0, "D": 0, "L": 0, "GF": 0, "GA": 0, "GD": 0, "Pts": 0, "Form": []}
                for team in VALID_TEAMS
            }
            st.session_state.match_counter = 1
            st.rerun()

# ============ ANALYTICS SECTION ============
# Only show analytics if we have match data
if "match_data" in st.session_state and st.session_state.match_data:
    st.markdown("---")
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["📊 Match Predictor", "🏆 League Insights"])
    
    with tab1:
        st.subheader("📊 Match Predictor & Analytics")
        
        # Create two columns for team selection
        pred_col1, pred_col2 = st.columns(2)
        
        with pred_col1:
            home_team = st.selectbox("Select Home Team", sorted(VALID_TEAMS), key="home_select")
        
        with pred_col2:
            away_team = st.selectbox("Select Away Team", sorted(VALID_TEAMS), key="away_select")
        
        if home_team == away_team:
            st.warning("Please select two different teams")
        else:
            # Calculate metrics
            team_metrics = calculate_team_metrics()
            
            # Get predictions
            predictions = predict_match_outcome(home_team, away_team, team_metrics)
            
            # Get head-to-head stats
            h2h_stats = create_head_to_head_stats(home_team, away_team)
            
            # Display predictions
            st.markdown("---")
            st.subheader("🎯 Match Predictions")
            
            # Create three columns for outcome probabilities
            prob_col1, prob_col2, prob_col3 = st.columns(3)
            
            with prob_col1:
                st.metric("🏠 Home Win", f"{predictions['home_win']}%")
                st.progress(predictions['home_win'] / 100)
            
            with prob_col2:
                st.metric("🤝 Draw", f"{predictions['draw']}%")
                st.progress(predictions['draw'] / 100)
            
            with prob_col3:
                st.metric("✈️ Away Win", f"{predictions['away_win']}%")
                st.progress(predictions['away_win'] / 100)
            
            # Display over/under probabilities
            st.markdown("---")
            st.subheader("⚽ Goal Markets")
            
            goal_col1, goal_col2, goal_col3, goal_col4 = st.columns(4)
            
            with goal_col1:
                st.metric("Over 2.5 Goals", f"{predictions['over_2_5']}%")
                st.progress(predictions['over_2_5'] / 100)
            
            with goal_col2:
                st.metric("Over 3.5 Goals", f"{predictions['over_3_5']}%")
                st.progress(predictions['over_3_5'] / 100)
            
            with goal_col3:
                st.metric("Over 4.5 Goals", f"{predictions['over_4_5']}%")
                st.progress(predictions['over_4_5'] / 100)
            
            with goal_col4:
                st.metric("Both Teams Score", f"{predictions['both_teams_score']}%")
                st.progress(predictions['both_teams_score'] / 100)
            
            # Expected goals
            st.metric("📈 Expected Total Goals", predictions['expected_goals'])
            st.caption(f"Predicted Score: {predictions['predicted_score']}")
            
            # Head-to-head statistics
            if h2h_stats:
                st.markdown("---")
                st.subheader("🤼 Head-to-Head History")
                
                h2h_col1, h2h_col2, h2h_col3, h2h_col4 = st.columns(4)
                
                with h2h_col1:
                    st.metric("Matches Played", h2h_stats["total_matches"])
                
                with h2h_col2:
                    st.metric(f"{home_team} Wins", h2h_stats["home_wins"])
                
                with h2h_col3:
                    st.metric(f"{away_team} Wins", h2h_stats["away_wins"])
                
                with h2h_col4:
                    st.metric("Draws", h2h_stats["draws"])
                
                # Show percentages
                st.markdown("**Historical Trends:**")
                trend_col1, trend_col2, trend_col3 = st.columns(3)
                
                with trend_col1:
                    st.metric("Over 2.5 Goals", f"{h2h_stats['over_2_5_pct']}%")
                
                with trend_col2:
                    st.metric("Over 3.5 Goals", f"{h2h_stats['over_3_5_pct']}%")
                
                with trend_col3:
                    st.metric("Both Teams Scored", f"{h2h_stats['both_teams_score_pct']}%")
                
                st.caption(f"Average Goals per Match: {h2h_stats['avg_goals']}")
            else:
                st.info("No head-to-head history available for these teams")
            
            # Team comparison
            st.markdown("---")
            st.subheader("📊 Team Comparison")
            
            compare_data = {
                "Metric": ["Win Rate", "Draw Rate", "Loss Rate", "Avg Goals For", "Avg Goals Against", 
                          "Points per Game", "Current Form"],
                home_team: [
                    f"{team_metrics[home_team]['win_rate']}%",
                    f"{team_metrics[home_team]['draw_rate']}%",
                    f"{team_metrics[home_team]['loss_rate']}%",
                    team_metrics[home_team]['avg_gf'],
                    team_metrics[home_team]['avg_ga'],
                    team_metrics[home_team]['points_per_game'],
                    " ".join(team_metrics[home_team]['form'])
                ],
                away_team: [
                    f"{team_metrics[away_team]['win_rate']}%",
                    f"{team_metrics[away_team]['draw_rate']}%",
                    f"{team_metrics[away_team]['loss_rate']}%",
                    team_metrics[away_team]['avg_gf'],
                    team_metrics[away_team]['avg_ga'],
                    team_metrics[away_team]['points_per_game'],
                    " ".join(team_metrics[away_team]['form'])
                ]
            }
            
            compare_df = pd.DataFrame(compare_data)
            st.dataframe(compare_df, use_container_width=True, hide_index=True)
    
    with tab2:
        st.subheader("🏆 League Insights")
        
        # Calculate rankings
        rankings = calculate_rankings()
        
        # Create league table DataFrame
        table_data = []
        for pos, (team, stats) in enumerate(rankings, 1):
            table_data.append([
                pos, team, stats["P"], stats["W"], stats["D"], stats["L"],
                stats["GF"], stats["GA"], stats["GD"], stats["Pts"], " ".join(stats["Form"][-5:])
            ])
        
        league_df = pd.DataFrame(
            table_data,
            columns=["Pos", "Team", "P", "W", "D", "L", "GF", "GA", "GD", "Pts", "Form"]
        )
        
        # League insights
        st.subheader("📊 League Statistics")
        
        # Top performers
        top_teams = league_df.head(5)
        bottom_teams = league_df.tail(5)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🔥 Top 5 Teams**")
            for _, row in top_teams.iterrows():
                st.write(f"{row['Pos']}. {row['Team']} - {row['Pts']} pts (GD: {row['GD']})")
        
        with col2:
            st.markdown("**⚠️ Relegation Zone**")
            for _, row in bottom_teams.iterrows():
                st.write(f"{row['Pos']}. {row['Team']} - {row['Pts']} pts (GD: {row['GD']})")
        
        # Key metrics
        st.subheader("🎯 Key Performance Indicators")
        
        metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)
        
        with metrics_col1:
            best_attack = league_df.loc[league_df['GF'].idxmax()]
            st.metric("Best Attack", best_attack['Team'], f"{best_attack['GF']} goals")
        
        with metrics_col2:
            best_defense = league_df.loc[league_df['GA'].idxmin()]
            st.metric("Best Defense", best_defense['Team'], f"{best_defense['GA']} conceded")
        
        with metrics_col3:
            best_gd = league_df.loc[league_df['GD'].idxmax()]
            st.metric("Best Goal Difference", best_gd['Team'], f"+{best_gd['GD']}")
        
        with metrics_col4:
            # Find team with best form
            best_form = max(st.session_state.team_stats.items(), 
                          key=lambda x: sum(1 for r in x[1]["Form"][-5:] if r == "W"))
            wins = sum(1 for r in best_form[1]["Form"][-5:] if r == "W")
            st.metric("Best Form", best_form[0], f"{wins}W in last 5")
