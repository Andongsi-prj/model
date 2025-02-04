import requests
from flask import Blueprint, request, jsonify

pipe_route = Blueprint('pipe', __name__)
FASTAPI_URL = "http://192.168.0.163:8000/predict/"

@pipe_route.route("/", methods=['POST'])
def predict():
    try:
        # Base64 데이터 수신
        image_data = request.json.get('image_base64')
        if not image_data:
            return jsonify({"error": "'image_base64' field missing"}), 400

        # FastAPI 서버로 전달
        response = requests.post(FASTAPI_URL, json={"image_base64": image_data})
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500
