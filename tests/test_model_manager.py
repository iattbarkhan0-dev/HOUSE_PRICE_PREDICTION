from sqlalchemy import create_engine 
from sqlalchemy.orm import sessionmaker,declarative_base 
DataBase_URL="sqlite:///./house_price.db" 
engine=create_engine(DataBase_URL,connect_args={"check_same_thread":False}) 
Sessionlocal=sessionmaker(autocommit=False,autoflush=False,bind=engine) 
Base=declarative_base() 
def get_db(): 
    db=Sessionlocal() 
    try: 
        yield db 
    finally: 
        db.close()  
from sqlalchemy import Column,String,Integer,Float,Boolean,DateTime 
from datetime import datetime
class ModelVersion(Base): 
    __tablename__="model_version" 
    id=Column(Integer,primary_key=True,index=True) 
    version=Column(String,unique=True,nullable=False) 
    model_path=Column(String,nullable=False) 
    mae = Column(Float) 
    rmse = Column(Float) 
    r2 = Column(Float) 
    is_active=Column(Boolean,default=False,nullable=False) 
    traffic_percentage = Column(Float, default=0.0,nullable=False) 
class PredictionLog(Base): 
     __tablename__ = "prediction_logs" 
     id = Column(Integer,primary_key=True,index=True) 
     model_version = Column(String,nullable=False) 
     prediction = Column(Float,nullable=False) 
     actual_price = Column(Float,nullable=True) 
     absolute_error = Column(Float,nullable=True) 
     created_at = Column(DateTime,default=datetime.utcnow,nullable=False) 
from pydantic import BaseModel,Field 
class HouseInput(BaseModel): 
    longitude: float = Field(...,ge=-180,le=180)
    latitude: float = Field(...,ge=-90,le=90)
    housing_median_age: float = Field(...,gt=0)
    total_rooms: float = Field(...,gt=0)
    total_bedrooms: float = Field(...,gt=0)
    population: float = Field(...,gt=0)
    households: float = Field(...,gt=0)
    median_income: float = Field(...,gt=0)
    ocean_proximity: str
class ActualPriceInput(BaseModel):
    prediction_id: int = Field(...,gt=0)
    actual_price: float = Field(...,gt=0)
import os
import random
import joblib
class ModelManager:
    def __init__(self):
        self.models = {}
        self.active_version = "v2"
        self.ab_testing = False
        self.ab_versions = ["v2","v3"]
        self.traffic = {"v2": 50,"v3": 50}
        self.load_models()
        self.validate_models()
    def load_models(self):
        base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),"models")
        for version in ["v1","v2","v3"]:
            model_path = os.path.join(base_path,f"model_{version}.pkl")
            if not os.path.exists(model_path):
                print(f"WARNING: {model_path} not found")
                continue
            try:
                self.models[version] = joblib.load(model_path)
            except Exception as e:
                raise RuntimeError(f"Could not load {version}: {e}")
    def validate_models(self):
        if not self.models:
            raise RuntimeError("No models were loaded.")
        if self.active_version not in self.models:
            raise RuntimeError(f"Active model {self.active_version} is not available.")
    def get_versions(self):
        return list(self.models.keys())
    def switch_model(self, version):
        if version not in self.models:
            raise ValueError(f"Model {version} does not exist")
        self.active_version = version
    def get_model(self):
        if self.ab_testing:
            versions = list(self.traffic.keys())
            weights = list(self.traffic.values())
            version = random.choices(versions,weights=weights,k=1)[0]
        else:
            version = self.active_version
        if version not in self.models:
            raise RuntimeError(f"Model {version} is not loaded")
        return (version,self.models[version])
    def enable_ab_testing(self,version1,version2,percentage1=50,percentage2=50):
        if version1 not in self.models:
            raise ValueError(f"{version1} does not exist")
        if version2 not in self.models:
            raise ValueError(f"{version2} does not exist")
        if version1 == version2:
            raise ValueError("A/B testing requires two different model versions")
        if percentage1 < 0 or percentage2 < 0:
            raise ValueError("Traffic percentages cannot be negative")
        if not abs((percentage1 + percentage2) - 100) < 1e-6:
            raise ValueError("Traffic percentages must equal 100")
        self.ab_versions = [version1,version2]
        self.traffic = {version1: percentage1,version2: percentage2}
        self.ab_testing = True
    def disable_ab_testing(self):
        self.ab_testing = False 
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session 
from app.database import get_db 
from app.models import ModelVersion, PredictionLog 
from app.schemas import HouseInput, ActualPriceInput 
from app.model_manager import ModelManager
router = APIRouter() 
model_manager = ModelManager()
@router.get("/versions")
def get_versions(db: Session = Depends(get_db)):
    versions = db.query(ModelVersion).all() 
    return versions
