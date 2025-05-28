from pymongo import MongoClient
from config import MONGO_URI, MONGO_DB
from utils import LOGGER

# Log MongoDB client creation
LOGGER.info("Creating MongoDB Client From MONGO_URL")

# Initialize MongoDB client
client = MongoClient(MONGO_URI)
db = client[MONGO_DB]

# Log successful creation
LOGGER.info("MongoDB Client Successfully Created!")

def get_db():
    """Return the MongoDB database instance."""
    return db