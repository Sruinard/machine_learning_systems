import os
import dotenv

dotenv.load_dotenv()

class ReviewServiceConfiguration:
    COSMOS_DB_HOST = os.getenv("COSMOS_DB_HOST")
    COSMOS_DB_MASTER_KEY = os.getenv("COSMOS_DB_MASTER_KEY")
    COSMOS_DB_DATABASE_ID = os.getenv("COSMOS_DB_DATABASE_ID")
    COSMOS_DB_CONTAINER_ID = os.getenv("COSMOS_DB_CONTAINER_ID")

