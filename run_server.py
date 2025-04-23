import uvicorn
from app.utils.logger import setup_logging

# Set up logging
setup_logging()

if __name__ == "__main__":
    # Run the FastAPI application with uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)