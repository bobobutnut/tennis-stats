from flask import Flask, render_template, request
import pandas as pd
import os

app = Flask(__name__)
CSV_PATH = os.path.join(app.root_path, 'data', 'atp_tennis.csv')


def check_score(score1, score2, score3, score4):
    return abs(score1 + score3 - score2 - score4) > 11


@app.route("/dominant")
def dominant_matches():
    if not os.path.exists(CSV_PATH):
        return "CSV file not found!", 500

    df = pd.read_csv(CSV_PATH)

    # Convert necessary columns
    df['Odd_1'] = pd.to_numeric(df['Odd_1'], errors='coerce')
    df['Odd_2'] = pd.to_numeric(df['Odd_2'], errors='coerce')
    df['Rank_1'] = pd.to_numeric(df['Rank_1'], errors='coerce')
    df['Rank_2'] = pd.to_numeric(df['Rank_2'], errors='coerce')

    # Heavy favorite matches (odds ≤ 1.10) where the favorite won
    # heavy_fav_p1 = (df['Odd_1'] <= 1.10) & (df['Winner'] == df['Player_1'])
    # heavy_fav_p2 = (df['Odd_2'] <= 1.10) & (df['Winner'] == df['Player_2'])
    # dominant = df[heavy_fav_p1 | heavy_fav_p2].copy()
    df2 = df[df['Score'].apply(lambda Score: len(Score)) == 7]
    dominant = df2[df2["Score"].apply(
        lambda x: check_score(int(x.split(" ")[0].split("-")[0]), int(x.split(" ")[0].split("-")[1]),
                              int(x.split(" ")[1].split("-")[0]), int(x.split(" ")[1].split("-")[1])))]

    # Determine winner and loser
    dominant['Dominant_Player'] = dominant.apply(
        lambda row: row['Player_1'] if row['Winner'] == row['Player_1'] else row['Player_2'], axis=1
    )
    dominant['Loser'] = dominant.apply(
        lambda row: row['Player_2'] if row['Winner'] == row['Player_1'] else row['Player_1'], axis=1
    )

    # Ranks
    dominant['Winner_Rank'] = dominant.apply(
        lambda row: row['Rank_1'] if row['Winner'] == row['Player_1'] else row['Rank_2'], axis=1
    )
    dominant['Loser_Rank'] = dominant.apply(
        lambda row: row['Rank_2'] if row['Winner'] == row['Player_1'] else row['Rank_1'], axis=1
    )

    # THIS IS THE KEY LINE — Add the actual odds of the winner
    dominant['Winner_Odds'] = dominant.apply(
        lambda row: row['Odd_1'] if row['Winner'] == row['Player_1'] else row['Odd_2'], axis=1
    )

    # Parse games from Score
    def parse_games_won(score):
        if pd.isna(score) or not isinstance(score, str):
            return 0, 0
        total_winner = total_loser = 0
        for s in str(score).split():
            if '-' in s:
                parts = s.split('-')
                if len(parts) == 2:
                    try:
                        g1 = int(parts[0])
                        g2 = int(parts[1].split('(')[0]) if '(' in parts[1] else int(parts[1])
                        total_winner += max(g1, g2)
                        total_loser += min(g1, g2)
                    except:
                        continue
        return total_winner, total_loser



    # Date handling
    dominant['Date'] = pd.to_datetime(dominant['Date'], errors='coerce')

    # Prepare data for template — NOW INCLUDING Winner_Odds
    dominant_list = dominant[[
        'Date', 'Tournament', 'Round', 'Surface',
        'Dominant_Player', 'Winner_Rank',
        'Loser', 'Loser_Rank',
        'Winner_Odds',  # ← This was missing!
        'Score'  # ← Also add Score if you want to show full score
    ]].to_dict(orient='records')

    # Clean and format
    for m in dominant_list:
        m['Winner_Rank'] = int(m['Winner_Rank']) if pd.notna(m['Winner_Rank']) else 'NR'
        m['Loser_Rank'] = int(m['Loser_Rank']) if pd.notna(m['Loser_Rank']) else 'NR'
        m['Date'] = m['Date'].strftime('%Y-%m-%d') if pd.notna(m['Date']) else 'N/A'
        m['Winner_Odds'] = float(f"{m['Winner_Odds']:.3f}") if pd.notna(m['Winner_Odds']) else '—'

    total_dominant = len(dominant_list)

    return render_template(
        'dominant.html',
        matches=dominant_list,
        total=total_dominant
    )

