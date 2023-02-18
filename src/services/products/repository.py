import requests
import dataclasses
import datetime
from typing import List
import uuid
from google.cloud import firestore


# given the following sample data, create a dataclass for each of the following
{
  "asin": "0000031852",
  "title": "Girls Ballet Tutu Zebra Hot Pink",
  "feature": ["Botiquecutie Trademark exclusive Brand",
              "Hot Pink Layered Zebra Print Tutu",
              "Fits girls up to a size 4T",
              "Hand wash / Line Dry",
              "Includes a Botiquecutie TM Exclusive hair flower bow"],
  "description": "This tutu is great for dress up play for your little ballerina. Botiquecute Trade Mark exclusive brand. Hot Pink Zebra print tutu.", 
  "price": 3.17,
  "imageURL": "http://ecx.images-amazon.com/images/I/51fAmVkTbyL._SY300_.jpg",
  "imageURLHighRes": "http://ecx.images-amazon.com/images/I/51fAmVkTbyL.jpg",
  "also_buy": ["B00JHONN1S", "B002BZX8Z6", "B00D2K1M3O", "0000031909", "B00613WDTQ", "B00D0WDS9A", "B00D0GCI8S", "0000031895", "B003AVKOP2", "B003AVEU6G", "B003IEDM9Q", "B002R0FA24", "B00D23MC6W", "B00D2K0PA0", "B00538F5OK", "B00CEV86I6", "B002R0FABA", "B00D10CLVW", "B003AVNY6I", "B002GZGI4E", "B001T9NUFS", "B002R0F7FE", "B00E1YRI4C", "B008UBQZKU", "B00D103F8U", "B007R2RM8W"],
  "also_viewed": ["B002BZX8Z6", "B00JHONN1S", "B008F0SU0Y", "B00D23MC6W", "B00AFDOPDA", "B00E1YRI4C", "B002GZGI4E", "B003AVKOP2", "B00D9C1WBM", "B00CEV8366", "B00CEUX0D8", "B0079ME3KU", "B00CEUWY8K", "B004FOEEHC", "0000031895", "B00BC4GY9Y", "B003XRKA7A", "B00K18LKX2", "B00EM7KAG6", "B00AMQ17JA", "B00D9C32NI", "B002C3Y6WG", "B00JLL4L5Y", "B003AVNY6I", "B008UBQZKU", "B00D0WDS9A", "B00613WDTQ", "B00538F5OK", "B005C4Y4F6", "B004LHZ1NY", "B00CPHX76U", "B00CEUWUZC", "B00IJVASUE", "B00GOR07RE", "B00J2GTM0W", "B00JHNSNSM", "B003IEDM9Q", "B00CYBU84G", "B008VV8NSQ", "B00CYBULSO", "B00I2UHSZA", "B005F50FXC", "B007LCQI3S", "B00DP68AVW", "B009RXWNSI", "B003AVEU6G", "B00HSOJB9M", "B00EHAGZNA", "B0046W9T8C", "B00E79VW6Q", "B00D10CLVW", "B00B0AVO54", "B00E95LC8Q", "B00GOR92SO", "B007ZN5Y56", "B00AL2569W", "B00B608000", "B008F0SMUC", "B00BFXLZ8M"],
  "salesRank": {"Toys & Games": 211836},
  "brand": "Coxlures",
  "categories": [["Sports & Outdoors", "Other Sports", "Dance"]]
}

@dataclasses.dataclass
class Product:
    asin: str
    title: str
    feature: List[str]
    description: str
    price: float
    image_url: str
    image_url_high_res: str
    also_buy: List[str]
    also_view: List[str]
    rank: dict
    brand: str
    category: List[List[str]]

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            asin=data['asin'],
            title=data['title'],
            feature=data['feature'],
            description=data['description'],
            price=data['price'],
            image_url=data['imageURL'],
            image_url_high_res=data['imageURLHighRes'],
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

    def get_all_products(self):
        docs = self.db.collection('products').stream()
        return [Product.from_dict(doc.to_dict()) for doc in docs]
        
