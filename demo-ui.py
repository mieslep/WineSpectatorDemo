#
# Open terminal, make sure .venv is activated, and then
#   streamlit run demo-ui.py

import streamlit as st
import os
from dotenv import load_dotenv, find_dotenv
from langchain.llms import OpenAI
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Cassandra

# Load the .env file
if not load_dotenv(find_dotenv(),override=True):
    raise Exception("Couldn't load .env file")

@st.cache_resource()
def init_connections():
    # Which LLM will we use
    llm = OpenAI(openai_api_key=os.environ['OPENAI_API_KEY'], temperature=0.1)

    # This is the model we used to generate our embeddings
    embed_model = "text-embedding-ada-002"
    embedding_function = OpenAIEmbeddings(model=embed_model)

    # Load our vector database
    cloud_config = {'secure_connect_bundle': os.environ['ASTRA_SECUREBUNDLE_PATH']}
    auth_provider = PlainTextAuthProvider(os.environ['ASTRA_CLIENT_ID'], os.environ['ASTRA_CLIENT_SECRET'])
    cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
    session = cluster.connect()

    cassVstore = Cassandra(
        embedding=embedding_function,
        session=session,
        keyspace=os.environ['ASTRA_KEYSPACE'],
        table_name=os.environ['ASTRA_TABLE']
        )

    return llm, cassVstore

##################################
st.title('🦜🔗 LLM Sommelier')

st.write("These wine pairings are based on [Daily Picks](https://www.winespectator.com/dailypicks) from Wine Spectator.")
with st.expander('**Scenario Details**'):
    st.write("""
The tasting notes have been embedded using [OpenAI's Text Embedding API](https://beta.openai.com/docs/api-reference/text-embeddings),
and stored in DataStax Astra.

Based on the meal description provided, this demo will:

1. Determine the best flavor parings for the meal, using the LLM;
2. Search the vector database for the best wine matches, using these flavor pairings;
3. Generate a sommelier-style description of the wine, using the LLM.
""")

llm, vstore = init_connections()

food_list = st.text_input('For what meal would you like a wine match?')

# If the user hits enter
if food_list:
    st.write("Finding flavour parings...")
    prompt = f"What are some suitable wine types, flavors, and aroma profiles for a meal with {food_list}? Please respond in format that would be suitable for searching a database of professional wine reviews."
    flavor_response = llm(prompt)

    st.write("Searching for wine matches...")
    wine_matches = vstore.similarity_search(flavor_response, k=3)

    sommelier_prompts=[]
    for i, d in enumerate(wine_matches):
        pairing_prompt = f"Given a meal with {food_list}, why would you pair it with {d.metadata['Wine Name']}, described as {d.page_content}? The response should be as a sommelier would describe it."
        sommelier_prompts.append(pairing_prompt)

    st.write("Generating wine recommendations...")
    recommendations = llm.generate(sommelier_prompts)
    
    st.write("Here are some wine recommendations:")
    
    rec_list=''
    for i, generation in enumerate(recommendations.generations):
        description = generation[0].text.strip('\n')
        url = f"https://www.winespectator.com{wine_matches[i].metadata['Wine URL']}"
        rec_list += f"- {description} [Add to Cart!]({url})\n"

    st.write(rec_list) 
