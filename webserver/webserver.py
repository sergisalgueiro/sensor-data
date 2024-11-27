import dotenv
import os

load_dotenv()
# Configuration
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")

if __name__ == "__main__":
    pass
