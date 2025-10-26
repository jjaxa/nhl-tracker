import json
import requests

OUTPUT_FILE = "players.json"

def fetch_skaters():
    """
    Fetch all active NHL skaters (excluding goalies) using the public stats API.
    """
    url = "https://api-web.nhle.com/v1/roster/active/20242025"  # Active player list for 2024–25
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    try:
        print(f"[INFO] Fetching from {url}")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"[ERROR] Could not fetch data: {e}")
        return {}

    players = {}

    # Parse players from the roster data
    for player in data.get("forwards", []) + data.get("defensemen", []):
        name = f"{player['firstName']['default']} {player['lastName']['default']}"
        player_id = player.get("id")
        players[name] = player_id

    print(f"[INFO] Loaded {len(players)} active skaters.")
    return players


def save_players(players):
    """
    Save players to players.json
    """
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(players, f, indent=2)
    print(f"[SUCCESS] Saved {len(players)} skaters to {OUTPUT_FILE}")


if __name__ == "__main__":
    skaters = fetch_skaters()
    save_players(skaters)
