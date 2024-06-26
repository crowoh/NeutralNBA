from flask import Flask, jsonify, request, render_template
import pandas as pd
from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import commonplayerinfo
from data_processor import fetch_game_logs, travel_data_to_json, find_team_abbreviation_for_player

app = Flask(__name__)

def find_player_id(player_name):
    all_players = players.get_players()
    player = next((player for player in all_players if player['full_name'].lower() == player_name.lower()), None)
    return player['id'] if player else None

@app.route('/')
def home():
    return render_template('base.html')

@app.route('/api/player-travel-data')
def get_player_travel_data():
    player_name = request.args.get('name')
    season = request.args.get('season', '2023-24')  # Updated default season to current
    playoffs_only = request.args.get('playoffsOnly', 'false').lower() == 'true'  # Capture playoffsOnly parameter

    if not player_name:
        return jsonify({"error": "Player name is required."}), 400

    player_id = find_player_id(player_name)
    if not player_id:
        return jsonify({"error": "Player not found."}), 404

    # Determine the type of season data to fetch
    season_type = 'Playoffs' if playoffs_only else 'Regular Season'
    game_logs_df = fetch_game_logs('player', player_id, season, season_type)  # Correctly pass season_type
    home_team_abbreviation = find_team_abbreviation_for_player(player_id, season)

    if not home_team_abbreviation:
        return jsonify({"error": "Could not determine player's team."}), 404

    travel_data = travel_data_to_json(game_logs_df, home_team_abbreviation)
    return jsonify(travel_data)

if __name__ == '__main__':
    app.run(debug=True)
