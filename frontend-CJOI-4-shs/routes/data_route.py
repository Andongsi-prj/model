from flask import Blueprint, jsonify, request
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from io import BytesIO
import base64



data_route = Blueprint('data', __name__)

plt.rc("font", family="Malgun Gothic")

# 데이터 로드
@data_route.route('/data', methods=['GET'])
def get_data():
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
    ERROR_MARGIN_TEMP = 2 * temp_std
    ERROR_MARGIN_VOLTAGE = 2 * voltage_std
    
    # 양품/불량품 분류
    df['quality'] = np.where(
        (abs(df['Temp'] - TEMP_TARGET) <= ERROR_MARGIN_TEMP) & 
        (abs(df['Voltage'] - VOLTAGE_TARGET) <= ERROR_MARGIN_VOLTAGE),
        '양품', '불량품'
    )
    
    # 양품/불량품 개수 계산
    quality_counts = df['quality'].value_counts()
    
    #  파이차트 생성
    plt.figure(figsize=(8, 8))
    labels = ['양품', '불량품']
    
    plt.pie(quality_counts, 
            labels=labels,
            autopct='%1.1f%%',
            colors=['#4caf50', '#f44336'],
            textprops={'fontsize': 16},
            counterclock=False,
            startangle=130 
            )
    
    plt.title('품질 분포 차트', fontsize=20)
    plt.legend(loc='upper right', fontsize=12)

    # 차트를 이미지로 변환
    img = BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    chart_data = base64.b64encode(img.getvalue()).decode("utf-8")   # 이미지를 base64로 인코딩    
    plt.close()
    
    return jsonify({
        'chart': chart_data,
        'total': int(len(df)),
        'normal': int(quality_counts['양품']),
        'defect': int(quality_counts['불량품'])
    })






