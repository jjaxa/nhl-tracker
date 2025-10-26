from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

NHL_API_BASE = "https://statsapi.web.nhl.com/api/v1"

def get_all_players():
    players = {}
    try:
        # Use a proxy service to fetch NHL API data safely
        proxy_url = "https://api.codetabs.com/v1/proxy?quest=https://statsapi.web.nhl.com/api/v1/teams"
        teams = requests.get(proxy_url, timeout=15).json()["teams"]

        for team in teams:
            team_id = team["id"]
            roster_proxy = f"https://api.codetabs.com/v1/proxy?quest=https://statsapi.web.nhl.com/api/v1/teams/{team_id}/roster"
            roster = requests.get(roster_proxy, timeout=15).json()
            for player in roster["roster"]:
                players[player["person"]["fullName"]] = player["person"]["id"]
    except Exception as e:
        print(f"[WARN] Unable to fetch players: {e}")
    return dict(sorted(players.items()))


@app.route("/")
def index():
    players = get_all_players()

    if not players:
        # if fetch failed, show a friendly message
        return render_template(
            "index.html",
            players={},
            error="Could not load players (API or proxy limit hit). Try reloading in a minute."
        )
    
    return render_template("index.html", players=players, error=None)


@app.route("/get_stats", methods=["POST"])
def get_stats():
    player_ids = request.form.getlist("player_ids[]")
    today = datetime.now().strftime("%Y-%m-%d")
    schedule = requests.get(f"{NHL_API_BASE}/schedule?date={today}").json()
    results = []

    for pid in player_ids:
        for date in schedule.get("dates", []):
            for game in date.get("games", []):
                game_pk = game["gamePk"]
                box = requests.get(f"{NHL_API_BASE}/game/{game_pk}/boxscore").json()
                for side in ("home", "away"):
                    for pdata in box["teams"][side]["players"].values():
                        if str(pdata["person"]["id"]) == pid:
                            stats = pdata.get("stats", {}).get("skaterStats", {})
                            results.append({
                                "name": pdata["person"]["fullName"],
                                "shots": stats.get("shots", 0),
                                "goals": stats.get("goals", 0),
                                "assists": stats.get("assists", 0),
                                "toi": stats.get("timeOnIce", "0:00")
                            })
    return jsonify(results)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
