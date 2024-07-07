import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

def fetch_odds(apiKey):
    url = f"https://api.the-odds-api.com/v4/sports/upcoming/odds/?apiKey={apiKey}&regions=uk,us,eu&markets=totals&oddsFormat=decimal"

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

def find_arbs(df):
    arbs = []
    games = df.groupby('game')
    
    for game_id, game_data in games:
        home_team = game_data['home'].iloc[0]
        away_team = game_data['away'].iloc[0]
        
        home_data = game_data[game_data['home'] == home_team]
        away_data = game_data[game_data['away'] == away_team]
        
        for team_data in [home_data, away_data]:
            over_outcomes = team_data[team_data['type'].str.startswith('Over')]
            under_outcomes = team_data[team_data['type'].str.startswith('Under')]
            
            for _, over in over_outcomes.iterrows():
                for _, under in under_outcomes.iterrows():
                    if over['point'] == under['point'] and over['price'] + under['price'] < 1:
                        arb = {
                            'game': game_id,
                            'team': home_team if team_data is home_data else away_team,
                            'outcome1': {
                                'type': over['type'],
                                'bookies': over['bookies'],
                                'price': over['price']
                            },
                            'outcome2': {
                                'type': under['type'],
                                'bookies': under['bookies'],
                                'price': under['price']
                            }
                        }
                        arbs.append(arb)
    
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
            print(f"{arb['outcome1']['home']} {arb['outcome1']['type']} - {arb['outcome1']['bookies']} @ {arb['outcome1']['price']}")
            print(f"{arb['outcome2']['away']} {arb['outcome2']['type']} - {arb['outcome2']['bookies']} @ {arb['outcome2']['price']}")


if __name__ == "__main__":
    main()
