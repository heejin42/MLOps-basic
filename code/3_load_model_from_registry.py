import os
from argparse import ArgumentParser

import mlflow
import pandas as pd
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

# 모델을 저장할 스토리지 주소 = MinIO api 서버 주소
os.environ["MLFLOW_S3_ENDPOINT_URL"] = "http://localhost:9000"
# 정보를 저장하기 위해 연결할 mlflow 서버 주소
os.environ["MLFLOW_TRACKING_URI"] = "http://localhost:5001"
# MinIO에 접근하기 위한 아이디
os.environ["AWS_ACCESS_KEY_ID"] = "minioheejin"
# MinIO에 접근하기 위한 비밀번호
os.environ["AWS_SECRET_ACCESS_KEY"] = "minio6843*"

parser = ArgumentParser()
parser.add_argument("--model-name", dest="model_name", type=str, default="sk_model")
parser.add_argument("--run-id", dest="run_id", type=str)
args = parser.parse_args()
print("!!!!!", args)

model_pipeline = mlflow.sklearn.load_model(f"runs:/{args.run_id}/{args.model_name}")

print(model_pipeline)
# Pipeline(steps=[('scaler', StandardScaler()), ('svc', SVC())])

df = pd.read_csv("data.csv")
X = df.drop(["id", "timestamp", "target"], axis="columns")
y = df["target"]
X_train, X_valid, y_train, y_valid = train_test_split(X, y, train_size=0.8, random_state=2022)
train_pred = model_pipeline.predict(X_train)
valid_pred = model_pipeline.predict(X_valid)

train_acc = accuracy_score(y_true=y_train, y_pred=train_pred)
valid_acc = accuracy_score(y_true=y_valid, y_pred=valid_pred)

print("Train Accuracy :", train_acc)
print("Valid Accuracy :", valid_acc)

# Train Accuracy : 0.9625
# Valid Accuracy : 0.95