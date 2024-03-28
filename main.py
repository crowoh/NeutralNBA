from api_handler import NBADataHandler
from data_processor import fetch_game_logs, analyze_travel
from datetime import datetime

def main():
    # Initializing handler for fetching data
    handler = NBADataHandler()

    # Season settings
    season = '2023-24'

    # Entities (players and teams) for analysis
    entities_to_analyze = [
        {'type': 'player', 'name': 'Seth Curry'},
        {'type': 'player', 'name': 'Stephen Curry'},
        {'type': 'player', 'name': 'Lebron James'},
        {'type': 'team', 'name': 'Golden State Warriors'}
    ]

    for entity in entities_to_analyze:
        if entity['type'] == 'player':
            print(f"\n--- Analyzing Player: {entity['name']} ---")
            player_info = handler.find_player_by_name(entity['name'])
            print(f"Player Info for {entity['name']}: {player_info}")  # Debug print
            if player_info:
                player_id = player_info[0]['id']
                home_team_abbreviation = handler.get_player_team_abbreviation(player_id)  # Ensure this method is implemented correctly
                if home_team_abbreviation:
                    game_logs = handler.get_player_game_logs(player_id, season)
                else:
                    print(f"Could not find team abbreviation for {entity['name']}.")
                    continue
            else:
                print(f"Player not found: {entity['name']}.")
                continue
        elif entity['type'] == 'team':
            print(f"\n--- Analyzing Team: {entity['name']} ---")
            team_info = handler.find_team_by_name(entity['name'])
            if team_info:
                team_id = team_info[0]['id']
                home_team_abbreviation = team_info[0]['abbreviation']  # Ensure this returns the correct abbreviation
                game_logs = handler.get_team_game_logs(team_id, season)
            else:
                print(f"Team not found: {entity['name']}.")
                continue

        # Analyze travel for both players and teams
        total_distance_km, total_fuel_gallons, total_emissions_kg, total_fuel_cost = analyze_travel(game_logs, home_team_abbreviation, analyze_losses_only=False)
        print(f"Total travel: {total_distance_km:.2f} km, Fuel: {total_fuel_gallons:.2f} gallons, Emissions: {total_emissions_kg:.2f} kg CO2, Cost: ${total_fuel_cost:.2f}")

        # If analyzing losses only
        total_distance_km, total_fuel_gallons, total_emissions_kg, total_fuel_cost = analyze_travel(game_logs, home_team_abbreviation, analyze_losses_only=True)
        print(f"Loss travel: {total_distance_km:.2f} km, Fuel: {total_fuel_gallons:.2f} gallons, Emissions: {total_emissions_kg:.2f} kg CO2, Cost: ${total_fuel_cost:.2f}")

if __name__ == "__main__":
    main()