@router.get("/active") 
def get_active_model(db: Session = Depends(get_db)):
    active_model = (db.query(ModelVersion).filter(ModelVersion.is_active ==True).first())
    if active_model is None: 
        return{"active_version":model_manager.active_version}
    return{"active_version":active_model.version}
@router.post("/switch/{version}")
def switch_model( version: str, db: Session = Depends(get_db)):
    if version not in model_manager.models:
        raise HTTPException( status_code=404,detail=f"Model {version} is not loaded")
    try:
        model_manager.switch_model(version)
        db.query(ModelVersion).update({ModelVersion.is_active: False })
        selected_model = ( db.query(ModelVersion) .filter(ModelVersion.version == version) .first() )

        if selected_model is None:
            selected_model = ModelVersion( version=version, model_path=f"models/model_{version}.pkl", is_active=True )
            db.add(selected_model)
        else:
            selected_model.is_active = True
        db.commit()
        return { "message": "Model switched successfully", "active_version": version }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Could not switch model: {str(e)}")
import pandas as pd
@router.post("/predict")
def predict( house: HouseInput, db: Session = Depends(get_db)):
    try:
        version, model = model_manager.get_model()
        input_data = pd.DataFrame([{ "longitude": house.longitude, "latitude": house.latitude, "housing_median_age": house.housing_median_age, "total_rooms": house.total_rooms, "total_bedrooms": house.total_bedrooms, "population": house.population, "households": house.households, "median_income": house.median_income, "ocean_proximity": house.ocean_proximity }])
        prediction = model.predict(input_data)[0]
        prediction_log = PredictionLog( model_version=version, prediction=float(prediction) )
        db.add(prediction_log)
        db.commit()
        db.refresh(prediction_log)
        return { "prediction_id": prediction_log.id, "prediction": float(prediction), "model_version": version }
    except Exception as e:
        db.rollback() 
        raise HTTPException( status_code=500, detail=f"Prediction failed: {str(e)}" )
@router.post("/ab-testing")
def configure_ab_testing(enabled: bool,version1: str = "v2",version2: str = "v3",percentage1: float = 50,percentage2: float = 50):
    if not enabled:
        model_manager.disable_ab_testing()
        return {"ab_testing": False,"message": "A/B testing disabled"}
    try:
        model_manager.enable_ab_testing(version1=version1,version2=version2,percentage1=percentage1,percentage2=percentage2)
        return {"ab_testing": True,"versions": [version1, version2],"traffic": {version1: percentage1,version2: percentage2}}
    except ValueError as e:
        raise HTTPException(status_code=400,detail=str(e))
@router.post("/actual-price") 
def save_actual_price( data: ActualPriceInput, db: Session = Depends(get_db) ):
    prediction = ( db.query(PredictionLog) .filter( PredictionLog.id == data.prediction_id ) .first() )
    if prediction is None: 
        raise HTTPException( status_code=404, detail="Prediction not found" )
    if prediction.actual_price is not None: 
        raise HTTPException( status_code=400, detail="Actual price has already been recorded" )
    prediction.actual_price = data.actual_price 
    prediction.absolute_error = abs( data.actual_price - prediction.prediction )
    db.commit() 
    db.refresh(prediction)
    return { "prediction_id": prediction.id, "model_version": prediction.model_version, "prediction": prediction.prediction, "actual_price": prediction.actual_price, "absolute_error": prediction.absolute_error } 
