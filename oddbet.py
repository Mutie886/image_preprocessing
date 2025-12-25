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

st.set_page_config(page_title="Football Results Dashboard", page_icon="⚽", layout="wide")
st.title("⚽ Complete Football Analytics Dashboard")

# ============ SESSION STATE INITIALIZATION ============
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
            "P": 0, "W": 0, "D": 0, "L": 0, "GF": 0, "GA": 0, 
            "GD": 0, "Pts": 0, "Form": []
        }
        for team in VALID_TEAMS
    }
if "match_counter" not in st.session_state:
    st.session_state.match_counter = 1
if "season_reset_done" not in st.session_state:
    st.session_state.season_reset_done = False

# ============ HELPER FUNCTIONS ============
def reset_league_for_new_season():
    """Reset all team statistics and match data for a new season"""
    st.session_state.match_data = []
    st.session_state.home_counters = {team: 0 for team in VALID_TEAMS}
    st.session_state.away_counters = {team: 0 for team in VALID_TEAMS}
    st.session_state.ha_counters = {team: 0 for team in VALID_TEAMS}
    st.session_state.status3_counters = {team: 0 for team in VALID_TEAMS}
    st.session_state.team_stats = {
        team: {
            "P": 0, "W": 0, "D": 0, "L": 0,
            "GF": 0, "GA": 0, "GD": 0, "Pts": 0, "Form": []
        }
        for team in VALID_TEAMS
    }
    st.session_state.match_counter = 1
    st.session_state.season_reset_done = True
    return True

