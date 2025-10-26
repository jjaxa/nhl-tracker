import json
import time
import requests

# Primary NHL API endpoint for team + roster data
TEAM_URL = "https://statsapi.web.nhl.com/api/v1/teams"
ROSTER_URL = "https://statsapi.web.nhl.com/api/v1/teams/{}/roster"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/122.0.0.0 Safari/537.36"
}


def get_teams():
    """Fetch all NHL teams."""
    try:
        r = requests.get(TEAM_URL, headers=HEADERS, timeout=20)
        r.raise_for_status()
        data = r.json()
        return [team["id"] for team in data.get("teams", [])]
    except Exception as e:
        print(f"[ERROR] Could not fetch teams: {e}")
        return []


def get_roster(team_id):
    """Fetch roster for a given team ID."""
    try:
        r = requests.get(ROSTER_URL.format(team_id), headers=HEADERS, timeout=20)
        r.raise_for_status()
        data = r.json()
        return data.get("roster", [])
    except Exception as e:
        print(f"[WARN] Could not fetch roster for team {team_id}: {e}")
        return []


def main():
    players = {}
    team_ids = get_teams()

    if not team_ids:
        print("❌ No teams found. Exiting.")
        open("players.json", "w").write("{}")
        return

    print(f"[INFO] Found {len(team_ids)} teams.")
    for tid in team_ids:
        roster = get_roster(tid)
        time.sleep(0.3)  # avoid hitting rate limits
        for p in roster:
            position = p.get("position", {}).get("code", "")
            if position == "G":
                continue  # skip goalies
            pid = p.get("person", {}).get("id")
            name = p.get("person", {}).get("fullName")
            if pid and name:
                players[name] = pid
        print(f"[INFO] Processed team {tid}, total players so far: {len(players)}")

    # Sort alphabetically by name
    sorted_players = dict(sorted(players.items()))

    with open("players.json", "w", encoding="utf-8") as f:
        json.dump(sorted_players, f, indent=2, ensure_ascii=False)

    print(f"✅ Wrote players.json with {len(sorted_players)} skaters (no goalies).")


if __name__ == "__main__":
    main()
