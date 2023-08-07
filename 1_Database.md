# MLOps for MLE
## 01. Database
Docker를 이용해서 DB server를 생성하고 psycopg2 패키지를 사용해 테이블을 생성하고 데이터 삽입을 해볼 것이다.
또한 Docker 파일과 Compose 파일을 만들어 Docker 컨테이너 안에서 계속 데이터를 생성하는 서비스를 구축해볼 것이다.

### Docker의 기능
- Build and run an image as a container.
- Share images using Docker Hub.
- Deploy Docker applications using multiple containers with a database.
- Run applications using Docker Compose.

### what is a container?
A container is a sandboxed process running on a host machine that is isolated from all other processes running on that host machine.
- Is a runnable instance of an image. We can create, start, stop, move, or delete a container using the DockerAPI or CLI.
- Can be run on local machines, virtual machines, or deployed to the cloud.
- Is portable (and can be run on any OS).
- Is isolated from other containers and runs its own software, binaries, configurations, etc.

### what is a container image?
A running container uses an isolated filesystem. This isolated filesystem is provided by a container image, and the container image must contain everything needed to run an application - all dependencies, configurations, scripts, binaries, etc. The image also contains other configurations for the container, such as environment variables, a default command to run, and other metadata.

------------------------------------------------

# 실습 - 1
## DB Server Creation

[설치링크](https://www.docker.com/)   
위 링크에서 Mac - Intel Chip 버전을 설치하였음.   

docker run 명령어를 통해 옵션을 설정하여 DB 서버를 생성할 수 있다.   
-d : 컨테이너가 detached 모드로 실행하게 되며, -d 옵션 없이 실행했다면 해당 터미널에서 Ctrl + C 를 눌러서 빠져나오는 순간 해당 컨테이너는 종료된다.   
--name : 컨테이너의 이름을 지정   
-p : 컨테이너에서 외부로 노출할 포트 포워딩 (port forwarding) 을 설정한다. 형식은 host:container 으로 사용되며, 여기서는 5432:5432 로 설정하겠다.   
-e : 필요한 환경 변수를 설정한다.   
POSTGRES_USER : 유저의 이름을 설정한다.   
POSTGRES_PASSWORD : 유저의 비밀번호를 설정한다.   
POSTGRES_DB : DB 의 이름을 설정한다.   
postgres:14.0 : 사용할 이미지를 지정한다.   

```python
docker run -d \
> --name postgres-server \
> -p 5432:5432 \
> -e POSTGRES_USER=***REMOVED*** \
> -e POSTGRES_PASSWORD=password \
> -e POSTGRES_DB=mydatabase \
> postgres:14.0
```

이렇게 서버가 생성되고 나면 docker ps 명령어를 통해 확인할 수 있다.   
```
CONTAINER ID   IMAGE           COMMAND                   CREATED          STATUS          PORTS                    NAMES
363e70063ae3   postgres:14.0   "docker-entrypoint.s…"   20 seconds ago   Up 16 seconds   0.0.0.0:5432->5432/tcp   postgres-server
```

### DB 서버 확인
PostgreSQL DB 서버를 확인할 때 사용하는 CLI 툴인 psql을 설치한다.   

[설치 링크](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads)   


PostgreSQL Version - 15.3 / Mac OS X 로 설치하였다. 그 다음 아래 커맨드로 psql을 통해 postgreSQL DB 서버로 접속한다.   
```python
PGPASSWORD=password psql -h localhost -p 5432 -U ***REMOVED*** -d mydatabase
```
아래와 같은 출력을 확인할 수 있다.   
```
psql (14.8 (Homebrew), server 14.0 (Debian 14.0-1.pgdg110+1))
Type "help" for help.

mydatabase=# \du
                                   List of roles
 Role name |                         Attributes                         | Member of 
-----------+------------------------------------------------------------+-----------
 ***REMOVED***    | Superuser, Create role, Create DB, Replication, Bypass RLS | {}

mydatabase=# 
```

----------------------------------------------

# 실습 - 2
## Table Creation
생성된 DB에 query를 작성하여 테이블을 생성해보겠다.

1. pandas, psycopg2-binary, scikit-learn 패키지를 설치한다.
2. Python 스크립트를 이용하여 DB 에 접근한다.
    - user : myuser
    - password : mypassword
    - host : localhost
    - port : 5432
    - database : mydatabase
3. psycopg2 패키지를 사용하여 iris_data 테이블을 생성한다.
    - 테이블은 다음과 같은 column 들을 갖고 있어야 한다.   
    - id, sepal length (cm), sepal width (cm), petal length (cm), petal width (cm), target   
4. psql 을 이용하여 생성한 테이블을 확인한다.

### 패키지 설치
```
pip install pandas psycopg2-binary scikit-learn
```
<버전정보>   
psycopg2-binary-2.9.6   
pandas 1.1.3   
scikit-learn 0.23.2

### 테이블 생성
python으로 PostgreSQL DB 서버에 접근하는 코드를 구현하는 가장 간단한 방법은 psycopg2 패키지를 이용하는 것이다. 자세한 내용은 [공식문서](https://www.psycopg.org/docs/)를 확인하자.   

**DB Connection**
psycopg2로 DB 접근하려면 connect 함수를 이용한다. db_connect이라는 connector 인스턴스를 생성한다. 일반적으로 DB 연결에는 user, password,host,port,database 5가지 정보가 필요하다.

```python
import psycopg2

db_connect = psycopg2.connect(
    user="***REMOVED***",
    password="***REMOVED***",
    host="localhost",
    port=5432,
    database="mydatabase",
)
```

테이블을 생성하기 위한 SQL 문은 아래와 같은 형식이다.   
```sql
CREATE TABLE table_name (
    column1 datatype,
    column2 datatype,
    column3 datatype,
)
```

그럼 한번 scikit-learn 패키지의 iris 데이터를 이용해서 입력해보겠다.   

```python
import pandas as pd
from sklearn.datasets import load_iris

X, y = load_iris(return_X_y = True, as_frame=True)
df = pd.concat([x, y], axis='columns')

print(df)
print(df.dtypes)
```

데이터 타입과 컬럼 이름에 수정해야 할 부분이 있다. 그래서 수정 사항을 반영하기 위해 query를 작성한다.   

```python
create_table_query = """
CREATE TABLE IF NOT EXISTS iris_data (
    id SERIAL PRIMARY KEY,
    timestamp timestamp,
    sepal_length float8,
    sepal_width float8,
    petal_length float8,
    petal_width float8,
    target int
);"""
```

**DB에 query 전달하기**
작성한 쿼리를 DB에 전달하기 위해 아래 과정이 필요하다.   
1. Connector에서 cursor를 열고 query를 전달한다.  
```python
cur = db_connect.cursor()
cur.execute(create_table_query)
```
2. 전달된 쿼리를 실행하기 위해 connector에 commit를 한다.   
```python
db_connect.commit()
```
3. cursor 사용이 끝나면 cursor를 close한다.   
```python
cur.close()
```

위 세가지 과정을 하나의 프로세스로 처리하자.   
```python
with db_connect.cursor() as cur:
    cur.excute(create_table_query)
    db_connect.commit()
```



### Query 실행
위 프로세스의 코드를 모아서 table_creator.py로 작성한다.    
```python
# table_creator.py
import psycopg2


def create_table(db_connect):
    create_table_query = """
    CREATE TABLE IF NOT EXISTS iris_data (
        id SERIAL PRIMARY KEY,
        timestamp timestamp,
        sepal_length float8,
        sepal_width float8,
        petal_length float8,
        petal_width float8,
        target int
    );"""
    print(create_table_query)
    with db_connect.cursor() as cur:
        cur.execute(create_table_query)
        db_connect.commit()


if __name__ == "__main__":
    db_connect = psycopg2.connect(
        user="myuser",
        password="mypassword",
        host="localhost",
        port=5432,
        database="mydatabase",
    )
    create_table(db_connect)
```

위 코드를 실행한다. 만약 실행 시 psycopg2 패키지 설치가 필요하다면 pip으로 설치하고 다시 실행하면 된다.

### 테이블 확인

1) psql로 DB 접속하기   
```
PGPASSWORD=password psql -h localhost -p 5432 -U ***REMOVED*** -d mydatabase
```
2) \d 를 입력해 생성된 테이블 목록을 확인하면 아래와 같이 생성되있을 것이다.   
```
psql (14.8 (Homebrew), server 14.0 (Debian 14.0-1.pgdg110+1))
Type "help" for help.

mydatabase=# \d
               List of relations
 Schema |       Name       |   Type   | Owner  
--------+------------------+----------+--------
 public | iris_data        | table    | ***REMOVED***
 public | iris_data_id_seq | sequence | ***REMOVED***
(2 rows)
```

