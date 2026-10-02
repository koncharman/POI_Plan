
import pandas as pd
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document
from langchain_chroma import Chroma
from prepare_poi_data import *


import os
import shutil
import re


'''
if os.path.exists("./chroma_poi"):
    shutil.rmtree("./chroma_poi", ignore_errors=True)

db_file = "./chroma_poi/chroma.sqlite3"
if os.path.exists(db_file):
    os.remove(db_file)

embeddings = OllamaEmbeddings(model="nomic-embed-text",
    base_url="http://localhost:11434")
'''




def store_data_poi(poi_df,embeddings,use_desc=False):

    documents_poi = []

    for _, row in poi_df.iterrows():



        documents_poi.append(
            Document(
                page_content=row["name"],  # POI main name
                metadata={
                    "poi_id": row["id"],           # POI ID
                    "poi_name": row["name"]           # POI name
                }
            )
        )

        if use_desc:

            split_desc = re.split(r'[.,;!?]|\band\b|\bor\b', #r'[.,;!?]|\band\b|\bor\b' r'[.,;!?]'
                                  row['description'])

            for text in split_desc:
                documents_poi.append(
                    Document(
                        page_content=text,  # POI part of text
                        metadata={
                            "poi_id": row["id"] , # POI ID
                            "poi_name": row['name'], #POI name
                        }
                    )
                )

    vector_store_poi = Chroma(
        collection_name="poi",
        embedding_function=embeddings,
        persist_directory="./chroma_poi"
    )

    batch_size = 10

    for i in range(0, len(documents_poi), batch_size):
        batch = documents_poi[i:i + batch_size]
        vector_store_poi.add_documents(batch)


    return documents_poi , vector_store_poi



def store_tags_poi(poi_df,embeddings,tag_df):

    tags_list=set(tag_df['tag'].to_list())
    area_list=set(poi_df['area'].to_list())
    cat_list=set(poi_df['category'].to_list())

    documents_tags = []

    documents_tags.append(Document(page_content="rain", metadata={"id": "rain", "type": "rain"}))
    documents_tags.append(Document(page_content="weather", metadata={"id": "rain", "type": "rain"}))
    documents_tags.append(Document(page_content="cloud", metadata={"id": "rain", "type": "rain"}))

    documents_tags.append(Document(page_content="famil", metadata={"id": "family", "type": "family"}))
    documents_tags.append(Document(page_content="child", metadata={"id": "family", "type": "family"}))
    documents_tags.append(Document(page_content="children", metadata={"id": "family", "type": "family"}))
    documents_tags.append(Document(page_content="boy", metadata={"id": "family", "type": "family"}))
    documents_tags.append(Document(page_content="girl", metadata={"id": "family", "type": "family"}))
    documents_tags.append(Document(page_content="daughter", metadata={"id": "family", "type": "family"}))

    for t in area_list:
        if t=="old town of corfu":
            documents_tags.append(Document(page_content="old town",metadata={"id": t,"type": "area"}))
        else:
            documents_tags.append(Document(page_content=t,metadata={"id": t,"type": "area"}))
    for t in cat_list:
        documents_tags.append(Document(page_content=t, metadata={"id": t, "type": "category"}))
    for t in tags_list:
        documents_tags.append(Document(page_content=t, metadata={"id": t, "type": "tag"}))

    documents_tags.append(Document(page_content="indoor", metadata={"id": "indoor", "type": "setting"}))
    documents_tags.append(Document(page_content="outdoor", metadata={"id": "outdoor", "type": "setting"}))

    vector_store_tag = Chroma(
        collection_name="tag",
        embedding_function=embeddings,
        persist_directory="./chroma_poi"
    )

    batch_size = 10

    for i in range(0, len(documents_tags), batch_size):
        batch = documents_tags[i:i + batch_size]
        vector_store_tag.add_documents(batch)

    return  documents_tags , vector_store_tag


