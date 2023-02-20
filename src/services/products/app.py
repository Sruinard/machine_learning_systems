from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from typing import Optional, List
import repository
import config
import os
import uvicorn
import json
import external_bulk_ingest


app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Event(BaseModel):
    bucket: str
    name: str

@app.post("/products/ingest")
async def ingest(event: dict):
    bucket, name = event['bucket'], event["name"]

    bulk_ingest = external_bulk_ingest.BulkIngest()
    blob = bulk_ingest.get_blob_reference(bucket, name)
    success, n_items_ingested = bulk_ingest.ingest(blob)
    return JSONResponse(status_code=200, content={"success": success, "n_items_ingested": n_items_ingested})

@app.get("/products", response_model=List[repository.Product])
def get_products():
    repo = repository.FireStoreRepository()
    products = repo.get_all_products()
    return products

@app.get("/products/{asin}", response_model=repository.Product)
def get_product(asin: str):
    repo = repository.FireStoreRepository()
    product = repo.get_product(asin)
    return product

@app.get("/")
def read_root():
    return {"Hello": "World"}

if __name__ == "__main__":
    port = os.getenv("PORT", 8080)
    uvicorn.run(app, host="0.0.0.0", port=port)