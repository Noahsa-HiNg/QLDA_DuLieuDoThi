import numpy as np
import os
import pandas as pd
import joblib

from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error
from sklearn.linear_model import LinearRegression
os.makedirs("output/result", exist_ok=True)
os.makedirs("output/models", exist_ok=True)
from data.preprocessing import set_up_data, scale_features , device_feature

df_train = set_up_data("../data/train/train_traffic.csv")
X_train, y_train = device_feature(df_train)

print("5 raw data train")
print(df_train.head())

df_val = set_up_data("../data/val/val_traffic.csv")
X_val, y_val = device_feature(df_val)

df_test = set_up_data("../data/test/test_traffic.csv")
X_test, y_test = device_feature(df_test)


# Encode dữ liệu
categorical = ['street_name']
numerical = ['vehicle_count', 'average_speed', 'hour', 'day', 'month']

preprocess = scale_features(categorical, numerical)


# model linear regression
linear_model = Pipeline([
    ('prep', preprocess),
    ('model', LinearRegression())
])

print("\nTraining Linear Regression...")

linear_model.fit(X_train, y_train)


# Predict
pred_train = linear_model.predict(X_train)
pred_val = linear_model.predict(X_val)
pred_test = linear_model.predict(X_test)


# RMSE
train_rmse = np.sqrt(mean_squared_error(y_train, pred_train))
val_rmse = np.sqrt(mean_squared_error(y_val, pred_val))
test_rmse = np.sqrt(mean_squared_error(y_test, pred_test))


print("\nModel Performance")
print("Train RMSE:", train_rmse)
print("Validation RMSE:", val_rmse)
print("Test RMSE:", test_rmse)



# lưu kết quả
results = pd.DataFrame([{
    "model": "LinearRegression",
    "train_rmse": train_rmse,
    "val_rmse": val_rmse,
    "test_rmse": test_rmse
}])

results.to_csv("output/result/linear_regression_results.csv", index=False)


# lưu model
joblib.dump(linear_model, "output/models/linear_regression_model.pkl")


print("\nResults saved to output/result/linear_regression_results.csv")
print("Model saved to output/models/linear_regression_model.pkl")