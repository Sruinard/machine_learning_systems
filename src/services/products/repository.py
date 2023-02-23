import requests
import dataclasses
import datetime
from typing import List, Optional, Union
import uuid
from google.cloud import firestore
from google.cloud import pubsub_v1
import json
import config

@dataclasses.dataclass
class Product:
    asin: str
    title: str
    feature: List[str]
    description: Union[str,List[str]]
    price: str
    # dataclass field is None, string or list of strings
    image_url: Optional[Union[str, List[str]]]
    # image_url: str 
    image_url_high_res: Optional[Union[None, str, List[str]]]
    also_buy: Optional[Union[None, str,List[str]]]
    also_view: Optional[Union[None, str,List[str]]]
    rank: Optional[Union[None, str, List[str]]]
    brand: str
    category: List[str]

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            asin=data['asin'],
            title=data['title'],
            feature=data['feature'],
            description=data['description'],
            price=data['price'],
            image_url=data['image_url'],
            image_url_high_res=data['image_url_high_res'],
            also_buy=data['also_buy'],
            also_view=data['also_view'],
            rank=data['rank'],
            brand=data['brand'],
            category=data['category']
        )


# Create a repository to add product items to firestore
class FireStoreRepository:

    def __init__(self):
        self.db = firestore.Client()

    def add_product(self, product: Product):
        # check if product exists
        # if not, add it
        # if it does, update it
        self.db.collection('products').document(product.asin).set(dataclasses.asdict(product))

    def add_products(self, products: List[Product]):
        batch = self.db.batch()
        for i, product in enumerate(products):
            doc_ref = self.db.collection('products').document(product.asin)
            batch.set(doc_ref, dataclasses.asdict(product))
            if i % 500 == 0: # commit every 500 as firestore can't handle more than 500 at a time per batch
                batch.commit()
                batch = self.db.batch()
        batch.commit()

    def get_product(self, asin: str):
        doc = self.db.collection('products').document(asin).get()
        return Product.from_dict(doc.to_dict())
    
    def get_products(self, asins: List[str]):
        docs = self.db.collection('products').where('asin', 'in', asins).stream()
        return [Product.from_dict(doc.to_dict()) for doc in docs]

        

# create a repository to add a product to pubsub
class PubSubRepository:
    
        def __init__(self):
            self.publisher = pubsub_v1.PublisherClient()
            self.topic_path = self.publisher.topic_path(config.ProductsConfig.project_id, config.ProductsConfig.pubs_sub_topic)
    
        def add_product(self, product: Product):
            data = json.dumps(dataclasses.asdict(product)).encode('utf-8')
            future = self.publisher.publish(self.topic_path, data=data)
            print(future.result())
    
        def add_products(self, products: List[Product]):
            for product in products:
                self.add_product(product)