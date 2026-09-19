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