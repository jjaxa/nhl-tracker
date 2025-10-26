import json
import requests

OUTPUT_FILE = "players.json"

def fetch_all_players():
    """
    Fetch all active NHL skaters (excluding goalies) by looping through each team.
    """
    base_url = "https://api-web.nhle.com/v1/roster/"
    team_url = "https://api-web.nhle.com/v1/standings/now"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        print("[INFO] Fetching active teams...")
        teams_data = requests.get(team_url, headers=headers, timeout=30).json()
    except Exception as e:
        print(f"[ERROR] Could not fetch team list: {e}")
        return {}

    players = {}

    # Loop through each team
    for record in teams_data.get("standings", []):
        team_abbrev = record["teamAbbrev"]["default"]
        roster_url = f"{base_url}{team_abbrev}/20242025"
        print(f"[INFO] Fetching roster for {team_abbrev}...")

        try:
            r = requests.get(roster_url, headers=headers, timeout=15)
            data = r.json()

            for group in ["forwards", "defensemen"]:
                for player in data.get(group, []):
                    name = f"{player['firstName']['default']} {player['lastName']['default']}"
                    players[name] = player["id"]
        except Exception as e:
            print(f"[WARN] Failed roster for {team_abbrev}: {e}")
            continue

    print(f"[SUCCESS] Loaded {len(players)} total skaters.")
    return dict(sorted(players.items()))


def save_players(players):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(players, f, indent=2)
    print(f"[SAVED] {len(players)} players saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    skaters = fetch_all_players()
    save_players(skaters)
