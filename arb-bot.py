import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

def fetch_odds(apiKey):
    url = f"https://api.the-odds-api.com/v4/sports/upcoming/odds/?apiKey={apiKey}&regions=uk&markets=totals&oddsFormat=decimal"

    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        print("Error fetching odds")
        return None
    
def process_odds(data):
    odds_data = []
    for event in data:
        for bookmaker in event['bookmakers']:
            for market in bookmaker['markets']:
                for outcome in market['outcomes']:
                    odds_data.append({
                        'sport': event['sport_title'],
                        'game': event['id'],
                        'bookies': bookmaker['title'],
                        'home': event['home_team'],
                        'away': event['away_team'],
                        'type': outcome['name'],
                        'point': outcome['point'],
                        'price': outcome['price']
                    })
    df = pd.DataFrame(odds_data)

    return df

def calculate_arb(over, under):
    return (1 / over) + (1 / under)

def find_arbs(df):
    arbs = []
    games = df.groupby(['game', 'point'])
    
    for game_id, game in games:
        overs = game[game['type'] == 'Over']
        unders = game[game['type'] == 'Under']

        for _, over in overs.iterrows():
            for _, under in unders.iterrows():
                arb_value = calculate_arb(over['price'], under['price'])
                if arb_value < 1:
                    profit_percent = (1 - arb_value) * 100
                    arbs.append({
                        'game': f"{game['home']} Vs {game['away']}",
                        'point': game['point'],
                        'over_bet': over['bookies'],
                        'over_price': over['price'],
                        'under_bet': under['bookies'],
                        'under_price': under['price'],
                        'profit': profit_percent
                    })
    
    return arbs


def main():
    api_key = os.getenv("API_KEY")
    if not api_key:
        print("Error retrieving api key")
        return

    data = fetch_odds(api_key)
    if data:
        df = process_odds(data)
        arbs = find_arbs(df)
        for arb in arbs:
            print(arb['game'])
            print(f"Over {arb['point']} on {arb['over_bet']} @ {arb['over_price']}")
            print(f"Under {arb['point']} on {arb['under_bet']} @ {arb['under_price']}")



if __name__ == "__main__":
    main()
