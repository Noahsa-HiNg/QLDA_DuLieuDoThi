import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer

def set_up_data (path):
    # đọc dataset
    df = pd.read_csv(path)

    # clean data
    df = df.dropna()
    df = df.drop_duplicates()

    # xử lý dữ liệu
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    df['hour'] = df['timestamp'].dt.hour
    df['day'] = df['timestamp'].dt.day
    df['month'] = df['timestamp'].dt.month

    df = df.drop(columns=['timestamp'])
    return df

def scale_features(categorical,numerical):
    preprocess = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(), categorical),
            ('num', StandardScaler(), numerical)
        ]
    )
    return preprocess
# chia feature và label
def device_feature(df):
    X = df.drop(columns=['congestion_level'])
    y = df['congestion_level']
    return X, y