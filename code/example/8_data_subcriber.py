import psycopg2
from json import loads
from kafka import KafkaConsumer

def create_table(db_connect):
    create_table_query="""
    CREATE TABLE IF NOT EXISTS iris_prediction (
        id SERIAL PRIMARY KEY,
        timestamp timestamp,
        iris_class int
    );"""
    print(create_table_query)
    with db_connect.cursor() as cur:
        cur.execute(create_table_query)
        db_connect.commit()

if __name__ == "__main__":
    db_connect = psycopg2.connect(
        user="targetuser", 
        password="targetpassword",
        host="target-postgres-server",
        port=5432,
        database="targetdatabase",
    )
    
    create_table(db_connect)

    consumer = KafkaConsumer(
        "postgres-source-iris_data",
        bootstrap_servers="broker:29092",
        auto_offset_reset="earliest",
        group_id="iris-data-consumer-group",
        value_deserializer=lambda x: loads(x),
    )
    

