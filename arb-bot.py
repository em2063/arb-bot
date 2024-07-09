import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

def fetch_odds(apiKey):
    url = f"https://api.the-odds-api.com/v4/sports/upcoming/odds/?apiKey={apiKey}&regions=uk&markets=h2h&oddsFormat=decimal"

    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        print("Error fetching odds")
        return None
    
def process_odds(data):
    arb_data = []
    for event in data:
        for bookmaker in event['bookmakers']:
            for market in bookmaker['markets']:
                for outcome in market['outcomes']:
                    if market['key'] == 'totals':
                        arb_data.append({
                            'market': 'h2h',
                            'game': event['id'],
                            'bookies': bookmaker['title'],
                            'home': event['home_team'],
                            'away': event['away_team'],
                            'type': outcome['name'],
                            'point': outcome['point'],
                            'price': outcome['price']
                        })
                    elif market['key'] == 'h2h':
                        arb_data.append({
                            'market': 'h2h',
                            'game_id': event['id'],
                            'bookies': bookmaker['title'],
                            'game': f"{event['home_team']} Vs {event['away_team']}",
                            'home_team': event['home_team'],
                            'away_team': event['away_team'],
                            'team': outcome['name'],
                            'price': outcome['price']
                        })
    
    df = pd.DataFrame(arb_data)

    return df
                    

def calculate_arb(over, under):
    return (1 / over) + (1 / under)

def find_arbs_totals(df, stake):
    arbs = []
    games = df.groupby(['game', 'point'])
    
    for game_id, game in games:
        overs = game[game['type'] == 'Over']
        unders = game[game['type'] == 'Under']

        for _, over in overs.iterrows():
            for _, under in unders.iterrows():
                arb_value = calculate_arb(over['price'], under['price'])

                
                bet_under = float(stake) * ( (1 /under['price']) / arb_value)
                bet_over = float(stake) * ( (1 / over['price']) / arb_value)
                

                if arb_value < 1:

                    profit_percent = ((1 / arb_value) - 1) * 100

                    arbs.append({
                        'game': f"{game['home'].iloc[0]} Vs {game['away'].iloc[0]}",
                        'point': game['point'],
                        'over_bet': over['bookies'],
                        'over_price': over['price'],
                        'under_bet': under['bookies'],
                        'under_price': under['price'],
                        'bet_amount_over': f"{bet_over:.2f}",
                        'bet_amount_under': f"{bet_under:.2f}",
                        'profit': f"{profit_percent:.2f}"
                    })

    arbs = sorted(arbs, key=lambda x: x['profit'], reverse=True)
    
    return arbs


def find_arbs_h2h(df, stake):
    arbs = []
    games = df.groupby('game_id')

    for game_id, game in games:
        home_team = game[game['team'] == game['home_team']]
        away_team = game[game['team'] == game['away_team']]
        draws = game[game['team'] == 'Draw']
            

        for _, home in home_team.iterrows():
            for _, away in away_team.iterrows():
                if not draws.empty:
                    for _, draw in draws.iterrows():
                        arb_value = (1 / home['price']) + (1 / away['price']) + (1 / draw['price'])

                        bet_home = float(stake) * ((1 / home['price']) / arb_value)
                        bet_away = float(stake) * ((1 / away['price']) / arb_value)
                        bet_draw = float(stake) * ((1 / draw['price']) / arb_value)

                        if arb_value < 1:
                            profit_percent = ((1 / arb_value) - 1) * 100

                            arbs.append({
                            'game': f"{game['home_team'].iloc[0]} Vs {game['away_team'].iloc[0]}",
                            'home_bet': home['bookies'],
                            'home_price': home['price'],
                            'away_bet': away['bookies'],
                            'away_price': away['price'],
                            'draw_bet': draw['bookies'],
                            'draw_price': draw['price'],
                            'bet_amount_home': f"{bet_home:.2f}",
                            'bet_amount_away': f"{bet_away:.2f}",
                            'bet_amount_draw': f"{bet_draw:.2f}",
                            'profit': f"{profit_percent:.2f}"
                        })
                else:

                    arb_value = calculate_arb(home['price'], away['price'])

                    bet_home = float(stake) * ((1 / home['price']) / arb_value)
                    bet_away = float(stake) * ((1 / away['price']) / arb_value)

                    if arb_value < 1:

                        profit_percent = ((1 / arb_value) - 1) * 100

                        arbs.append({
                            'game': f"{game['home_team'].iloc[0]} Vs {game['away_team'].iloc[0]}",
                            'home_bet': home['bookies'],
                            'home_price': home['price'],
                            'away_bet': away['bookies'],
                            'away_price': away['price'],
                            'bet_amount_home': f"{bet_home:.2f}",
                            'bet_amount_away': f"{bet_away:.2f}",
                            'profit': f"{profit_percent:.2f}"
                        })

    return arbs



def retrieve_key():
    api_key = os.getenv("API_KEY")
    if not api_key:
        print("Error retrieving api key")
        return None
    
    return api_key


def main():
    api_key = retrieve_key()

    data = fetch_odds(api_key)
    
    if data:
        df = process_odds(data)     

        stake = input("> Enter your stake: ")

        arbs = find_arbs_h2h(df, stake)

        for arb in arbs:
            print(arb)
            print(" ")

        # for arb in arbs:
        #     print(f"Game: {arb['game']}")
        #     print(" ")
        #     print(f"Over {arb['point'].iloc[0]} on {arb['over_bet']}. Bet {arb['bet_amount_over']} @ {arb['over_price']}")
        #     print(f"Under {arb['point'].iloc[0]} on {arb['under_bet']}. Bet {arb['bet_amount_under']} @ {arb['under_price']}")
        #     print(" ")
        #     print(f"Profit: {arb['profit']}%")
        #     print(" ")
    else:
        print("Error fetching data")



if __name__ == "__main__":
    main()
