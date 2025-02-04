import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNet
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, GlobalAveragePooling2D
from tensorflow.keras.optimizers import Adam

# 데이터 경로 설정
train_dir = 'C:/Users/Admin/Desktop/data/resized/학습'
validation_dir = 'C:/Users/Admin/Desktop/data/resized/테스트'


# 데이터 전처리
train_datagen = ImageDataGenerator(
    rescale=1.0/255,           
    rotation_range=40,
    width_shift_range=0.2,          
    height_shift_range=0.2,    
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True
)

validation_datagen = ImageDataGenerator(rescale=1.0/255)

train_generator = train_datagen.flow_from_directory(
    train_dir,
    target_size=(150, 150),
    batch_size=32,
    class_mode='binary'
)

# print(f'[데이터 정보] 학습 데이터 클래스: {train_generator.class_indices}')
# print(f'[데이터 정보] 학습 데이터 샘플 수: {train_generator.samples}')


validation_generator = validation_datagen.flow_from_directory(
    validation_dir,
    target_size=(150, 150),
    batch_size=32,
    class_mode='binary'
)

# print(f'[데이터 정보] 검증 데이터 샘플 수: {validation_generator.samples}')

# MobileNet 모델 로드 (사전 학습된 가중치 사용)
base_model = MobileNet(weights='imagenet', include_top=False, input_shape=(150, 150, 3))

# 사전 학습된 레이어 고정 (옵션)
base_model.trainable = False  # 학습 가능하게 하려면 True로 설정

# 모델 구축
model = Sequential([
    base_model,
    GlobalAveragePooling2D(),  # GlobalAveragePooling은 Flatten과 비슷하지만 더 효율적
    Dense(512, activation='relu'),
    Dropout(0.5),
    Dense(1, activation='sigmoid')  # 이진 분류이므로 sigmoid 활성화 함수 사용
])

# 모델 컴파일
model.compile(
    loss='binary_crossentropy',
    optimizer=Adam(learning_rate=0.001),
    metrics=['accuracy']
)

# 모델 학습
history = model.fit(
    train_generator,
    epochs=20,
    validation_data=validation_generator
)

# 모델 저장
model.save('pipe.keras')