import sqlite3
import requests
import time
from tqdm import tqdm

# Define database name
# This file has already been created, you can find it in .zip file https://drive.google.com/file/d/1wWganXifTIxgPF-7b6fW0fQm36FAMcqn/view?usp=sharing
database_name = 'wine_data.db'

# Define list of URLs and respective pages
url_list = ['https://www.winespectator.com/dailypicks/less_than_20/page/', 
            'https://www.winespectator.com/dailypicks/20_to_40/page/',
            'https://www.winespectator.com/dailypicks/more_than_40/page/']

pages = [5, 5, 5]

# Connect to the SQLite database
# If database doesn't exist, it will be created
conn = sqlite3.connect(database_name)

# Create a cursor object
cur = conn.cursor()

# Create table to store HTML content if it doesn't exist
cur.execute('''CREATE TABLE IF NOT EXISTS pages
               (url TEXT PRIMARY KEY, content TEXT)''')

# Iterate over URLs and their respective pages
for base_url, max_page in zip(url_list, pages):
    # Wrap your loop with tqdm for progress bar
    for page in tqdm(range(1, max_page + 1)):
        url = base_url + str(page)
        
        # Check if URL is already in the database
        cur.execute('SELECT content FROM pages WHERE url=?', (url,))
        result = cur.fetchone()
        if result is None:
            # URL is not in database, download content and store it
            response = requests.get(url)
            cur.execute('INSERT INTO pages (url, content) VALUES (?, ?)', 
                        (url, response.text))
            # Commit the transaction
            conn.commit()

        # Be polite to the server
        time.sleep(1)

# Close the connection
conn.close()
