from app.database import Sessionlocal, Base, engine
from app.models import ModelVersion


# Make sure database tables exist
Base.metadata.create_all(bind=engine)

db = Sessionlocal()

# Check whether models are already seeded
existing = db.query(ModelVersion).count()

if existing > 0:
    print(f"Database already contains {existing} model records.")
    db.close()
    exit()


models = [
    ModelVersion(
        version="v1",
        model_path="models/model_v1.pkl",
        mae=70092.18,
        rmse=93842.14,
        r2=0.3280,
        is_active=False,
        traffic_percentage=0.0,
    ),

    ModelVersion(
        version="v2",
        model_path="models/model_v2.pkl",
        mae=34923.27,
        rmse=53167.85,
        r2=0.7843,
        is_active=True,
        traffic_percentage=0.0,
    ),

    ModelVersion(
        version="v3",
        model_path="models/model_v3.pkl",
        mae=48567.81,
        rmse=67685.01,
        r2=0.6504,
        is_active=False,
        traffic_percentage=0.0,
    ),
]

db.add_all(models)
db.commit()

print("Database seeded successfully.")

for model in models:
    print(
        model.version,
        "| MAE:", model.mae,
        "| RMSE:", model.rmse,
        "| R2:", model.r2,
        "| ACTIVE:", model.is_active
    )

db.close()