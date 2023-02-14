from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from typing import Optional
import collect_reviews
import config
import os
import uvicorn


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

class Review(BaseModel):
    id: str
    uid: str
    product_id: str
    title: str
    content: str
    rating: int
    date: str
    verified_purchase: bool

    @classmethod
    def from_dict(cls, data: collect_reviews.Review) -> "Review":
        return cls(
            id=data.id,
            uid=data.uid,
            product_id=data.asin,
            title=data.title,
            content=data.review,
            rating=data.rating,
            date=data.date,
            verified_purchase=data.verified_purchase
        )


class Reviews(BaseModel):
    reviews: list[Review]

repo = collect_reviews.CosmosDBRepository(
    config.ReviewServiceConfiguration.COSMOS_DB_HOST,
    config.ReviewServiceConfiguration.COSMOS_DB_MASTER_KEY,
    config.ReviewServiceConfiguration.COSMOS_DB_DATABASE_ID,
    config.ReviewServiceConfiguration.COSMOS_DB_CONTAINER_ID,
)
# on startup, collect reviews for the products in the database
@app.on_event("startup")
async def startup_event():


    # create container if it doesn't exist
    repo.create_database()
    repo.create_container()

    if os.getenv("COLLECT_REVIEWS_ON_STARTUP", False):
        # delete all reviews
        repo.delete_all_reviews()

        # collect reviews for all products in the database
        products = repo.get_all_products()
        for product in products:
            reviews = collect_reviews.retrieve_product_reviews_from_amazon(product.uid)
            for review in reviews:
                repo.insert_review(review)


@app.post("/reviews/{product_id}", response_model=Reviews)
def collect_aws_reviews(product_id: str):
    reviews = collect_reviews.retrieve_product_reviews_from_amazon(product_id)
    for review in reviews:
        repo.insert_review(review)
    return Reviews(reviews=reviews)

@app.post("/reviews", response_model=Review)
def create_review(review: Review):
    repo.insert_review(review)
    return review

@app.get("/reviews", response_model=Reviews)
def get_all_reviews():
    reviews = repo.get_all_reviews()
    reviews_response_model = [Review.from_dict(review) for review in reviews]
    return Reviews(reviews=reviews_response_model)

@app.delete("/reviews")
def delete_all_reviews():
    repo.delete_all_reviews()
    return JSONResponse(status_code=200, content=jsonable_encoder({"message": "success"}))

@app.get("/reviews/{id}", response_model=Review)
def get_review(id: str):
    review = repo.get_review(id)
    return Review.from_dict(review)


if __name__ == "__main__":
    port = os.getenv("PORT", 8080)
    uvicorn.run(app, host="0.0.0.0", port=port)
