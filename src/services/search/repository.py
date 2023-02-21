# create a function which accepts an event from google cloud pub sub and writes the data to gcs

import base64
import json
import time
import os
import glob

from google.cloud import storage

# create a storage client
storage_client = storage.Client()
# get the bucket
bucket = storage_client.get_bucket('searchpal_datasets')

def event_handler(event, context):
    # event is a dictionary with a key 'data' which is a base64 encoded string
    # decode the string and convert it to a dictionary
    data = json.loads(base64.b64decode(event['data']).decode('utf-8'))
    # write the data to gcs
    # use the timestamp as the filename
    filename = str(time.time())
    # prepend asin to the filename
    filename ='products/' + data['asin'] + '_' + filename
    # create a blob object
    blob = bucket.blob(filename)
    # write the data to the blob
    blob.upload_from_string(json.dumps(data))
    # return a success message
    return 'success'
    


def download_index(index_dest: str, bucket_name: str = "searchpal-ml-artifacts"):
    # download index from gcs
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    # list blobs using prefix
    blobs = bucket.list_blobs(prefix=index_dest)
    for blob in blobs:
        print(f'Downloading {blob.name}')
        if not os.path.exists(os.path.dirname(blob.name)):
            os.makedirs(os.path.dirname(blob.name))
        blob.download_to_filename(blob.name)
        print(f'Path in GCS: {blob.name}')
    
def upload_index(index_dest: str, bucket_name: str = "searchpal-ml-artifacts"):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    # upload blob to gcs from filename
    for str_path_file in glob.glob(f'{index_dest}/**/*'):
        print(f'Uploading {str_path_file}')
        # The name of file on GCS once uploaded
        blob = bucket.blob(str_path_file)
        # The content that will be uploaded
        blob.upload_from_filename(str_path_file)
        print(f'Path in GCS: {str_path_file}')