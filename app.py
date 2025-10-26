from flask import Flask, render_template, request, jsonify
import json
import requests
import os

app = Flask(__name__)

# -------------------------------------------------------------------------
# Load players.json (generated automatically by GitHub Actions)
# -------------------------------------------------------------------------
def load_players():
    try:
        with open("players.json", "r", encoding="utf-8") as f:
            players = json.load(f)
            print(f"[INFO] Loaded {len(players)} players from players.json")
            return players
    except Exception as e:
        print(f"[WARN] Could not load players.json: {e}")
        return {}

PLAYERS = load_players()

# -------------------------------------------------------------------------
# Helper: fetch live stats for a few selected players
# -------------------------------------------------------------------------
def get_live_stats(player_ids):
    results = {}

    for pid in player_ids:
        try:
            url = f"https://api-web.nhle.com/v1/player/{pid}/landing"
            r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            data = r.json()

            # Player name
            name = data.get("player", {}).get("fullName", f"Player {pid}")

            # Default stats
            goals = 0
            shots = 0
            label = "Season Totals"

            featured = data.get("featuredStats", {})
            reg = featured.get("regularSeason", {}).get("subSeason", {})

            # Pull season totals
            goals = reg.get("goals", 0)
            shots = reg.get("shots", 0)

            # Check if a live game is happening
            live = featured.get("currentTeam", {}).get("liveData", {})
            if live:
                label = "Live Game Stats"
                goals = live.get("goals", goals)
                shots = live.get("shots", shots)

            results[name] = {
                "label": label,
                "goals": goals if isinstance(goals, int) else 0,
                "shots": shots if isinstance(shots, int) else 0
            }

        except Exception as e:
            print(f"[WARN] Failed to get stats for {pid}: {e}")
            results[f"Player {pid}"] = {
                "label": "Unavailable",
                "goals": 0,
                "shots": 0
            }

    return results



# -------------------------------------------------------------------------
# Routes
# -------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html", players=PLAYERS)

@app.route("/live_stats", methods=["POST"])
def live_stats():
    ids = request.form.getlist("player_ids[]")
    stats = get_live_stats(ids)
    return jsonify(stats)

# -------------------------------------------------------------------------
# Flask entrypoint (Render uses gunicorn, so no app.run() here)
# -------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
