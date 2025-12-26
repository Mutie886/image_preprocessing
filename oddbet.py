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

# Mobile-optimized layout
st.set_page_config(page_title="Football Dashboard", page_icon="⚽", layout="wide")
st.markdown("<h1 style='font-size: 1.8rem; text-align: center;'>⚽ Football Analytics Dashboard</h1>", unsafe_allow_html=True)

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
if "season_number" not in st.session_state:
    st.session_state.season_number = 1

# ============ HELPER FUNCTIONS ============
def reset_league_for_new_season():
    """Reset team statistics for a new season while preserving match history"""
    st.session_state.team_stats = {
        team: {
            "P": 0, "W": 0, "D": 0, "L": 0,
            "GF": 0, "GA": 0, "GD": 0, "Pts": 0, "Form": []
        }
        for team in VALID_TEAMS
    }
    
    st.session_state.home_counters = {team: 0 for team in VALID_TEAMS}
    st.session_state.away_counters = {team: 0 for team in VALID_TEAMS}
    st.session_state.ha_counters = {team: 0 for team in VALID_TEAMS}
    st.session_state.status3_counters = {team: 0 for team in VALID_TEAMS}
    
    st.session_state.season_number += 1
    st.session_state.match_counter = 1
    
    return True

def check_and_reset_season():
    """Check if any team has reached 38 matches and reset if needed"""
    for team in VALID_TEAMS:
        if st.session_state.team_stats[team]["P"] >= 38:
            st.warning(f"⚠️ **Season {st.session_state.season_number} Complete!** Starting Season {st.session_state.season_number + 1}...")
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

def get_status3_color(status3_value):
    """Get color based on Status3 value"""
    if status3_value == 0:
        return "#FF6B6B"  # Red - just had 3-goal match
    elif status3_value <= 3:
        return "#4CAF50"  # Green - recently had 3-goal match
    elif status3_value <= 6:
        return "#FFD700"  # Yellow - medium since last 3-goal match
    else:
        return "#3498DB"  # Blue - long time since last 3-goal match

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
        
        bts_matches = 0
        for match in st.session_state.match_data:
            if (match[1] == team and match[2] > 0 and match[3] > 0) or \
               (match[4] == team and match[2] > 0 and match[3] > 0):
                bts_matches += 1
        
        bts_rate = (bts_matches / total_matches * 100) if total_matches > 0 else 0
        
        metrics[team] = {
            "win_rate": round(win_rate, 1),
            "draw_rate": round(draw_rate, 1),
            "loss_rate": round(loss_rate, 1),
            "avg_gf": round(avg_gf, 2),
            "avg_ga": round(avg_ga, 2),
            "bts_rate": min(100, round(bts_rate, 1)),
            "form": stats["Form"][-5:] if len(stats["Form"]) >= 5 else stats["Form"],
            "points_per_game": round(stats["Pts"] / total_matches, 2) if total_matches > 0 else 0,
        }
    
    return metrics

def predict_match_outcome(home_team, away_team, team_metrics):
    """Predict match outcome probabilities"""
    
    home_metrics = team_metrics[home_team]
    away_metrics = team_metrics[away_team]
    
    home_win_prob = home_metrics["win_rate"] * (1 - away_metrics["win_rate"] / 100)
    away_win_prob = away_metrics["win_rate"] * (1 - home_metrics["win_rate"] / 100)
    draw_prob = (home_metrics["draw_rate"] + away_metrics["draw_rate"]) / 2
    
    home_advantage = 15
    home_win_prob += home_advantage
    away_win_prob = max(0, away_win_prob - home_advantage * 0.5)
    
    total = home_win_prob + away_win_prob + draw_prob
    if total > 0:
        home_win_prob = (home_win_prob / total * 100)
        away_win_prob = (away_win_prob / total * 100)
        draw_prob = (draw_prob / total * 100)
    else:
        home_win_prob = draw_prob = away_win_prob = 33.3
    
    total_goals_expected = home_metrics["avg_gf"] + away_metrics["avg_gf"]
    
    over_2_5_prob = min(90, max(10, (total_goals_expected - 1.5) * 30))
    over_3_5_prob = min(70, max(5, (total_goals_expected - 2.5) * 25))
    over_4_5_prob = min(50, max(2, (total_goals_expected - 3.5) * 20))
    
    both_teams_score_prob = (home_metrics["bts_rate"] + away_metrics["bts_rate"]) / 2
    both_teams_score_prob = min(100, max(0, both_teams_score_prob))
    
    return {
        "home_win": min(100, max(0, round(home_win_prob, 1))),
        "away_win": min(100, max(0, round(away_win_prob, 1))),
        "draw": min(100, max(0, round(draw_prob, 1))),
        "over_2_5": min(100, max(0, round(over_2_5_prob, 1))),
        "over_3_5": min(100, max(0, round(over_3_5_prob, 1))),
        "over_4_5": min(100, max(0, round(over_4_5_prob, 1))),
        "both_teams_score": min(100, max(0, round(both_teams_score_prob, 1))),
        "expected_goals": round(total_goals_expected, 2),
        "predicted_score": f"{round(home_metrics['avg_gf'], 1)}-{round(away_metrics['avg_gf'], 1)}"
    }

