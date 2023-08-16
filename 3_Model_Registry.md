# MLOps for MLE
## Chapter 3 - Model Registry
Chapter2 - Model development 파트에서는 모델을 학습시키고 모델 파이프라인을 만드는 것을 해보았다면 Chapter3에서는 만들어진 모델을 저장, 관리하는 방법을 학습해보겠다. 이를 위해 MLflow 서버를 구축하는 과정, 구축된 서버에 모델을 저장하는 과정을 실습해보겠다.   
![img](./img/model-registry.png)

앞서 작성해놓은 2_db_train.py 코드와 생성되어 있는 DB Server를 활용할 것이다.


-------------


# 실습 - 1 
## MLflow Setup
MLflow 구성 요소를 이해하고, Docker Compose를 이용해 실제 서비스 환경을 비슷하게 만들어 MLflow 서버를 띄워보자.


### 1) MLflow Backend Store
- **Backend Store 란?**   
    * 수치 데이터와 MLflow 서버의 정보들을 체계적으로 관리하기 위한 DB   
    * 수치 데이터: 모델의 학습 결과인 accuracy, f1-score, 모델이 학습되면서 생기는 loss, 모델 자체의 정보인 hyperparameters 등   
    * MLflow 서버의 정보: run_id, run_name, experiment_name 등 MLflow의 메타 데이터   

- **PostgreSQL DB Server**   
    * Backend Store로 사용하기 위해 PostgreSQL DB를 새롭게 생성한다.    
    * 원하는 PostgreSQL DB 서버의 스펙을 Docker Compose 파일에 서비스 이름, 유저 이름, 비밀번호, DB 이름을 환경 변수로 설정한다.
    ```yaml
    # docker-compose.yaml
    version: "3"

    services:
        mlflow-backend-store:
            image: postgres:14.0
            container_name: mlflow-backend-store
            environment:
                POSTGRES_USER: mlflowuser
                POSTGRES_PASSWORD: mlflowpw
                POSTGRES_DB: mlflowdatabase
            healthcheck:
                test: ["CMD", "pg_isready", "-q", "-U", "mlflowheejin", "-d", "mlflowdatabase"]
                interval: 10s
                timeout: 5s
                retries: 5
    ```


### 2) MLflow Artifact Store   

- **Artifact Store 란?**   
    - MLflow에서 학습된 모델을 저장하는 Model Registry로써 이용하는 스토리지 서비스   
    - 기본적인 파일 시스템보다 체계적으로 관리할 수 있고 외부에 있는 스토리지 서버도 사용할 수 있다.   

