import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import streamlit as st

# 한글 폰트 설정
plt.rc("font", family="Malgun Gothic")


# 1. CSV 파일 경로 설정
data_dir = "C:/Users/Admin/Desktop/1month"  # CSV 파일들이 저장된 폴더 경로
csv_files = [os.path.join(data_dir, file) for file in os.listdir(data_dir) if file.endswith(".csv")]

# 2. 데이터 통합
dataframes = []
for file in csv_files:
    # 파일명에서 날짜 추출
    file_name = os.path.basename(file)  # 파일명만 추출
    date_str = file_name.split("kemp-abh-sensor-")[-1].split(".csv")[0]
    date = pd.to_datetime(date_str, format="%Y.%m.%d")
    df = pd.read_csv(file)
    df['Date'] = date  # 데이터프레임에 날짜 추가
    dataframes.append(df)

# 모든 데이터 합치기
df = pd.concat(dataframes, ignore_index=True)

# 3. 품질 기준 설정 (K-means로 중심점 계산)ㄴ
from sklearn.cluster import KMeans

X = df[['Temp', 'Voltage']].values
kmeans = KMeans(n_clusters=1, random_state=42)
kmeans.fit(X)

# 목표값 (중심점)
TEMP_TARGET = kmeans.cluster_centers_[0][0]
VOLTAGE_TARGET = kmeans.cluster_centers_[0][1]

# 오차 범위 (2시그마 기준)
temp_std = df['Temp'].std()
voltage_std = df['Voltage'].std()
ERROR_MARGIN_TEMP = 2 * temp_std
ERROR_MARGIN_VOLTAGE = 2 * voltage_std

# 4. 양품/불량품 분류
df['quality'] = np.where(
    (abs(df['Temp'] - TEMP_TARGET) <= ERROR_MARGIN_TEMP) &
    (abs(df['Voltage'] - VOLTAGE_TARGET) <= ERROR_MARGIN_VOLTAGE),
    '양품', '불량품'
)

# 5. 날짜별 분석
daily_summary = df.groupby(['Date', 'quality']).size().unstack(fill_value=0)

# 6. 주간 및 월간 분석
df['Week'] = df['Date'].dt.to_period('W').apply(lambda r: r.start_time)  # 주 시작일 
df['Month'] = df['Date'].dt.to_period('M').apply(lambda r: r.start_time)  # 월 시작일

weekly_summary = df.groupby(['Week', 'quality']).size().unstack(fill_value=0)
monthly_summary = df.groupby(['Month', 'quality']).size().unstack(fill_value=0)

# 날짜 포맷 함수 정의
def format_date(x):
    return x.strftime('%m/%d')

def format_week(x):
    return x.strftime('%m/%d')

def format_month(x):
    return x.strftime('%Y-%m')

# 7. 시각화
plt.figure(figsize=(15, 10))

# (1) 일간 분석
plt.subplot(3, 1, 1)
daily_summary.plot(kind='bar', stacked=False, ax=plt.gca(), width=0.8)
plt.title("일간 양품 및 불량품 분포")
plt.ylabel("개수")
plt.xlabel("날짜")
plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format_date(daily_summary.index[int(x)])))
plt.xticks(rotation=45)

# (2) 주간 분석
plt.subplot(3, 1, 2)
weekly_summary.plot(kind='bar', stacked=False, ax=plt.gca(), width=0.8)
plt.title("주간 양품 및 불량품 분포")
plt.ylabel("개수")
plt.xlabel("주 시작일")
plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format_week(weekly_summary.index[int(x)])))
plt.xticks(rotation=45)

# (3) 월간 분석
plt.subplot(3, 1, 3)
monthly_summary.plot(kind='bar', stacked=False, ax=plt.gca(), width=0.8)
plt.title("월간 양품 및 불량품 분포")
plt.ylabel("개수")
plt.xlabel("월 시작일")
plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format_month(monthly_summary.index[int(x)])))
plt.xticks(rotation=45)

plt.tight_layout()
plt.show()

# 데이터 확인을 위한 출력
print("\n일간 데이터:")
print(daily_summary)
print("\n주간 데이터:")
print(weekly_summary)
print("\n월간 데이터:")
print(monthly_summary)

