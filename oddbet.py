import streamlit as st
import pandas as pd
import numpy as np
from collections import defaultdict
import plotly.graph_objects as go
import plotly.express as px

# Add these functions to your existing code

def calculate_team_metrics():
    """Calculate detailed metrics for each team"""
    metrics = {}
    
    for team in VALID_TEAMS:
        stats = st.session_state.team_stats[team]
        
        # Basic win/draw/loss rates
        total_matches = stats["P"]
        win_rate = (stats["W"] / total_matches * 100) if total_matches > 0 else 0
        draw_rate = (stats["D"] / total_matches * 100) if total_matches > 0 else 0
        loss_rate = (stats["L"] / total_matches * 100) if total_matches > 0 else 0
        
        # Goals per match
        avg_gf = stats["GF"] / total_matches if total_matches > 0 else 0
        avg_ga = stats["GA"] / total_matches if total_matches > 0 else 0
        
        # Clean sheet and scoring rates
        clean_sheets = st.session_state.team_stats[team].get("clean_sheets", 0)
        clean_sheet_rate = (clean_sheets / total_matches * 100) if total_matches > 0 else 0
        
        metrics[team] = {
            "win_rate": round(win_rate, 1),
            "draw_rate": round(draw_rate, 1),
            "loss_rate": round(loss_rate, 1),
            "avg_gf": round(avg_gf, 2),
            "avg_ga": round(avg_ga, 2),
            "clean_sheet_rate": round(clean_sheet_rate, 1),
            "form": stats["Form"][-5:] if len(stats["Form"]) >= 5 else stats["Form"],
            "points_per_game": round(stats["Pts"] / total_matches, 2) if total_matches > 0 else 0,
            "home_advantage": calculate_home_advantage(team),
            "over_2_5_rate": calculate_over_under_rate(team, 2.5, "over"),
            "over_3_5_rate": calculate_over_under_rate(team, 3.5, "over"),
            "both_teams_score_rate": calculate_bts_rate(team)
        }
    
    return metrics

def calculate_home_advantage(team):
    """Calculate home vs away performance"""
    # You'll need to track home/away separately in session state
    # For now, using simplified version
    return 0  # Placeholder

def calculate_over_under_rate(team, threshold, direction="over"):
    """Calculate percentage of matches over/under threshold"""
    # Need to track match details
    return 0  # Placeholder

def calculate_bts_rate(team):
    """Calculate both teams scored rate"""
    return 0  # Placeholder

def predict_match_outcome(home_team, away_team, team_metrics):
    """Predict match outcome probabilities"""
    
    home_metrics = team_metrics[home_team]
    away_metrics = team_metrics[away_team]
    
    # Base probabilities from win rates
    home_win_prob = home_metrics["win_rate"] * (1 - away_metrics["win_rate"] / 100)
    away_win_prob = away_metrics["win_rate"] * (1 - home_metrics["win_rate"] / 100)
    draw_prob = (home_metrics["draw_rate"] + away_metrics["draw_rate"]) / 2
    
    # Adjust for form
    form_adjustment = calculate_form_adjustment(home_metrics["form"], away_metrics["form"])
    home_win_prob += form_adjustment["home"]
    away_win_prob += form_adjustment["away"]
    
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
    
    both_teams_score_prob = (home_metrics["both_teams_score_rate"] + 
                           away_metrics["both_teams_score_rate"]) / 2
    
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

def calculate_form_adjustment(home_form, away_form):
    """Adjust probabilities based on recent form"""
    home_score = sum(3 if r == "W" else (1 if r == "D" else 0) for r in home_form)
    away_score = sum(3 if r == "W" else (1 if r == "D" else 0) for r in away_form)
    
    total = home_score + away_score
    if total == 0:
        return {"home": 0, "away": 0}
    
    home_adj = (home_score / total * 10) - 5
    away_adj = (away_score / total * 10) - 5
    
    return {"home": home_adj, "away": away_adj}

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

