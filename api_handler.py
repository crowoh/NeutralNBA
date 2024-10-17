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

    def get_player_game_logs(self, player_id, season='2023-24', playoffs_only=False):
        # Set the season type based on the playoffs_only flag
        season_type = 'Playoffs' if playoffs_only else 'Regular Season'

        # Fetch the game logs using the SWAR NBA API
        logs = playergamelog.PlayerGameLog(
            player_id=player_id,
            season=season,
            season_type_all_star=season_type  # Pass season type for filtering
        ).get_data_frames()[0]
        if logs.empty:
            return pd.DataFrame()

        # Process the logs
        logs['TEAM_ABBREVIATION'] = logs['MATCHUP'].apply(self.extract_team_abbreviation)
        logs['LOCATION'] = logs['MATCHUP'].apply(lambda x: 'Road' if '@' in x else 'Home')
        logs['TRADED'] = logs['TEAM_ABBREVIATION'].ne(logs['TEAM_ABBREVIATION'].shift().bfill())

        return logs

    def get_team_game_logs(self, team_id, season='2023-24', playoffs_only=False):
        # Set the season type based on the playoffs_only flag
        season_type = 'Playoffs' if playoffs_only else 'Regular Season'

        # Fetch the team game logs using the SWAR NBA API
        logs = teamgamelog.TeamGameLog(
            team_id=team_id,
            season=season,
            season_type_all_star=season_type  # Pass season type for filtering
        ).get_data_frames()[0]
        if logs.empty:
            return pd.DataFrame()

        # Process the logs
        logs['TEAM_ABBREVIATION'] = logs['MATCHUP'].apply(self.extract_team_abbreviation)
        logs['LOCATION'] = logs['MATCHUP'].apply(lambda x: 'Road' if '@' in x else 'Home')

        return logs

    @staticmethod
    def find_player_by_name(name):
        return players.find_players_by_full_name(name)

    @staticmethod
    def find_team_by_name(name):
        return teams.find_teams_by_full_name(name)

    @staticmethod
    def extract_team_abbreviation(matchup):
        """Extracts the team abbreviation from the MATCHUP string."""
        if '@' in matchup:
            return matchup.split(' ')[0]  # Away team is second
        else:
            return matchup.split(' ')[0]  # Home team is first