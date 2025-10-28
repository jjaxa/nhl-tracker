from flask import Flask, render_template, request, jsonify
import json
import requests
import os
from datetime import datetime

app = Flask(__name__)

# -------------------------------------------------------------------------
# Load the player ID → name mapping
# -------------------------------------------------------------------------
def load_players():
    try:
        with open("players.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Could not load players.json: {e}")
        return {}

# -------------------------------------------------------------------------
# Helper: Clean player name format
# -------------------------------------------------------------------------
def clean_name_field(raw):
    if isinstance(raw, dict):
        return raw.get("default", "")
    return raw or ""

# -------------------------------------------------------------------------
# Get today's live or in-progress NHL games
# -------------------------------------------------------------------------
def get_live_games():
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        url = f"https://api-web.nhle.com/v1/score/{today}"
        r = requests.get(url, timeout=10)
        data = r.json()

        live_games = {}
        for game in data.get("games", []):
            if game.get("gameState") in ["LIVE", "CRIT"]:
                live_games[game["gameId"]] = {
                    "home": game["homeTeam"]["abbrev"],
                    "away": game["awayTeam"]["abbrev"]
                }
        return live_games
    except Exception as e:
        print(f"[ERROR] Could not fetch live games: {e}")
        return {}

# -------------------------------------------------------------------------
# Helper: Fetch true LIVE stats for a player
# -------------------------------------------------------------------------
def get_live_stats(pid):
    try:
        live_games = get_live_games()
        if not live_games:
            return None

        # Search through all live boxscores to find this player
        for game_id in live_games:
            box_url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/boxscore"
            box = requests.get(box_url, timeout=10).json()

            for group in box.get("playerByGameStats", {}).values():
                for player_id, pinfo in group.items():
                    if str(player_id) == str(pid):
                        name = pinfo.get("name", {}).get("default", pinfo.get("name", "Unknown"))
                        stats = {
                            "label": f"LIVE Game ({live_games[game_id]['away']} vs {live_games[game_id]['home']})",
                            "shots": pinfo.get("sog", 0),
                            "goals": pinfo.get("goals", 0),
                            "assists": pinfo.get("assists", 0),
                            "points": pinfo.get("goals", 0) + pinfo.get("assists", 0),
                            "games": None,
                            "live": True
                        }
                        return name, stats
        return None
    except Exception as e:
        print(f"[WARN] No live data for {pid}: {e}")
        return None

# -------------------------------------------------------------------------
# Fallback: Fetch season totals if no live data
# -------------------------------------------------------------------------
def get_season_stats(pid):
    try:
        url = f"https://api-web.nhle.com/v1/player/{pid}/landing"
        r = requests.get(url, timeout=10)
        data = r.json()

        first = clean_name_field(data.get("firstName", ""))
        last = clean_name_field(data.get("lastName", ""))
        name = f"{first} {last}".strip()

        stats = data.get("featuredStats", {}).get("regularSeason", {}).get("subSeason", {})
        goals = stats.get("goals", 0)
        assists = stats.get("assists", 0)
        shots = stats.get("shots", 0)
        games = stats.get("gamesPlayed", 0)
        points = goals + assists

        return name, {
            "label": "Season Totals (2024–25)",
            "shots": shots,
            "goals": goals,
            "assists": assists,
            "points": points,
            "games": games,
            "live": False
        }
    except Exception as e:
        print(f"[ERROR] Season stats for {pid}: {e}")
        return f"Player {pid}", {
            "label": "Error loading stats",
            "shots": 0, "goals": 0, "assists": 0, "points": 0, "games": 0, "live": False
        }

# -------------------------------------------------------------------------
# Flask Routes
# -------------------------------------------------------------------------
@app.route("/")
def index():
    players = load_players()
    return render_template("index.html", players=players)

@app.route("/live_stats", methods=["POST"])
def live_stats():
    ids = request.form.getlist("player_ids[]")
    results = {}

    for pid in ids:
        live_data = get_live_stats(pid)
        if live_data:
            name, stats = live_data
        else:
            name, stats = get_season_stats(pid)
        results[name] = stats

    return jsonify(results)

# -------------------------------------------------------------------------
# Entry point
# -------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
