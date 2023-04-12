import pandas as pd
import statistics
import mysql.connector
import json
from nba_api.stats.static import players
from nba_api.stats.endpoints import leaguegamefinder
import numpy as np

def calculate_diff_percentage(num, lower_limit, upper_limit):
    return (upper_limit-num)/(upper_limit-lower_limit)

def calculate_team_defenses_coefficient():
    team_defenses = pd.read_csv('../nba.com_scrapper/team_defenses_13_14.csv')

    pdef = team_defenses.sort_values('DEF')['DEF'].values
    min_pdef = pdef[0]
    max_pdef = pdef[len(pdef) - 1]

    rdef = team_defenses.sort_values('RDEF')['RDEF'].values
    min_rdef = rdef[0]
    max_rdef = rdef[len(pdef) - 1]

    team_defenses_coefficient = {}
    for index, row in team_defenses.iterrows():
        team_defenses_coefficient[row['Team']] = (calculate_diff_percentage(row['DEF'], min_pdef, max_pdef)*0.5+0.75,
            calculate_diff_percentage(row['RDEF'], min_rdef, max_rdef)*0.5+0.75)
    return team_defenses_coefficient

def get_players_positions():
    defense_dash_lt10 = pd.read_csv('../nba.com_scrapper/defense_dash_lt10_13_14.csv')
    defense_dash_lt10 = defense_dash_lt10[pd.notna(defense_dash_lt10.MP)]
    player_positions = {}
    for index, row in defense_dash_lt10.iterrows():
        if row['Player'] not in player_positions:
            player_positions[row['Player']] = row['Position']
    return player_positions

def player_stops_lt10(lt10):
    diff = lt10.sort_values('DIFF%')['DIFF%'].values
    best_diff = diff[0]
    worst_diff = diff[len(diff) - 1]
    dfg = lt10.sort_values('DFG%')['DFG%'].values
    best_dfg = dfg[0]
    worst_dfg = dfg[len(diff) - 1]
    players_stops = {}
    for index, row in lt10.iterrows():
        stop1 = row['BLKR']
        stop2 = (calculate_diff_percentage(row['DIFF%'], best_diff, worst_diff)*0.5+0.75) * \
                (calculate_diff_percentage(row['DFG%'], best_dfg, worst_dfg)*0.5+0.75)
        players_stops[row['Player']] = [0.5*stop1 + stop2, row['Team'], stop1, stop2]
    return players_stops

def teams_total_stops(stops):
    team_total_stops = {}
    for player, value in stops.items():
        stop = value[0]
        team = value[1]
        if team not in team_total_stops:
            team_total_stops[team] = [stop]
        else:
            team_total_stops[team].append(stop)
    return team_total_stops

def final_rating(stops, team_total_stops, team_defenses_coefficient, traded_players, gt10):
    for player, value in stops.items():
        if player in traded_players:
            player_contribution = 0
            stop = value[0]
            total_games_played = sum(traded_players[player].values())
            team_defense = 0
            for team, games_num in traded_players[player].items():
                average_team_stops = statistics.mean(team_total_stops[team])
                player_contribution += (stop/average_team_stops) * (games_num/total_games_played)
                if gt10:
                    team_defense += team_defenses_coefficient[team][0]*(games_num/total_games_played)
                else:
                    team_defense += team_defenses_coefficient[team][1]*(games_num/total_games_played)
            player_team = player_contribution * team_defense
            final_rating = stop + player_team
            stops[player].extend([average_team_stops, player_contribution, team_defense, player_team, final_rating])
        else:
            stop = value[0]
            team = value[1]
            average_team_stops = statistics.mean(team_total_stops[team])
            # Player ranking based on how much he contributes to his team, compare him to average
            player_contribution = stop / average_team_stops
            if gt10:
                team_defense = team_defenses_coefficient[team][0]
            else:
                team_defense = team_defenses_coefficient[team][1]
            player_team = player_contribution * team_defense
            final_rating = stop + player_team
            # Collect all data
            # stop, team, stop1, stop2, player_team_rating, team_pdef_coefficient, final_pdef
            stops[player].extend([average_team_stops, player_contribution, team_defense, player_team, final_rating])
    return stops

def defense_dash_lt10():
    defense_dash_lt10 = pd.read_csv('../nba.com_scrapper/defense_dash_lt10_13_14.csv')
    # Remove useless datadefense_dash_gt15
    defense_dash_lt10 = defense_dash_lt10[pd.notna(defense_dash_lt10.MP)]
    defense_dash_lt10 = defense_dash_lt10[defense_dash_lt10.MP > 18]
    defense_dash_lt10 = defense_dash_lt10[defense_dash_lt10.GP > 15]
    return defense_dash_lt10

def defense_dash_overall():
    defense_dash_overall = pd.read_csv('../nba.com_scrapper/defense_dash_overall_13_14.csv')
    # Remove useless datadefense_dash_gt15
    defense_dash_overall = defense_dash_overall[pd.notna(defense_dash_overall.MP)]
    defense_dash_overall = defense_dash_overall[defense_dash_overall.MP > 18]
    defense_dash_overall = defense_dash_overall[defense_dash_overall.GP > 15]
    return defense_dash_overall

