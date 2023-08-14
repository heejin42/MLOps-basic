# MLOps for MLE
## Chapter 2. Model Development
지금까지는 MLOps에서 데이터를 생성하고 축적하는 프로세스에 대해 알아보았다. 이번 챕터에서는 그 데이터를 활용해 머신러닝 모델을 학습하고 저장하는 프로세스를 배워보겠다. 앞에서 생성한 postgres server와 data generator, iris 데이터를 이용할 것이다. 

![img](model-development.png)

------------------------

# 실습 - 1
## Base Model Development
목표 - 모델을 학습하고 저장하는 기본적인 파이프라인을 작성한다.
패키지 설치 - pandas, scikit-learn, joblib
코드 - base_train.py, base_validate_saved_model.py



### 1) 학습 및 평가 데이터 선정
- sklearn.datasets 에서 load_iris 함수를 통해 iris 데이터를 불러오고 각각 X, y에 할당한다.
- sklearn.model_selection의 train_test_split 함수를 이용해 데이터를 학습&평가 데이터로 나눈다. 여기서 추후에 재현할 수 있도록 random_seed를 지정한다. 
    - 여기서 random_seed란? random 모듈을 사용한 무작위 공정은 수많은 경우의 수를 가지고 있다. 여기서 공정의 완전한 재현이 가능하게 만들어주는 것이 random 모듈의 seed() 함수로 무작위 결과를 특정한 값으로 고정한다.
- 분리된 데이터에서 학습 데이터를 X_train, y_train에 할당하고, 평가 데이터는 X_valid, y_valid에 할당한다.

```python
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split

X, y = load_iris(return_X_y=True, as_frame=True)
X_train, X_vaild, y_train, y_valid = train_test_split(X, y, train_size=0.8, random_state=2023)
```

### 2) 모델 개발 및 학습
- 데이터를 scaling한다. 학습에 용이하게 데이터를 전처리하는 과정 중에 하나로 평균을 0 , 분산을 1로 조정하는 sklearn.preprocessing의 StandardScaler를 할당했다. 방법은 할당한 scaler를 fit_trainsform(X_train) 한 후, transform(X_valid)하면 된다. scaling 전 데이터와 후 데이터를 비교해서 확인해보자.
```python
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
scaled_X_train = scaler.fit_transform(X_train)
scaled_X_valid = scaler.transform(X_valid)

print(X_train.values[0])
print(scaled_X_train[0])

# [4.9 3.1 1.5 0.1]
# [-1.17088947  0.11301185 -1.34354813 -1.48656219]
```
- 모델을 학습한다. 사용할 모델은 sklearn.svm의 SVC로 먼저 모델을 classifier에 할당한다. 그리고 fit() 함수와 scaled_X_train, y_train 데이터를 이용한다. 학습한 모델에 predict() 함수를 적용해 주어진 데이터에 대한 예측값을 얻고 각각 train_pred와 valid_pred에 할당해준다.  

```python
from sklearn.svm import SVC
classifier = SVC()
classifier.fit(scaled_X_train, y_train)

train_pred = classifier.predict(scaled_X_train)
valid_pred = classifier.predict(scaled_X_valid)
```

- 정확도를 계산해보자. 정확도는 sklearn.metrics에서 제공하는 accuracy_score를 이용해서 계산한다.
```python
from sklearn.metrics import accuracy_score

train_acc = accuracy_score(y_true=y_train, y_pred=train_pred)
valid_acc = accuracy_score(y_true=y_valid, y_pred=valid_pred)

print("Train Accuracy : ", train_acc)
print("Valid Accuracy : ", valid_acc)

# Load Model Train Accuracy : 0.9833333333333333
# Load Model Valid Accuracy : 0.9666666666666667
```


### 3) 학습된 모델 저장
scikit-learn에서 공식적으로 권장하는 모델 저장 방법은 joblib 패키지를 이용하는 것이다. joblib,dump(model, "model_name") 형식의 코드를 실행하면 경로에 파일이 생성된다.