def create_head_to_head_stats(home_team, away_team):
    """Calculate head-to-head statistics"""
    if len(st.session_state.match_data) == 0:
        return None
    
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
    stats["over_2_5_pct"] = min(100, round(stats["over_2_5"] / len(h2h_matches) * 100, 1))
    stats["over_3_5_pct"] = min(100, round(stats["over_3_5"] / len(h2h_matches) * 100, 1))
    stats["both_teams_score_pct"] = min(100, round(stats["both_teams_score"] / len(h2h_matches) * 100, 1))
    
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
    
    bts_prob = predictions['both_teams_score']
    if bts_prob >= 50:
        reason = f"{home_team} leaks goals ({home_metrics['avg_ga']} GA) | {away_team} scores ({away_metrics['avg_gf']} GF)"
        if h2h_stats and h2h_stats['both_teams_score_pct'] >= 70:
            reason += f" | History: {h2h_stats['both_teams_score_pct']}%"
        recommendations["best_bets"].append(("Both Teams Score: YES", reason))
    else:
        recommendations["avoid_bets"].append("Both Teams Score")
    
    home_win_or_draw = predictions['home_win'] + predictions['draw']
    if home_win_or_draw >= 65:
        recommendations["best_bets"].append((f"{home_team} or Draw", f"{home_win_or_draw}% probability"))
    
    if predictions['over_2_5'] < 50:
        under_prob = 100 - predictions['over_2_5']
        recommendations["best_bets"].append(("Under 2.5 Goals", f"{under_prob}% | {away_team}'s defense"))
    else:
        recommendations["best_bets"].append(("Over 2.5 Goals", f"{predictions['over_2_5']}% | High expected goals"))
    
    if home_metrics['avg_ga'] > 1.4:
        recommendations["avoid_bets"].append(f"{home_team} Clean Sheet")
    
    if predictions['over_3_5'] < 25:
        recommendations["avoid_bets"].append("Over 3.5 Goals")
    
    if predictions['over_4_5'] < 10:
        recommendations["avoid_bets"].append("Over 4.5 Goals")
    
    if home_metrics['avg_gf'] > away_metrics['avg_gf']:
        recommendations["insights"].append(f"{home_team} better attack")
    else:
        recommendations["insights"].append(f"{away_team} better attack")
    
    if away_metrics['avg_ga'] < home_metrics['avg_ga']:
        recommendations["insights"].append(f"{away_team} better defense")
    else:
        recommendations["insights"].append(f"{home_team} better defense")
    
    if h2h_stats and h2h_stats['total_matches'] > 0:
        if h2h_stats['home_wins'] == 0 and h2h_stats['away_wins'] == 0:
            recommendations["insights"].append(f"{h2h_stats['draws']}/{h2h_stats['total_matches']} draws historically")
    
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

# ============ MOBILE-OPTIMIZED DASHBOARD ============

# Top section: Data Input
st.markdown("### 📥 Data Input")
input_col1, input_col2 = st.columns([2, 1])

with input_col1:
    raw_input = st.text_area(
        "**Paste match data**", 
        height=100,
        placeholder="Paste data here:\nTeam\nScore\nScore\nTeam\n..."
    )
    
    parse_clicked = st.button("🚀 Parse Matches", type="primary", use_container_width=True)