@app.route("/upsets")
def upset_matches():
    if not os.path.exists(CSV_PATH):
        return "CSV file not found!", 500

    df = pd.read_csv(CSV_PATH)

    # Convert necessary columns
    df['Odd_1'] = pd.to_numeric(df['Odd_1'], errors='coerce')
    df['Odd_2'] = pd.to_numeric(df['Odd_2'], errors='coerce')
    df['Rank_1'] = pd.to_numeric(df['Rank_1'], errors='coerce')
    df['Rank_2'] = pd.to_numeric(df['Rank_2'], errors='coerce')

    df2 = df[((df['Rank_1'] < df['Rank_2'] - 700) & (df['Winner'] == df["Player_2"])) | ( (df['Rank_2'] < df['Rank_1'] - 700) & (df['Winner'] == df["Player_1"]))]

    df2['Underdog_Player'] = df2.apply(
        lambda row: row['Player_1'] if row['Winner'] == row['Player_1'] else row['Player_2'], axis=1
    )
    df2['Loser'] = df2.apply(
        lambda row: row['Player_2'] if row['Winner'] == row['Player_1'] else row['Player_1'], axis=1
    )

    # Ranks
    df2['Winner_Rank'] = df2.apply(
        lambda row: row['Rank_1'] if row['Winner'] == row['Player_1'] else row['Rank_2'], axis=1
    )
    df2['Loser_Rank'] = df2.apply(
        lambda row: row['Rank_2'] if row['Winner'] == row['Player_1'] else row['Rank_1'], axis=1
    )

    # THIS IS THE KEY LINE — Add the actual odds of the winner
    df2['Winner_Odds'] = df2.apply(
        lambda row: row['Odd_1'] if row['Winner'] == row['Player_1'] else row['Odd_2'], axis=1
    )

    # Parse games from Score
    def parse_games_won(score):
        if pd.isna(score) or not isinstance(score, str):
            return 0, 0
        total_winner = total_loser = 0
        for s in str(score).split():
            if '-' in s:
                parts = s.split('-')
                if len(parts) == 2:
                    try:
                        g1 = int(parts[0])
                        g2 = int(parts[1].split('(')[0]) if '(' in parts[1] else int(parts[1])
                        total_winner += max(g1, g2)
                        total_loser += min(g1, g2)
                    except:
                        continue
        return total_winner, total_loser

    df2[['Games_Won', 'Games_Lost']] = df2['Score'].apply(
        lambda x: pd.Series(parse_games_won(x))
    )

    df2['Date'] = pd.to_datetime(df2['Date'], errors='coerce')

    # Prepare data for template — NOW INCLUDING Winner_Odds
    dominant_list = df2[[
        'Date', 'Tournament', 'Round', 'Surface',
        'Underdog_Player', 'Winner_Rank',
        'Loser', 'Loser_Rank',
        'Games_Won', 'Games_Lost',
        'Winner_Odds',  # ← This was missing!
        'Score'  # ← Also add Score if you want to show full score
    ]].to_dict(orient='records')

    # Clean and format
    for m in dominant_list:
        m['Winner_Rank'] = int(m['Winner_Rank']) if pd.notna(m['Winner_Rank']) else 'NR'
        m['Loser_Rank'] = int(m['Loser_Rank']) if pd.notna(m['Loser_Rank']) else 'NR'
        m['Date'] = m['Date'].strftime('%Y-%m-%d') if pd.notna(m['Date']) else 'N/A'
        m['Winner_Odds'] = float(f"{m['Winner_Odds']:.3f}") if pd.notna(m['Winner_Odds']) else '—'

    total_dominant = len(dominant_list)

    return render_template(
        'Upsets.html',
        matches=dominant_list,
        total=total_dominant
    )

