import os
import pathlib
from typing import List

import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier
import joblib


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
APP_ROOT = PROJECT_ROOT / "core" / "ml"
DATA_PATH = APP_ROOT / "data" / "crop_dataset.csv"
MODEL_PATH = APP_ROOT / "crop_model.joblib"
LABEL_ENCODER_PATH = APP_ROOT / "label_encoder.joblib"


SOIL_ORDER: List[str] = ["clay", "sandy", "loamy", "silt", "peat", "chalk"]
SEASON_ORDER: List[str] = ["winter", "summer", "monsoon"]
RAINFALL_ORDER: List[str] = ["low", "medium", "high"]


def one_hot_row(soil: str, season: str, rainfall: str) -> List[int]:
    features: List[int] = []
    for value, allowed in [
        (soil, SOIL_ORDER),
        (season, SEASON_ORDER),
        (rainfall, RAINFALL_ORDER),
    ]:
        for category in allowed:
            features.append(1 if value == category else 0)
    return features


def train_and_save() -> None:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found at {DATA_PATH}. Please add a CSV with columns: soil_type,season,rainfall_level,crop")

    df = pd.read_csv(DATA_PATH)
    required_cols = {"soil_type", "season", "rainfall_level", "crop"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"Dataset must contain columns: {required_cols}")

    X = [
        one_hot_row(str(row["soil_type"]).strip().lower(),
                    str(row["season"]).strip().lower(),
                    str(row["rainfall_level"]).strip().lower())
        for _, row in df.iterrows()
    ]

    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(df["crop"].astype(str).str.strip().str.lower())

    model = DecisionTreeClassifier(max_depth=None, random_state=42)
    model.fit(X, y)

    APP_ROOT.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(label_encoder, LABEL_ENCODER_PATH)

    print(f"Saved model to {MODEL_PATH}")
    print(f"Saved label encoder to {LABEL_ENCODER_PATH}")


if __name__ == "__main__":
    train_and_save()