```python
import joblib
joblib.dump(scaler, "scaler.joblib")
joblib.dump(classifier, "classifier.joblib")
```

### 4) 저장된 모델 불러오기
다음은 모델이 정상적으로 저장이 되었는지 확인하고 검증해보겠다.

- 학습할 때 나눈 데이터를 똑같이 재현한다.
```python
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split

X, y = load_iris(return_X_y=True, as_frame=True)
X_train, X_valid, y_train, y_valid = train_test_split(X, y, train_size=0.8, random_state=2023)
```
- 저장된 모델들을 불러온다.
```python
import joblib

scaler_load = joblib.load("scaler.joblib")
classifier_load = joblib.load("classifier.joblib")
```
- 불러온 모델로 학습 및 평가 데이터를 예측해본다.
```python
scaled_X_train = scaler_load.transform(X_train)
scaled_X_valid = scaler_load.transform(X_valid)

load_train_pred = classifier_load.predict(scaled_X_train)
load_valid_pred = classifier_load.predict(scaled_X_valid)
```
- 정확도 계산해서 불러오기 전의 모델과 정확도가 같은지 비교해본다. 
```python
from sklearn.metrics import accuracy_score

load_train_acc = accuracy_score(y_true=y_train, y_pred=load_train_pred)
load_valid_acc = accuracy_score(y_true=y_valid, y_pred=load_valid_pred)

print("Load Model Train Accuracy :", load_train_acc)
print("Load Model Valid Accuracy :", load_valid_acc)

# Load Model Train Accuracy : 0.9833333333333333
# Load Model Valid Accuracy : 0.9666666666666667
```


------------------------


# 실습 - 2
## Model Pipeline
이번에는 여러 개의 모델들을 하나의 파이프라인으로 작성하고 검증하는 작업을 해보겠다. 

### 1) Model Pipeline
- Scaler & SVC
앞서 사용한 모델에는 scaler와 SVC 두 가지가 있었다. 즉 SVC 모델로 정상적으로 예측하기 위해서는 스케일러가 필요한 것인데 다른 경우에 스케일러를 사용하지 않을 수도 있고, 다른 스케일러를 사용할 수도 있다. 이런 실수를 막기 위해서는 모델들을 파이프라인화 시기면 된다. 파이프라인 된 모델에는 scaler와 svc가 같이 존재하기 때문에 학습 데이터를 파이프라인 된 모델 하나에 넣어주면 된다. 편리하긴 하지만 한번 구축된 파이프라인은 수정하기 어렵고, scaler는 여러 모델에 사용하는 경우가 있는데, 그때마다 중복적으로 학습하게 되는 단점이 있을 수 있다.    

일단 한번 코드로 작성해보겠다.
- sklearn.pipeline의 Pipeline을 사용해 작성할 수 있으며 파이프라인 안에 들어가는 값는 리스트로 (모델이름, 모델객체) 값들의 리스트가 들어간다.

```python
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score

X, y = load_iris(return_X_y=True, as_frame=True)
X_train, X_valid, y_train, y_valid = train_test_split(X, y, train_size=0.8, random_state=2022)

model_pipeline = Pipeline([("scaler", StandardScaler()), ("svc", SVC())])
model_pipeline.fit(X_train, y_train)

train_pred = model_pipeline.predict(X_train)
valid_pred = model_pipeline.predict(X_valid)

train_acc = accuracy_score(y_true=y_train, y_pred=train_pred)
valid_acc = accuracy_score(y_true=y_valid, y_pred=valid_pred)

print("Train Accuracy :", train_acc)
```
- 다음으로 모델을 저장하겠다.
```python
import joblib

joblib.dump(model_pipeline, "model_pipeline.joblib")
```

### 2) pipeline_validate_save_model.py
저장된 파이프라인이 정상적으로 동작하는지 검증해보겠다. 

