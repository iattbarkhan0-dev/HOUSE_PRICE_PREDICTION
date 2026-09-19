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