with input_col2:
    st.markdown("#### 🛠️ Actions")
    
    max_matches = 0
    if st.session_state.team_stats:
        max_matches = max([st.session_state.team_stats[team]["P"] for team in VALID_TEAMS])
    st.metric("Season", f"S{st.session_state.season_number}", f"{max_matches}/38")
    
    if st.button("🔄 Reset Season", use_container_width=True):
        reset_league_for_new_season()
        st.rerun()
    
    if st.button("🗑️ Clear All", use_container_width=True):
        st.session_state.match_data = []
        reset_league_for_new_season()
        st.rerun()

# Process input data
if parse_clicked and raw_input.strip():
    new_matches, errors, cleaned_lines = clean_and_parse_matches(raw_input)
    
    if errors:
        st.error(f"❌ {len(errors)} errors")
        for error in errors[:2]:
            st.write(f"- {error}")
    
    if new_matches:
        needs_reset = False
        for home_team, home_score, away_score, away_team in new_matches:
            if st.session_state.team_stats[home_team]["P"] >= 38 or st.session_state.team_stats[away_team]["P"] >= 38:
                needs_reset = True
                break
        
        if needs_reset:
            check_and_reset_season()
        
        processed_count = 0
        for home_team, home_score, away_score, away_team in new_matches:
            if st.session_state.team_stats[home_team]["P"] >= 38 or st.session_state.team_stats[away_team]["P"] >= 38:
                check_and_reset_season()
            
            match_id = st.session_state.match_counter
            st.session_state.match_counter += 1
            
            total_goals = home_score + away_score
            
            total_g_display = "Won" if total_goals == 4 else ("3 ✔" if total_goals == 3 else str(total_goals))
            
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
            
            st.session_state.team_stats[home_team]["P"] += 1
            st.session_state.team_stats[home_team]["GF"] += home_score
            st.session_state.team_stats[home_team]["GA"] += away_score
            st.session_state.team_stats[home_team]["GD"] = st.session_state.team_stats[home_team]["GF"] - st.session_state.team_stats[home_team]["GA"]
            
            st.session_state.team_stats[away_team]["P"] += 1
            st.session_state.team_stats[away_team]["GF"] += away_score
            st.session_state.team_stats[away_team]["GA"] += home_score
            st.session_state.team_stats[away_team]["GD"] = st.session_state.team_stats[away_team]["GF"] - st.session_state.team_stats[away_team]["GA"]
            
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
            
            if len(st.session_state.team_stats[home_team]["Form"]) > 5:
                st.session_state.team_stats[home_team]["Form"].pop(0)
            if len(st.session_state.team_stats[away_team]["Form"]) > 5:
                st.session_state.team_stats[away_team]["Form"].pop(0)
            
            home_rank = get_team_position(home_team)
            away_rank = get_team_position(away_team)
            
            st.session_state.match_data.append([
                match_id, home_team, home_score, away_score, away_team,
                total_goals, total_g_display, result,
                home_score - away_score,
                "Yes" if home_score > 0 and away_score > 0 else "No",
                "Over 2.5" if total_goals > 2.5 else "Under 2.5",
                home_rank, away_rank,
                st.session_state.home_counters[home_team],
                st.session_state.away_counters[away_team],
                st.session_state.ha_counters[home_team],
                st.session_state.ha_counters[away_team],
                st.session_state.status3_counters[home_team],
                st.session_state.status3_counters[away_team],
                f"{home_team}: {st.session_state.ha_counters[home_team]} | {away_team}: {st.session_state.ha_counters[away_team]}",
                f"{home_team}: {st.session_state.status3_counters[home_team]} | {away_team}: {st.session_state.status3_counters[away_team]}",
                st.session_state.season_number,
                f"Season {st.session_state.season_number}"
            ])
            
            processed_count += 1
        
        st.success(f"✅ Added {processed_count} matches")
        st.rerun()
    else:
        st.warning("⚠️ No valid matches found")

