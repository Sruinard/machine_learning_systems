import tensorflow as tf
from transformers import TFAutoModel, TFBertTokenizer
from tensorflow_similarity.models import SimilarityModel
import tensorflow_similarity as tfsim
from typing import Generator
from google.cloud import storage
from google.cloud.storage import Blob
import repository
import glob
import os
import json


class TFSentenceTransformer(tf.keras.layers.Layer):
    def __init__(self, model_name_or_path, **kwargs):
        super(TFSentenceTransformer, self).__init__()
        # loads transformers model
        self.model = TFAutoModel.from_pretrained(model_name_or_path, **kwargs)

    def call(self, inputs, normalize=True):
        # runs model on inputs
        model_output = self.model(inputs)
        # Perform pooling. In this case, mean pooling.
        embeddings = self.mean_pooling(model_output, inputs["attention_mask"])
        # normalizes the embeddings if wanted
        if normalize:
            embeddings = self.normalize(embeddings)
        return embeddings

    def mean_pooling(self, model_output, attention_mask):
        # First element of model_output contains all token embeddings
        token_embeddings = model_output[0]
        input_mask_expanded = tf.cast(
            tf.broadcast_to(tf.expand_dims(attention_mask, -1),
                            tf.shape(token_embeddings)),
            tf.float32
        )
        return tf.math.reduce_sum(token_embeddings * input_mask_expanded, axis=1) / tf.clip_by_value(tf.math.reduce_sum(input_mask_expanded, axis=1), 1e-9, tf.float32.max)

    def normalize(self, embeddings):
        embeddings, _ = tf.linalg.normalize(embeddings, 2, axis=1)
        return embeddings


class E2ESentenceTransformer(tf.keras.Model):
    def __init__(self, model_name_or_path):
        super().__init__()

        self.tokenizer = TFBertTokenizer.from_pretrained(model_name_or_path)
        self.model = TFSentenceTransformer(model_name_or_path)

    def call(self, inputs):
        tokenized = self.tokenizer(
            inputs, padding="max_length", max_length=128, truncation=True)
        embedding = self.model(tokenized)
        return embedding


def create_similarity_model(model_id='sentence-transformers/all-MiniLM-L6-v2'):

    # specify input layer
    tokenizer_input = tf.keras.Input(
        shape=(), dtype='string', name="text_inputs")
    # loading model with tokenizer and sentence transformer
    e2e_model = E2ESentenceTransformer(model_id)
    # merge model with input layer
    outputs = e2e_model(tokenizer_input)

    # create similarity model
    sim_model = tfsim.models.SimilarityModel(tokenizer_input, outputs)
    return sim_model

def preprocessing(product: dict):
    product_id = product["asin"]
    text = f"<TITLE> {product['title']} </TITLE> <DESCRIPTION> {' '.join(product['description'])} </DESCRIPTION> <FEATURE> {' '.join(product['feature'])} </FEATURE>"
    return product_id, text


def create_index_from_historical_product_data(sim_model: tfsim.models.SimilarityModel, index_dest: str, historical_data_bucket_name: str = "searchpal_datasets"):
    storage_client = storage.Client()
    bucket = storage_client.bucket(historical_data_bucket_name)
    products = bucket.list_blobs(prefix='products')
    sim_model.create_index()
    # batch ingest products
    indexing_ids_and_texts = []
    indexing_batch = []
    for blob in products:
        data = blob.download_as_string()
        # convert the string to a dictionary
        data = json.loads(data)
        # add the product to the index
        product_id, text = preprocessing(data)
        indexing_ids_and_texts.append((product_id, text))
        indexing_batch.append(text)

        if len(indexing_batch) == 1000:
            try: 
                sim_model.index(x=tf.constant(indexing_batch), data=indexing_ids_and_texts)
            except Exception as e:
                print(e)
            indexing_batch = []
    # save index
    sim_model.index(x=tf.constant(indexing_batch), data=indexing_ids_and_texts)
    sim_model.save_index(index_dest)
    # upload index to gcs
    repository.upload_index(index_dest)


    
def load_index(sim_model: tfsim.models.SimilarityModel, index_dest: str ):

    # download index from gcs
    repository.download_index(index_dest)
    # load index in memory
    sim_model.load_index(index_dest)
    return sim_model

def find(query: str, sim_model: tfsim.models.SimilarityModel, top_k: int = 3):
    # query the index
    results = sim_model.lookup(x=tf.constant([query]), k=top_k)[0]
    product_descriptions = [str(result.data) for result in results]
    return product_descriptions