def player_stops_gt10(lt10, overall):
    dd_lt10 = {}
    dd_gt10 = {}
    for index, row in lt10.iterrows():
        dd_lt10[row['Player']] = (row['DFGM'], row['DFGA'])

    for index, row in overall.iterrows():
        player = row['Player']
        if player in dd_lt10:
            dfgm = row['DFGM']-dd_lt10[player][0]
            dfga = row['DFGA']-dd_lt10[player][1]
            dfg = (dfgm/dfga)*100
            dd_gt10[player] = dfg

    key_max = max(dd_gt10.keys(), key=(lambda k: dd_gt10[k]))
    key_min = min(dd_gt10.keys(), key=(lambda k: dd_gt10[k]))
    print("max", key_max)
    print("min", key_min)
    min_dfg = dd_gt10[key_min]
    max_dfg = dd_gt10[key_max]
    players_stops = {}

    for index, row in overall.iterrows():
        stop1 = row['STL'] + row['BLKP'] + row['Charges']
        stop2 = calculate_diff_percentage(dd_gt10[row['Player']], min_dfg, max_dfg)*0.5+0.75
        players_stops[row['Player']] = [0.25*stop1 + stop2, row['Team'], stop1, stop2]
    return players_stops

def get_traditional_stats():
    traditional = pd.read_csv('../nba.com_scrapper/traditional_13_14.csv')
    return traditional

def traded_players(lt10):
    # Set the season year and team abbreviation
    season_year = '2013-14'
    players_teams = {}
    for player_name in lt10.keys():
        player_teams = {}
        gamefinder = leaguegamefinder.LeagueGameFinder(team_id_nullable=None,
                                                       player_id_nullable=None,
                                                       season_nullable=season_year,
                                                       season_type_nullable='Regular Season',
                                                       league_id_nullable='00',
                                                       player_or_team_abbreviation='P')

        games = gamefinder.get_data_frames()[0]
        player_games = games[games.PLAYER_NAME == player_name]
        arr = player_games['TEAM_ABBREVIATION'].values
        unique_vals = np.unique(arr)
        if len(unique_vals) > 1:
            # Count occurrences of each value in array
            for val in unique_vals:
                count = np.count_nonzero(arr == val)
                player_teams[val] = count
            players_teams[player_name] = player_teams
    return players_teams

def insert_in_db(traditional, lt10, gt10, player_positions):
    data = json.load(open('db.json'))

    # Connect to DB
    mydb = mysql.connector.connect(
        host= "localhost",
        user= data["user"],
        password= data["password"],
        port= data["port"],
        database= data["database"]
    )

    mycursor = mydb.cursor()

    for index, row in traditional.iterrows():
        player = row['Player']
        if player in player_positions:
            sql = "INSERT INTO player (Player, Team, Age, GP, MIN, PTS, FGM, FGA, FG, 3PM, 3PA, 3P, FTM, FTA, FT, OREB, DREB, REB, AST, TOV, STL, BLK, PF, PlusMinus, Position, Stop1Perimeter, Stop2Perimeter, StopPerimeter, AverageTeamStopPerimeter, PlayerContributionPerimeter, TeamDefensePerimeter, PlayerTeamPerimeter, PDEF, Stop1Rim, Stop2Rim, StopRim, AverageTeamStopRim, PlayerContributionRim, TeamDefenseRim, PlayerTeamRim, RDEF, DEF, SeasonYear, NbaPlayerId) " \
                  "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            val = row.values.tolist()
            val.append(player_positions[player])
            if player in lt10:
                # Add stop1, stop2, stop
                val.extend([gt10[player][2], gt10[player][3], gt10[player][0]])
                # Add average_team_stops, player_contribution, team_defense, player_team, final_rating
                val.extend(gt10[player][4:])
                # Add stop1, stop2, stop
                val.extend([lt10[player][2], lt10[player][3], lt10[player][0]])
                # Add average_team_stops, player_contribution, team_defense, player_team, final_rating
                val.extend(lt10[player][4:])
                val.append(gt10[player][-1]+lt10[player][-1])
            else:
                val.extend([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
            val.append("13/14")
            player_api = [player_api for player_api in players.get_players() if player_api['full_name'] == player][0]
            val.append(player_api['id'])
            mycursor.execute(sql, val)
    mydb.commit()

teams_defense = calculate_team_defenses_coefficient()

lt10 = defense_dash_lt10()
lt10_stops = player_stops_lt10(lt10)
traded_players = traded_players(lt10_stops)
team_total_stops = teams_total_stops(lt10_stops)
lt10_rating = final_rating(lt10_stops, team_total_stops, teams_defense, traded_players, False)

overall = defense_dash_overall()
gt10_stops = player_stops_gt10(lt10, overall)
team_total_stops = teams_total_stops(gt10_stops)
gt10_rating = final_rating(gt10_stops, team_total_stops, teams_defense, traded_players, True)

player_positions = get_players_positions()
traditional = get_traditional_stats()
insert_in_db(traditional, lt10_rating, gt10_rating, player_positions)
