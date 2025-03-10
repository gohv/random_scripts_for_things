#!/usr/bin/env python3
"""
Games to Discord Webhook with Screenshots

This script fetches information about upcoming game releases from the RAWG.io API,
including screenshots, and sends them to a Discord webhook. It formats the game data 
in a readable way using Discord's markdown formatting and embeds a screenshot for each game.

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
        "rawg_api_key": "",
        "discord_webhook_url": ""
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

def fetch_game_screenshot(api_key: str, game_id: int) -> Optional[str]:
    """
    Fetch a screenshot for a game from RAWG.io API.
    
    Args:
        api_key: RAWG.io API key
        game_id: ID of the game
    
    Returns:
        URL of a screenshot or None if not found
    """
    # API endpoint for screenshots
    url = f"https://api.rawg.io/api/games/{game_id}/screenshots"
    
    # Parameters for the API request
    params = {
        "key": api_key
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        
        # Return the URL of the first screenshot if available
        if results and len(results) > 0:
            return results[0].get("image")
        
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching screenshot for game {game_id}: {str(e)}")
        return None

def format_discord_message(games: List[Dict[str, Any]], screenshots: Dict[int, str]) -> Dict[str, Any]:
    """
    Format game data into a Discord message with screenshots.
    
    Args:
        games: List of game data dictionaries
        screenshots: Dictionary mapping game IDs to screenshot URLs
    
    Returns:
        Formatted Discord message payload
        
    Note:
        Discord has a limit of 10 embeds per message, so we use 1 for the header
        and up to 9 for individual games.
    """
    if not games:
        return {"content": "No upcoming games found!"}
    
    # Create an array to hold multiple embeds
    embeds = []
    
    # Create a main embed with title and description
    main_embed = {
        "title": "\U0001F3AE Upcoming Game Releases \U0001F3AE",
        "color": 0x7289DA,  # Discord blue color
        "description": "Here are the upcoming game releases with screenshots:",
    }
    
    embeds.append(main_embed)
    
    # Create a separate embed for each game with its screenshot
    # Limit to 9 games (+ 1 header embed = 10 total) to comply with Discord's limit of 10 embeds per message
    for game in games[:9]:
        game_id = game.get("id")
        name = game.get("name", "Unknown Title")
        release_date = game.get("released", "TBA")
        # Handle None platforms value by using empty list as fallback
        platforms_list = game.get("platforms") or []
        platforms = ", ".join([p.get("platform", {}).get("name", "") for p in platforms_list if p.get("platform")])
        
        # Create embed for this game
        game_embed = {
            "title": name,
            "color": 0x3498DB,  # Different color for game embeds
            "fields": [
                {
                    "name": "Release Date",
                    "value": f"\U0001F4C5 **{release_date}**",
                    "inline": True
                }
            ]
        }
        
        # Add platforms if available
        if platforms:
            game_embed["fields"].append({
                "name": "Platforms",
                "value": f"\U0001F3AE {platforms}",
                "inline": True
            })
        
        # Add screenshot if available
        if game_id in screenshots and screenshots[game_id]:
            game_embed["image"] = {
                "url": screenshots[game_id]
            }
        else:
            # Add a note if no screenshot is available
            game_embed["footer"] = {
                "text": "No screenshot available for this game"
            }
        
        embeds.append(game_embed)
    
    # Create current timestamp for the footer of the main embed
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    embeds[0]["footer"] = {
        "text": f"Data from RAWG.io • Generated on {current_time}"
    }
    
    return {"embeds": embeds}

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
    print("Games to Discord Webhook with Screenshots")
    print("----------------------------------------")
    
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
    
    # Fetch screenshots for each game
    print("Fetching screenshots for games...")
    screenshots = {}
    for game in games:
        game_id = game.get("id")
        if game_id:
            print(f"  Fetching screenshot for: {game.get('name', 'Unknown')}")
            screenshot_url = fetch_game_screenshot(config["rawg_api_key"], game_id)
            if screenshot_url:
                screenshots[game_id] = screenshot_url
            else:
                print(f"  No screenshot found for: {game.get('name', 'Unknown')}")
    
    print(f"Found screenshots for {len(screenshots)} out of {len(games)} games.")
    
    print("Formatting message for Discord...")
    # Note: Only the first 9 games will be included in the Discord message due to Discord's embed limits
    discord_payload = format_discord_message(games, screenshots)
    
    print("Sending message to Discord...")
    if send_to_discord(config["discord_webhook_url"], discord_payload):
        print("Success! Message with screenshots sent to Discord.")
    else:
        print("Failed to send message to Discord.")

if __name__ == "__main__":
    main()

