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
Determine your Python envrionment. It is suggested to use venv or Conda; the example code was developed with Python 3.11. Similarly,
you should have an environment with Jupyter installed.

## Open the Setup Notebook
Open [setup.ipynb](setup.ipynb) in a Jupyter-compatible viewer, and follow the instructions there.

## Open the Demo Notebook
Once the setup is complete, open [demo.ipynb](demo.ipynb) in a Jupyter-compatible viewer, and follow the instructions there.
