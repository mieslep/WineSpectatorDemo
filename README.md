# Sommelier Agent Demo

This demonstrates using Astra as a vector store to support a sommelier LLM agent. A restaurant or food retailer could introduce such an 
agent to their website or app.

For example Ocado has an [extensive collection of wines](https://www.ocado.com/browse/beer-wine-spirits-43510/wine-135827),
with curated descriptions such as "A fresh and vibrant sauvignon blanc with zesty notes of lime and tropical fruit." Ocado sells food to 
varying degrees of preparation from raw unprocessed foods thorugh ready-to-heat meals, so one might imagine an LLM agent could help 
select a wine based on not only past preferences, but also what is in the shopping cart or meal plan.

Wine Spectator publishes [Daily Picks](https://www.winespectator.com/dailypicks), in which tasting notes of a recent review are highlighted
in one of three different price categories.As this is nicely structured, it can serve as a simulation for what a restaurant or other 
food-related retailer might be able to access from their own wine catalogue. We will use this as the expert basis for our demo.

## Python and Jupyter Environment
Determine your Python envrionment. It is suggested to use venv or Conda; the example code was developed with Python 3.11.4. Similarly,
you should have an environment with Jupyter installed.

## Open the Setup Notebook
Open [setup.ipynb](setup.ipynb) in a Jupyter-compatible viewer, and follow the instructions there.

### Other Scripts
There are a few other scripts within this repository that are not used by the setup or demo, but were used to create the dataset 
and embeddings.

* [`download.py`](download.py) - downloads the Wine Spectator Daily Picks from winespectator.com. DO NOT run this script, as it will 
  download the entire archive of Daily Picks, which is not necessary for the demo. The raw downloaded information is
  available by downloading the `.zip` file described in the setup notebook.
* [`scrape.py`](scrape.py) - Referencing the downloaded Daily Picks, this script extracts the tasting notes and other information
  from the HTML pages and stores them in a `.parquet` file. This is the file used by the demo. If you wanted to alter 
  how the HTML is scraped, this is the file to modify.
* [`embed.py`](embed.py) - This script uses makes calls to OpenAI embeddings API to generate text embeddings of the downloaded and
  scraped tasting notes. If you wanted to modify the embedded text, or try a different embedding engine, this is the 
  file to modify.

## Run the Demos
### Jupyter Notebook
Once the setup is complete, open [demo.ipynb](demo.ipynb) in a Jupyter-compatible viewer and follow the instructions there. The notebook 
gives a step-by-step "under the covers" description of what is happening.

### Streamlit UI
Alternately, a simple UI allows you to interact with the agent; it is a single-prompt that looks for a meal description, and 
returns a list of 3 wine recommendations.

```
streamlit run demo-ui.py
```