@router.get("/performance")
def get_performance(db: Session = Depends(get_db)):
    models = db.query(ModelVersion).all()
    performance = []
    for model in models:
        logs = (db.query(PredictionLog).filter(PredictionLog.model_version == model.version,PredictionLog.actual_price.isnot(None)).all())
        if logs:
            total_error = sum(log.absolute_error for log in logs)
            mae = total_error / len(logs)
            requests = len(logs)
        else:
            mae = None
            requests = 0
        performance.append({"version": model.version,"mae": mae,"requests": requests,"r2": model.r2,"rmse": model.rmse})
    return performance
from fastapi import FastAPI
from app.database import Base, engine 
from app.routes import router
Base.metadata.create_all(bind=engine)
app = FastAPI( title="House Price Prediction API", description="Model versioning, A/B testing and rollback system", version="1.0.0" )
app.include_router(router)
@app.get("/") 
def home():
    return { "message": "House Price Prediction API is running" }
@router.post("/rollback/{version}")
def rollback_model(
    version: str,db: Session = Depends(get_db)):
    if version not in model_manager.models:
        raise HTTPException(status_code=404,detail=f"Model {version} is not loaded")
    try:
        model_manager.switch_model(version)
        db.query(ModelVersion).update({ModelVersion.is_active: False})
        selected_model = (db.query(ModelVersion).filter(ModelVersion.version == version).first())
        if selected_model is None:
            selected_model = ModelVersion(version=version,
            model_path=f"models/model_{version}.pkl",is_active=True)
            db.add(selected_model)
        else:
            selected_model.is_active = True
        db.commit()
        return {"message": "Model rollback successful","active_version": version}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500,detail=f"Rollback failed: {str(e)}")
import streamlit as st
import requests
import pandas as pd
API_URL = "http://127.0.0.1:8000"
st.title("House Price Model Admin Panel")
st.header("Model Versions")
response = requests.get(f"{API_URL}/versions")
if response.status_code == 200:
    versions = response.json()
    if versions:
        df = pd.DataFrame(versions)
        st.dataframe(df)
    else:
        st.warning("No model versions found in database.")
else:
    st.error("Could not load model versions.")
st.header("Active Model")
response = requests.get(f"{API_URL}/active")
if response.status_code == 200:
    active_version = response.json()["active_version"]
    st.success(f"Active Model: {active_version}")
else:
    st.error("Could not get active model.")
st.header("Switch Active Model")
version = st.selectbox("Select model version",["v1", "v2", "v3"])
if st.button("Switch Model"):
    response = requests.post(f"{API_URL}/switch/{version}")
    if response.status_code == 200:
        st.success(f"Active model changed to {version}")
        st.rerun()
    else:
        st.error(response.text)
st.header("A/B Testing")
ab_enabled = st.checkbox("Enable A/B Testing")
version1 = st.selectbox("Version 1",["v1", "v2", "v3"],index=1)
version2 = st.selectbox("Version 2",["v1", "v2", "v3"],index=2)
percentage1 = st.number_input(f"Traffic for {version1} (%)",min_value=0.0,max_value=100.0,value=50.0)
percentage2 = 100 - percentage1
st.write(f"{version2} traffic: {percentage2}%")
if st.button("Configure A/B Testing"):
    params = {"enabled": ab_enabled,"version1": version1,"version2": version2,"percentage1": percentage1,"percentage2": percentage2}
    response = requests.post(f"{API_URL}/ab-testing",params=params)
    if response.status_code == 200:
        st.success("A/B testing configuration updated.")
    else:
        st.error(response.text)
st.header("Live Model Performance")
response = requests.get(f"{API_URL}/performance")
if response.status_code == 200:
    performance = response.json()
    if performance:
        performance_df = pd.DataFrame(performance)
        st.dataframe(performance_df)
        chart_data = performance_df[["version", "mae"]].dropna()
    if not chart_data.empty:
        chart_data = chart_data.set_index("version")
        st.bar_chart(chart_data)
    else:
        st.info("No performance data available yet.")
else:
    st.error("Could not load performance data.") 

        

    

    

    
    
   
 
 
 
 
                
 
