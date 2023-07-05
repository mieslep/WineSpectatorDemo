import pandas as pd
import openai
import pyarrow.parquet as pq
import numpy as np
import pyarrow as pa
from tqdm.auto import tqdm
from dotenv import load_dotenv
import time

load_dotenv()
import os
openai.api_key = os.environ['OPENAI_API_KEY']

if len(openai.Engine.list()['data'])==0:
    raise Exception("OPENAI_API_KEY invalid, or otherwise unable to connect")

# This file has already been created, you can find it in .zip file https://drive.google.com/file/d/1wWganXifTIxgPF-7b6fW0fQm36FAMcqn/view?usp=sharing
parquet_filename = 'wines.parquet'
embeddings_parquet_filename = 'wines-embeddings.parquet'
embed_model = "text-embedding-ada-002"

def get_embeddings(text_list):
    done = False
    embedding_list = None
    while not done:
        try:
            response = openai.Embedding.create(input=text_list, engine=embed_model)
            embedding_list = [data['embedding'] for data in response['data']]
            done = True
        except Exception as e:
            print(f"Exception occurred: {e}. Retrying in 5 seconds...")
            time.sleep(5)
    return embedding_list

data = pd.read_parquet(parquet_filename)

# Map category values to more human-readable ones
# Batch size for embedding
batch_size = 100

# DataFrame batches
data_batches = [data[i:i+batch_size] for i in range(0, len(data), batch_size)]

# Writer for parquet file
writer = None

for batch in tqdm(data_batches):
    # Modify descriptions to include winery information
    text_list = [f"From the winery: {entry['Winery']}, wine: {entry['Wine Name']}, flavour notes: {entry['Description']}" for _, entry in batch.iterrows()]

    # Get embeddings
    embeddings = get_embeddings(text_list)

    for i, (_, entry) in enumerate(batch.iterrows()):
        # Add the embeddings to the batch entry
        entry['Embedding'] = embeddings[i]
        df = pd.DataFrame([entry])
        table = pa.Table.from_pandas(df)

        if writer is None:
            writer = pq.ParquetWriter(embeddings_parquet_filename, table.schema, compression='snappy')

        writer.write_table(table)
        
if writer is not None:
    writer.close()
