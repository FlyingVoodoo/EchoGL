import requests

def get_twitch_access_token(client_id, client_secret):
    params = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }
    response = requests.post("https://id.twitch.tv/oauth2/token", data=params)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print("Getting token error:", response.text)
        return None
    
def get_igdb_game_info(access_token, client_id, game_name):
    headers = {
        'Client-ID': client_id,
        'Authorization': f'Bearer {access_token}'
    }
    query_body = f'fields name,cover.url,genres.name,platforms.name,summary; search "{game_name}"; limit 1;'

    response = requests.post("https://api.igdb.com/v4/games", headers=headers, data=query_body)
    if response.status_code == 200:
        return response.json()
    else:
        print("Getting game info error:", response.text)
        return None
