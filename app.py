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

            # Extract key live stat data if available
            stats = data.get("featuredStats", {}).get("regularSeason", {}).get("subSeason", {})
            shots = stats.get("shots", 0)
            goals = stats.get("goals", 0)

            name = data["player"]["fullName"]
            results[name] = {"goals": goals, "shots": shots}

        except Exception as e:
            print(f"[WARN] Failed to get stats for {pid}: {e}")

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