def create_analytics_dashboard():
    """Main analytics dashboard"""
    
    st.subheader("📊 Match Predictor & Analytics")
    
    # Create two columns for team selection
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col1:
        home_team = st.selectbox("Select Home Team", sorted(VALID_TEAMS), key="home_select")
    
    with col3:
        away_team = st.selectbox("Select Away Team", sorted(VALID_TEAMS), key="away_select")
    
    if home_team == away_team:
        st.warning("Please select two different teams")
        return
    
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
    pred_col1, pred_col2, pred_col3 = st.columns(3)
    
    with pred_col1:
        st.metric("🏠 Home Win", f"{predictions['home_win']}%")
        st.progress(predictions['home_win'] / 100)
    
    with pred_col2:
        st.metric("🤝 Draw", f"{predictions['draw']}%")
        st.progress(predictions['draw'] / 100)
    
    with pred_col3:
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
    
    # Create visualizations
    st.markdown("---")
    st.subheader("📈 Probability Visualization")
    
    # Outcome probabilities chart
    outcome_data = pd.DataFrame({
        "Outcome": ["Home Win", "Draw", "Away Win"],
        "Probability": [predictions['home_win'], predictions['draw'], predictions['away_win']]
    })
    
    fig1 = px.bar(outcome_data, x='Outcome', y='Probability', 
                 color='Outcome',
                 color_discrete_map={'Home Win': '#2E86AB', 'Draw': '#A23B72', 'Away Win': '#F18F01'},
                 text='Probability')
    fig1.update_layout(title="Match Outcome Probabilities", showlegend=False)
    st.plotly_chart(fig1, use_container_width=True)
    
    # Goal market probabilities
    goal_data = pd.DataFrame({
        "Market": ["Over 2.5", "Over 3.5", "Over 4.5", "Both Teams Score"],
        "Probability": [predictions['over_2_5'], predictions['over_3_5'], 
                       predictions['over_4_5'], predictions['both_teams_score']]
    })
    
    fig2 = px.bar(goal_data, x='Market', y='Probability', color='Market',
                 color_discrete_sequence=px.colors.sequential.Viridis,
                 text='Probability')
    fig2.update_layout(title="Goal Market Probabilities", showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

# Add this to your main app layout (after the existing columns)
def add_analytics_section():
    """Add analytics tab to the main app"""
    
    # Add a new tab or section for analytics
    st.markdown("---")
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 Match Predictor", "🏆 League Insights", "📈 Team Analytics"])
    
    with tab1:
        create_analytics_dashboard()
    
    with tab2:
        create_league_insights()
    
    with tab3:
        create_team_analytics()

def create_league_insights():
    """Create league-wide insights dashboard"""
    
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
    
    st.subheader("🏆 Current League Table")
    st.dataframe(league_df, use_container_width=True, height=400)
    
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
        best_form_team = max(st.session_state.team_stats.items(), 
                           key=lambda x: sum(3 if r == "W" else (1 if r == "D" else 0) 
                                           for r in x[1]["Form"][-5:]))
        st.metric("Best Form", best_form_team[0], 
                 f"{sum(1 for r in best_form_team[1]['Form'][-5:] if r == 'W')}W in last 5")

def create_team_analytics():
    """Create detailed team analytics"""
    
    team = st.selectbox("Select Team for Analysis", sorted(VALID_TEAMS))
    
    if not team:
        return
    
    stats = st.session_state.team_stats[team]
    
    st.subheader(f"📈 {team} - Detailed Analytics")
    
    # Performance metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Points", stats["Pts"])
    
    with col2:
        win_rate = (stats["W"] / stats["P"] * 100) if stats["P"] > 0 else 0
        st.metric("Win Rate", f"{win_rate:.1f}%")
    
    with col3:
        avg_gf = stats["GF"] / stats["P"] if stats["P"] > 0 else 0
        st.metric("Avg Goals For", f"{avg_gf:.2f}")
    
    with col4:
        avg_ga = stats["GA"] / stats["P"] if stats["P"] > 0 else 0
        st.metric("Avg Goals Against", f"{avg_ga:.2f}")
    
    # Form chart
    st.subheader("📊 Form Progression")
    
    form_data = []
    points = 0
    for i, result in enumerate(stats["Form"]):
        if result == "W":
            points += 3
        elif result == "D":
            points += 1
        
        form_data.append({
            "Match": i + 1,
            "Result": result,
            "Cumulative Points": points,
            "Points from Match": 3 if result == "W" else (1 if result == "D" else 0)
        })
    
    if form_data:
        form_df = pd.DataFrame(form_data)
        fig = px.line(form_df, x="Match", y="Cumulative Points", 
                     title="Points from Last 5 Matches",
                     markers=True)
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent matches
    st.subheader("🔄 Recent Matches")
    
    team_matches = []
    for match in reversed(st.session_state.match_data[-20:]):  # Last 20 matches
        if match[1] == team or match[4] == team:
            is_home = match[1] == team
            opponent = match[4] if is_home else match[1]
            team_score = match[2] if is_home else match[3]
            opp_score = match[3] if is_home else match[2]
            
            result = "W" if team_score > opp_score else ("D" if team_score == opp_score else "L")
            
            team_matches.append({
                "Match ID": match[0],
                "Home/Away": "Home" if is_home else "Away",
                "Opponent": opponent,
                "Score": f"{team_score}-{opp_score}",
                "Result": result,
                "Total Goals": team_score + opp_score
            })
    
    if team_matches:
        matches_df = pd.DataFrame(team_matches[:10])  # Show last 10
        st.dataframe(matches_df, use_container_width=True, hide_index=True)

# In your main app, call this after displaying existing content
if st.session_state.match_data:
    add_analytics_section()
