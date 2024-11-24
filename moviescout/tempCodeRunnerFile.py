from flask import Flask
from resources import Config
from blueprints import home_bp,similar_movies_bp,movie_chat_bp

app = Flask(__name__)
app.config.from_object(Config)

app.register_blueprint(home_bp)
app.register_blueprint(similar_movies_bp)
app.register_blueprint(movie_chat_bp)

if __name__ == '__main__':
    app.run(debug=True)