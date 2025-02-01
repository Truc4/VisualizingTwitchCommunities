from json import load
from urllib.error import HTTPError
import math
import sqlalchemy as sql
import os
from dotenv import load_dotenv
from pathlib import Path
import sys
from viewer_data_collector import lambda_handler as lambda2_handler

load_dotenv()

BATCH_SIZE = 100


def lambda_handler(event, context):
    """
    Reads NUM_CHANNELS channels from database, splits channels into batches, and triggers several instances of a 
    separate lambda function to get viewers from each channel
    """
    print(f"LAMBDA 1 TRIGGERED")

    # Get channel batches
    channel_batches = get_channel_batches()

    # Process each batch locally by calling Lambda2
    for batch in channel_batches:
        process_batch(batch)


def process_batch(batch):
    """
    Process a batch of channels by directly invoking the Lambda2 function.
    """
    print(f"Processing batch: {batch}")
    event = batch
    context = None
    lambda2_handler(event, context)  # Call Lambda2 function directly


def get_channel_batches():
    """
    Retrieves a list of current top streamers from the database, 
    splits them into batches, and returns the list of batches.
    """
    # Create SQLAlchemy engine and metadata object
    engine = sql.create_engine(os.environ.get('DB_URL'))
    metadata_obj = sql.MetaData()

    # Define the channels table
    try:
        channels_table = sql.Table('channels', metadata_obj, autoload_with=engine)
    except Exception as e:
        print(f"Error loading table 'channels': {e}")
        exit(1)

    # Query to get current top streamers
    query = sql.select(channels_table.c.url_name).filter(channels_table.c.is_current_top_stream == True)

    # Execute the query with transaction handling
    channels = []
    with engine.connect() as conn:
        trans = conn.begin()  # Start a transaction
        try:
            result_proxy = conn.execute(query)
            channel_set = result_proxy.fetchall()
            channels = [tup[0] for tup in channel_set]  # Extract channel names
            trans.commit()  # Commit the transaction
            print(f"Successfully retrieved {len(channels)} channels.")
        except Exception as e:
            trans.rollback()  # Roll back the transaction in case of an error
            print(f"Error fetching channels from the database: {e}")
            exit(1)

    # Batch channels into chunks of BATCH_SIZE
    channel_batches = [channels[i:i + BATCH_SIZE] for i in range(0, len(channels), BATCH_SIZE)]
    print(f"Created {len(channel_batches)} channel batches.")
    return channel_batches


if __name__ == '__main__':
    lambda_handler(None, None)
