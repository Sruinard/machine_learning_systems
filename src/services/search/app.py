# create a fastapi with an endpoint to index the products and write to gcs
# and an endpoint to make lookup similar products based on a query

import os
from typing import List

import requests
import tensorflow_text  # import required
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
import repository

import predict

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8080",
]


if config.SearchConfig.load_model_and_index:
    SIM_MODEL = predict.create_similarity_model()
    predict.load_index(SIM_MODEL, config.SearchConfig.index)



app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# add endpoint to listen to pub/sub messages
@app.post("/pubsub")
def pubsub(event, context):
    repository.event_handler(event, context)


# add an endpoint which loads all products from storage and indexes them
@app.post("/jobs/index")
def index_database():
    predict.create_index_from_historical_product_data(SIM_MODEL, config.SearchConfig.index)

    repository.index_database(SIM_MODEL)
    return {"message": "indexing complete"}



@app.post("/search")
def search(query: str) -> List[str]:
    results = predict.find(query, SIM_MODEL, 3)
    return results

if __name__ == "__main__":
    port = os.getenv("PORT", 8080)
    uvicorn.run(app, host="0.0.0.0", port=port)