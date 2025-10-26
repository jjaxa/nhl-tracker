from flask import Flask, render_template, request, jsonify
import json
import requests
import os

app = Flask(__name__)

# -------------------------------------------------------------------------
# Helper: Load players.json (player name → ID)
# -------------------------------------------------------------------------
def load_players():
    try:
        with open("players.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Could not load players.json: {e}")
        return {}

# -------------------------------------------------------------------------
# Helper: Fetch player season stats
# -------------------------------------------------------------------------
def get_season_stats(pid):
    try:
        url = f"https://api-web.nhle.com/v1/player/{pid}/landing"
        r = requests.get(url, timeout=10)
        data = r.json()

        # Handle both string and {"default": "..."} name formats
        first_raw = data.get("firstName", "")
        last_raw = data.get("lastName", "")
        first = first_raw["default"] if isinstance(first_raw, dict) else first_raw
        last = last_raw["default"] if isinstance(last_raw, dict) else last_raw
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
# Helper: Fetch live game stats if available
# -------------------------------------------------------------------------
def get_live_stats(pid):
    try:
        url = f"https://api-web.nhle.com/v1/player/{pid}/landing"
        r = requests.get(url, timeout=10)
        data = r.json()

        first_raw = data.get("firstName", "")
        last_raw = data.get("lastName", "")
        first = first_raw["default"] if isinstance(first_raw, dict) else first_raw
        last = last_raw["default"] if isinstance(last_raw, dict) else last_raw
        name = f"{first} {last}".strip()

        # Look for today's game (if it exists)
        game_log = data.get("gameLog", [])
        if game_log and "goals" in game_log[0]:
            latest = game_log[0]
            if latest.get("isCurrentGame", False):
                goals = latest.get("goals", 0)
                assists = latest.get("assists", 0)
                shots = latest.get("shots", 0)
                points = goals + assists
                return name, {
                    "label": "LIVE Game",
                    "shots": shots,
                    "goals": goals,
                    "assists": assists,
                    "points": points,
                    "games": None,
                    "live": True
                }

        return None
    except Exception as e:
        print(f"[WARN] No live data for {pid}: {e}")
        return None

# -------------------------------------------------------------------------
# Home route
# -------------------------------------------------------------------------
@app.route("/")
def index():
    players = load_players()
    return render_template("index.html", players=players)

# -------------------------------------------------------------------------
# Fetch live + season stats for selected players
# -------------------------------------------------------------------------
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
# Entry point (for local testing)
# -------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
