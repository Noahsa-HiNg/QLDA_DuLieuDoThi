import os
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
import math
from data.preprocessing import set_up_data

os.makedirs("output/result", exist_ok=True)
os.makedirs("output/models", exist_ok=True)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ==============================
# LOAD DATA
# ==============================

train_df = set_up_data("../data/train/train_traffic.csv")
test_df = set_up_data("../data/test/test_traffic.csv")

if "hour" in train_df.columns:
    train_df = train_df.sort_values("hour")
    test_df = test_df.sort_values("hour")

# ==============================
# FEATURES
# ==============================

features = ['vehicle_count', 'average_speed', 'hour', 'day', 'month']

X_train = train_df[features]
y_train = train_df['congestion_level']

X_test = test_df[features]
y_test = test_df['congestion_level']

# ==============================
# SCALE DATA
# ==============================

scaler = MinMaxScaler()

X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# ==============================
# CREATE SEQUENCES
# ==============================

def create_sequences(X, y, time_steps=10):

    Xs, ys = [], []

    for i in range(len(X) - time_steps):
        Xs.append(X[i:(i + time_steps)])
        ys.append(y.iloc[i + time_steps])

    return np.array(Xs), np.array(ys)

time_steps = 10

X_train_seq, y_train_seq = create_sequences(
    pd.DataFrame(X_train_scaled),
    y_train,
    time_steps
)

X_test_seq, y_test_seq = create_sequences(
    pd.DataFrame(X_test_scaled),
    y_test,
    time_steps
)

# ==============================
# BUILD MODEL
# ==============================

model = Sequential([
    LSTM(64, input_shape=(time_steps, len(features))),
    Dense(32, activation='relu'),
    Dense(1)
])

model.compile(
    optimizer='adam',
    loss='mse'
)

# ==============================
# TRAIN
# ==============================

print("Training LSTM model...")

model.fit(
    X_train_seq,
    y_train_seq,
    epochs=20,
    batch_size=32,
    validation_split=0.1,
    verbose=1
)

# ==============================
# EVALUATE
# ==============================

train_pred = model.predict(X_train_seq)
test_pred = model.predict(X_test_seq)

train_rmse = math.sqrt(mean_squared_error(y_train_seq, train_pred))
test_rmse = math.sqrt(mean_squared_error(y_test_seq, test_pred))

print("\nLSTM Model Performance")
print("Train RMSE:", train_rmse)
print("Test RMSE:", test_rmse)

# ==============================
# SAVE RESULT
# ==============================

os.makedirs("output/result", exist_ok=True)
os.makedirs("output/models", exist_ok=True)

metrics = pd.DataFrame({
    "dataset": ["train", "test"],
    "rmse": [train_rmse, test_rmse]
})

metrics.to_csv("output/result/lstm_metrics.csv", index=False)

# ==============================
# SAVE MODEL
# ==============================

model_dir = os.path.join(BASE_DIR, "output/models")

model.save(os.path.join(model_dir, "lstm_model.h5"))

print("\nModel saved to output/models/lstm_model.h5")