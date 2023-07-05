from tqdm.auto import tqdm
import threading
from concurrent.futures import ThreadPoolExecutor
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
import pyarrow.parquet as pq
import pandas as pd
import hashlib
import json
from dotenv import load_dotenv
load_dotenv()
import os
import time

KEYSPACE_NAME = os.environ['ASTRA_KEYSPACE']
TABLE_NAME = os.environ['ASTRA_TABLE']
EMBEDDING_DIMENSION = 1536

# This file has already been created, you can find it in .zip file https://drive.google.com/file/d/1wWganXifTIxgPF-7b6fW0fQm36FAMcqn/view?usp=sharing
embeddings_parquet_filename = 'wines-embeddings.parquet'

from multiprocessing import Value
processed_counter = Value('i', 0)
error_counter = Value('i', 0)
retry_counter = Value('i', 0)

pfile = pq.ParquetFile(embeddings_parquet_filename)
df = pfile.read().to_pandas()

cloud_config = {'secure_connect_bundle': os.environ['ASTRA_SECUREBUNDLE_PATH']}
auth_provider = PlainTextAuthProvider(os.environ['ASTRA_CLIENT_ID'], os.environ['ASTRA_CLIENT_SECRET'])
cluster = Cluster(cloud=cloud_config
                  ,auth_provider=auth_provider
)
session = cluster.connect()

# This table structure is compatible with CassIO 0.0.6
session.execute(f"""
    CREATE TABLE IF NOT EXISTS {KEYSPACE_NAME}.{TABLE_NAME} 
    (document_id text, embedding_vector VECTOR<FLOAT, {EMBEDDING_DIMENSION}>, document TEXT, metadata_blob TEXT, PRIMARY KEY(document_id))
""")

# This index definition is compatible with CassIO 0.0.6, and excludes 
#    WITH OPTIONS = {{ 'similarity_function': 'dot_product' }}
session.execute(f"""
    CREATE CUSTOM INDEX IF NOT EXISTS {TABLE_NAME}_ann 
    ON {KEYSPACE_NAME}.{TABLE_NAME} (embedding_vector) 
    USING 'org.apache.cassandra.index.sai.StorageAttachedIndex' 
""")

class DB:
    class JSONEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, pd.Timestamp):
                return obj.isoformat()
            return super().default(obj)
    
    def __init__(self, cluster: Cluster):
        self.session = cluster.connect()
        self.pinsert = self.session.prepare(f"""
            INSERT INTO {KEYSPACE_NAME}.{TABLE_NAME}
            (document_id, embedding_vector, document, metadata_blob)
            VALUES (?, ?, ?, ?)
        """)
        self.encoder = self.JSONEncoder()

    def upsert_one(self, row):
        id_hash = hashlib.md5(str(row['Wine URL']).encode()).hexdigest()
        metadata = {k: v for k, v in row.items() if k not in ['Description', 'Embedding']}
        self.session.execute(self.pinsert, [
                id_hash,
                row['Embedding'],
                row['Description'],
                self.encoder.encode(metadata)]
        )#, timeout=5)

thread_local_storage = threading.local()

def get_db():
    if not hasattr(thread_local_storage, 'db_handle'):
        thread_local_storage.db_handle = DB(cluster)
    return thread_local_storage.db_handle

def upsert_row(indexed_row):
    _, row = indexed_row  # unpack tuple
    db = get_db()
    row = row.to_dict()
    row['Embedding'] = row['Embedding'].tolist()

    # Wrap the database operation and counter increment in a try/except block
    retries = 5
    loaded = False
    tryCount = 0
    while not loaded:
        try:
            db.upsert_one(row)
            with processed_counter.get_lock():  # ensure thread-safety with a lock
                processed_counter.value += 1
            loaded = True
        except Exception as e:
            if tryCount < retries:
                print(f"Error processing row: {e}. Retrying...")
                tryCount += 1
                with retry_counter.get_lock():  # ensure thread-safety with a lock
                    retry_counter.value += 1
                time.sleep(1)
            else:
                with error_counter.get_lock():  # ensure thread-safety with a lock
                    error_counter.value += 1
                print(f"Error processing row: {e}. Fatal.")  
                loaded = True

num_threads = 64
with ThreadPoolExecutor(max_workers=num_threads) as executor:
    list(tqdm(executor.map(upsert_row, df.iterrows()), total=df.shape[0]))

# After all the data is processed
print(f"Total rows processed: {processed_counter.value}")
print(f"Retries: {retry_counter.value}")
print(f"Error rows: {error_counter.value}")
