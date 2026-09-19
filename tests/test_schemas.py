import pytest
from pydantic import ValidationError
from app.schemas import HouseInput, ActualPriceInput
def test_valid_house_input():
    house = HouseInput(longitude=-122.23,latitude=37.88,housing_median_age=41,
        total_rooms=880,
        total_bedrooms=129,
        population=322,
        households=126,
        median_income=8.3252,
        ocean_proximity="NEAR BAY")

    assert house.longitude == -122.23
    assert house.latitude == 37.88
    assert house.ocean_proximity == "NEAR BAY"
def test_invalid_longitude():
    with pytest.raises(ValidationError):
        HouseInput(longitude=500,
            latitude=37.88,
            housing_median_age=41,
            total_rooms=880,
            total_bedrooms=129,
            population=322,
            households=126,
            median_income=8.3252,
            ocean_proximity="NEAR BAY")
def test_invalid_latitude():

    with pytest.raises(ValidationError):
        HouseInput(
            longitude=-122.23,
            latitude=200,
            housing_median_age=41,
            total_rooms=880,
            total_bedrooms=129,
            population=322,
            households=126,
            median_income=8.3252,
            ocean_proximity="NEAR BAY")


def test_negative_rooms():
    with pytest.raises(ValidationError):
        HouseInput(
            longitude=-122.23,
            latitude=37.88,
            housing_median_age=41,
            total_rooms=-880,
            total_bedrooms=129,
            population=322,
            households=126,
            median_income=8.3252,
            ocean_proximity="NEAR BAY")
def test_negative_population():
    with pytest.raises(ValidationError):
        HouseInput(
            longitude=-122.23,
            latitude=37.88,
            housing_median_age=41,
            total_rooms=880,
            total_bedrooms=129,
            population=-322,
            households=126,
            median_income=8.3252,
            ocean_proximity="NEAR BAY")
def test_valid_actual_price():
    data = ActualPriceInput(
        prediction_id=1,
        actual_price=350000)
    assert data.prediction_id == 1
    assert data.actual_price == 350000
def test_invalid_prediction_id():

    with pytest.raises(ValidationError):

        ActualPriceInput(
            prediction_id=0,
            actual_price=350000
        )
def test_negative_actual_price():
    with pytest.raises(ValidationError):
        ActualPriceInput(
            prediction_id=1,
            actual_price=-100)