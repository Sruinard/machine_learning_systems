
import io
from google.cloud import storage
import gzip
import repository
import json
import os
import repository

class BulkIngest:
    def __init__(self, storage_client = storage.Client(), firestore_repo = repository.FireStoreRepository(), pubsub_repo = repository.PubSubRepository()):
        self.storage_client = storage_client 
        self.firestore_repo = firestore_repo
        self.pubsub_repo = pubsub_repo

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
                # publish to pubsub
                self.pubsub_repo.add_product(product)
                n_items_ingested += 1
        return "success", n_items_ingested

    def ingest_from_file(self, bucket_name, blob_name):
        # download file from bucket

        file = self.get_blob_reference(bucket_name, blob_name)
        file.download_to_filename(blob_name)


        n_items_ingested = 0
        with open(blob_name, 'r') as f:
            for line in f:
                json_object = json.loads(line)
                # write to firestore
                product = repository.Product.from_dict(json_object)
                self.firestore_repo.add_product(product)
                # publish to pubsub
                self.pubsub_repo.add_product(product)
                n_items_ingested += 1
        return "success", n_items_ingested
    
    def upload_book_category_to_gcs(self, bucket_name, blob_name, book_data_file="./data/books.json"):
        bucket = self.storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        # create named temporary file and add
        temporary_file = os.path.join('/tmp', blob_name)




        with open(book_data_file, 'r') as infile, open(temporary_file, 'w') as outfile:
            data = json.load(infile)
            for row in data:
                if "Entrepreneurship" in row["category"]:
                    json.dump(row, outfile)
                    outfile.write('\n')
        blob.upload_from_filename(temporary_file)