```python
import joblib
from sklearn.datasets import load_iris
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

# 1. reproduce data
X, y = load_iris(return_X_y=True, as_frame=True)
X_train, X_valid, y_train, y_valid = train_test_split(X, y, train_size=0.8, random_state=2022)

# 2. load model
model_pipeline_load = joblib.load("model_pipeline.joblib")

# 3. validate
load_train_pred = model_pipeline_load.predict(X_train)
load_valid_pred = model_pipeline_load.predict(X_valid)

load_train_acc = accuracy_score(y_true=y_train, y_pred=load_train_pred)
load_valid_acc = accuracy_score(y_true=y_valid, y_pred=load_valid_pred)

print("Load Model Train Accuracy :", load_train_acc)
print("Load Model Valid Accuracy :", load_valid_acc)

# Load Model Train Accuracy : 0.9833333333333333
# Load Model Valid Accuracy : 0.9666666666666667

```

----------------------------
# 실습 - 3
## Load Data from Database
이번에는 DB에서 데이터를 가져오는 파이프라인을 작성해보겠다.

### 1) 데이터 불러오기
- id 컬럼을 기준으로 최신 데이터 100개 추출하는 쿼리문을 작성한다.
```sql
SELECT * FROM iris_data ORDER BY id DESC LIMIT 100;
```

- pandas.read_sql로 query와 DB connector를 전달한다. 여기서 PostgreSQL DB 에 연결할 수 있는 DB connector 를 생성 후 query 와 DB connector 를 이용한다. 
```python
import pandas as pd
import psycopg2

db_connect = psycopg2.connect(host="localhost", database="mydatabase", user="myuser", password="mypassword")
df = pd.read_sql("SELECT * FROM iris_data ORDER BY id DESC LIMIT 100", db_connect)
df.head(5)
```
```
(base) ihuijin-ui-MacBook-Air:code leeheejin$ python3 2_db_train.py
      id                  timestamp  ...  petal_width  target
0  38122 2023-08-10 08:22:54.053846  ...          0.2       0
1  38121 2023-08-10 08:22:53.047250  ...          0.2       0
2  38120 2023-08-10 08:22:52.040039  ...          2.1       2
3  38119 2023-08-10 08:22:51.031754  ...          0.3       0
4  38118 2023-08-10 08:22:50.024209  ...          1.5       1

[5 rows x 7 columns]
```

- 전체 코드는 다음과 같다.
```python
# db_train.py
import joblib
import pandas as pd
import psycopg2
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC

# 1. get data
db_connect = psycopg2.connect(host="localhost", database="mydatabase", user="myuser", password="mypassword")
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
joblib.dump(model_pipeline, "db_pipeline.joblib")

# 4. save data
df.to_csv("data.csv", index=False)
```

### 2) validate_save_model
앞선 챕터에서 저장된 모델을 검증하는 base_validate_save_model.py 를 수정해 db_validate_save_model.py 로 저장한다. 그리고 # 1. reproduce data 에서 저장된 데이터를 불러오도록 수정한다.

```python
# db_validate_save_model.py
import joblib
import pandas as pd
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

# 1. reproduce data
df = pd.read_csv("data.csv")
X = df.drop(["id", "timestamp", "target"], axis="columns")
y = df["target"]
X_train, X_valid, y_train, y_valid = train_test_split(X, y, train_size=0.8, random_state=2022)

# 2. load model
pipeline_load = joblib.load("db_pipeline.joblib")

# 3. validate
load_train_pred = pipeline_load.predict(X_train)
load_valid_pred = pipeline_load.predict(X_valid)

load_train_acc = accuracy_score(y_true=y_train, y_pred=load_train_pred)
load_valid_acc = accuracy_score(y_true=y_valid, y_pred=load_valid_pred)

print("Load Model Train Accuracy :", load_train_acc)
print("Load Model Valid Accuracy :", load_valid_acc)
```

