import pandas as pd

def calculate_diff_percentage(num, lower_limit, upper_limit):
    #return ((num - lower_limit)/(upper_limit-lower_limit))
    return (upper_limit-num)/(upper_limit-lower_limit)

def calculate_team_defenses_coefficient():
    team_defenses = pd.read_csv('../nba.com_scrapper/team_defenses.csv')

    pdef = team_defenses.sort_values('PDEF')['PDEF'].values
    min_pdef = pdef[0]
    max_pdef = pdef[len(pdef) - 1]

    rdef = team_defenses.sort_values('RDEF')['RDEF'].values
    min_rdef = rdef[0]
    max_rdef = rdef[len(pdef) - 1]

    team_defenses_coefficient = {}
    for index, row in team_defenses.iterrows():
        team_defenses_coefficient[row['Team']] = (calculate_diff_percentage(row['PDEF'], min_pdef, max_pdef),
            calculate_diff_percentage(row['RDEF'], min_rdef, max_rdef))
    return team_defenses_coefficient

def get_defense_dash_gt15():
    defense_dash_gt15 = pd.read_csv('../nba.com_scrapper/defense_dash_gt15.csv')
    # Remove useless data
    defense_dash_gt15 = defense_dash_gt15[pd.notna(defense_dash_gt15.MP)]
    defense_dash_gt15 = defense_dash_gt15[defense_dash_gt15.MP > 18]
    defense_dash_gt15 = defense_dash_gt15[defense_dash_gt15.GP > 15]
    return defense_dash_gt15

def get_player_stops(defense_dash_gt15):
    diff = defense_dash_gt15.sort_values('DIFF%')['DIFF%'].values
    best_diff = diff[0]
    worst_diff = diff[len(diff) - 1]
    players_stops = {}

    for index, row in defense_dash_gt15.iterrows():
        stop1 = row['STL'] + row['BLKP']
        stop2 = calculate_diff_percentage(row['DIFF%'], best_diff, worst_diff)
        players_stops[row['Player']] = (0.3 * stop1 + stop2, row['Team'])


team_defenses_coefficient = calculate_team_defenses_coefficient()
defense_dash_gt15 = get_defense_dash_gt15()

diff = defense_dash_gt15.sort_values('DIFF%')['DIFF%'].values
best_diff = diff[0]
worst_diff = diff[len(diff)-1]
players_stops = {}
teams_players = {}

for index, row in defense_dash_gt15.iterrows():
    team = row['Team']
    if team not in teams_players:
        teams_players[team] = [row['Player']]
    else:
        teams_players[team].append(row['Player'])
    stop1 = row['STL'] + row['BLKP']
    stop2 = calculate_diff_percentage(row['DIFF%'], best_diff, worst_diff)
    players_stops[row['Player']] = (0.3*stop1 + stop2, row['Team'])

team_total_stops = {}
for team, players in teams_players.items():
    stop_sum = 0
    for player in players:
        stop_sum += players_stops[player][0]
    team_total_stops[team] = stop_sum

players_teams_coefficient = {}
players_final_pdef = {}
for player, tuple in players_stops.items():
    player_stops = tuple[0]
    team = tuple[1]
    # Player ranking based on how much he contributes to his team
    player_team_rating = player_stops/team_total_stops[team]
    team_pdef_coefficient = team_defenses_coefficient[team][0]
    player_team_coefficient = player_team_rating*team_pdef_coefficient*5
    players_teams_coefficient[player] = player_team_coefficient
    players_final_pdef[player] = player_stops + player_team_coefficient

sorted_dict = dict(sorted(players_final_pdef.items(), key=lambda item: item[1]))

for key, value in sorted_dict.items():
    print(key, value)

