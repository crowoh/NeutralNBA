import pandas as pd
import numpy as np
from nba_api.stats.endpoints import playergamelog, teamgamelog, commonplayerinfo
from nba_api.stats.static import teams
from datetime import datetime

# Constants for calculations
AVG_FUEL_CONSUMPTION_PER_KM = 0.36  # gallons per kilometer
KG_CO2_PER_GALLON_JET_FUEL = 9.57  # kg CO2 emissions per gallon of jet fuel
COST_PER_GALLON_JET_FUEL = 2.22  # cost per gallon of jet fuel in dollars

nba_arenas_coordinates = {
    'ATL': (33.7573, -84.3963),  # Atlanta Hawks - State Farm Arena
    'BOS': (42.3662, -71.0621),  # Boston Celtics - TD Garden
    'BKN': (40.6826, -73.9745),  # Brooklyn Nets - Barclays Center
    'CHA': (35.2255, -80.8390),  # Charlotte Hornets - Spectrum Center
    'CHI': (41.8807, -87.6742),  # Chicago Bulls - United Center
    'CLE': (41.4965, -81.6882),  # Cleveland Cavaliers - Rocket Mortgage FieldHouse
    'DAL': (32.7902, -96.8102),  # Dallas Mavericks - American Airlines Center
    'DEN': (39.7487, -105.0077),  # Denver Nuggets - Ball Arena
    'DET': (42.3411, -83.0553),  # Detroit Pistons - Little Caesars Arena
    'GSW': (37.7680, -122.3878),  # Golden State Warriors - Chase Center
    'HOU': (29.7508, -95.3621),  # Houston Rockets - Toyota Center
    'IND': (39.7631, -86.1555),  # Indiana Pacers - Gainbridge Fieldhouse
    'LAC': (34.0430, -118.2673),  # LA Clippers - Crypto.com Arena
    'LAL': (34.0430, -118.2673),  # LA Lakers - Crypto.com Arena
    'MEM': (35.1380, -90.0506),  # Memphis Grizzlies - FedExForum
    'MIA': (25.7814, -80.1866),  # Miami Heat - FTX Arena
    'MIL': (43.0436, -87.9169),  # Milwaukee Bucks - Fiserv Forum
    'MIN': (44.9795, -93.2761),  # Minnesota Timberwolves - Target Center
    'NOP': (29.9489, -90.0811),  # New Orleans Pelicans - Smoothie King Center
    'NYK': (40.7505, -73.9934),  # New York Knicks - Madison Square Garden
    'OKC': (35.4634, -97.5151),  # Oklahoma City Thunder - Paycom Center
    'ORL': (28.5392, -81.3838),  # Orlando Magic - Amway Center
    'PHI': (39.9018, -75.1714),  # Philadelphia 76ers - Wells Fargo Center
    'PHX': (33.4457, -112.0712),  # Phoenix Suns - Footprint Center
    'POR': (45.5315, -122.6664),  # Portland Trail Blazers - Moda Center
    'SAC': (38.5802, -121.4994),  # Sacramento Kings - Golden 1 Center
    'SAS': (29.4268, -98.4375),  # San Antonio Spurs - AT&T Center
    'TOR': (43.6435, -79.3791),  # Toronto Raptors - Scotiabank Arena
    'UTA': (40.7683, -111.9011),  # Utah Jazz - Vivint Arena
    'WAS': (38.8981, -77.0209),  # Washington Wizards - Capital One Arena
}

def parse_date(date_string):
    try:
        return datetime.strptime(date_string, '%a, %b %d')  # Adjust format if necessary
    except ValueError:
        return None  # Or raise an error
def fetch_game_logs(entity, entity_id, season='2023-24'):
    if entity == 'player':
        response = playergamelog.PlayerGameLog(player_id=entity_id, season=season)
    elif entity == 'team':
        response = teamgamelog.TeamGameLog(team_id=entity_id, season=season)
    else:
        raise ValueError("Entity must be either 'player' or 'team'")

    game_logs_df = response.get_data_frames()[0]

    # Annotate with 'HOME_OR_AWAY' based on 'MATCHUP'
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


def find_team_abbreviation_for_player(player_id):
    """
    Fetch the team abbreviation for a given player ID.

    Parameters:
    - player_id (str): The NBA API player ID.

    Returns:
    - str: The team abbreviation (e.g., 'GSW' for Golden State Warriors).
    """
    # Fetch player info
    player_info = commonplayerinfo.CommonPlayerInfo(player_id=player_id).get_normalized_dict()

    # Extract the team ID from player info
    team_id = player_info['CommonPlayerInfo'][0]['TEAM_ID']

    # Fetch all NBA teams
    all_teams = teams.get_teams()

    # Find the team by ID and return its abbreviation
    team = next((team for team in all_teams if team['id'] == team_id), None)
    if team:
        return team['abbreviation']

    return None
