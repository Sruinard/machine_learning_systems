import tensorflow as tf
from transformers import AutoTokenizer, TFT5ForConditionalGeneration
import preprocessing
import constants

def build_model(hparams={}):

    # tf_text_tokenizer = preprocessing.create_tf_text_tokenizer(constants.PRETRAINED_MODEL_FAMILY)
    model = TFT5ForConditionalGeneration.from_pretrained(constants.PRETRAINED_MODEL_FAMILY)
    # model.tokenizer = tf_text_tokenizer
    return model


def _get_serve_features_signature(model, tf_transform_output):
    """Returns a function that parses a raw inputs and applies TFT."""

    model.tft_layer_inference = tf_transform_output.transform_features_layer()

    @tf.function(
        input_signature=(tf.TensorSpec((None,), tf.string, name="text"),)
    )
    def serving(text, context=None):

        text = tf.reshape(text, shape=[-1, 1])

        return text

        # transformed_features = model.tft_layer_inference({"text": text})
        # outputs = model.generate(
        #     input_ids=transformed_features["input_ids"],
        #     attention_mask=transformed_features["attention_mask"],
        #     max_new_tokens=constants.DECODER_MAX_LEN,
        #     # return_dict_in_generate=True,
        # )

        # return transformed_features


        # return outputs

        # sentences = model.tokenizer.detokenize(outputs["sequences"])
        
        # return {"outputs" : sentences}

    return serving

def save_model(serving_model_dir, model, tf_transform_output, signatures):
    model.save(
        serving_model_dir,
        save_format="tf",
        signatures={
            "serving_default": _get_serve_features_signature(model, tf_transform_output)
        }
    )