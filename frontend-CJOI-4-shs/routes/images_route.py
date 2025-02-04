import os
import base64
import random
from flask import Blueprint, jsonify

images_route = Blueprint('images_route', __name__)

@images_route.route("/")
def get_images():
    image_folder = 'frontend-CJOI-4-shs/static/image/test'
    image_data = []

    for filename in os.listdir(image_folder):
        if filename.lower().endswith('.png'):
            filepath = os.path.join(image_folder, filename)
            with open(filepath, "rb") as image_file:
                encoded = base64.b64encode(image_file.read()).decode('utf-8')
                image_data.append(f"data:image/png;base64,{encoded}")

    # 랜덤으로 이미지 섞기
    random.shuffle(image_data)
    return jsonify(image_data)
