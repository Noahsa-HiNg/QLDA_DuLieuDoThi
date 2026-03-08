import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, accuracy_score

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense

# đọc dataset
df = pd.read_csv("./../data/raw_traffic_1000000.csv")

print(df.head())

# xử lý dữ liệu
df['timestamp'] = pd.to_datetime(df['timestamp'])

df['hour'] = df['timestamp'].dt.hour
df['day'] = df['timestamp'].dt.day
df['month'] = df['timestamp'].dt.month

df = df.drop(columns=['timestamp'])

# chia feature và lable
X = df.drop(columns=['congestion_level'])
y = df['congestion_level'] 

#Encode dữ liệu
categorical = ['street_name']
numerical = ['vehicle_count','average_speed','hour','day','month']

preprocess = ColumnTransformer(
    transformers=[
        ('cat', OneHotEncoder(), categorical),
        ('num', StandardScaler(), numerical)
    ]
)

# train / test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# model linear regression
linear_model = Pipeline([
    ('prep', preprocess),
    ('model', LinearRegression())
])

linear_model.fit(X_train, y_train)

pred_lr = linear_model.predict(X_test)

print("Linear Regression RMSE:",
      np.sqrt(mean_squared_error(y_test, pred_lr)))
# model random forest
rf_model = Pipeline([
    ('prep', preprocess),
    ('model', RandomForestRegressor(
        n_estimators=100,
        random_state=42
    ))
])

rf_model.fit(X_train, y_train)

pred_rf = rf_model.predict(X_test)

print("Random Forest RMSE:",
      np.sqrt(mean_squared_error(y_test, pred_rf)))

#model LSTM
df_lstm = df.sort_values('hour')

features = ['vehicle_count','average_speed','hour']

X_lstm = df_lstm[features].values
y_lstm = df_lstm['congestion_level'].values
scaler = StandardScaler()
X_lstm = scaler.fit_transform(X_lstm)
X_train_lstm, X_test_lstm, y_train_lstm, y_test_lstm = train_test_split(
    X_lstm, y_lstm, test_size=0.2, random_state=42
)
X_train_lstm = X_train_lstm.reshape((X_train_lstm.shape[0],1,X_train_lstm.shape[1]))
X_test_lstm = X_test_lstm.reshape((X_test_lstm.shape[0],1,X_test_lstm.shape[1]))
model = Sequential([
    LSTM(64, input_shape=(1,3)),
    Dense(32, activation='relu'),
    Dense(1)
])

model.compile(
    optimizer='adam',
    loss='mse'
)

model.fit(
    X_train_lstm,
    y_train_lstm,
    epochs=20,
    batch_size=8
)
pred_lstm = model.predict(X_test_lstm)

print("LSTM RMSE:",
      np.sqrt(mean_squared_error(y_test_lstm, pred_lstm)))