# 실습 - 3
## Data Insertion
이번에는 앞서 생성한 테이블에 데이터를 삽입하고 확인해볼 것이다.

### 데이터 삽입
1) Iris 데이터 불러오기    
    삽입할 데이터는 Iris 데이터로 scikit-learn 패키지의 load_iris를 이용한다. 데이터를 불러와서 앞에 생성해놓은 테이블과 컬럼명이 일치하도록 수정해준다.  

2) 데이터를 한줄 추출하여 입력하는 query를 포함하여 입력 함수를 작성한다.   
```python
def insert_data(db_connect, data):
    insert_row_query = f"""
    INSERT INTO iris_data
        (timestamp, sepal_length, sepal_width, petal_length, petal_width, target)
        VALUES (
            NOW(),
            {data.sepal_length},
            {data.sepal_width},
            {data.petal_length},
            {data.petal_width},
            {data.target}
        );"""
    print(insert_row_query)
    with db_connect.cursor() as cur:
        cur.execute(insert_row_query)
        db_connect.commit()
```


3) 확인하기      
위의 과정을 하나의 파이썬 파일 data_insertion.py로 작성하고 실행한 다음, psql로 DB 서버 접속하여 확인해보면 데이터가 한줄 입력된 것을 확인할 수 있다.
```
    PGPASSWORD=password psql -h localhost -p 5432 -U ***REMOVED*** -d mydatabase
```
```mysql
select * from iris_data;
```

mydatabase=# select * from iris_data;
 id |         timestamp          | sepal_length | sepal_width | petal_length | petal_width | target 
----+----------------------------+--------------+-------------+--------------+-------------+--------
  1 | 2023-08-05 09:00:25.150453 |          6.3 |         3.3 |            6 |         2.5 |      2
(1 row)


# 실습 - 4
## Data Insertion Loop
이번에는 데이터를 계속해서 생성해보고 계속 DB에 삽입되고 있는지 확인해보겠다.    
data_insertion.py 코드에 insert_data 파트에 반복 루프를 추가한다. 여기서 너무 빠른 시간에 추가되면 DB에 부하가 생길 수 있으므로 1초 간격을 넣어준다. 그리고 코드를 실행하면 계속 실행되며 DB에도 데이터가 계속 추가되는 것을 확인할 수 있다.
