from flask import Flask, jsonify, request, render_template
from api_handler import NBADataHandler  # Import your existing API handler
from data_processor import travel_data_to_json  # Import the updated data processor

app = Flask(__name__)
handler = NBADataHandler()

@app.route('/')
def home():
    return render_template('base.html')  # Render the main page

@app.route('/api/player-travel-data')
def get_player_travel_data():
    # Retrieve parameters from the request
    name = request.args.get('name')
    season = request.args.get('season', '2023-24')
    playoffs_only = request.args.get('playoffsOnly', 'false').lower() == 'true'  # Handle playoffsOnly flag

    if not name:
        return jsonify({"error": "Player or Team name is required."}), 400

    # Determine if it's a player or team search
    player_info = handler.find_player_by_name(name)
    team_info = handler.find_team_by_name(name)

    # Handle player data if found
    if player_info:
        player_id = player_info[0]['id']
        game_logs = handler.get_player_game_logs(player_id, season, playoffs_only)  # Pass playoffs_only flag

        # Check if no playoff games were found when playoffs_only is True
        if playoffs_only and game_logs.empty:
            return jsonify({"message": "No playoff games detected for this player in the selected season."})

        player_output = travel_data_to_json(game_logs)
        return jsonify(player_output)  # Return the processed JSON data to the frontend

    # Handle team data if found
    elif team_info:
        team_id = team_info[0]['id']
        game_logs = handler.get_team_game_logs(team_id, season, playoffs_only)  # Pass playoffs_only flag

        # Check if no playoff games were found when playoffs_only is True
        if playoffs_only and game_logs.empty:
            return jsonify({"message": "No playoff games detected for this team in the selected season."})

        team_output = travel_data_to_json(game_logs)
        return jsonify(team_output)  # Return the processed JSON data to the frontend

    else:
        # Return error if neither player nor team is found
        return jsonify({"error": "Player or Team not found."}), 404

if __name__ == '__main__':
    app.run(debug=True)
