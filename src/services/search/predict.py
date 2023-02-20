import tensorflow as tf
from transformers import TFAutoModel, TFBertTokenizer
from tensorflow_similarity.models import SimilarityModel
import tensorflow_similarity as tfsim
from typing import Generator
from google.cloud import storage
import glob
import os


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

def create_index(products: Generator, sim_model: tfsim.models.SimilarityModel, index_dest: str):
    sim_model.create_index()
    # batch ingest products
    indexing_batch = []
    for product in products:
        index_data =" ".join([product["title"]] + product["description"] + product['feature'])
        indexing_batch.append(index_data)

        if len(indexing_batch) == 1000:
            try: 
                sim_model.index(x=tf.constant(indexing_batch), data=indexing_batch)
            except Exception as e:
                print(e)
            indexing_batch = []
    # save index
    sim_model.index(x=tf.constant(indexing_batch), data=indexing_batch)

    sim_model.save_index(index_dest)

    storage_client = storage.Client()
    bucket = storage_client.bucket("searchpal-ml-artifacts")
    # upload blob to gcs from filename
    for str_path_file in glob.glob(f'{index_dest}/**/*'):
        print(f'Uploading {str_path_file}')
        # The name of file on GCS once uploaded
        blob = bucket.blob(str_path_file)
        # The content that will be uploaded
        blob.upload_from_filename(str_path_file)
        print(f'Path in GCS: {str_path_file}')

    
def load_index(sim_model: tfsim.models.SimilarityModel, index_dest: str ):

    # download index from gcs
    storage_client = storage.Client()
    bucket = storage_client.bucket("searchpal-ml-artifacts")

    # list blobs using prefix
    blobs = bucket.list_blobs(prefix=index_dest)
    for blob in blobs:
        print(f'Downloading {blob.name}')
        if not os.path.exists(os.path.dirname(blob.name)):
            os.makedirs(os.path.dirname(blob.name))
        blob.download_to_filename(blob.name)
        print(f'Path in GCS: {blob.name}')

    sim_model.load_index(index_dest)
    return sim_model

def find(query: str, sim_model: tfsim.models.SimilarityModel, top_k: int = 5):
    # query the index
    results = sim_model.lookup(x=tf.constant([query]), k=top_k)[0]
    product_descriptions = [str(result.data) for result in results]
    return product_descriptions