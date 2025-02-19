import mysql.connector
from mysql.connector import Error
import pandas as pd
from statsmodels.tsa.api import VAR

# -----------------------------
# MySQL 관련 함수
# -----------------------------

def connect_to_mysql():
    """MySQL 데이터베이스에 연결"""
    try:
        connection = mysql.connector.connect(
            host='5gears.iptime.org',
            user='root',
            password='andong1234',
            database='analysis'
        )
        if connection.is_connected():
            print("MySQL에 성공적으로 연결되었습니다.")
            return connection
    except Error as e:
        print(f"MySQL 연결 중 오류가 발생했습니다: {e}")
        return None


def fetch_data_from_mysql(connection, table_name):
    """MySQL에서 데이터를 가져와 DataFrame으로 반환"""
    try:
        cursor = connection.cursor()
        sql_query = f"SELECT * FROM {table_name};"
        cursor.execute(sql_query)
        records = cursor.fetchall()
        columns = [i[0] for i in cursor.description]
        df = pd.DataFrame(records, columns=columns)
        print(f"테이블 '{table_name}'에서 {cursor.rowcount}개의 행을 가져왔습니다.")
        return df
    except Error as e:
        print(f"MySQL에서 데이터를 가져오는 중 오류가 발생했습니다: {e}")
        return None


def insert_forecast_to_mysql(connection, table_name, forecast_data):
    """예측 데이터를 MySQL 테이블에 삽입 (중복 방지 및 dm_id 자동 처리)"""
    try:
        cursor = connection.cursor()

        # 열 이름 추출 및 백틱으로 감싸기 (dm_id 제외)
        columns = ', '.join([f'`{col}`' for col in forecast_data.columns if col != 'dm_id'])
        placeholders = ', '.join(['%s'] * len(forecast_data.columns))
        sql_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

        # 중복 확인 및 데이터 삽입
        for _, row in forecast_data.iterrows():
            check_query = f"SELECT COUNT(*) FROM {table_name} WHERE `record_month` = %s"
            cursor.execute(check_query, (row['record_month'],))
            count = cursor.fetchone()[0]

            if count > 0:
                print(f"테이블 '{table_name}'에 이미 날짜 {row['record_month']}가 존재합니다. 데이터를 추가하지 않습니다.")
                continue

            # dm_id를 제외한 데이터 삽입 실행
            row_data = tuple(row[col] for col in forecast_data.columns if col != 'dm_id')
            cursor.execute(sql_query, row_data)

        # 변경 사항 커밋
        connection.commit()
        print(f"테이블 '{table_name}'에 중복을 제외하고 {len(forecast_data)}개의 행이 추가되었습니다.")
    except Error as e:
        print(f"데이터 삽입 중 오류가 발생했습니다: {e}")
    finally:
        if connection.is_connected():
            cursor.close()


# -----------------------------
# 데이터 전처리 및 예측 함수
# -----------------------------

def preprocess_data(df):
    """데이터 전처리: 불필요한 열 제거, 결측값 처리 등"""
    df = df.drop(columns=['dm_id'])
    df['record_month'] = pd.to_datetime(df['record_month'])
    df.set_index('record_month', inplace=True)

    # 데이터 형 변환 및 결측값 처리
    for column in df.columns:
        df[column] = pd.to_numeric(df[column], errors='coerce')
    df = df.mask((df >= -0.1) & (df <= 0.1))  # -0.1 ~ 0.1 사이 값을 결측값으로 처리
    df = df.apply(lambda col: col.fillna(col.mean()))  # 결측값을 평균값으로 대체

    return df


def train_and_forecast_VAR(df, steps=1):
    """VAR 모델 학습 및 예측"""
    # 데이터 차분 (첫 번째 차분)
    df_diff = df.diff().dropna()

    # VAR 모델 생성 및 학습
    model = VAR(df_diff)
    model_fitted = model.fit(maxlags=15)

    # 예측 수행
    forecast_diff = model_fitted.forecast(y=df_diff.values[-model_fitted.k_ar:], steps=steps)

    # 예측 결과를 데이터프레임으로 변환 및 차분 복원
    forecast_df = pd.DataFrame(
        forecast_diff,
        index=[df.index[-1] + pd.DateOffset(months=i) for i in range(1, steps + 1)],
        columns=df.columns
    )
    forecast_restored = forecast_df + df.iloc[-1]

    return forecast_restored


# -----------------------------
# 메인 실행 흐름
# -----------------------------

def main():
    # MySQL 연결 생성
    connection = connect_to_mysql()
    
    if not connection:
        return

    try:
        # 데이터 가져오기
        car_data = fetch_data_from_mysql(connection, "dm_car_market")
        ram_data = fetch_data_from_mysql(connection, "dm_ram_market")

        if car_data is None or ram_data is None:
            return

        # 데이터 전처리
        car_df = preprocess_data(car_data)
        ram_df = preprocess_data(ram_data)

        # VAR 모델 학습 및 예측
        forecast_car_restored = train_and_forecast_VAR(car_df, steps=1).reset_index()
        forecast_car_restored.rename(columns={'index': 'record_month'}, inplace=True)

        forecast_ram_restored = train_and_forecast_VAR(ram_df, steps=1).reset_index()
        forecast_ram_restored.rename(columns={'index': 'record_month'}, inplace=True)

        # 결과 출력
        print("\nCAR Market Forecast:")
        print(forecast_car_restored)

        print("\nRAM Market Forecast:")
        print(forecast_ram_restored)

        # 예측 데이터를 데이터베이스에 삽입 (중복 방지)
        insert_forecast_to_mysql(connection, 'dm_car_predict', forecast_car_restored)
        insert_forecast_to_mysql(connection, 'dm_ram_predict', forecast_ram_restored)

    finally:
        if connection and connection.is_connected():
            connection.close()
            print("MySQL 연결이 닫혔습니다.")


if __name__ == "__main__":
    main()
