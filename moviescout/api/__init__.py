from flask import Blueprint

# 'api' Blueprint'ini oluştur
api_blueprint = Blueprint('api', __name__)

# Blueprint'e view'ları dahil et
from . import views