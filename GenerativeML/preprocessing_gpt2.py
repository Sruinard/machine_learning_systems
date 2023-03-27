from typing import Dict, Text, Any
from transformers import GPT2TokenizerFast
import os
import keras_nlp
import tensorflow as tf
import tensorflow_text
import constants


def get_gpt_tokenizer():
    vocab_dir = "vocab_gpt2"
    if not os.path.exists(vocab_dir):
        os.makedirs(vocab_dir)

    base_tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")
    base_tokenizer.save_vocabulary(vocab_dir)
    tokenizer = keras_nlp.tokenizers.BytePairTokenizer(
        'vocab_gpt2/vocab.json', 'vocab_gpt2/merges.txt', dtype='int64'
    )
    return tokenizer


def preprocessing_fn(inputs:  tf.Tensor)-> Dict[Text, Any]:
    out = {}

    # init to not reinitialize every function call
    with tf.init_scope():
        tokenizer = get_gpt_tokenizer()
    PAD_ID = tf.constant(tokenizer.vocabulary.get("<|endoftext|>"), dtype=tf.int64)
    
    # extract text and reshape
    text = inputs['text']
    text = tf.reshape(text, (-1, ))

    # tokenize text
    tokenized_inputs = tokenizer.tokenize(text)
    tokenized_inputs = tf.cast(tokenized_inputs, dtype=tf.int64)

    # convert to dense tensor and add padding
    tokenized_inputs = tokenized_inputs.to_tensor(PAD_ID)
    input_ids_dense = tokenized_inputs[:, : constants.ENCODER_MAX_LEN]
    padding = constants.ENCODER_MAX_LEN - tf.shape(input_ids_dense)[1]
    input_ids_dense = tf.pad(input_ids_dense, [[0, 0], [padding, 0]], constant_values=PAD_ID)
    input_ids_dense = tf.cast(tf.reshape(input_ids_dense, (-1, constants.ENCODER_MAX_LEN)), tf.int64)
    input_ids_dense = tf.cast(input_ids_dense, tf.int64)
    # attention_mask
    attention_mask = tf.cast(tf.not_equal(input_ids_dense, PAD_ID), tf.int64)

    out["input_ids"] = input_ids_dense
    out["attention_mask"] = attention_mask
    return out