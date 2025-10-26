from flask import Flask, render_template, request, jsonify
import json
import requests
import os

app = Flask(__name__)

# -------------------------------------------------------------------------
# Helper: Load players.json
# -------------------------------------------------------------------------
def load_players():
    try:
        with open("players.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Could not load players.json: {e}")
        return {}

# -------------------------------------------------------------------------
# Home route: load player list fresh every time
# -------------------------------------------------------------------------
@app.route("/")
def index():
    players = load_players()
    return render_template("index.html", players=players)

# -------------------------------------------------------------------------
# Fetch season stats for selected players
# -------------------------------------------------------------------------
@app.route("/live_stats", methods=["POST"])
def live_stats():
    ids = request.form.getlist("player_ids[]")
    results = {}

    for pid in ids:
        try:
            # NHL Player Detail endpoint (reliable)
            url = f"https://api-web.nhle.com/v1/player/{pid}/landing"
            r = requests.get(url, timeout=10)
            data = r.json()

            # Extract player name and season stats
            first = data.get("firstName", "")
            last = data.get("lastName", "")
            full_name = f"{first} {last}".strip()

            stats = data.get("featuredStats", {}).get("regularSeason", {}).get("subSeason", {})
            goals = stats.get("goals", 0)
            shots = stats.get("shots", 0)
            assists = stats.get("assists", 0)
            points = goals + assists
            games = stats.get("gamesPlayed", 0)

            results[full_name] = {
                "label": "2024–25 Season Totals",
                "shots": shots,
                "goals": goals,
                "points": points,
                "games": games
            }

        except Exception as e:
            print(f"[ERROR] Fetching stats for player {pid}: {e}")
            results[f"Player {pid}"] = {
                "label": "Error fetching data",
                "shots": 0,
                "goals": 0,
