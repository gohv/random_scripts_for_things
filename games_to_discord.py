#!/usr/bin/env python3
"""
Games to Discord Webhook

This script fetches information about upcoming game releases from the RAWG.io API
and sends them to a Discord webhook. It formats the game data in a readable way
using Discord's markdown formatting.

Requirements:
- requests
- datetime (built-in)
- json (built-in)
- os (built-in)
"""

import requests
import json
import os
import datetime
from typing import Dict, List, Any, Optional

# Configuration file
CONFIG_FILE = "games_discord_config.json"

def load_config() -> Dict[str, str]:
    """Load configuration from file or create a new one."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Error: {CONFIG_FILE} is corrupted. Creating a new one.")
    
    # Default configuration
    config = {
        "rawg_api_key": "d430c2ba8e9146d7af53c78d27ba9a57",
        "discord_webhook_url": "https://discord.com/api/webhooks/1326943556698640455/CrfsqFW9DohoFB-Fu-z3Dl17uOHnnMN0XJ1xdt4klALd9JcNsEQ4OSNoXxpYkBXvq84Z"
    }
    
    # Ask for configuration values
    config["rawg_api_key"] = input("Enter your RAWG.io API key: ")
    config["discord_webhook_url"] = input("Enter your Discord webhook URL: ")
    
    # Save configuration
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)
    
    return config

def fetch_upcoming_games(api_key: str, count: int = 20) -> List[Dict[str, Any]]:
    """
    Fetch upcoming games from RAWG.io API.
    
    Args:
        api_key: RAWG.io API key
        count: Number of games to fetch
    
    Returns:
        List of game data dictionaries
    """
    # Get today's date and 180 days in the future
    today = datetime.date.today()
    future_date = today + datetime.timedelta(days=180)
    
    # Format dates for API
    today_str = today.isoformat()
    future_str = future_date.isoformat()
    
    # API endpoint
    url = f"https://api.rawg.io/api/games"
    
    # Parameters for the API request
    params = {
        "key": api_key,
        "dates": f"{today_str},{future_str}",
        "ordering": "released",
        "page_size": count
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching games from RAWG.io: {str(e)}")
        return []

def format_discord_message(games: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Format game data into a Discord message.
    
    Args:
        games: List of game data dictionaries
    
    Returns:
        Formatted Discord message payload
    """
    if not games:
        return {"content": "No upcoming games found!"}
    
    # Create a rich embed message
    embed = {
        "title": "🎮 Upcoming Game Releases 🎮",
        "color": 0x7289DA,  # Discord blue color
        "description": "Here are the upcoming game releases:",
        "fields": []
    }
    
    # Add each game as a field
    for game in games:
        name = game.get("name", "Unknown Title")
        release_date = game.get("released", "TBA")
        # Handle None platforms value by using empty list as fallback
        platforms_list = game.get("platforms") or []
        platforms = ", ".join([p.get("platform", {}).get("name", "") for p in platforms_list if p.get("platform")])
        
        # Create field for this game
        field = {
            "name": f"**{name}**",
            "value": f"📅 Release Date: **{release_date}**\n" +
                     (f"🎮 Platforms: {platforms}" if platforms else "")
        }
        embed["fields"].append(field)
    
    # Create current timestamp for the footer
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    embed["footer"] = {
        "text": f"Data from RAWG.io • Generated on {current_time}"
    }
    
    return {"embeds": [embed]}

def send_to_discord(webhook_url: str, payload: Dict[str, Any]) -> bool:
    """
    Send formatted message to Discord webhook.
    
    Args:
        webhook_url: Discord webhook URL
        payload: Formatted message payload
    
    Returns:
        True if successful, False otherwise
    """
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(webhook_url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error sending message to Discord: {str(e)}")
        return False

def main():
    """Main function to run the script."""
    print("Games to Discord Webhook")
    print("------------------------")
    
    # Load configuration
    config = load_config()
    
    # Check if configuration is valid
    if not config["rawg_api_key"] or not config["discord_webhook_url"]:
        print("Error: Missing API key or webhook URL. Please update the configuration.")
        return
    
    print("Fetching upcoming games...")
    games = fetch_upcoming_games(config["rawg_api_key"])
    
    if not games:
        print("No games found or error occurred.")
        return
    
    print(f"Found {len(games)} upcoming games.")
    print("Formatting message for Discord...")
    discord_payload = format_discord_message(games)
    
    print("Sending message to Discord...")
    if send_to_discord(config["discord_webhook_url"], discord_payload):
        print("Success! Message sent to Discord.")
    else:
        print("Failed to send message to Discord.")

if __name__ == "__main__":
    main()

