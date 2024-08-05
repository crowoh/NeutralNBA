import pandas as pd
import numpy as np
from nba_api.stats.endpoints import playergamelog, teamgamelog, commonplayerinfo
from nba_api.stats.static import teams
from datetime import datetime
from nba_coords import nba_arenas_coordinates as arenas


# Constants for calculations
AVG_FUEL_CONSUMPTION_PER_KM = 0.36  # gallons per kilometer
KG_CO2_PER_GALLON_JET_FUEL = 9.57  # kg CO2 emissions per gallon of jet fuel
COST_PER_GALLON_JET_FUEL = 2.22  # cost per gallon of jet fuel in dollars

nba_arenas_coordinates = arenas

def parse_date(date_string):
    try:
        return datetime.strptime(date_string, '%a, %b %d')  # Adjust format if necessary
    except ValueError:
        return None  # Or raise an error
def fetch_game_logs(entity, entity_id, season='2023-24', season_type='Regular Season'):
    if entity == 'player':
        response = playergamelog.PlayerGameLog(player_id=entity_id, season=season, season_type_all_star=season_type)
    elif entity == 'team':
        response = teamgamelog.TeamGameLog(team_id=entity_id, season=season, season_type_all_star=season_type)
    else:
        raise ValueError("Entity must be either 'player' or 'team'")

    game_logs_df = response.get_data_frames()[0]
    game_logs_df['HOME_OR_AWAY'] = game_logs_df['MATCHUP'].apply(lambda x: 'AWAY' if '@' in x else 'HOME')
    return game_logs_df


def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    r = 6371  # Radius of Earth in kilometers
    return c * r

def calculate_distance(game_logs_df, home_team_abbreviation, return_road_trips=False):
    game_logs_df['GAME_DATE'] = pd.to_datetime(game_logs_df['GAME_DATE'])
    game_logs_df.sort_values('GAME_DATE', ascending=True, inplace=True)

    detailed_trips = []
    previous_location = home_team_abbreviation

    for index, row in game_logs_df.iterrows():
        game_date = row['GAME_DATE'].strftime('%Y-%m-%d')
        matchup = row['MATCHUP']
        home_or_away = 'away' if '@' in matchup else 'home'
        opponent_abbreviation = matchup.split(' ')[2] if home_or_away == 'away' else matchup.split(' ')[0]

        current_location = opponent_abbreviation if home_or_away == 'away' else home_team_abbreviation
        start_coords = nba_arenas_coordinates[previous_location]
        end_coords = nba_arenas_coordinates[current_location]

        distance = 0 if home_or_away == 'home' and previous_location == home_team_abbreviation else haversine(start_coords[1], start_coords[0], end_coords[1], end_coords[0])

        segment = {
            "start": {"city": previous_location, "coords": start_coords},
            "end": {"city": current_location, "coords": end_coords},
            "date": game_date,
            "distance": distance,
            "matchup": matchup,
            "type": home_or_away
        }

        detailed_trips.append(segment)
        previous_location = current_location

    # Add a final segment for returning to home base if last game was away
    if previous_location != home_team_abbreviation:
        start_coords = nba_arenas_coordinates[previous_location]
        end_coords = nba_arenas_coordinates[home_team_abbreviation]
        distance = haversine(start_coords[1], start_coords[0], end_coords[1], end_coords[0])
        detailed_trips.append({
            "start": {"city": previous_location, "coords": start_coords},
            "end": {"city": home_team_abbreviation, "coords": end_coords},
            "date": "Returning home",
            "distance": distance,
            "matchup": "End of Season",
            "type": "return"
        })

    if return_road_trips:
        return detailed_trips

    # Calculate total distance from detailed trips
    total_distance_km = sum([trip['distance'] for trip in detailed_trips])
    return total_distance_km



def calculate_jet_fuel_usage(distance_km):
    return distance_km * AVG_FUEL_CONSUMPTION_PER_KM

def calculate_emissions(fuel_gallons):
    return fuel_gallons * KG_CO2_PER_GALLON_JET_FUEL

def calculate_fuel_cost(fuel_gallons):
    return fuel_gallons * COST_PER_GALLON_JET_FUEL

def analyze_travel(game_logs, home_team_abbreviation, analyze_losses_only=False):
    if analyze_losses_only:
        game_logs = game_logs[game_logs['WL'] == 'L']

    total_distance_km = calculate_distance(game_logs, home_team_abbreviation)
    total_fuel_gallons = calculate_jet_fuel_usage(total_distance_km)
    total_emissions_kg = calculate_emissions(total_fuel_gallons)
    total_fuel_cost = calculate_fuel_cost(total_fuel_gallons)

    return total_distance_km, total_fuel_gallons, total_emissions_kg, total_fuel_cost


def travel_data_to_json(game_logs_df, home_team_abbreviation):
    return calculate_distance(game_logs_df, home_team_abbreviation, return_road_trips=True)


def find_team_abbreviation_for_player(player_id, season):
    """
    Infer the team abbreviation for a given player ID for a specific season
    by analyzing game logs.

    Parameters:
    - player_id (str): The NBA API player ID.
    - season (str): The NBA season in 'YYYY-YY' format.

    Returns:
    - str: The team abbreviation for the specified season, or None if unable to determine.
    """
    try:
        # Fetch player game logs for the specified season
        game_logs = playergamelog.PlayerGameLog(player_id=player_id, season=season).get_data_frames()[0]

        if game_logs.empty:
            print(f"No game logs found for player ID {player_id} in season {season}")
            return None

        # Extract the team abbreviation from the first game log's MATCHUP field
        first_game_matchup = game_logs.iloc[0]['MATCHUP']
        team_abbreviation = first_game_matchup.split(" ")[0]
        return team_abbreviation
    except Exception as e:
        print(f"Error determining team abbreviation for player ID {player_id}, season {season}: {e}")
        return None