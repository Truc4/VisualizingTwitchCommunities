import sqlalchemy as sql
from sqlalchemy.sql.expression import func
from datetime import datetime, timezone
import _pickle as cPickle
import logging
import json
import os
logging.basicConfig(filename='overlaps.log', level=logging.DEBUG, 
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger=logging.getLogger(__name__)

class OverlapsManager:
    start_time = None
    end_time = None
    engine = None
    metadata_obj = None
    overlaps = None

    def __init__(self, *, start_time, end_time, db_url):
        self.start_time = start_time
        self.end_time = end_time
        self.engine = sql.create_engine(db_url)
        self.metadata_obj = sql.MetaData()
    
    def run(self, gen_chatter_sets = True, calc_chatter_overlaps = True):
        logging.info("Starting Overlaps Run")
        print("Starting Overlaps Run")

        # Get list of channels to calculate overlaps for 
        channels_table = sql.Table('channels', self.metadata_obj, autoload_with=self.engine)
        stmt = sql.select(channels_table.c.url_name).where(channels_table.c.is_current_top_stream == True)
        with self.engine.connect() as conn:
            res = conn.execute(stmt).fetchall()
            channels = [r for r, in res]  # Flatten tuple response into a list

        print(f"Fetched channels: {channels}")

        if gen_chatter_sets:
            print("Generating chatter sets...")
            self.generate_chatter_sets(channels)

        if calc_chatter_overlaps:
            print("Calculating overlaps...")
            combinations = self.get_top_channel_combinations(channels)
            # print(f"Channel combinations: {combinations}")
            overlaps = self.calc_overlaps(combinations)
            # print(f"Calculated overlaps: {overlaps}")
            self.overlaps = overlaps

    def dump_overlaps_to_db(self):
        print("Dumping overlaps to database...")
        logging.info("Dumping overlaps to database")
        overlaps = self.overlaps
        overlaps_table = sql.Table("channel_overlaps", self.metadata_obj, autoload_with=self.engine)

        # Get next batch_id
        print("Fetching max batch_id...")
        stmt = sql.select(func.max(overlaps_table.c.batch_id))
        with self.engine.connect() as conn:
            res = conn.execute(stmt).fetchall()

        prev_batch_id = res[0][0]
        new_batch_id = int(prev_batch_id) + 1 if prev_batch_id is not None else 0
        print(f"New batch_id: {new_batch_id}")

        for overlap in overlaps:
            overlap["batch_id"] = new_batch_id

        # print(f"Overlaps to insert: {overlaps}")

        chunks = [overlaps[x:x+100] for x in range(0, len(overlaps), 100)]
        with self.engine.connect() as conn:
            index = 1
            for chunk in chunks:
                print(f"Inserting chunk {index}/{len(chunks)}")
                logging.info(f"Insertion chunk progress: {index}/{len(chunks)}")
                try:
                    stmt = sql.insert(overlaps_table).values(chunk)
                    conn.execute(stmt)
                    conn.commit()
                except Exception as e:
                    print(f"Failed to insert data: {e}")
                    logging.error(f"Failed to insert data: {e}")
                index += 1

        print("Deleting temporary files...")
        self.delete_dir('./tmp')

    def delete_dir(self, path):
        import shutil
        print(f"Deleting directory: {path}")
        shutil.rmtree(path)
                
    def get_top_channel_combinations(self, channels):
        print("Generating channel combinations...")
        combinations = {}
        for i, channel in enumerate(channels):
            combinations[channel] = channels[i+1:]

        return combinations

    def condense_chatters(self, res):
        channel_chatters = set()
        for entry in res:
            chatters = entry['chatters']
            channel_chatters |= set(chatters)

        return channel_chatters

    def get_chatters(self, chatters_table, channel):
        print(f"Fetching chatters for channel: {channel}")
        stmt = sql.select(chatters_table.c.chatters_json).where(
            chatters_table.c.url_name == channel, 
            chatters_table.c.log_time >= self.start_time, 
            chatters_table.c.log_time <= self.end_time
        )

        with self.engine.connect() as conn:
            res = conn.execute(stmt).fetchall()

        # Convert JSON strings to Python dictionaries
        res = [json.loads(r[0]) for r in res]  # Convert each row's JSON data into a dictionary

        return self.condense_chatters(res)

    def calc_overlaps(self, channel_combinations):
        print("Calculating overlaps...")
        data = []
        counter = 0
        combination_count = sum([len(combinations) for c1, combinations in channel_combinations.items()])
        for c1, combinations in channel_combinations.items():
            print(f"Processing overlaps for channel: {c1}")
            logging.info(f"Calculating {len(combinations)} Overlaps for Channel {c1}")

            # Load chatters from pkl object
            with open(f'tmp/channel_{c1}_set.pkl', 'rb') as handle:
                c1_set = cPickle.load(handle)

            for c2 in combinations:
                counter += 1
        
                # Load comparison chatters from pkl object
                with open(f'tmp/channel_{c2}_set.pkl', 'rb') as handle:
                    c2_set = cPickle.load(handle)
                
                # Calculate overlaps and append to result
                overlap_count = len(c1_set & c2_set)
                data.append({"source": c1, "target": c2, "weight": overlap_count, "log_time": datetime.now(timezone.utc)})

        print(f"Overlap calculation complete. Total overlaps: {len(data)}")
        return data

    def generate_chatter_sets(self, channels):
        print("Generating chatter sets...")
        logging.info("Generating chatter sets as pkl objects")
        chatters_table = sql.Table('chatters', self.metadata_obj, autoload_with=self.engine)

        # Ensure the 'tmp' directory exists
        os.makedirs("tmp", exist_ok=True)

        with self.engine.connect() as conn:
            for channel in channels:
                print(f"Fetching chatters for channel: {channel}")
                chatter_set = self.get_chatters(chatters_table, channel)
                with open(f'tmp/channel_{channel}_set.pkl', 'wb') as handle:
                    cPickle.dump(chatter_set, handle)
                print(f"Chatter set dumped for channel: {channel}")
                logging.info(f"Dumped chatter set for {channel}")

    def calc_stats(self, batch_id):
        import networkx as nx
        print(f"Calculating network stats for batch_id: {batch_id}")
        overlaps_table = sql.Table("channel_overlaps", self.metadata_obj, autoload_with=self.engine)

        stmt = sql.select(overlaps_table.c.source, overlaps_table.c.target, overlaps_table.c.weight).where((overlaps_table.c.batch_id == batch_id) & (overlaps_table.c.weight >= 1000))
        with self.engine.connect() as conn:
            res = conn.execute(stmt).fetchall()
        
        network_data = {}
        for source, target, weight in res:
            if source in network_data:
                network_data[source][target] = {"weight": weight}
            else:
                network_data[source] = {target: {"weight": weight}}
        
        G = nx.from_dict_of_dicts(network_data)
        ec = nx.eigenvector_centrality(G, weight='weight', max_iter=1000)
        ec = sorted([(v, c) for v, c in ec.items()], key=lambda x: x[1], reverse=True)

        bc = nx.betweenness_centrality(G, weight='weight')
        bc = sorted([(v, c) for v, c in bc.items()], key=lambda x: x[1], reverse=True)

        cc = nx.closeness_centrality(G)
        cc = sorted([(v, c) for v, c in cc.items()], key=lambda x: x[1], reverse=True)

        print("Network stats calculation complete.")
        return {
            "eigenvector_centrality": ec,
            "betweeness_centrality": bc,
            "closeness_centrality": cc
        }


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()

    start_time = "2022-10-10 00:00:00.000"
    end_time = "2026-11-08 00:00:00.000"

    om = OverlapsManager(start_time=start_time, end_time=end_time, db_url=os.environ.get("DB_URL"))
    om.run(gen_chatter_sets = True, calc_chatter_overlaps = True)
    om.dump_overlaps_to_db()