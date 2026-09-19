from fastapi import FastAPI
from app.database import Base, engine 
from app.routes import router
Base.metadata.create_all(bind=engine)
app = FastAPI( title="House Price Prediction API", description="Model versioning, A/B testing and rollback system", version="1.0.0" )
app.include_router(router)
@app.get("/") 
def home():
    return { "message": "House Price Prediction API is running" }