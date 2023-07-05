from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
import sqlite3
import re
from dateutil.parser import parse as dateparse

# Connect to the SQLite database
# This file has already been created, you can find it in .zip file https://drive.google.com/file/d/1wWganXifTIxgPF-7b6fW0fQm36FAMcqn/view?usp=sharing
database_name = 'wine_data.db'
conn = sqlite3.connect(database_name)
cur = conn.cursor()

# This file has already been created, you can find it in .zip file https://drive.google.com/file/d/1wWganXifTIxgPF-7b6fW0fQm36FAMcqn/view?usp=sharing
parquet_filename = 'wines.parquet'
columns = ['Review Date', 'Category', 'Score', 'Winery', 'Winery URL', 'Wine Name', 'Wine URL', 'Price', 'Description', 'Reviewer']
data = pd.DataFrame(columns=columns)

# regular expression to match date format "Mon. DD, YYYY" in the HTML content
date_pattern = re.compile(r'\b\w{3}\. \d{2}, \d{4}\b')

# Define the category mapping
category_mapping = {
    "less_than_20": "Less than $20",
    "20_to_40": "$20 to $40",
    "more_than_40": "More than $40",
}

def parse_entry(date_elem, entry_elem, category):
    # Helper function to parse a single entry.
    score = entry_elem.find('span', {'class': 'pwl-score'}).text
    winery = entry_elem.find('h3').find('a')
    winery_name = winery.text
    winery_url = winery['href']
    wine = entry_elem.find('h4').find('a')
    wine_name = wine.text
    wine_url = wine['href']
    price = entry_elem.find_all('p')[0].text.strip().replace('$', '')  # Remove the dollar sign
    description, reviewer = entry_elem.find_all('p')[1].text.strip().rsplit('—', 1)
    description = description.strip()  # remove any extra spaces around the description
    reviewer = reviewer.strip()  # remove any extra spaces around the reviewer's name
    review_date = dateparse(date_elem.text.strip())  # Parse the review date

    # Create a DataFrame row from the parsed data.   
    rdf = pd.DataFrame([{'Review Date' : review_date,
                             'Category': category_mapping[category],  # use category map value instead of key
                             'Score': score, 
                             'Winery': winery_name,
                             'Winery URL': winery_url, 
                             'Wine Name': wine_name, 
                             'Wine URL': wine_url,
                             'Price': price, 
                             'Description': description, 
                             'Reviewer': reviewer}])

    # Convert Score to integer, replacing any errors with NaN
    rdf['Score'] = pd.to_numeric(rdf['Score'], errors='coerce').astype('Int64')  # 'Int64' (capital "I") can hold NaN

    # Convert Price to float, replacing any errors with NaN
    rdf['Price'] = pd.to_numeric(rdf['Price'], errors='coerce')

    return rdf

# Get the total count of URLs from the SQLite database
cur.execute('SELECT COUNT(*) FROM pages')
total_urls = cur.fetchone()[0]

# Initialize the progress bar
pbar = tqdm(total=total_urls)

# Retrieve all URLs from the SQLite database
cur.execute('SELECT url, content FROM pages')
for url, html_content in cur:
    # Parse the category from the URL
    category = url.split('/')[-3]
    price_range = category_mapping[category]
    
    soup = BeautifulSoup(html_content, 'html.parser')
    price_range_header = soup.find('h2', string=lambda s: s.strip() == price_range)

    if price_range_header is None:
        print(f"Couldn't find a header matching '{price_range}' on page {url}. Skipping this page.")
        continue

    # Get the first <p> sibling after the header
    p_sibling = price_range_header.find_next_sibling("p")

    # Check each <p> sibling to see if it's a date element
    while p_sibling is not None:
        # Check if this sibling is a date element
        date_elem_text = p_sibling.text.strip()  # remove whitespace around the date
        if date_pattern.match(date_elem_text):
            # the current p_sibling is a date_elem
            date_elem = p_sibling
            entry_elem = date_elem.find_next_sibling("div")

            # only process if we found a div sibling after the p sibling
            if entry_elem is not None:
                new_row = parse_entry(date_elem, entry_elem, category)
                data = pd.concat([data, new_row])

        # go to the next p sibling
        p_sibling = p_sibling.find_next_sibling("p")

    # Update the progress bar
    pbar.update()

# Close the progress bar
pbar.close()

# Save the updated DataFrame to the Parquet file
data.to_parquet(parquet_filename, index=False)
print(data)

# Close the connection
conn.close()
