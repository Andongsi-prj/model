import pymysql


def get_db_connection():
    return pymysql.connect(
        host='192.168.0.163',
        port=3306,
        user='manufacture_user',
        password='andong1234',
        database='manufacture',
        
    )