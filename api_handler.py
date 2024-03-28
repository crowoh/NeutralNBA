from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import commonplayerinfo, teaminfocommon, playergamelog, teamgamelog
import pandas as pd

class NBADataHandler:
    def __init__(self):
        pass

    def get_player_info(self, player_id):
        info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
        return info.common_player_info.get_data_frame()

    def get_team_info(self, team_id):
        info = teaminfocommon.TeamInfoCommon(team_id=team_id)
        return info.team_info_common.get_data_frame()

    def get_player_game_logs(self, player_id, season='2023-24'):
        logs = playergamelog.PlayerGameLog(player_id=player_id, season=season).get_data_frames()[0]
        logs['LOCATION'] = logs['MATCHUP'].apply(lambda x: 'Road' if '@' in x else 'Home')
        return logs

    def get_team_game_logs(self, team_id, season='2023-24'):
        logs = teamgamelog.TeamGameLog(team_id=team_id, season=season).get_data_frames()[0]
        logs['LOCATION'] = logs['MATCHUP'].apply(lambda x: 'Road' if '@' in x else 'Home')
        return logs

    @staticmethod
    def find_player_by_name(name):
        return players.find_players_by_full_name(name)

    @staticmethod
    def find_team_by_name(name):
        return teams.find_teams_by_full_name(name)

    def get_player_team_abbreviation(self, player_id):
        try:
            player_info = self.get_player_info(player_id)
            team_abbreviation = player_info['TEAM_ABBREVIATION'].iloc[0]
            return team_abbreviation
        except Exception as e:
            print(f"Error fetching team abbreviation for player ID {player_id}: {e}")
            return None
