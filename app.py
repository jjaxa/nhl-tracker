from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

NHL_API_BASE = "https://statsapi.web.nhl.com/api/v1"

def get_all_players():
    players = {}
    urls = [
        "https://statsapi.web.nhl.com/api/v1/teams",
        "https://api.codetabs.com/v1/proxy?quest=https://statsapi.web.nhl.com/api/v1/teams",
        "https://thingproxy.freeboard.io/fetch/https://statsapi.web.nhl.com/api/v1/teams"
    ]

    for base in urls:
        try:
            print(f"[INFO] Trying player list via {base}")
            teams = requests.get(base, timeout=15).json().get("teams", [])
            if not teams:
                continue

            for team in teams:
                tid = team.get("id")
                if not tid:
                    continue

                roster_urls = [
                    f"https://statsapi.web.nhl.com/api/v1/teams/{tid}/roster",
                    f"https://api.codetabs.com/v1/proxy?quest=https://statsapi.web.nhl.com/api/v1/teams/{tid}/roster",
                    f"https://thingproxy.freeboard.io/fetch/https://statsapi.web.nhl.com/api/v1/teams/{tid}/roster"
                ]

                for roster_url in roster_urls:
                    try:
                        roster = requests.get(roster_url, timeout=15).json().get("roster", [])
                        for p in roster:
                            players[p["person"]["fullName"]] = p["person"]["id"]
                        break
                    except Exception:
                        continue
            if players:
                print(f"[INFO] Loaded {len(players)} players successfully.")
                return dict(sorted(players.items()))
        except Exception as e:
            print(f"[WARN] {base} failed: {e}")

    print("[ERROR] All player source attempts failed.")
    return {}



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
