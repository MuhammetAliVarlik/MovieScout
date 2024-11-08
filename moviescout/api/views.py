from flask import jsonify
from . import api_blueprint

# /api/hello URL'ine gelen GET isteğine cevap verir
@api_blueprint.route('/hello', methods=['GET'])
def hello():
    return jsonify(message="Hello, World!")  # JSON formatında bir mesaj döner