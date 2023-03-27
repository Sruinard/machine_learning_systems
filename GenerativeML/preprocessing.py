from typing import Dict, Text, Any, Union
import os
import tempfile
import tensorflow as tf
from transformers import T5TokenizerFast
import tensorflow_text as text
import constants
import requests
import sentencepiece.sentencepiece_model_pb2 as spmodel

def create_tf_text_tokenizer(base_tokenizer_model="t5-large"):
    base_tokenizer = T5TokenizerFast.from_pretrained(base_tokenizer_model)
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Save the vocabulary to the temporary directory
        base_tokenizer.save_vocabulary(tmp_dir)
        # Load the model file as a protobuf object
        model_proto = load_model_proto(tmp_dir)
        # Add additional special tokens to the protobuf object
        add_special_tokens(base_tokenizer, model_proto)
        # Save the modified protobuf object to the model file
        save_model_proto(tmp_dir, model_proto)
        # Load the modified model file as a TensorFlow Text tokenizer
        tokenizer = load_tf_text_tokenizer(tmp_dir)
    return tokenizer

def load_model_proto(tmp_dir):
    model_proto = spmodel.ModelProto()
    with open(os.path.join(tmp_dir, "spiece.model"), "rb") as f:
        model_proto.ParseFromString(f.read())
    return model_proto

def add_special_tokens(base_tokenizer, model_proto):
    for token, token_score in zip(base_tokenizer.additional_special_tokens, base_tokenizer.additional_special_tokens_ids):
        new_token = spmodel.ModelProto().SentencePiece()
        new_token.piece = token
        new_token.score = token_score
        model_proto.pieces.append(new_token)

def save_model_proto(tmp_dir, model_proto):
    with open(os.path.join(tmp_dir, "spiece.model"), 'wb') as f:
        f.write(model_proto.SerializeToString())

def load_tf_text_tokenizer(tmp_dir):
    with open(os.path.join(tmp_dir, "spiece.model"), "rb") as f:
        tokenizer_model_content = f.read()
        tokenizer = text.SentencepieceTokenizer(model=tokenizer_model_content)
    return tokenizer


# def load_pretrained_tokenizer_as_tf_text_tokenizer(base_tokenizer_model="t5-large"):
#     base_tokenizer = T5TokenizerFast.from_pretrained(base_tokenizer_model)

#     # create temporary directory
#     with tempfile.TemporaryDirectory() as tmp_dir:
#         # save tokenizer to temporary directory

#         base_tokenizer.save_vocabulary(tmp_dir)
#         m = model.ModelProto()
#         m.ParseFromString(open(os.path.join(tmp_dir, "spiece.model"), "rb").read())

#         for token, token_score in zip(base_tokenizer.additional_special_tokens, base_tokenizer.additional_special_tokens_ids):
#           new_token = model.ModelProto().SentencePiece()
#           new_token.piece = token
#           new_token.score = token_score
#           m.pieces.append(new_token)
#         with open(os.path.join(tmp_dir, "spiece.model"), 'wb') as f:
#           f.write(m.SerializeToString())
#         # load tokenizer from temporary directory
#         print(f"Filenames in tmp_dir: {os.listdir(tmp_dir)}")
#         with open(os.path.join(tmp_dir, "spiece.model"), "rb") as f:
#             tokenizer_model_content = f.read()
#             tokenizer = tensorflow_text.SentencepieceTokenizer(
#                 model=tokenizer_model_content
#             )
#     return tokenizer

# TOKENIZER = load_pretrained_tokenizer_as_tf_text_tokenizer(constants.PRETRAINED_MODEL_FAMILY)
def fill_in_missing(x: Union[tf.Tensor, tf.SparseTensor]) -> tf.Tensor:
    """Replace missing values in a SparseTensor.
    Fills in missing values of `x` with '' or 0, and converts to a
    dense tensor.
    Args:
      x: A `SparseTensor` of rank 2.  Its dense shape should have
        size at most 1 in the second dimension.
    Returns:
      A rank 1 tensor where missing values of `x` have been filled in.
    """
    if isinstance(x, tf.sparse.SparseTensor):
        default_value = "" if x.dtype == tf.string else 0
        x = tf.sparse.to_dense(
            tf.SparseTensor(x.indices, x.values, [x.dense_shape[0], 1]),
            default_value,
        )
    return tf.squeeze(x, axis=1)


def preprocessing_fn(inputs: tf.Tensor) -> Dict[Text, Any]:
    """tf.transform's callback function for preprocessing inputs.
    Args:
      inputs: map from feature keys to raw not-yet-transformed features.
    Returns:
      Map from string feature key to transformed feature operations.
    """

    outputs = {}
    tmp = {}

    PAD_ID = tf.constant(0, dtype=tf.int32)

    TOKENIZER = create_tf_text_tokenizer(constants.PRETRAINED_MODEL_FAMILY)

    text = tf.reshape(inputs["text"], (-1, ))
    # text = fill_in_missing(inputs["text"])
    input_ids = TOKENIZER.tokenize(text)
    input_ids_dense = input_ids.to_tensor(default_value=PAD_ID)
    # input_ids_dense = tf.squeeze(input_ids_dense, axis=1)
    input_ids_dense = input_ids_dense[:, : constants.ENCODER_MAX_LEN]
    padding = constants.ENCODER_MAX_LEN - tf.shape(input_ids_dense)[1]
    input_ids_dense = tf.pad(input_ids_dense, [[0, 0], [0, padding]], constant_values=PAD_ID)
    input_ids_dense = tf.cast(tf.reshape(input_ids_dense, (-1, constants.ENCODER_MAX_LEN)), tf.int64)
    input_mask = tf.cast(input_ids_dense > 0, tf.int64)



    # output_feature_ids = TOKENIZER.tokenize(fill_in_missing(inputs["simplifications"]))
    # output_feature_ids_dense = output_feature_ids.to_tensor(default_value=PAD_ID)
    # output_feature_ids_dense = output_feature_ids_dense[:, : constants.DECODER_MAX_LEN]
    # padding = constants.DECODER_MAX_LEN - tf.shape(output_feature_ids_dense)[1]
    # output_feature_ids_dense = tf.pad(output_feature_ids_dense, [[0, 0], [0, padding]], constant_values=PAD_ID)
    # output_feature_ids_dense = tf.cast(tf.reshape(output_feature_ids_dense, (-1, constants.DECODER_MAX_LEN)), tf.int64)
    # output_feature_mask = tf.cast(output_feature_ids_dense > 0, tf.int64)

    # Stitch together output dict
    outputs["input_ids"] = input_ids_dense
    outputs["attention_mask"] = input_mask
    # outputs["labels"] = output_feature_ids_dense
    # outputs["decoder_attention_mask"] = output_feature_mask
    return outputs