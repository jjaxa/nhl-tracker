from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# Modern NHL Stats API endpoint (stable, public)
PLAYER_API = "https://api.nhle.com/stats/rest/en/skater/summary"
PLAYER_DETAIL = "https://api.nhle.com/stats/rest/en/skater/{}"

# -------------------------------------------------------------------------
# Fetch all current skaters
# -------------------------------------------------------------------------
def get_all_skaters():
    print("[INFO] Fetching player list from NHL API...")
    players = {}

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/122.0.0.0 Safari/537.36"
    }

    params = {
        "isAggregate": "false",
        "isGame": "false",
        "sort": '[{"property":"points","direction":"DESC"}]',
        "start": 0,
        "limit": 5000,
        "factCayenneExp": "gameTypeId=2"
    }

    try:
        resp = requests.get(PLAYER_API, params=params, headers=headers, timeout=20)
        data = resp.json()
        for row in data.get("data", []):
            name = f"{row['playerFirstName']} {row['playerLastName']}"
            players[name] = row["playerId"]
        print(f"[INFO] Loaded {len(players)} skaters.")
    except Exception as e:
        print(f"[ERROR] Could not fetch player list: {e}")

    return dict(sorted(players.items()))

def index():
    players = get_all_skaters()
    return render_template("index.html", players=players)

@app.route("/live_stats", methods=["POST"])
def live_stats():
    ids = request.form.getlist("player_ids[]")
    data = get_player_stats(ids)
    return jsonify(data)

# -------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
