from tensorflow.keras.preprocessing import image
import numpy as np
import tensorflow as tf

# 모델 로드
model = tf.keras.models.load_model('pipe.keras')

# 이미지 로드 및 전처리
def load_and_preprocess_image(img_path):
    img = image.load_img(img_path, target_size=(150, 150))  # 모델에 맞는 입력 크기
    img_array = image.img_to_array(img)  # 이미지를 배열로 변환
    img_array = np.expand_dims(img_array, axis=0)  # 배치를 추가 (모델은 배치 형태를 요구)
    img_array = img_array / 255.0  # 스케일 조정 (0~1로)
    return img_array

# 테스트 이미지 경로
img_path = 'C:/Users/Admin/Desktop/data/resized/학습/정상.PNG'

# 이미지 처리
preprocessed_img = load_and_preprocess_image(img_path)

# 예측
prediction = model.predict(preprocessed_img)

# 결과 출력
if prediction[0] > 0.5:
    print(f"The image is predicted to be a acceptance with confidence: {prediction[0][0]:.2f}")
else:
    print(f"The image is predicted to be a defective with confidence: {1 - prediction[0][0]:.2f}")