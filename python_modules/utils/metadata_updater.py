import os
from dotenv import load_dotenv

load_dotenv()

from .igdb_api_client import get_twitch_access_token, get_igdb_game_info
from data.db_manager import DBManager, get_db_manager
from core.cover_downloader import CoverDownloader

def update_all_games_with_metadata():
    client_id = os.getenv("TWITCH_CLIENT_ID")
    client_secret = os.getenv("TWITCH_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("Client ID or Client Secret not found. Check your .env file.")
        return

    access_token = get_twitch_access_token(client_id, client_secret)
    if not access_token:
        print("Cannot get access token. Imposible to update metadata.")
        return
    
    db_manager = get_db_manager()

    try:

        all_games = db_manager.get_all_games()

        for game in all_games:
            print(f"Game: {game['name']}, IGDB ID from DB: {game.get('igdb_id')}")
            if game.get('igdb_id') is None:
                game_name = game['name']
                print(f"Updating metadata for game '{game_name}'...")

                print(f"Fetching IGDB info for '{game_name}'...")

                igdb_data_list = get_igdb_game_info(access_token, client_id, game['appid'] )

                print(f"Finished fetching IGDB info for '{game_name}'.")

                if igdb_data_list:
                    igdb_info = igdb_data_list[0]

                    igdb_id = igdb_info.get('id')
                    summary = igdb_info.get('summary')

                    genres_list = [g['name'] for g in igdb_info.get('genres', [])]
                    platform_list = [p['name'] for p in igdb_info.get('platforms', [])]

                    genres_str = ", ".join(genres_list)
                    platform_str = ", ".join(platform_list)

                    cover_url = igdb_info.get('cover', {}).get('url')

                    new_cover_path = None
                    if cover_url and not game.get('cover_path'):

                        print(f"Starting cover download for '{game_name}'...")

                        cover_downloader = CoverDownloader()
                        new_cover_path = cover_downloader.download_igdb_cover(cover_url, game['name'])

                        print(f"Finished cover download for '{game_name}'.")

                    db_manager.update_game_metadata(
                        appid=game['appid'],
                        igdb_id=igdb_id,
                        summary=summary,
                        genres=genres_str,
                        platforms=platform_str,
                        cover_path=new_cover_path,
                    )

                    updated_game = db_manager.get_game_by_appid(game['appid'])
                    print(f"After update, {updated_game['name']} has IGDB ID: {updated_game.get('igdb_id')}")

                else:
                    print(f"Metadata for game '{game_name}' not found.")
            else:
                print(f"Metadata for game '{game['name']}'already exists.")
    finally:
        if db_manager:
            db_manager.close()

if __name__ == "__main__":
    update_all_games_with_metadata()



