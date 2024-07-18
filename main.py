import uvicorn
import logging

from src.services.api import app

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

if __name__ == "__main__":
    # uvicorn main:app --reload --port=8080
    uvicorn.run(app=app, host="0.0.0.0", port=8080)