def retrieve_docs_rag(poi_df,vector_store_poi,user_input="old fortress",top_k=10,threshold=0.2):

    user_input=user_input.lower()
    split_input = re.split(r'[.,;!?]|\band\b|\bor\b',  # r'[.,;!?]|\band\b|\bor\b' r'[.,;!?]'
                          user_input)

    phrases = []

    for part in split_input:

        words = part.split()

        if len(words) == 0:
            continue

        # unigrams, bigrams, trigrams
        for n in range(1, 4):

            if len(words) >= n:
                phrases.extend([
                    " ".join(words[i:i + n])
                    for i in range(len(words) - n + 1)
                ])

    results=[]

    for sp in phrases:


        results.extend( vector_store_poi.similarity_search_with_score(
            query=sp,
            k=top_k
        ))

    results=[r for r in results if r[1]<=threshold]




    ids_fin = {"id":[r[0].metadata["poi_id"] for r in results],
                   "name":[r[0].metadata["poi_name"] for r in results],
                    "score":[r[1] for r in results]}

    for _ , row in poi_df.iterrows():
            if row['name'] in user_input:
                ids_fin['id'].append(row['id'])
                ids_fin['name'].append(row['name'])
                ids_fin['score'].append(0)

    ids_fin = pd.DataFrame(ids_fin).sort_values(by="score").reset_index(drop=True).drop_duplicates(subset='id')

    return ids_fin


def retrieve_tags_rag(vector_store_tag,user_input="i want to eat seafood",top_k=20,threshold=0.3):

    user_input=user_input.lower()
    split_input = re.split(r'[.,;!?]|\band\b|\bor\b',  # r'[.,;!?]|\band\b|\bor\b' r'[.,;!?]'
                          user_input)

    phrases = []

    for part in split_input:

        words = part.split()

        if len(words) == 0:
            continue

        # unigrams, bigrams, trigrams
        for n in range(1, 4):

            if len(words) >= n:
                phrases.extend([
                    " ".join(words[i:i + n])
                    for i in range(len(words) - n + 1)
                ])

    results=[]

    for sp in phrases:
        results.extend( vector_store_tag.similarity_search_with_score(
            query=sp,
            k=top_k
        ))

    results=[r for r in results if r[1]<=threshold]



    results=pd.DataFrame({
            'id':[r[0].metadata["id"] for r in results ],
            'type':[r[0].metadata["type"] for r in results],
            'score':[r[1] for r in results]
        }).sort_values(by='score').drop_duplicates(subset=['id','type'])

    return results




def examples_test_rag():

    input_examples = [
        "Plan a four-hour visit to Corfu focused on art and museums on Monday, October 5, 2026, from 13:00 to 17:00.",
        "Plan a four-hour walking itinerary in Corfu focused on historical attractions on Tuesday, October 6, 2026, from 11:00 to 15:00.",
        "Can I visit Old Fortress, New Fortress, Achilleion Palace, Mon Repos Museum of Palaiopolis, and Museum of Asian Art on foot in just 90 minutes on Tuesday, October 6, 2026, between 11:00 and 12:30? Create an itinerary if possible.",
        "Plan a four-hour itinerary in Corfu focused on outdoor historical attractions on Wednesday, October 7, 2026, from 13:00 to 17:00.",
        "What should I see if I enjoy Venetian history?",
        "Make me a realistic four-hour walking plan starting at 11:00.",
        "Replace the second stop; my child would prefer something outdoors",
        "Will it rain later? Adjust the plan if necessary.",
        "Can I fit five attractions into 90 minutes?"
    ]


    #input="garitsa"
    input=input_examples[4]
    print(input)

    results_rag=retrieve_docs_rag(input)
    results_tag=retrieve_tags_rag(input)


def cosine_examples(embeddings,input_1,input_2):

    input_1="garitsa"
    input_2='garitsa / old town'

    emb1 = embeddings.embed_query(input_1)
    emb2 = embeddings.embed_query(input_2)

    similarity = sum(a * b for a, b in zip(emb1, emb2)) / (
                sum(a * a for a in emb1) ** 0.5 *
                sum(b * b for b in emb2) ** 0.5
    )

    print(similarity)
