from flask import Flask, render_template, request, jsonify
import json, requests

app = Flask(__name__)

# -------------------------------------------------------------------------
# Load players from local JSON
# -------------------------------------------------------------------------
def load_local_players():
    try:
        with open("players.json", "r") as f:
            data = json.load(f)
        print(f"[INFO] Loaded {len(data)} players from local file.")
        return data
    except Exception as e:
        print(f"[ERROR] Could not load players.json: {e}")
        return {}

# -------------------------------------------------------------------------
# Fetch player stats
# -------------------------------------------------------------------------
def get_player_stats(player_ids):
    stats = []
    headers = {"User-Agent": "Mozilla/5.0"}

    for pid in player_ids:
        try:
            url = f"https://api-web.nhle.com/v1/player/{pid}/landing"
            resp = requests.get(url, headers=headers, timeout=15)
            data = resp.json()

            latest = data.get("careerTotals", {}).get("regularSeason", {}).get("subSeason", [])
            if latest:
                season = latest[-1]
                stats.append({
                    "name": f"{data.get('firstName', '')} {data.get('lastName', '')}",
                    "team": data.get("currentTeamAbbrev", ""),
                    "gamesPlayed": season.get("gamesPlayed", 0),
                    "goals": season.get("goals", 0),
                    "assists": season.get("assists", 0),
                    "points": season.get("points", 0),
                    "shots": season.get("shots", 0)
                })
        except Exception as e:
            print(f"[WARN] Failed to fetch stats for {pid}: {e}")

    return stats

# -------------------------------------------------------------------------
# Routes
# -------------------------------------------------------------------------
@app.route("/")
def index():
    players = load_local_players()
    return render_template("index.html", players=players)

@app.route("/live_stats", methods=["POST"])
def live_stats():
    ids = request.form.getlist("player_ids[]")
    data = get_player_stats(ids)
    return jsonify(data)

# -------------------------------------------------------------------------
# Gunicorn entry point
# -------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
