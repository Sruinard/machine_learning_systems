
import io
from google.cloud import storage
import gzip
import repository
import json
import os
import repository

class BulkIngest:
    def __init__(self, storage_client = storage.Client(), firestore_repo = repository.FireStoreRepository()):
        self.storage_client = storage_client 
        self.firestore_repo = firestore_repo

    def get_blob_reference(self, bucket_name, blob_name):
        bucket = self.storage_client.bucket(bucket_name)
        return bucket.blob(blob_name)

    def ingest(self, blob: storage.Blob):
        n_items_ingested = 0

        compressed_data = io.BytesIO(blob.download_as_string())

        with gzip.open(compressed_data, mode='rt') as f:
            for line in f:
                json_object = json.loads(line)
                # write to firestore
                product = repository.Product.from_dict(json_object)
                self.firestore_repo.add_product(product)
                n_items_ingested += 1
        return "success", n_items_ingested