import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans

# 한글 폰트 설정
plt.rc("font", family="Malgun Gothic")

# 데이터 로드
data_path = "C:/Users/Admin/Desktop/data/kemp-abh-sensor-2021.09.06.csv"
df = pd.read_csv(data_path)

# 데이터 준비
X = df[['Temp', 'Voltage']].values

# K-means 클러스터링으로 중심점 찾기
kmeans = KMeans(n_clusters=1, random_state=42)
kmeans.fit(X)

# 중심점 (목표값) 설정
TEMP_TARGET = kmeans.cluster_centers_[0][0]
VOLTAGE_TARGET = kmeans.cluster_centers_[0][1]

# 표준편차를 이용한 오차 범위 설정
temp_std = df['Temp'].std()
voltage_std = df['Voltage'].std()
ERROR_MARGIN_TEMP = 2 * temp_std  # 2시그마 (약 95% 신뢰구간)
ERROR_MARGIN_VOLTAGE = 2 * voltage_std

print(f"\n계산된 목표값:")
print(f"온도 목표값: {TEMP_TARGET:.2f}°C (오차범위: ±{ERROR_MARGIN_TEMP:.2f})")
print(f"전압 목표값: {VOLTAGE_TARGET:.2f}V (오차범위: ±{ERROR_MARGIN_VOLTAGE:.2f})")

# 양품/불량품 분류
df['quality'] = np.where(
    (abs(df['Temp'] - TEMP_TARGET) <= ERROR_MARGIN_TEMP) & 
    (abs(df['Voltage'] - VOLTAGE_TARGET) <= ERROR_MARGIN_VOLTAGE),
    '양품', '불량품'
)

# 양품/불량품 개수 계산
quality_counts = df['quality'].value_counts()
print("\n품질 분류 결과:")
print(quality_counts)
print("\n비율:")
print(quality_counts / len(df) * 100, "%")

# 시각화
plt.figure(figsize=(15, 5))

# 산점도 그리기
plt.subplot(1, 2, 1)  
colors = {'양품': 'green', '불량품': 'red'}
for quality in ['양품', '불량품']:
    mask = df['quality'] == quality
    plt.scatter(df[mask]['Temp'], df[mask]['Voltage'], 
               c=colors[quality], label=quality, alpha=0.6)

# 기준 영역 표시
plt.axvline(x=TEMP_TARGET, color='gray', linestyle='--', alpha=0.5)
plt.axhline(y=VOLTAGE_TARGET, color='gray', linestyle='--', alpha=0.5)
plt.axvspan(TEMP_TARGET-ERROR_MARGIN_TEMP, TEMP_TARGET+ERROR_MARGIN_TEMP, 
           alpha=0.2, color='gray')
plt.axhspan(VOLTAGE_TARGET-ERROR_MARGIN_VOLTAGE, VOLTAGE_TARGET+ERROR_MARGIN_VOLTAGE, 
           alpha=0.2, color='gray')

plt.xlabel('온도 (°C)')
plt.ylabel('전압 (V)')
plt.title('온도 vs 전압 (품질)')
plt.legend()
plt.grid(True, alpha=0.3)


# 파이 차트
plt.subplot(1, 2, 2)

# 라벨에 개수 정보 추가
labels = [f'양품\n({quality_counts["양품"]:,}개)', 
          f'불량품\n({quality_counts["불량품"]:,}개)']

plt.pie(quality_counts, 
        labels=labels,
        autopct='%1.1f%%',
        colors=['green', 'red'])
plt.title('품질 분포')


# 상세 통계 정보
print("\n상세 통계 정보:")
total_count = len(df)
print(f"총 생산개수: {total_count:,}")
print(f"양품 개수: {quality_counts['양품']:,}")
print(f"불량품 개수: {quality_counts['불량품']:,}")

plt.tight_layout()
plt.show()