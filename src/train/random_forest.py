import numpy as np
import os
import pandas as pd
import joblib

from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error
from sklearn.ensemble import RandomForestRegressor

from data.preprocessing import (
    set_up_data,
    scale_features,
    device_feature
)

# =============================
# Setup output folder
# =============================
os.makedirs("output/result", exist_ok=True)
os.makedirs("output/models", exist_ok=True)
# =============================
# Load datasets
# =============================
df_train = set_up_data("../data/train/train_traffic.csv")
df_val = set_up_data("../data/val/val_traffic.csv")
df_test = set_up_data("../data/test/test_traffic.csv")

X_train, y_train = device_feature(df_train)
X_val, y_val = device_feature(df_val)
X_test, y_test = device_feature(df_test)

print("Train size:", len(X_train))
print("Val size:", len(X_val))
print("Test size:", len(X_test))


# =============================
# Preprocessing
# =============================
categorical = ['street_name']

numerical = [
    'vehicle_count',
    'average_speed',
    'hour',
    'day',
    'month'
]

preprocess = scale_features(categorical, numerical)


# =============================
# Model
# =============================
rf_model = Pipeline([
    ('prep', preprocess),

    ('model', RandomForestRegressor(
        n_estimators=200,
        max_depth=10,
        random_state=42
    ))
])


# =============================
# Train model
# =============================
print("\nTraining Random Forest...")

rf_model.fit(X_train, y_train)


# =============================
# Evaluation
# =============================
def evaluate(model, X, y):

    pred = model.predict(X)

    rmse = np.sqrt(mean_squared_error(y, pred))

    return rmse, pred


train_rmse, pred_train = evaluate(rf_model, X_train, y_train)
val_rmse, pred_val = evaluate(rf_model, X_val, y_val)
test_rmse, pred_test = evaluate(rf_model, X_test, y_test)

print("\nModel Performance")

print("Train RMSE:", train_rmse)
print("Validation RMSE:", val_rmse)
print("Test RMSE:", test_rmse)


# =============================
# Save metrics
# =============================
metrics = pd.DataFrame({

    "dataset": ["train", "validation", "test"],

    "rmse": [train_rmse, val_rmse, test_rmse]

})

metrics.to_csv("output/result/random_forest_metrics.csv", index=False)


# =============================
# Save predictions
# =============================
pred_df = pd.DataFrame({

    "y_true": y_test,

    "y_pred": pred_test

})

pred_df.to_csv("output/result/random_forest_predictions.csv", index=False)


# =============================
# Save model
# =============================
joblib.dump(rf_model, "output/models/random_forest_model.pkl")

print("\nModel saved to output/models/random_forest_model.pkl")
print("Results saved in output/")