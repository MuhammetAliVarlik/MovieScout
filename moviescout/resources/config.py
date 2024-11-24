# config.py
import secrets
from flask_caching import Cache

 

class Config:
    # Güvenli, rastgele bir secret_key oluşturun
    SECRET_KEY = secrets.token_hex(16)  # 16 baytlık rastgele bir anahtar
    cache = Cache(config={'CACHE_TYPE': 'simple'})