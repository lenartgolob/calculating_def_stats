import pandas as pd
from prettytable import PrettyTable

def calculate_diff_percentage(num, lower_limit, upper_limit):
    #return ((num - lower_limit)/(upper_limit-lower_limit))
    return (upper_limit-num)/(upper_limit-lower_limit)

def calculate_team_defenses_coefficient():
    team_defenses = pd.read_csv('../nba.com_scrapper/team_defenses.csv')

    pdef = team_defenses.sort_values('DEF')['DEF'].values
    min_pdef = pdef[0]
    max_pdef = pdef[len(pdef) - 1]

    rdef = team_defenses.sort_values('RDEF')['RDEF'].values
    min_rdef = rdef[0]
    max_rdef = rdef[len(pdef) - 1]

    team_defenses_coefficient = {}
    for index, row in team_defenses.iterrows():
        team_defenses_coefficient[row['Team']] = (calculate_diff_percentage(row['DEF'], min_pdef, max_pdef)*0.5,
            calculate_diff_percentage(row['RDEF'], min_rdef, max_rdef)*0.5)
    return team_defenses_coefficient

def get_defense_dash_gt15():
    defense_dash_gt15 = pd.read_csv('../nba.com_scrapper/defense_dash_gt15.csv')
    # Remove useless datadefense_dash_gt15
    defense_dash_gt15 = defense_dash_gt15[pd.notna(defense_dash_gt15.MP)]
    defense_dash_gt15 = defense_dash_gt15[defense_dash_gt15.MP > 18]
    defense_dash_gt15 = defense_dash_gt15[defense_dash_gt15.GP > 15]
    return defense_dash_gt15

def get_player_stops(defense_dash_gt15, gt15):
    diff = defense_dash_gt15.sort_values('DIFF%')['DIFF%'].values
    best_diff = diff[0]
    worst_diff = diff[len(diff) - 1]
    dfg = defense_dash_gt15.sort_values('DFG%')['DFG%'].values
    best_dfg = dfg[0]
    worst_dfg = dfg[len(diff) - 1]
    players_stops = {}
    for index, row in defense_dash_gt15.iterrows():
        stop2 = (calculate_diff_percentage(row['DIFF%'], best_diff, worst_diff)*0.5+0.75) * \
                (calculate_diff_percentage(row['DFG%'], best_dfg, worst_dfg)*0.5+0.75)
        if gt15:
            stop1 = row['STL'] + row['BLKP'] + row['Charges']
            players_stops[row['Player']] = [0.5*stop1 + 2*stop2, row['Team'], stop1, stop2]
        else:
            stop1 = row['BLKR']
            players_stops[row['Player']] = [stop1 + 2*stop2, row['Team'], stop1, stop2]
    return players_stops

def get_teams_total_stops(players_stops):
    team_total_stops = {}
    for player, value in players_stops.items():
        stop = value[0]
        team = value[1]
        if team not in team_total_stops:
            team_total_stops[team] = stop
        else:
            team_total_stops[team] += stop
    return team_total_stops

def get_final_def_rtg(players_stops, team_total_stops, gt15):
    players_teams_coefficient = {}
    players_final_pdef = {}
    for player, value in players_stops.items():
        player_stops = value[0]
        team = value[1]
        # Player ranking based on how much he contributes to his team
        player_team_rating = player_stops / team_total_stops[team]
        if gt15:
            team_pdef_coefficient = team_defenses_coefficient[team][0]
        else:
            team_pdef_coefficient = team_defenses_coefficient[team][1]
        player_team_coefficient = (player_team_rating + team_pdef_coefficient)*2.5
        players_teams_coefficient[player] = player_team_coefficient
        final_pdef = player_stops + player_team_coefficient
        players_final_pdef[player] = final_pdef
        # Collect all data
        # stop, team, stop1, stop2, player_team_rating, team_pdef_coefficient, final_pdef
        players_stops[player].extend([player_team_rating, team_pdef_coefficient, player_team_coefficient, final_pdef])
    #return players_final_pdef
    return players_stops

