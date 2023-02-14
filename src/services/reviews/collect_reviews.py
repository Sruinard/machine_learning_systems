import requests
import dataclasses
import datetime
from typing import List
from azure.cosmos import CosmosClient, PartitionKey
import uuid

@dataclasses.dataclass
class Product:
    uid: str

@dataclasses.dataclass
class Review:
    uid: str
    rating: int
    title: str
    review: str
    date: str
    asin: str
    verified_purchase: bool
    id: str = dataclasses.field(default_factory=lambda: str(uuid.uuid4()))


    @classmethod
    def from_dict(cls, data: dict) -> "Review":
        return cls(
            uid=data["uid"],
            rating=data["rating"],
            title=data["title"],
            review=data["review"],
            date=data["date"],
            asin=data["asin"],
            verified_purchase=data["verified_purchase"],
            id=data["id"]
        )
        

def convert_unix_to_iso_date(unix_date: int) -> str:
    return datetime.datetime.fromtimestamp(unix_date).isoformat()

def review_from_amazon_review(review: dict) -> Review:
    return Review(
        uid=review["id"],
        rating=review["rating"],
        title=review["title"],
        review=review["review"],
        date=convert_unix_to_iso_date(review["date"]['unix']),
        asin=review["asin"]['original'],
        verified_purchase=review["verified_purchase"],
    )

def retrieve_product_reviews_from_amazon(product_asin) -> List[Review]:
    url = "https://amazon23.p.rapidapi.com/reviews"
    querystring = {"asin":product_asin,"sort_by":"recent","country":"US"}
    headers = {
        "X-RapidAPI-Key": "75d17fd97cmshbe07fa66f4cabfap1bce8fjsnc14dcd849f49",
        "X-RapidAPI-Host": "amazon23.p.rapidapi.com"
    }
    response = requests.request("GET", url, headers=headers, params=querystring)

    reviews = []
    for review in response.json()["result"]:
        reviews.append(review_from_amazon_review(review))
    return reviews


class DBRepository:


    def create_database(self):
        raise NotImplementedError

    def create_container(self):
        raise NotImplementedError

    def insert_review(self, review: Review):
        raise NotImplementedError

    def insert_reviews(self, reviews: List[Review]):
        raise NotImplementedError

    def get_review(self, id: str) -> List[Review]:
        raise NotImplementedError

    def get_all_reviews(self) -> List[Review]:
        raise NotImplementedError

    def delete_all_reviews(self):
        raise NotImplementedError


class CosmosDBRepository(DBRepository):

    def __init__(self, endpoint, key, database, container):
        self.endpoint = endpoint
        self.key = key
        self.database = database
        self.container = container
    
    def create_database(self):
        client = CosmosClient(self.endpoint, self.key)
        database = client.create_database_if_not_exists(id=self.database)
        return database

    def create_container(self):
        client = CosmosClient(self.endpoint, self.key)
        database = client.get_database_client(self.database)
        container = database.create_container_if_not_exists(
            id=self.container, 
            partition_key=PartitionKey(path="/uid"),
        )
        return container

    def insert_review(self, review: Review):
        client = CosmosClient(self.endpoint, self.key)
        database = client.get_database_client(self.database)
        container = database.get_container_client(self.container)
        container.upsert_item(dataclasses.asdict(review))

    def insert_reviews(self, reviews: List[Review]):
        client = CosmosClient(self.endpoint, self.key)
        database = client.get_database_client(self.database)
        container = database.get_container_client(self.container)
        for review in reviews:
            container.upsert_item(dataclasses.asdict(review))

    def get_review(self, uid: str) -> List[Review]:
        client = CosmosClient(self.endpoint, self.key)
        database = client.get_database_client(self.database)
        container = database.get_container_client(self.container)
        query = "SELECT * FROM c WHERE c.uid = @uid"
        params = { "uid": uid }
        reviews = []
        for review in container.query_items(query=query, parameters=params, enable_cross_partition_query=True):
            reviews.append(Review.from_dict(review))
        return reviews

    def get_all_reviews(self) -> List[Review]:
        client = CosmosClient(self.endpoint, self.key)
        database = client.get_database_client(self.database)
        container = database.get_container_client(self.container)
        query = "SELECT * FROM c"
        
        reviews = []
        for review in container.query_items(query=query, enable_cross_partition_query=True):
            reviews.append(Review.from_dict(review))
        return reviews

    def delete_all_reviews(self):
        client = CosmosClient(self.endpoint, self.key)
        database = client.get_database_client(self.database)
        container = database.get_container_client(self.container)
        query = "SELECT * FROM c"
        for review in container.query_items(query=query, enable_cross_partition_query=True):
            container.delete_item(item=review, partition_key=review["uid"])

    def get_all_products(self):
        return [
            Product(uid="B0BCXJ8BF4") # XBOX ONE PRODUCT ASIN
        ]
