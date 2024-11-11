# config.py
import secrets

class Config:
    # Güvenli, rastgele bir secret_key oluşturun
    SECRET_KEY = secrets.token_hex(16)  # 16 baytlık rastgele bir anahtar