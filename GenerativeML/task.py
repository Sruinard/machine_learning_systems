# load dataset from TFTransform component
import constants
import tensorflow as tf
from transformers import TFT5ForConditionalGeneration

metrics = [tf.keras.metrics.SparseTopKCategoricalAccuracy(name="accuracy")]
model = TFT5ForConditionalGeneration.from_pretrained(constants.MODEL_FAMILY)
model.compile(metrics=metrics)


_ = model.fit(train_dataset,
                epochs=constants.EPOCHS,
                validation_data=eval_dataset,
                verbose=2
)

model.save(
    fn_args.serving_model_dir,
    save_format="tf",
    signatures={
        "serving_default": _get_serve_features_signature(model, tf_transform_output)
    }
)
