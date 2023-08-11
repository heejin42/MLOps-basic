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
                test: ["CMD", "pg_isready", "-q", "-U", "mlflow***REMOVED***", "-d", "mlflowdatabase"]
                interval: 10s
                timeout: 5s
                retries: 5
    ```


### 2) MLflow Artifact Store   

- **Artifact Store 란?**   
    - MLflow에서 학습된 모델을 저장하는 Model Registry로써 이용하는 스토리지 서비스   
    - 기본적인 파일 시스템보다 체계적으로 관리할 수 있고 외부에 있는 스토리지 서버도 사용할 수 있다.   

- **MinIO**   
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