- **MinIO**  
    - Minio는 경량 Amazon S3 호환 오브젝트 스토리지 서버로 고성능 분산 처리를 통해 대규모의 프라이빗 클라우드 인프라용으로 사용할 수 있도록 설계되었다. 자세한 설명은 ![링크](https://www.ibm.com/docs/ko/cloud-private/3.2.x?topic=private-minio)에서 확인할 수 있다.
    - Artifact Store로 MiniIO 서버를 이용하는 이유는 다음과 같다.   
        - S3를 대체할 수 있는 오픈 소스 고성능 개체 스토리지다.
        - AWS S3의 API와도 호환이 되어서 SDK도 동일하게 사용할 수 있다.   
        - MLflow에서는 AWS S3를 스토리지로 쓰도록 권장하기 때문에 같은 결과를 얻을 수 있는 MinIO를 사용한다.
    - MinIO Server
        - MinIO의 스펙을 Docker Compose 파일에 서비스 이름, 유저 이름, 비밀번호를 환경변수로 정의하고 호스트와 연결되는 포트도 정의하여 서비스에 추가한다.   
        ```yaml
        version: "3"

        services:
            mlflow-artifact-store:
                image: minio/minio
                container_name: mlflow-artifact-store
                ports:
                    - 9000:9000
                    - 9001:9001
                environment:
                    MINIO_ROOT_USER: minio
                    MINIO_ROOT_PASSWORD: miniostorage
                command: server /data/minio --console-address :9001
                healthcheck:
                    test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
                    interval: 30s
                    timeout: 20s
                    retries: 3
        ```
        - 추가 설명
            - image: MinIO 서버에 사용할 이미지는 minio/minio 이다. 
            - ports: 각각 호스트와 컨테이너의 포트를 설정한다. MinIO의 API 포트는 9000으로 포트 포워딩하고, MinIO의 Console 포트는 9001로 포트 포워딩했다.   
            - command: MinIO Server를 실행시키는 명령어로, --console-address를 통해 컨테이너의 9001 포트로 MinIO에 접근할 수 있게 한다. 


### 3) MLflow Server
앞서 만든 Backend Store 와 Artifact Store 에 접근 가능한 MLflow 서버를 생성한다. 여기서 서버 docker 컨테이너를 생성하려면 docker create [이미지이름] 명령이 필요하며 먼저 docker 이미지, 즉 Dockerfile을 만들어야 한다.
- **Dockerfile**
    ```
    FROM amd64/python:3.9-slim

    RUN apt-get update && apt-get install -y \
        git \
        wget \
        && rm -rf /var/lib/apt/lists/*

    RUN pip install -U pip &&\
        pip install boto3==1.26.8 mlflow==1.30.0 psycopg2-binary

    RUN cd /tmp && \
        wget https://dl.min.io/client/mc/release/linux-amd64/mc && \
        chmod +x mc && \
        mv mc /usr/bin/mc
    ```
- **설명**
    - FROM: Base 이미지를 Python 3.9가 포함된 이미지로 설정
    - RUN: git , wget 을 설치한다. git 은 MLflow 서버 내부 동작에, wget 은 MinIO Client 를 설치하기 위해 사용된다.
    - RUN: MLflow 를 비롯해 PostgreSQL DB, AWS S3에 관련된 Python 패키지를 설치한다.
    - RUN: 앞서 설치한 wget 을 활용하여 MinIO Client를 설치한다.
- **Docker Compose**
    - 위의 Dockerfile을 빌드하도록 Compose 파일의 서비스에 아래 내용을 담아 추가한다.
        - MinIO에 접근하기 위한 계정 정보를 환경 변수로 설정
        - 모델을 저장할 때 사용할 MinIO 초기 버켓을 생성
        - MLflow 서버를 띄우는 명령어를 작성한다. 여기서 PostgreSQL DB에 연결하기 위한 keyword argument도 추가해야 하며, MinIO에 연결하기 위한 keyword argument도 추가해야 한다.
        - docker-compose
        ```yaml
        version: "3"

        services:
            mlflow-server:
                build:
                    context: .
                    dockerfile: Dockerfile
                container_name: mlflow-server
                depends_on:
                    mlflow-backend-store:
                        condition: service_healthy
                    mlflow-artifact-store:
                        condition: service_healthy
                ports:
                    - 5001: 5000
                environment:
                    AWS_ACCESS_KEY_ID: miniouser
                    AWS_SECRET_ACCESS_KEY: miniopassword
                    MLFLOW_S3_ENDPOINT_URL: http://mlflow-artifact-store:9000
                command:
                    - /bin/sh
                    - -c
                    - |
                    mc config host add mlflowminio http://mlflow-artifact-store:9000 miniouser miniopassword &&
                    mc mb --ignore-existing mlflowminio/mlflow
                    mlflow server \
                    --backend-store-uri postgresql://mlflowuser:mlflowpassword@mlflow-backend-store/mlflowdatabase \
                    --default-artifact-root s3://mlflow/ \
                    --host 0.0.0.0
        ```
    - 설명
        - depends_on: MLflow 서버가 띄워지기 전에, PostgreSQL DB 와 MinIO 서버를 먼저 띄우도록 한다.
        - ports: 5001:5000 포트를 설정한다.
        - environment: AWS_ACCESS_KEY_ID는 AWS S3 의 credential 정보이지만 여기서는 MinIO 의 MINIO_ROOT_USER 와 동일하다. AWS_SECRET_ACCESS_KEY 또한 AWS S3 의 credential 정보이지만 여기서는 MinIO 의 MINIO_ROOT_PASSWORD 와 동일하다. MLFLOW_S3_ENDPOINT_URL은 AWS S3 의 주소를 설정하는데 여기서는 MinIO 의 주소와 같다.
        - command : MinIO 초기 버켓을 생성 하고, MLflow 서버를 실행한다.
        - mc config ~ : MinIO Client 를 활용해 MinIO 서버에 호스트를 등록한다. mc mb ~는 등록된 호스트를 통해 초기 버켓을 생성하고, mlflow server는 MLflow 서버를 동작시킨다. --backend-store-url은 명시된 정보를 통해 PostgreSQL DB 와 연결하고 --default-artifact-root는 명시된 버켓을 통해 MinIO 의 초기 버켓과 연결한다.

### 4) Docker Compose - 서비스 띄우기

그럼 위에서 작성한 Docker Compose 파일을 이용해 정의된 서비스를 백그라운드에 띄워보겠다. 그럼 3분 가량 시간동안 각각의 도커 컨테이너가 생성될 것이다.
```
docker compose up -d
docker ps

CONTAINER ID   IMAGE                       COMMAND                   CREATED         STATUS                   PORTS                              NAMES
2bf133816c3d   mlops-basic-mlflow-server   "/bin/sh -c 'mc conf…"   2 minutes ago   Up About a minute        0.0.0.0:5001->5000/tcp             mlflow-server
d3d68d13ba44   minio/minio                 "/usr/bin/docker-ent…"   2 minutes ago   Up 2 minutes (healthy)   0.0.0.0:9000-9001->9000-9001/tcp   mlflow-artifact-store
47d4075dfb66   postgres:14.0               "docker-entrypoint.s…"   2 minutes ago   Up 2 minutes (healthy)   5432/tcp                           mlflow-backend-store

```
   
- http://localhost:5001/ 에 접속하여 MLflow 서버 동작을 확인   
- http://localhost:9001/ 에 접속해서 MinIO 서버 동작을 확인   


-------------------------


# 실습 - 2
## Save Model from Registry
이번 실습에서는 모델을 학습하고 MLflow 서버에 저장해보겠다. 그 과정에서 MLflow의 모델 저장 구조를 이해해볼 것이다. 
먼저 필요한 패키지를 설치하자.
```
pip install boto3==1.26.8 mlflow==1.30.0 scikit-learn
```

### 1) 모델 학습
2_Model Development 파트의 세번째 실습에서 작성한 db_train.py 코드를 활용해 모델을 업로드하는 코드를 작성해볼 것이다. 기존 코드에서 MLflow와 통신하기 위한 환경 변수를 추가해야 하며, 모델을 mlflow에 저장하는 코드를 추가해야 한다. 
[기존코드]
```python
import pandas as pd
import psycopg2
from sklearn.model_selection import train_test_split

db_connect = psycopg2.connect(host="localhost", database="mydatabase", user="heejin", password
                              ="lhj6843*")
df = pd.read_sql("SELECT * FROM iris_data ORDER BY id DESC LIMIT 100", db_connect)
X = df.drop(["id", "timestamp", "target"], axis="columns")
y = df["target"]
X_train, X_valid, y_train, y_valid = train_test_split(X, y, train_size=0.8, random_state=2022))
```

**환경 변수 추가**
```python
import os
# 모델을 저장할 스토리지 주소 = MinIO api 서버 주소
os.environ["MLFLOW_S3_ENDPOINT_URL"] = "http://localhost:9000"
# 정보를 저장하기 위해 연결할 mlflow 서버 주소
os.environ["MLFLOW_TRACKING_URI"] = "http://localhost:5001"
# MinIO에 접근하기 위한 아이디
os.environ["AWS_ACCESS_KEY_ID"] = "minioheejin"
# MinIO에 접근하기 위한 비밀번호
os.environ["AWS_SECRET_ACCESS_KEY"] = "minio6843*"
```

**저장 기능 추가**
MLflow는 정보를 저장하기 위해 experiment와 run을 사용한다.    
- experiment:  MLflow 에서 정보를 관리하기 위해 나누는 일종의 directory이다. BERT, ResNet 과 같이 특정 이름을 통해 생성 할 수 있으며, 생성하지 않고 MLflow 에 정보를 저장하는 경우 Default 라는 이름의 experiment가 저장된다.
- run: experiment에 저장되는 모델의 실험 결과로 해당 run 에 실제 정보들이 저장되게 되며, experiment/run의 구조를 갖는다.   
MLflow는 저장에 관련된 스트립트를 실행할 때 명시된 experiment에 run을 동적으로 생성한다. 이때 각각의 run은 run_id를 부여받으며, 이 아이디를 통해 저장된 후에도 해당 정보에 접근할 수 있다. 

먼저 MLflow에서 모델을 저장할 때 이름을 설정하여 관리하기 떼문에 모델의 이름을 설정할 외부 변수를 만들어주자   
```python
from argparser import ArgumentParser
parser = ArqumentParser()
parser.add_argument("--model-name", dest="model_name", type=str, args=parser.parse_args())
```

그 다음으로는 experiment를 설정하겠다. mlflow의 set_experiment 함수는 experiment를 생성하거나 이미 존재하는 experiment를 사용한다.
```python
mlflow.set_experiment("new_exp")
```

추후에 잘못된 정보가 들어올 경우 에러를 발생시키기 위해 입력값 정보들을 설정한다.
```python
signature = mlflow.models.signature.infer_signature(model_input=X_train, model_output=train_pred))
input_sample = X_train.iloc[:10]
```

run을 생성하고 정보를 저장한다.
- mlflow.log_metrics: 모델의 결과 metrics를 dictionary 형태로 입력해 생성된 run 에 저장한다.
- mlflow.sklearn.log_model: sklearn 의 모델은 mlflow.sklearn를 사용해 업로드한다. 학습된 모델 결과물이 sklearn 객체일 경우 [MLFlow Storage Format]의 구조로 run에 저장한다.
```python
with mlflow.start_run():
    mlflow.log_metrics({"train_acc":train_acc, "valid_acc":valid_acc})
    mlflow.sklearn.log_model(
        sk_model=model_pipeline,
        artifact_path=args.model_name,
        signature=signature,
        input_example=input_sample,
    )
```

모델이 저장된 구조는 다음과 같다.
```python
# Directory written by mlflow.sklearn.save_model(model, "sk_model")

sk_model/
├── MLmodel
├── model.pkl
├── conda.yaml
├── python_env.yaml
└── requirements.txt
```

### 2) MLflow 서버에 저장하고 확인하기
완성된 코드를 실행한다.
```python
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
```

```
python save_model_to_registry.py --model-name "sk_model"
```

코드 실행의 결과를 localhost:5001 (MLflow 서버) 에서 확인한다.
![img](./img/3_mlflow_capture1.png)
![img](./img/3_mlflow_capture2.png)

코드 실행의 결과를 localhost:9001 (MinIO서버) 에서 확인한다.
![img](./img/3_mlflow_capture.png)



-------------------


# 실습 - 3
## Load Model from Registry
이번에는 MLflow에 저장해놓은 모델을 불러와서 추론하고 결과를 확인해보겠다. 

먼저 학습이 끝나서 저장되어 있는 모델을 MLflow의 built-in method를 사용해 MLflow에서 불러올 것이다.
그리고 불러온 모델을 이용해 학습 데이터의 결과를 추론해볼 것이다.

![img](./img/MLflow-model-load-diagram.png)

### 1) 환경 변수 설정
앞의 실습과 마찬가지로 MLflow 서버에 접근하기 위한 환경 변수를 설정한다.
```python
import os

os.environ["MLFLOW_S3_ENDPOINT_URL"] = "http://localhost:9000"
os.environ["MLFLOW_TRACKING_URI"] = "http://localhost:5001"
os.environ["AWS_ACCESS_KEY_ID"] = "minio"
os.environ["AWS_SECRET_ACCESS_KEY"] = "miniostorage"
```

### 2_ 모델 불러오기
불러올 모델이 sklearn 모델이기 때문에 mlflow.sklearn.load_model 함수로 저장된 모델을 불러온다. 모델을 가지고 있는 run_id와 모델을 저장할 때 설정했던 이름을 받아 외부 변수로 설정해야 한다. 그 다음 runs:/run_id/model_name의 형식으로 문자열을 만들어주고 이 문자열을 mlflow.sklearn.load_model에 입력으로 넣어준다. 
```python
parser = ArgumentParser()
parser.add_argument("--run_id", dest="run_id", type=str)
parser.add_argument("--model-name", dest="model_name", type=str, default="sk_model")
args = parser.parse_args()

model_pipeline = mlflow.sklearn.load_model(f"runs:/{args.run_id}/{args.model_name}")

print(model_pipeline)
```

코드를 실행하기 위해서는 model-name과 run-id 정보를 줘야한다.
```
python load_model_from_registry.py --model-name "sk_model" --run-id "RUN_ID"
# python3 3_load_model_from_registry.py --model-name "sk_model" --run-id "c175dd75b5d948e48aec04912765efe3"
```


### 3) pyfunc 모델 불러오기
MLflow에서는 지정한 방식에 따라 저장되어 있는 모델을 mlflow.pyfunc.load_model을 이용해 쉽게 불러올 수 있다. 이때 로드된 모델은 기존의 클래스가 아니라 mlflow.pyfunc.PyFuncModel 라는 새로 정희된 클래스로 불러와지며 이는 결과 추론 기능이 predict method를 호출하도록 wrapping된 클래스다. 
```python
model_pipeline = mlflow.pyfunc.load_model(f"runs:/{args.run_id}/{args.model_name}")
# print(model_pipeline)
# mlflow.pyfunc.loaded_model:
#   artifact_path: sk_model
#   flavor: mlflow.sklearn
#   run_id: c175dd75b5d948e48aec04912765efe3
```

### 4) 추론 코드 작성하기
먼저 앞의 채버에서 저장했던 데이터인 data.csv.를 불러와서 학습 조건과 같도록 불필요한 컬럼은 제거하고 학습 데이터와 평가 데이터로 분리한다.
```python
df = pd.read_csv(data.csv)
X = df.drop(["id", "timestamp", "target"], axis="columns")
y = df["target"]
X_train, X_valid, y_train, y_valid = train_test_split(X, y, train_size=0.8, random_state=2022)
```

그 다음으로는 2.Model Development 파트와 같이 결과를 계산하고 출력한다.
```python
train_pred = model_pipeline.predict(X_train)
valid_pred = model_pipeline_predict(X_valid)

train_acc = accuracy_score(y_true=y_train, y_tred=train_pred)
valid_acc = accuracy_score(y_true=y_valid, y_tred=valid_pred)

print("Train Accuracy :", train_acc)
print("Valid Accuracy :", valid_acc)
# Train Accuracy : 0.9625
# Valid Accuracy : 0.95
```