def get_final_def_rtg_duplicate(players_stops, team_total_stops, gt15):
    players_teams_coefficient = {}
    players_final_pdef = {}
    for player, value in players_stops.items():
        player_stops = value[0]
        team = value[1]
        # Player ranking based on how much he contributes to his team
        player_team_rating = player_stops / team_total_stops[team]
        if gt15:
            team_pdef_coefficient = team_defenses_coefficient[team][0]
        else:
            team_pdef_coefficient = team_defenses_coefficient[team][1]
        player_team_coefficient = (player_team_rating + team_pdef_coefficient)*2.5
        players_teams_coefficient[player] = player_team_coefficient
        final_pdef = player_team_coefficient + player_stops
        players_final_pdef[player] = final_pdef
        # Collect all data
        # stop, team, stop1, stop2, player_team_rating, team_pdef_coefficient, final_pdef
        players_stops[player].extend([player_team_rating, team_pdef_coefficient, final_pdef])
    return players_final_pdef

def get_defense_dash_lt10():
    defense_dash_lt10 = pd.read_csv('../nba.com_scrapper/defense_dash_lt10.csv')
    # Remove useless datadefense_dash_gt15
    defense_dash_lt10 = defense_dash_lt10[pd.notna(defense_dash_lt10.MP)]
    defense_dash_lt10 = defense_dash_lt10[defense_dash_lt10.MP > 18]
    defense_dash_lt10 = defense_dash_lt10[defense_dash_lt10.GP > 15]
    return defense_dash_lt10

team_defenses_coefficient = calculate_team_defenses_coefficient()
defense_dash_gt15 = get_defense_dash_gt15()
players_stops = get_player_stops(defense_dash_gt15, True)
team_total_stops = get_teams_total_stops(players_stops)
#players_final_pdef = get_final_def_rtg(players_stops, team_total_stops)
players_stops = get_final_def_rtg(players_stops, team_total_stops, True)
players_final_pdef = get_final_def_rtg_duplicate(players_stops, team_total_stops, True)


#sorted_dict = dict(sorted(players_final_pdef.items(), key=lambda item: item[1]))
#i = len(sorted_dict)
#for key, value in sorted_dict.items():
#    print(i, key, value)
#    i -= 1


sorted_dict = dict(sorted(players_final_pdef.items(), key=lambda item: item[1]))
i = len(sorted_dict)
t = PrettyTable(['Num', 'player', 'team', 'stop1', 'stop2', 'stop', 'player_comparison_teamates', 'team_defense',
        'player_team_combined', 'final_pdef'])
for player, value in sorted_dict.items():
    t.add_row([i, player, players_stops[player][1], players_stops[player][2], players_stops[player][3], players_stops[player][0],
          players_stops[player][4], players_stops[player][5], players_stops[player][6], players_stops[player][7]])
    i -= 1
print(t)

defense_dash_lt10 = get_defense_dash_lt10()
#players_stops = get_player_stops(defense_dash_lt10, False)
team_total_stops = get_teams_total_stops(players_stops)
players_stops = get_final_def_rtg(players_stops, team_total_stops, False)
players_final_pdef = get_final_def_rtg_duplicate(players_stops, team_total_stops, False)

sorted_dict = dict(sorted(players_final_pdef.items(), key=lambda item: item[1]))
i = len(sorted_dict)
t = PrettyTable(['Num', 'player', 'team', 'stop1', 'stop2', 'stop', 'player_comparison_teamates', 'team_defense',
        'player_team_combined', 'final_pdef'])
for player, value in sorted_dict.items():
    t.add_row([i, player, players_stops[player][1], players_stops[player][2], players_stops[player][3], players_stops[player][0],
          players_stops[player][4], players_stops[player][5], players_stops[player][6], players_stops[player][7]])
    i -= 1
#print(t)



