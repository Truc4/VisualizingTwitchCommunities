import datetime
import json
import os
import sqlalchemy as sql
from dotenv import load_dotenv

load_dotenv()

def get_viewers_for_streamer(streamer):
    """
    Retrieve chatters from JSON files for a given streamer.
    """
    chatters = set()
    chat_downloads_folder = os.path.abspath("./DataCollection/ChatDownloads")

    # Get all JSON files for the streamer
    for filename in os.listdir(chat_downloads_folder):
        lower_filename = filename.lower()
        lower_streamer = streamer.lower()
        if f"{lower_streamer}".lower() in lower_filename and lower_filename.endswith(".json"):
            file_path = os.path.join(chat_downloads_folder, filename)
            try:
                # Read JSON file
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Extract chatters from comments
                if "comments" in data:
                    for comment in data["comments"]:
                        if "commenter" in comment and "name" in comment["commenter"]:
                            chatters.add(comment["commenter"]["name"])

            except Exception as e:
                print(f"Error reading {file_path}: {e}")

    broadcaster_in_chat = streamer.lower() in [c.lower() for c in chatters]

    return {
        streamer: {
            "chatters": list(chatters),
            "broadcaster_in_chat": broadcaster_in_chat,
        }
    }

def create_streamer_viewer_dict(channel_list):
    """
    Retrieve chatter data from JSON files for each streamer in the list.
    """
    streamer_data = {}
    for streamer in channel_list:
        streamer_data.update(get_viewers_for_streamer(streamer))
    return streamer_data

def write_data(data):
    # Filter out streamers with empty chatters
    filtered_data = {streamer: obj for streamer, obj in data.items() if obj["chatters"]}

    if not filtered_data:
        print("No valid data to insert. Skipping database operation.")
        return

    # Prepare data for insertion
    insert_data = [
        {
            "url_name": streamer,
            "chatters_json": json.dumps({'chatters': obj['chatters']}),
            "broadcaster_in_chat": obj["broadcaster_in_chat"],
            "log_time": datetime.datetime.utcnow()
        }
        for streamer, obj in filtered_data.items()
    ]

    # Set up SQLAlchemy engine and table
    engine = sql.create_engine(os.environ.get("DB_URL"))
    metadata_obj = sql.MetaData()
    chatters_table = sql.Table('chatters', metadata_obj, autoload_with=engine)

    insert_stmt = sql.insert(chatters_table).values(insert_data)

    # Execute with transaction management
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            conn.execute(insert_stmt)
            trans.commit()
            print(f"Successfully inserted {len(insert_data)} records into 'chatters'.")
        except Exception as e:
            trans.rollback()
            print(f"Error inserting data into 'chatters': {e}")

def lambda_handler(event, context):
    print(f"LAMBDA 2 TRIGGERED")
    print(f"EVENT: {event}")

    data = create_streamer_viewer_dict(event)
    print(data)
    write_data(data)

if __name__ == '__main__':
    event = ['109ace','truc_e','1win_slots','sodapoppin','39daph']
    lambda_handler(event, None)