# ============ MAIN DASHBOARD SECTIONS ============
if len(st.session_state.match_data) > 0:
    column_names = [
        "Match_ID", "Home_Team", "Home_Score", "Away_Score", "Away_Team",
        "Total_Goals", "Total-G", "Match_Result", "Goal_Difference", 
        "Both_Teams_Scored", "Over_Under", "Home_Rank", "Away_Rank",
        "Games_Since_Last_Won_Home", "Games_Since_Last_Won_Away",
        "Games_Since_Last_Won_Combined_Home", "Games_Since_Last_Won_Combined_Away",
        "Games_Since_Last_3Goals_Home", "Games_Since_Last_3Goals_Away",
        "F!=4HA", "Status3", "Season_Number", "Season_Label"
    ]
    
    df = pd.DataFrame(st.session_state.match_data, columns=column_names)
    
    st.markdown("---")
    st.markdown(f"### 📊 Season {st.session_state.season_number} Dashboard")
    
    # ============ COMPACT LEAGUE TABLE ============
    with st.expander("🏆 League Table", expanded=True):
        rankings = calculate_rankings()
        
        table_data = []
        for pos, (team, stats) in enumerate(rankings, 1):
            table_data.append([
                pos, team, stats["P"], stats["W"], stats["D"], stats["L"],
                stats["GF"], stats["GA"], stats["GD"], stats["Pts"], 
                "".join(stats["Form"][-3:]) if stats["Form"] else "-"
            ])
        
        league_df = pd.DataFrame(
            table_data,
            columns=["Pos", "Team", "P", "W", "D", "L", "GF", "GA", "GD", "Pts", "Form"]
        )
        
        # Display with smaller font
        st.dataframe(league_df.style.set_properties(**{
            'font-size': '0.8em',
            'padding': '2px'
        }), use_container_width=True, height=300)
        
        # Compact league insights
        cols = st.columns(4)
        if len(league_df) > 0:
            with cols[0]:
                best_attack = league_df.loc[league_df['GF'].idxmax()]
                st.metric("⚡ Attack", best_attack['Team'], f"{best_attack['GF']}", help="Most goals scored")
            with cols[1]:
                best_defense = league_df.loc[league_df['GA'].idxmin()]
                st.metric("🛡️ Defense", best_defense['Team'], f"{best_defense['GA']}", help="Fewest goals conceded")
            with cols[2]:
                best_gd = league_df.loc[league_df['GD'].idxmax()]
                st.metric("📈 GD", best_gd['Team'], f"+{best_gd['GD']}", help="Best goal difference")
            with cols[3]:
                top_scorer = league_df.loc[league_df['Pts'].idxmax()]
                st.metric("👑 Leader", top_scorer['Team'], f"{top_scorer['Pts']}", help="Most points")
    
    # ============ COMPACT MATCH SUMMARIES ============
    col1, col2 = st.columns(2)
    
    with col1:
        with st.expander("🔄 Recent Matches", expanded=True):
            st.markdown("""
                <div style="background-color:black; color:white; padding:10px; border-radius:8px; border:1px solid #444; font-size:0.85em;">
            """, unsafe_allow_html=True)
            
            recent_matches = st.session_state.match_data[-8:] if len(st.session_state.match_data) > 0 else []
            
            for match in recent_matches[::-1]:
                home = match[1]
                away = match[4]
                home_score = match[2]
                away_score = match[3]
                home_rank = match[11] if len(match) > 11 else "?"
                away_rank = match[12] if len(match) > 12 else "?"
                
                if home_score > away_score:
                    home_style = "color: #4CAF50; font-weight: bold;"
                    away_style = "color: #FF6B6B;"
                elif away_score > home_score:
                    home_style = "color: #FF6B6B;"
                    away_style = "color: #4CAF50; font-weight: bold;"
                else:
                    home_style = away_style = "color: #FFD700;"
                
                st.markdown(
                    f"<div style='margin-bottom:5px; padding:3px; border-bottom:1px solid #333;'>"
                    f"<span style='{home_style}'>{home_rank}. {home[:10]}</span> "
                    f"{home_score}-{away_score} "
                    f"<span style='{away_style}'>{away[:10]} ({away_rank}.)</span>"
                    f"</div>", 
                    unsafe_allow_html=True
                )
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        with st.expander("🎯 Status3 Summary", expanded=True):
            st.markdown("""
                <div style="background-color:#1a1a1a; color:white; padding:10px; border-radius:8px; border:1px solid #444; font-size:0.85em;">
                <div style='color:#888; font-size:0.75em; margin-bottom:5px;'>Games since last 3-goal match</div>
            """, unsafe_allow_html=True)
            
            # Get recent teams from last 5 matches
            recent_teams = set()
            for match in st.session_state.match_data[-5:]:
                if len(match) > 1:
                    recent_teams.add(match[1])  # Home team
                    recent_teams.add(match[4])  # Away team
            
            # Show Status3 for recent teams
            for team in sorted(recent_teams):
                status3_value = st.session_state.status3_counters.get(team, 0)
                status3_color = get_status3_color(status3_value)
                status3_display = "0 🔴" if status3_value == 0 else f"{status3_value} 🟢" if status3_value <= 3 else f"{status3_value} 🟡" if status3_value <= 6 else f"{status3_value} 🔵"
                
                st.markdown(
                    f"<div style='margin-bottom:4px; padding:3px; border-bottom:1px solid #333;'>"
                    f"<span style='color:{status3_color}; font-weight:bold;'>{team[:12]}</span> "
                    f"<span style='float:right;'>{status3_display}</span>"
                    f"</div>", 
                    unsafe_allow_html=True
                )
            
            # Status3 legend
            st.markdown("""
                <div style='margin-top:10px; font-size:0.7em; color:#888;'>
                🟢 0-3: Recent 3-goal match<br>
                🟡 4-6: Medium<br>
                🔵 7+: Long time<br>
                🔴 0: Just had 3 goals
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    # ============ COMPACT MATCH PREDICTOR ============
    with st.expander("🎯 Match Predictor", expanded=False):
        pred_col1, pred_col2 = st.columns(2)
        
        with pred_col1:
            home_team = st.selectbox("Home Team", sorted(VALID_TEAMS), key="home_select_mobile")
        
        with pred_col2:
            away_team = st.selectbox("Away Team", sorted(VALID_TEAMS), key="away_select_mobile")
        
        if home_team == away_team:
            st.warning("Select different teams")
        else:
            team_metrics = calculate_team_metrics()
            predictions = predict_match_outcome(home_team, away_team, team_metrics)
            h2h_stats = create_head_to_head_stats(home_team, away_team)
            
            # Compact outcome probabilities
            st.markdown("#### 📈 Predictions")
            outcome_cols = st.columns(3)
            with outcome_cols[0]:
                home_win_value = min(1.0, max(0.0, predictions['home_win'] / 100))
                st.metric("🏠 Home", f"{predictions['home_win']}%")
                st.progress(home_win_value, height=10)
            with outcome_cols[1]:
                draw_value = min(1.0, max(0.0, predictions['draw'] / 100))
                st.metric("🤝 Draw", f"{predictions['draw']}%")
                st.progress(draw_value, height=10)
            with outcome_cols[2]:
                away_win_value = min(1.0, max(0.0, predictions['away_win'] / 100))
                st.metric("✈️ Away", f"{predictions['away_win']}%")
                st.progress(away_win_value, height=10)
            
            # Compact goal markets
            st.markdown("#### ⚽ Goal Markets")
            goal_cols = st.columns(4)
            with goal_cols[0]:
                over_2_5_value = min(1.0, max(0.0, predictions['over_2_5'] / 100))
                st.metric("O2.5", f"{predictions['over_2_5']}%")
                st.progress(over_2_5_value, height=8)
            with goal_cols[1]:
                over_3_5_value = min(1.0, max(0.0, predictions['over_3_5'] / 100))
                st.metric("O3.5", f"{predictions['over_3_5']}%")
                st.progress(over_3_5_value, height=8)
            with goal_cols[2]:
                over_4_5_value = min(1.0, max(0.0, predictions['over_4_5'] / 100))
                st.metric("O4.5", f"{predictions['over_4_5']}%")
                st.progress(over_4_5_value, height=8)
            with goal_cols[3]:
                bts_value = min(1.0, max(0.0, predictions['both_teams_score'] / 100))
                st.metric("BTS", f"{predictions['both_teams_score']}%")
                st.progress(bts_value, height=8)
            
            # Expected goals
            exp_cols = st.columns(2)
            with exp_cols[0]:
                st.metric("📊 xG", predictions['expected_goals'])
            with exp_cols[1]:
                st.metric("🔮 Score", predictions['predicted_score'])
            
            # Betting Recommendations
            recommendations = generate_betting_recommendations(
                home_team, away_team, predictions, team_metrics, h2h_stats
            )
            
            if recommendations["best_bets"]:
                with st.expander("💰 Betting Tips", expanded=False):
                    for bet, reason in recommendations["best_bets"][:2]:  # Show only top 2
                        st.write(f"✅ **{bet}**")
                        st.caption(f"{reason}")
            
            # Quick team comparison
            with st.expander("📋 Quick Compare", expanded=False):
                compare_data = {
                    "Metric": ["Win%", "Draw%", "Avg GF", "Avg GA", "Form"],
                    home_team: [
                        f"{team_metrics[home_team]['win_rate']}%",
                        f"{team_metrics[home_team]['draw_rate']}%",
                        team_metrics[home_team]['avg_gf'],
                        team_metrics[home_team]['avg_ga'],
                        "".join(team_metrics[home_team]['form'][-3:]) if team_metrics[home_team]['form'] else "-"
                    ],
                    away_team: [
                        f"{team_metrics[away_team]['win_rate']}%",
                        f"{team_metrics[away_team]['draw_rate']}%",
                        team_metrics[away_team]['avg_gf'],
                        team_metrics[away_team]['avg_ga'],
                        "".join(team_metrics[away_team]['form'][-3:]) if team_metrics[away_team]['form'] else "-"
                    ]
                }
                
                compare_df = pd.DataFrame(compare_data)
                st.dataframe(compare_df, use_container_width=True, hide_index=True)
    
    # ============ COMPACT DATA EXPORT ============
    with st.expander("💾 Export Data", expanded=False):
        exp_cols = st.columns(3)
        
        with exp_cols[0]:
            csv_full = df.to_csv(index=False)
            st.download_button(
                "📥 All Data",
                data=csv_full,
                file_name=f"all_matches.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with exp_cols[1]:
            current_season_df = df[df["Season_Number"] == st.session_state.season_number]
            if len(current_season_df) > 0:
                csv_current = current_season_df.to_csv(index=False)
                st.download_button(
                    f"📥 S{st.session_state.season_number}",
                    data=csv_current,
                    file_name=f"season_{st.session_state.season_number}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        with exp_cols[2]:
            csv_league = league_df.to_csv(index=False)
            st.download_button(
                "📥 Table",
                data=csv_league,
                file_name=f"league_table.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        # Season warning
        max_played = 0
        if st.session_state.team_stats:
            max_played = max([st.session_state.team_stats[team]["P"] for team in VALID_TEAMS])
        if max_played >= 35:
            st.warning(f"⚠️ Season {st.session_state.season_number}: {max_played}/38 matches")
    
    # ============ COMPACT STATS SUMMARY ============
    with st.expander("📊 Quick Stats", expanded=False):
        total_matches = len(st.session_state.match_data)
        current_season_matches = [m for m in st.session_state.match_data if m[-2] == st.session_state.season_number]
        
        if current_season_matches:
            current_df = pd.DataFrame(current_season_matches, columns=column_names)
            avg_goals = current_df["Total_Goals"].mean()
            home_wins = len(current_df[current_df["Match_Result"] == "Home Win"])
            away_wins = len(current_df[current_df["Match_Result"] == "Away Win"])
            draws = len(current_df[current_df["Match_Result"] == "Draw"])
            
            stat_cols = st.columns(4)
            with stat_cols[0]:
                st.metric("Matches", len(current_season_matches))
            with stat_cols[1]:
                st.metric("Avg Goals", round(avg_goals, 1))
            with stat_cols[2]:
                st.metric("Home Wins", home_wins)
            with stat_cols[3]:
                st.metric("Away Wins", away_wins)

else:
    # Welcome message when no data exists
    st.markdown("---")
    st.markdown("### 🚀 Getting Started")
    
    col_welcome1, col_welcome2 = st.columns(2)
    
    with col_welcome1:
        st.markdown("""
        **📝 How to use:**
        1. **Paste match data** above
        2. Click **Parse Matches**
        3. View **league table**
        4. Use **predictor**
        5. **Download data**
        """)
    
    with col_welcome2:
        st.markdown("""
        **💡 Tips:**
        - Format: Team, Score, Score, Team
        - Cleaner removes dates/times
        - Example:
        ```
        Team A
        2
        1
        Team B
        ```
        """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; font-size: 0.8em;'>"
    f"⚽ Season {st.session_state.season_number} • 38-match reset • All data preserved"
    "</div>",
    unsafe_allow_html=True
)
