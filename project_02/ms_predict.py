import mysql.connector
from mysql.connector import Error
import pandas as pd
from statsmodels.tsa.api import VAR

# -----------------------------
# MySQL 관련 설정 및 함수
# -----------------------------

MYSQL_CONFIG = {
    'host': '5gears.iptime.org',
    'user': 'root',
    'password': 'andong1234',
    'database': 'analysis'
}


def connect_to_mysql():
    """MySQL 데이터베이스에 연결"""
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        if connection.is_connected():
            print("MySQL에 성공적으로 연결되었습니다.")
            return connection
    except Error as e:
        print(f"MySQL 연결 중 오류: {e}")
        return None


def fetch_data_from_mysql(connection, table_name):
    """MySQL에서 데이터를 가져와 DataFrame으로 반환"""
    try:
        sql_query = f"SELECT * FROM {table_name};"
        df = pd.read_sql(sql_query, con=connection)
        print(f"테이블 '{table_name}'에서 {len(df)}개의 행을 가져왔습니다.")
        return df
    except Error as e:
        print(f"MySQL 데이터 가져오기 오류: {e}")
        return None


def insert_forecast_to_mysql(connection, table_name, forecast_data):
    """예측 데이터를 MySQL 테이블에 삽입 (중복 방지)"""
    try:
        cursor = connection.cursor()
        for _, row in forecast_data.iterrows():
            # 중복 확인 쿼리
            check_query = f"SELECT COUNT(*) FROM {table_name} WHERE `record_date` = %s"
            cursor.execute(check_query, (row['record_date'],))
            if cursor.fetchone()[0] > 0:
                print(f"'{row['record_date']}' 데이터는 이미 존재합니다. 삽입을 건너뜁니다.")
                continue

            # 데이터 삽입 쿼리
            columns = ', '.join([f'`{col}`' for col in forecast_data.columns])
            placeholders = ', '.join(['%s'] * len(forecast_data.columns))
            insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            cursor.execute(insert_query, tuple(row))

        connection.commit()
        print(f"테이블 '{table_name}'에 예측 데이터가 성공적으로 삽입되었습니다.")
    except Error as e:
        print(f"데이터 삽입 오류: {e}")
    finally:
        if connection.is_connected():
            cursor.close()


# -----------------------------
# 데이터 전처리 및 예측 함수
# -----------------------------

def preprocess_data(df):
    """데이터 전처리"""
    df['record_date'] = pd.to_datetime(df['record_date'])
    df.set_index('record_date', inplace=True)

    # 숫자형 변환 및 결측값 처리
    df = df.apply(pd.to_numeric, errors='coerce')
    return df


def train_and_forecast_VAR(df, steps=1):
    """VAR 모델 학습 및 예측"""
    # 차분 처리
    df_diff = df.diff().dropna()

    # VAR 모델 학습
    model = VAR(df_diff)
    model_fitted = model.fit(maxlags=15)

    # 예측 수행
    forecast_diff = model_fitted.forecast(y=df_diff.values[-model_fitted.k_ar:], steps=steps)

    # 차분 복원 및 결과 반환
    forecast_df = pd.DataFrame(
        forecast_diff,
        index=[df.index[-1] + pd.DateOffset(months=i) for i in range(1, steps + 1)],
        columns=df.columns
    )
    return forecast_df + df.iloc[-1]


# -----------------------------
# 메인 실행 흐름
# -----------------------------

def main():
    """메인 실행 함수"""
    connection = connect_to_mysql()
    
    if not connection:
        return

    try:
        # 데이터 가져오기
        ms_data = fetch_data_from_mysql(connection, "market_stable")
        if ms_data is None or ms_data.empty:
            print("데이터를 가져오지 못했습니다.")
            return

        # 데이터 전처리
        ms_df = preprocess_data(ms_data)

        # VAR 모델 학습 및 예측 수행
        forecast_ms_restored = train_and_forecast_VAR(ms_df, steps=1).reset_index()
        forecast_ms_restored.rename(columns={'index': 'record_date'}, inplace=True)

        # 결과 출력 및 저장
        print("\nMarket Stable Forecast:")
        print(forecast_ms_restored)

        insert_forecast_to_mysql(connection, 'market_stable_predict', forecast_ms_restored)

    finally:
        if connection and connection.is_connected():
            connection.close()
            print("MySQL 연결이 닫혔습니다.")


if __name__ == "__main__":
    main()
