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

    # cur = db_connect.cursor()
    # cur.excute(create_table_query)
    # db_connect.commit()

    # cur.close()

    with db_connect.cursor() as cur:
        cur.execute(create_table_query)
        db_connect.commit()

if __name__ == "__main__":
    db_connect = psycopg2.connect(
        user='heejin',
        password='lhj6843*',
        host="localhost",
        port=5432,
        database="mydatabase",
    )
    create_table(db_connect)