def check_and_reset_season():
    """Check if any team has reached 38 matches and reset if needed"""
    for team in VALID_TEAMS:
        if st.session_state.team_stats[team]["P"] >= 38:
            reset_league_for_new_season()
            return True
    return False

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
        
        # Calculate actual Both Teams Scored rate from match data
        bts_matches = 0
        for match in st.session_state.match_data:
            if match[1] == team and match[2] > 0 and match[3] > 0:
                bts_matches += 1
            elif match[4] == team and match[2] > 0 and match[3] > 0:
                bts_matches += 1
        
        bts_rate = (bts_matches / total_matches * 100) if total_matches > 0 else 0
        
        metrics[team] = {
            "win_rate": round(win_rate, 1),
            "draw_rate": round(draw_rate, 1),
            "loss_rate": round(loss_rate, 1),
            "avg_gf": round(avg_gf, 2),
            "avg_ga": round(avg_ga, 2),
            "bts_rate": round(bts_rate, 1),
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
    
    # Adjust for home advantage
    home_advantage = 15  # percentage points
    home_win_prob += home_advantage
    away_win_prob -= home_advantage * 0.5
    
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
    
    # Both teams score probability
    both_teams_score_prob = (home_metrics["bts_rate"] + away_metrics["bts_rate"]) / 2
    
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
        
        if match[1] == home_team:
            if home_score > away_score:
                stats["home_wins"] += 1
            elif away_score > home_score:
                stats["away_wins"] += 1
            else:
                stats["draws"] += 1
        else:
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

def generate_betting_recommendations(home_team, away_team, predictions, team_metrics, h2h_stats):
    """Generate betting recommendations based on analysis"""
    
    home_metrics = team_metrics[home_team]
    away_metrics = team_metrics[away_team]
    
    recommendations = {
        "best_bets": [],
        "avoid_bets": [],
        "insights": []
    }
    
    # 1. Both Teams to Score analysis
    bts_prob = predictions['both_teams_score']
    if bts_prob >= 50:
        reason = f"{home_team} leaks goals ({home_metrics['avg_ga']} GA/game) | "
        reason += f"{away_team} can score ({away_metrics['avg_gf']} GF/game)"
        if h2h_stats and h2h_stats['both_teams_score_pct'] >= 70:
            reason += f" | Historical: {h2h_stats['both_teams_score_pct']}% both teams scored"
        recommendations["best_bets"].append(("Both Teams to Score: YES", reason))
    else:
        recommendations["avoid_bets"].append("Both Teams to Score")
    
    # 2. Double Chance (Home Win or Draw)
    home_win_or_draw = predictions['home_win'] + predictions['draw']
    if home_win_or_draw >= 65:
        reason = f"{home_win_or_draw}% probability | Covers both likely outcomes"
        recommendations["best_bets"].append((f"{home_team} or Draw (Double Chance)", reason))
    
    # 3. Under/Over markets
    if predictions['over_2_5'] < 50:
        under_prob = 100 - predictions['over_2_5']
        reason = f"{under_prob}% probability | "
        reason += f"{away_team}'s defense ({away_metrics['avg_ga']} GA) considered"
        recommendations["best_bets"].append(("Under 2.5 Goals", reason))
    else:
        reason = f"{predictions['over_2_5']}% probability | High expected goals ({predictions['expected_goals']})"
        recommendations["best_bets"].append(("Over 2.5 Goals", reason))
    
    # 4. Clean Sheet analysis
    if home_metrics['avg_ga'] > 1.4:
        reason = f"Poor defense ({home_metrics['avg_ga']} GA/game) | Rarely keeps clean sheets"
        recommendations["avoid_bets"].append(f"{home_team} to Win to Nil (Clean Sheet)")
    
    # 5. High over markets
    if predictions['over_3_5'] < 25:
        reason = f"Only {predictions['over_3_5']}% probability | Low scoring teams"
        recommendations["avoid_bets"].append("Over 3.5 Goals")
    
    if predictions['over_4_5'] < 10:
        recommendations["avoid_bets"].append("Over 4.5 Goals")
    
    # Add insights
    if home_metrics['avg_gf'] > away_metrics['avg_gf']:
        recommendations["insights"].append(f"{home_team} has better attack ({home_metrics['avg_gf']} vs {away_metrics['avg_gf']} GF/game)")
    else:
        recommendations["insights"].append(f"{away_team} has better attack ({away_metrics['avg_gf']} vs {home_metrics['avg_gf']} GF/game)")
    
    if away_metrics['avg_ga'] < home_metrics['avg_ga']:
        recommendations["insights"].append(f"{away_team} has better defense ({away_metrics['avg_ga']} vs {home_metrics['avg_ga']} GA/game)")
    else:
        recommendations["insights"].append(f"{home_team} has better defense ({home_metrics['avg_ga']} vs {away_metrics['avg_ga']} GA/game)")
    
    if h2h_stats and h2h_stats['total_matches'] > 0:
        if h2h_stats['home_wins'] == 0 and h2h_stats['away_wins'] == 0:
            recommendations["insights"].append(f"Historical trend: {h2h_stats['draws']}/{h2h_stats['total_matches']} matches ended in draw")
        elif h2h_stats['home_wins'] > h2h_stats['away_wins'] * 2:
            recommendations["insights"].append(f"Strong historical advantage for {home_team}")
        elif h2h_stats['away_wins'] > h2h_stats['home_wins'] * 2:
            recommendations["insights"].append(f"Strong historical advantage for {away_team}")
    
    return recommendations

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

# ============ MAIN DASHBOARD LAYOUT ============

# Check for season reset
if check_and_reset_season() and not st.session_state.season_reset_done:
    st.session_state.season_reset_done = False

# Top section: Data Input
st.header("📥 Data Input & Processing")
col1, col2 = st.columns([2, 1])

with col1:
    raw_input = st.text_area(
        "**Paste match data** (with dates/times - will be cleaned automatically)", 
        height=150,
        placeholder="Paste your messy data here, e.g.:\nAston V\n1\n2\nSheffield U\nEnglish League WEEK 17 - #2025122312\n3:58 pm\nSouthampton\n2\n0\nEverton\n..."
    )
    
    parse_clicked = st.button("🚀 Parse and Add Matches", type="primary")

with col2:
    st.markdown("### 🛠️ Quick Actions")
    if st.button("🔄 Manual Season Reset", help="Reset all data for a new season"):
        if reset_league_for_new_season():
            st.rerun()
    
    if st.button("🗑️ Clear All Data", help="Remove all match data"):
        reset_league_for_new_season()
        st.rerun()
    
    # Display season status
    max_matches = max([st.session_state.team_stats[team]["P"] for team in VALID_TEAMS])
    st.metric("📈 Current Season Progress", f"{max_matches}/38 matches", 
              help="Season resets automatically when any team reaches 38 matches")

# Process input data
if parse_clicked and raw_input.strip():
    new_matches, errors, cleaned_lines = clean_and_parse_matches(raw_input)
    
    if new_matches:
        st.info(f"✅ Successfully parsed {len(new_matches)} matches")
    
    if errors:
        st.error(f"❌ Found {len(errors)} parsing errors")
        if new_matches:
            st.warning(f"But found {len(new_matches)} valid matches. Adding them...")
    
    # Process matches
    for home_team, home_score, away_score, away_team in new_matches:
        # Check season reset
        if st.session_state.team_stats[home_team]["P"] >= 38 or st.session_state.team_stats[away_team]["P"] >= 38:
            reset_league_for_new_season()
        
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
        
        # Update team stats
        st.session_state.team_stats[home_team]["P"] += 1
        st.session_state.team_stats[home_team]["GF"] += home_score
        st.session_state.team_stats[home_team]["GA"] += away_score
        st.session_state.team_stats[home_team]["GD"] = st.session_state.team_stats[home_team]["GF"] - st.session_state.team_stats[home_team]["GA"]
        
        st.session_state.team_stats[away_team]["P"] += 1
        st.session_state.team_stats[away_team]["GF"] += away_score
        st.session_state.team_stats[away_team]["GA"] += home_score
        st.session_state.team_stats[away_team]["GD"] = st.session_state.team_stats[away_team]["GF"] - st.session_state.team_stats[away_team]["GA"]
        
        # Update points and results
        if home_score > away_score:
            st.session_state.team_stats[home_team]["W"] += 1
            st.session_state.team_stats[home_team]["Pts"] += 3
            st.session_state.team_stats[home_team]["Form"].append("W")
            
            st.session_state.team_stats[away_team]["L"] += 1
            st.session_state.team_stats[away_team]["Form"].append("L")
            
            result = "Home Win"
        elif away_score > home_score:
            st.session_state.team_stats[away_team]["W"] += 1
            st.session_state.team_stats[away_team]["Pts"] += 3
            st.session_state.team_stats[away_team]["Form"].append("W")
            
            st.session_state.team_stats[home_team]["L"] += 1
            st.session_state.team_stats[home_team]["Form"].append("L")
            
            result = "Away Win"
        else:
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
        
        # Add match data
        st.session_state.match_data.append([
            match_id, home_team, home_score, away_score, away_team,
            total_goals, total_g_display, result,
            home_score - away_score,
            "Yes" if home_score > 0 and away_score > 0 else "No",
            "Over 2.5" if total_goals > 2.5 else "Under 2.5",
            get_team_position(home_team), get_team_position(away_team),
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
        st.success(f"✅ Added {len(new_matches)} matches to the database")
        st.rerun()

# ============ MAIN DASHBOARD SECTIONS ============
if "match_data" in st.session_state and st.session_state.match_data:
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
    
    # Create three main columns for the dashboard
    st.markdown("---")
    st.header("📊 Live Dashboard Overview")
    
    # Row 1: League Table and Recent Matches
    col_league, col_recent = st.columns([2, 1])
    
    with col_league:
        st.subheader("🏆 Current League Table")
        rankings = calculate_rankings()
        
        table_data = []
        for pos, (team, stats) in enumerate(rankings, 1):
            table_data.append([
                pos, team, stats["P"], stats["W"], stats["D"], stats["L"],
                stats["GF"], stats["GA"], stats["GD"], stats["Pts"], 
                " ".join(stats["Form"][-5:]) if stats["Form"] else "No matches"
            ])
        
        league_df = pd.DataFrame(
            table_data,
            columns=["Pos", "Team", "P", "W", "D", "L", "GF", "GA", "GD", "Pts", "Form"]
        )
        
        st.dataframe(league_df, use_container_width=True, height=500)
        
        # Quick league insights
        st.subheader("📈 League Insights")
        insight_col1, insight_col2, insight_col3, insight_col4 = st.columns(4)
        
        with insight_col1:
            best_attack = league_df.loc[league_df['GF'].idxmax()]
            st.metric("Best Attack", best_attack['Team'], f"{best_attack['GF']} GF")
        
        with insight_col2:
            best_defense = league_df.loc[league_df['GA'].idxmin()]
            st.metric("Best Defense", best_defense['Team'], f"{best_defense['GA']} GA")
        
        with insight_col3:
            best_gd = league_df.loc[league_df['GD'].idxmax()]
            st.metric("Best GD", best_gd['Team'], f"+{best_gd['GD']}")
        
        with insight_col4:
            top_scorer = league_df.loc[league_df['Pts'].idxmax()]
            st.metric("League Leader", top_scorer['Team'], f"{top_scorer['Pts']} Pts")
    
    with col_recent:
        st.subheader("🔄 Recent Match Summary")
        
        st.markdown("""
            <div style="background-color:black; color:white; padding:15px; border-radius:10px; border:2px solid #444;">
        """, unsafe_allow_html=True)
        
        if len(st.session_state.match_data) > 0:
            recent_matches = st.session_state.match_data[-10:]  # Last 10 matches
            for match in recent_matches:
                home = match[1]
                away = match[4]
                home_score = match[2]
                away_score = match[3]
                home_rank = match[11] if len(match) > 11 else "?"
                away_rank = match[12] if len(match) > 12 else "?"
                
                st.markdown(
                    f"<div style='font-size:14px; margin-bottom:8px; padding:5px; border-bottom:1px solid #333;'>"
                    f"<strong>{home_rank}. {home}</strong> {home_score}-{away_score} <strong>{away}</strong> ({away_rank}.)"
                    f"</div>", 
                    unsafe_allow_html=True
                )
        else:
            st.markdown("<div style='color:#888; text-align:center;'>No matches yet</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Quick stats
        st.subheader("📋 Quick Stats")
        total_matches = len(st.session_state.match_data)
        avg_goals = df["Total_Goals"].mean() if total_matches > 0 else 0
        home_wins = len(df[df["Match_Result"] == "Home Win"])
        away_wins = len(df[df["Match_Result"] == "Away Win"])
        draws = len(df[df["Match_Result"] == "Draw"])
        
        st.metric("Total Matches", total_matches)
        st.metric("Avg Goals/Match", round(avg_goals, 2))
        st.metric("Home Wins / Draws / Away Wins", f"{home_wins} / {draws} / {away_wins}")
    
    # Row 2: Match Predictor
    st.markdown("---")
    st.header("🎯 Match Predictor & Analytics")
    
    pred_col1, pred_col2 = st.columns(2)
    
    with pred_col1:
        home_team = st.selectbox("**Select Home Team**", sorted(VALID_TEAMS), key="home_select")
    
    with pred_col2:
        away_team = st.selectbox("**Select Away Team**", sorted(VALID_TEAMS), key="away_select")
    
    if home_team == away_team:
        st.warning("⚠️ Please select two different teams")
    else:
        # Calculate predictions
        team_metrics = calculate_team_metrics()
        predictions = predict_match_outcome(home_team, away_team, team_metrics)
        h2h_stats = create_head_to_head_stats(home_team, away_team)
        
        # Display predictions in columns
        st.subheader("📈 Match Predictions")
        
        # Outcome probabilities
        outcome_col1, outcome_col2, outcome_col3 = st.columns(3)
        
        with outcome_col1:
            st.metric("🏠 Home Win", f"{predictions['home_win']}%")
            st.progress(predictions['home_win'] / 100)
        
        with outcome_col2:
            st.metric("🤝 Draw", f"{predictions['draw']}%")
            st.progress(predictions['draw'] / 100)
        
        with outcome_col3:
            st.metric("✈️ Away Win", f"{predictions['away_win']}%")
            st.progress(predictions['away_win'] / 100)
        
        # Goal markets
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
        col_exp1, col_exp2 = st.columns(2)
        with col_exp1:
            st.metric("📊 Expected Total Goals", predictions['expected_goals'])
        with col_exp2:
            st.metric("🔮 Predicted Score", predictions['predicted_score'])
        
        # Head-to-head statistics
        if h2h_stats:
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
            
            # Historical trends
            st.markdown("**📊 Historical Trends:**")
            trend_col1, trend_col2, trend_col3 = st.columns(3)
            
            with trend_col1:
                st.metric("Over 2.5 Goals", f"{h2h_stats['over_2_5_pct']}%")
            
            with trend_col2:
                st.metric("Over 3.5 Goals", f"{h2h_stats['over_3_5_pct']}%")
            
            with trend_col3:
                st.metric("Both Teams Scored", f"{h2h_stats['both_teams_score_pct']}%")
            
            st.caption(f"Average Goals per Match: {h2h_stats['avg_goals']}")
        
        # Betting Recommendations
        st.markdown("---")
        st.subheader("💰 Betting Recommendations")
        
        recommendations = generate_betting_recommendations(
            home_team, away_team, predictions, team_metrics, h2h_stats
        )
        
        # Display recommendations in columns
        rec_col1, rec_col2 = st.columns(2)
        
        with rec_col1:
            if recommendations["best_bets"]:
                st.markdown("#### ✅ **BEST BETS:**")
                for bet, reason in recommendations["best_bets"]:
                    with st.expander(f"**{bet}**", expanded=False):
                        st.write(f"**Why:** {reason}")
        
        with rec_col2:
            if recommendations["avoid_bets"]:
                st.markdown("#### ❌ **AVOID:**")
                for bet in recommendations["avoid_bets"]:
                    st.write(f"- {bet}")
        
        # Key Insights
        if recommendations["insights"]:
            st.markdown("#### 📊 **KEY INSIGHTS:**")
            insight_text = ""
            for insight in recommendations["insights"]:
                insight_text += f"• {insight}\n"
            st.info(insight_text)
        
        # Team Comparison
        st.markdown("---")
        st.subheader("📋 Team Comparison")
        
        compare_data = {
            "Metric": ["Win Rate", "Draw Rate", "Loss Rate", "Avg Goals For", 
                      "Avg Goals Against", "Points per Game", "Current Form"],
            home_team: [
                f"{team_metrics[home_team]['win_rate']}%",
                f"{team_metrics[home_team]['draw_rate']}%",
                f"{team_metrics[home_team]['loss_rate']}%",
                team_metrics[home_team]['avg_gf'],
                team_metrics[home_team]['avg_ga'],
                team_metrics[home_team]['points_per_game'],
                " ".join(team_metrics[home_team]['form']) if team_metrics[home_team]['form'] else "No form"
            ],
            away_team: [
                f"{team_metrics[away_team]['win_rate']}%",
                f"{team_metrics[away_team]['draw_rate']}%",
                f"{team_metrics[away_team]['loss_rate']}%",
                team_metrics[away_team]['avg_gf'],
                team_metrics[away_team]['avg_ga'],
                team_metrics[away_team]['points_per_game'],
                " ".join(team_metrics[away_team]['form']) if team_metrics[away_team]['form'] else "No form"
            ]
        }
        
        compare_df = pd.DataFrame(compare_data)
        st.dataframe(compare_df, use_container_width=True, hide_index=True)
    
    # Row 3: Data Export and Management
    st.markdown("---")
    st.header("💾 Data Management & Export")
    
    exp_col1, exp_col2, exp_col3 = st.columns(3)
    
    with exp_col1:
        # Export match data
        csv_full = df.to_csv(index=False)
        st.download_button(
            "📋 Download Full Match Data",
            data=csv_full,
            file_name="football_results_complete.csv",
            mime="text/csv",
            help="Includes all matches with rankings and predictions"
        )
    
    with exp_col2:
        # Export league table
        csv_league = league_df.to_csv(index=False)
        st.download_button(
            "🏆 Download League Table",
            data=csv_league,
            file_name="current_league_table.csv",
            mime="text/csv",
            help="Current league standings only"
        )
    
    with exp_col3:
        # Export predictions
        predictions_data = {
            "Home Team": [home_team],
            "Away Team": [away_team],
            "Home Win %": [predictions['home_win']],
            "Draw %": [predictions['draw']],
            "Away Win %": [predictions['away_win']],
            "Over 2.5 %": [predictions['over_2_5']],
            "Over 3.5 %": [predictions['over_3_5']],
            "Both Teams Score %": [predictions['both_teams_score']],
            "Expected Goals": [predictions['expected_goals']],
            "Predicted Score": [predictions['predicted_score']]
        }
        predictions_df = pd.DataFrame(predictions_data)
        csv_predictions = predictions_df.to_csv(index=False)
        st.download_button(
            "🎯 Download Predictions",
            data=csv_predictions,
            file_name=f"predictions_{home_team}_vs_{away_team}.csv",
            mime="text/csv",
            help="Current match predictions only"
        )
    
    # Season reset warning
    max_played = max([st.session_state.team_stats[team]["P"] for team in VALID_TEAMS])
    if max_played >= 35:
        st.warning(f"⚠️ **Season End Approaching**: Teams have played up to {max_played}/38 matches. "
                  f"The league will reset automatically when any team reaches 38 matches.")

else:
    # Welcome message when no data exists
    st.markdown("---")
    st.subheader("🚀 Getting Started")
    
    col_welcome1, col_welcome2 = st.columns(2)
    
    with col_welcome1:
        st.markdown("""
        ### 📝 How to use this dashboard:
        1. **Paste match data** in the text area above
        2. Click **"Parse and Add Matches"** to process
        3. View **live league table** and statistics
        4. Use the **Match Predictor** for analytics
        5. **Download data** for further analysis
        
        ### 🔄 Automatic Season Management:
        - League resets automatically after 38 matches
        - All data clears for a new season
        - Manual reset button available
        """)
    
    with col_welcome2:
        st.markdown("""
        ### 📊 What you'll see:
        - **Live League Table** with rankings
        - **Match Predictions** with probabilities
        - **Betting Recommendations** based on data
        - **Head-to-Head Statistics**
        - **Team Comparison** metrics
        - **Data Export** options
        
        ### 💡 Tips:
        - Use consistent team names from the list
        - Data format: Team, Score, Score, Team
        - The cleaner removes dates, times, and league info
        """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; font-size: 0.9em;'>"
    "⚽ Football Analytics Dashboard • Automatic 38-match season reset • Live predictions and recommendations"
    "</div>",
    unsafe_allow_html=True
)
