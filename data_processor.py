import pandas as pd
from math import radians, sin, cos, sqrt, asin
from arenas import nba_arenas_coordinates as arenas

# Constants for calculations
AVG_FUEL_CONSUMPTION_PER_KM = 0.36
KG_CO2_PER_GALLON_JET_FUEL = 9.57
COST_PER_GALLON_JET_FUEL = 2.22

nba_arenas_coordinates = arenas

def haversine(lon1, lat1, lon2, lat2):
    R = 6371  # Radius of the Earth in kilometers
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return R * c

def calculate_distance(game_logs_df, initial_team_abbreviation, return_road_trips=False):
    game_logs_df['GAME_DATE'] = pd.to_datetime(game_logs_df['GAME_DATE'], format='%b %d, %Y')
    game_logs_df.sort_values('GAME_DATE', ascending=True, inplace=True)

    detailed_trips = []
    current_team_abbreviation = initial_team_abbreviation
    home_coords = nba_arenas_coordinates.get(initial_team_abbreviation)
    trade_occurred = False
    trade_date = None

    for index, row in game_logs_df.iterrows():
        game_date = row['GAME_DATE'].strftime('%Y-%m-%d')
        matchup = row['MATCHUP']
        player_team_abbreviation = matchup.split(' ')[0]  # Extract the player's team

        if player_team_abbreviation != current_team_abbreviation:
            trade_occurred = True
            trade_date = game_date
            current_team_abbreviation = player_team_abbreviation
            home_coords = nba_arenas_coordinates.get(current_team_abbreviation)  # Update to new home

        opponent_abbreviation = matchup.split(' ')[-1]  # Opponent team abbreviation
        home_or_away = 'away' if '@' in matchup else 'home'
        current_location = opponent_abbreviation if home_or_away == 'away' else current_team_abbreviation
        start_coords = nba_arenas_coordinates.get(current_team_abbreviation)
        end_coords = nba_arenas_coordinates.get(current_location)

        if home_or_away == 'home':
            end_coords = home_coords  # Ensure home games use updated home coordinates after trade

        distance = haversine(start_coords[1], start_coords[0], end_coords[1], end_coords[0]) if start_coords and end_coords else 0

        segment = {
            "start": {"city": current_team_abbreviation, "coords": start_coords},
            "end": {"city": current_location, "coords": end_coords},
            "date": game_date,
            "distance": distance,
            "matchup": matchup,
            "type": home_or_away,
            "traded": trade_occurred
        }
        detailed_trips.append(segment)
        trade_occurred = False  # Reset the trade flag after logging the segment

    return (detailed_trips, trade_date) if return_road_trips else sum(trip['distance'] for trip in detailed_trips)

def travel_data_to_json(game_logs_df):
    # Automatically detect the initial team from the first game
    initial_team_abbreviation = game_logs_df.iloc[0]['TEAM_ABBREVIATION']
    detailed_trips, trade_date = calculate_distance(game_logs_df, initial_team_abbreviation, return_road_trips=True)

    player_output = {
        "Player/Team": initial_team_abbreviation,
        "Total Games": len(detailed_trips),
        "Games": [{
            "start": {"city": trip["start"]["city"], "coords": trip["start"]["coords"]},
            "end": {"city": trip["end"]["city"], "coords": trip["end"]["coords"]},
            "date": trip["date"],
            "distance": trip["distance"],
            "matchup": trip["matchup"],
            "type": trip["type"],
            "traded": trip["traded"]
        } for trip in detailed_trips],
        "Traded During Season": trade_date is not None,
        "Trade Date": trade_date if trade_date else "No trade"
    }

    return player_output


def analyze_travel(game_logs, analyze_losses_only=False):
    if analyze_losses_only:
        game_logs = game_logs[game_logs['WL'] == 'L']

    # Automatically use the correct initial team abbreviation from the first game
    initial_team_abbreviation = game_logs.iloc[0]['TEAM_ABBREVIATION']
    
    total_distance_km, trade_occurred, trade_date = calculate_distance(game_logs, initial_team_abbreviation)
    total_fuel_gallons = calculate_jet_fuel_usage(total_distance_km)
    total_emissions_kg = calculate_emissions(total_fuel_gallons)
    total_fuel_cost = calculate_fuel_cost(total_fuel_gallons)

    return total_distance_km, total_fuel_gallons, total_emissions_kg, total_fuel_cost

def calculate_jet_fuel_usage(distance_km):
    return distance_km * AVG_FUEL_CONSUMPTION_PER_KM

def calculate_emissions(fuel_gallons):
    return fuel_gallons * KG_CO2_PER_GALLON_JET_FUEL

def calculate_fuel_cost(fuel_gallons):
    return fuel_gallons * COST_PER_GALLON_JET_FUEL