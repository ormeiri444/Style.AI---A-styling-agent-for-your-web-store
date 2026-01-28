import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
IMAGE_OUTPUT_SIZE = os.getenv("IMAGE_OUTPUT_SIZE", "2K")
MAX_CATALOG_ITEMS = int(os.getenv("MAX_CATALOG_ITEMS", "50"))
