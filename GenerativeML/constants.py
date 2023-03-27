import os

ENCODER_MAX_LEN = 128
DECODER_MAX_LEN = 64
PRETRAINED_MODEL_FAMILY = "t5-small"
EPOCHS = 2

# This is the root directory for your TFX pip package installation.
ROOT_DIR = "/home/azureuser/"
ARTIFACT_DIR = os.path.join(ROOT_DIR, "pipelines/artifacts")
PIPELINE_NAME = "generative_dense_writing"