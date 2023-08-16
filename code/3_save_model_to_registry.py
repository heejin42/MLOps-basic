import os
from argparse import ArgumentParser

import mlflow
import pandas as pd
import psycopg2
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC


# 모델을 저장할 스토리지 주소 = MinIO api 서버 주소
os.environ["MLFLOW_S3_ENDPOINT_URL"] = "http://localhost:9000"
# 정보를 저장하기 위해 연결할 mlflow 서버 주소
os.environ["MLFLOW_TRACKING_URI"] = "http://localhost:5001"
# MinIO에 접근하기 위한 아이디
os.environ["AWS_ACCESS_KEY_ID"] = "minioheejin"
# MinIO에 접근하기 위한 비밀번호
os.environ["AWS_SECRET_ACCESS_KEY"] = "minio6843*"

# 1. get data
db_connect = psycopg2.connect(user="heejin", password="lhj6843*", host="localhost", port=5432, database="mydatabase")
df = pd.read_sql("SELECT * FROM iris_data ORDER BY id DESC LIMIT 100", db_connect)
X = df.drop(["id", "timestamp", "target"], axis="columns")
y = df["target"]
X_train, X_valid, y_train, y_valid = train_test_split(X, y, train_size=0.8, random_state=2022)

# 2. model development and train
model_pipeline = Pipeline([("scaler", StandardScaler()), ("svc", SVC())])
model_pipeline.fit(X_train, y_train)

train_pred = model_pipeline.predict(X_train)
valid_pred = model_pipeline.predict(X_valid)

train_acc = accuracy_score(y_true=y_train, y_pred=train_pred)
valid_acc = accuracy_score(y_true=y_valid, y_pred=valid_pred)

print("Train Accuracy :", train_acc)
print("Valid Accuracy :", valid_acc)

# 3. save model
parser = ArgumentParser()
parser.add_argument("--model-name", dest="model_name", type=str, default="sk_model")
args = parser.parse_args()

mlflow.set_experiment("new-exp")

signature = mlflow.models.signature.infer_signature(model_input=X_train, model_output=y_train)
input_sample = X_train.iloc[:10]

with mlflow.start_run():
    mlflow.log_metrics({"train_acc":train_acc, "valid_acc":valid_acc})
    mlflow.sklearn.log_model(
        sk_model=model_pipeline,
        artifact_path=args.model_name,
        signature=signature,
        input_example=input_sample
    )
    
# 4. save date
df.to_csv("data.csv", index=False)

코드를 실행하기 위해서는 model-name과 run-id 정보를 줘야한다.
```
python load_model_from_registry.py --model-name "sk_model" --run-id "RUN_ID"
# python3 3_load_model_from_registry.py --model-name "sk_model" --run-id "c175dd75b5d948e48aec04912765efe3"
```
