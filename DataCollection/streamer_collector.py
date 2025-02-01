import sqlalchemy as sql
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
import os
from dotenv import load_dotenv

load_dotenv()

NUM_CHANNELS = 1000

def lambda_handler(event, context):
    # Sample channel list for testing
    channel_list = [
        {'url_name': "pikabooirl", 'display_name': "Pikabooirl", 'is_current_top_stream': True, 'view_minutes': 0},
        {'url_name': "lacy", 'display_name': "Lacy", 'is_current_top_stream': True, 'view_minutes': 0},
        {'url_name': "northernlion", 'display_name': "Northernlion", 'is_current_top_stream': True, 'view_minutes': 0},
        {'url_name': "sodapoppin", 'display_name': "sodapoppin", 'is_current_top_stream': True, 'view_minutes': 0},
        {'url_name': "summit1g", 'display_name': "summit1g", 'is_current_top_stream': True, 'view_minutes': 0},
        {'url_name': "misterarther", 'display_name': "MISTERARTHER", 'is_current_top_stream': True, 'view_minutes': 0},
        {'url_name': "hasanabi", 'display_name': "HasanAbi", 'is_current_top_stream': True, 'view_minutes': 0},
        {'url_name': "shroud", 'display_name': "shroud", 'is_current_top_stream': True, 'view_minutes': 0},
        {'url_name': "caseoh_", 'display_name': "caseoh_", 'is_current_top_stream': True, 'view_minutes': 0},
        {'url_name': "tubbo", 'display_name': "Tubbo", 'is_current_top_stream': True, 'view_minutes': 0},
        {'url_name': "nmplol", 'display_name': "Nmplol", 'is_current_top_stream': True, 'view_minutes': 0},
        {'url_name': "mizkif", 'display_name': "Mizkif", 'is_current_top_stream': True, 'view_minutes': 0},
        {'url_name': "lck", 'display_name': "LCK", 'is_current_top_stream': True, 'view_minutes': 0},
        {'url_name': "zackrawrr", 'display_name': "zackrawrr", 'is_current_top_stream': True, 'view_minutes': 0},
        {'url_name': "loltyler1", 'display_name': "loltyler1", 'is_current_top_stream': True, 'view_minutes': 0},
        {'url_name': "mrsavage", 'display_name': "MrSavage", 'is_current_top_stream': True, 'view_minutes': 0},
        {'url_name': "moonmoon", 'display_name': "MOONMOON", 'is_current_top_stream': True, 'view_minutes': 0},
        {'url_name': "xqc", 'display_name': "xQc", 'is_current_top_stream': True, 'view_minutes': 0},
        {'url_name': "plaqueboymax", 'display_name': "plaqueboyMax", 'is_current_top_stream': True, 'view_minutes': 0},
        {'url_name': "thebausffs", 'display_name': "Thebausffs", 'is_current_top_stream': True, 'view_minutes': 0},
        {'url_name': "kaicenat", 'display_name': "KaiCenat", 'is_current_top_stream': True, 'view_minutes': 0},
        {'url_name': "caedrel", 'display_name': "Caedrel", 'is_current_top_stream': True, 'view_minutes': 0},
        {'url_name': "ohnepixel", 'display_name': "ohnePixel", 'is_current_top_stream': True, 'view_minutes': 0},
        {'url_name': "stableronaldo", 'display_name': "stableronaldo", 'is_current_top_stream': True, 'view_minutes': 0},
        {'url_name': "piratesoftware", 'display_name': "PirateSoftware", 'is_current_top_stream': True, 'view_minutes': 0},
    ]

    # Get database URL from environment
    db_url = os.environ.get('DB_URL')
    if not db_url:
        raise ValueError("DB_URL is not set. Please configure it in your .env file.")

    print(f"Using database at: {db_url}")

    # Connect to the database
    engine = sql.create_engine(db_url)
    metadata_obj = sql.MetaData()

    # Define the channels table
    channels_table = sql.Table(
        'channels',
        metadata_obj,
        sql.Column('url_name', sql.String, primary_key=True),
        sql.Column('display_name', sql.String),
        sql.Column('is_current_top_stream', sql.Boolean),
        sql.Column('view_minutes', sql.Integer),
        autoload_with=engine
    )

    # Update all existing streamers to not be the current top streamers
    update_stmt = sql.update(channels_table).where(
        channels_table.c.is_current_top_stream == True
    ).values(is_current_top_stream=False)

    # Upsert statement
    insert_stmt = sqlite_insert(channels_table).values(channel_list)

    do_upsert_stmt = insert_stmt.on_conflict_do_update(
        index_elements=['url_name'],
        set_={
            'is_current_top_stream': True,
            'view_minutes': insert_stmt.excluded.view_minutes
        }
    )

    # Execute statements
    try:
        with engine.connect() as conn:
            trans = conn.begin()  # Start a transaction
            try:
                print("Updating existing channels...")
                conn.execute(update_stmt)

                print("Inserting or updating channels...")
                conn.execute(do_upsert_stmt, channel_list)  # Correct execution

                trans.commit()  # Commit the transaction
                print(f"Successfully upserted {len(channel_list)} channels.")
            except Exception as e:
                print(f"Error before rollback: {e}")  # Print error before rollback
                trans.rollback()
    except Exception as e:
        print(f"Database operation failed: {e}")

if __name__ == '__main__':
    lambda_handler(None, None)
