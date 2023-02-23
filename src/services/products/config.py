import os
import dotenv

dotenv.load_dotenv()


# create configuration for products service
class ProductsConfig:
    pubs_sub_topic: str = os.getenv("PUBSUB_TOPIC")
    project_id: str = os.getenv("PROJECT_ID")