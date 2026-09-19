from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime
from datetime import datetime
from app.database import Base
class ModelVersion(Base):
    __tablename__ = "model_version"
    id = Column(Integer, primary_key=True, index=True)
    version = Column(String, unique=True, nullable=False)
    model_path = Column(String, nullable=False)
    mae = Column(Float)
    rmse = Column(Float)
    r2 = Column(Float)
    is_active = Column(Boolean, default=False, nullable=False)
    traffic_percentage = Column(Float, default=0.0, nullable=False)
class PredictionLog(Base):
    __tablename__ = "prediction_logs"
    id = Column(Integer, primary_key=True, index=True)
    model_version = Column(String, nullable=False)
    prediction = Column(Float, nullable=False)
    actual_price = Column(Float, nullable=True)
    absolute_error = Column(Float, nullable=True)
    created_at = Column(DateTime,default=datetime.utcnow,nullable=False)