@app.route("/")
def home():
    return render_template('home.html')
@app.route("/rate")
def win_rates():
    if not os.path.exists(CSV_PATH):
        return "CSV file not found!", 500

    df = pd.read_csv(CSV_PATH)

    # Strip whitespace from player names
    df['Player_1'] = df['Player_1'].astype(str).str.strip()
    df['Player_2'] = df['Player_2'].astype(str).str.strip()
    df['Winner'] = df['Winner'].astype(str).str.strip()

    # Count wins
    wins = df['Winner'].value_counts()

    # Count total matches (appearances as Player_1 or Player_2)
    all_players = pd.concat([df['Player_1'], df['Player_2']])
    total_matches = all_players.value_counts()

    # Build stats DataFrame
    stats = pd.DataFrame({
        'Wins': wins,
        'Total_Matches': total_matches
    })
    stats['Wins'] = stats['Wins'].fillna(0).astype(int)
    stats['Losses'] = stats['Total_Matches'] - stats['Wins']
    stats['Win_Rate (%)'] = (stats['Wins'] / stats['Total_Matches'] * 100).round(1)

    # Filter: at least 50 matches, sort by win rate
    stats = stats[stats['Total_Matches'] >= 50]
    stats = stats.sort_values('Win_Rate (%)', ascending=False)

    return render_template('rate.html', stats=stats)


@app.route("/recents")
def recent_matches():
    if not os.path.exists(CSV_PATH):
        return "CSV file not found!", 500

    df = pd.read_csv(CSV_PATH)
    df2 = df.tail(50)
    recent_list = df2[[
        'Tournament', 'Date', 'Series', 'Court', 'Surface',
        'Round', 'Best of',
        'Player_1', 'Player_2',
        'Winner', 'Rank_1',
        'Rank_2', 'Pts_1', 'Pts_2',
        'Odd_1', 'Odd_2',# ← This was missing!
        'Score'  # ← Also add Score if you want to show full score
    ]].to_dict(orient='records')

    return render_template(
        'recent.html',
        matches=recent_list
    )

@app.route("/search")
def search_player():
    if not os.path.exists(CSV_PATH):
        return "CSV file not found!", 500

    player_query = request.args.get('q', '').strip()
    if not player_query:
        return render_template('search.html', matches=[], query="", total=0)

    df = pd.read_csv(CSV_PATH)

    # Search in both Player_1 and Player_2 (case insensitive)
    mask = (
        df['Player_1'].astype(str).str.contains(player_query, case=False, na=False) |
        df['Player_2'].astype(str).str.contains(player_query, case=False, na=False)
    )
    player_matches = df[mask].copy()

    # Sort by most recent
    player_matches['Date'] = pd.to_datetime(player_matches['Date'], errors='coerce')
    player_matches = player_matches.sort_values('Date', ascending=False)

    # Take last 30 matches
    player_matches = player_matches.head(30)

    matches_list = player_matches[[
        'Date', 'Tournament', 'Round', 'Surface',
        'Player_1', 'Player_2', 'Winner', 'Score',
        'Rank_1', 'Rank_2', 'Odd_1', 'Odd_2'
    ]].to_dict(orient='records')

    # Format data
    for m in matches_list:
        m['Date'] = pd.to_datetime(m['Date']).strftime('%Y-%m-%d') if pd.notna(m['Date']) else 'N/A'
        m['Rank_1'] = int(m['Rank_1']) if pd.notna(m['Rank_1']) else 'NR'
        m['Rank_2'] = int(m['Rank_2']) if pd.notna(m['Rank_2']) else 'NR'

    return render_template(
        'search.html',
        matches=matches_list,
        query=player_query,
        total=len(matches_list)
    )

if __name__ == '__main__':
    app.run(debug=True)