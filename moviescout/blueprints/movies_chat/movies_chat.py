from flask import Blueprint,request,jsonify,Response,render_template
from resources import MovieRecommendationEngine,MovieSearchService,MovieRecommendationRAG,Config

cache = Config.cache
movie_recommender = MovieRecommendationEngine()
movie_recommender_service = MovieSearchService(movie_recommender)
movie_rag=None

movie_chat_bp = Blueprint(
    'movie_chat_bp', __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/%s' % __name__
)

@movie_chat_bp.route('/search_movies', methods=['POST'])
def search_movies():
    movie_name = request.form.get('movieName', '')
    result = movie_recommender_service.search_movies(movie_name)
    return jsonify(result)

@movie_chat_bp.route('/search_chat_movies', methods=['POST'])
def search_chat_movies():
    movie_name = request.form.get('movieName', '')
    result = movie_recommender_service.search_chat_movies(movie_name)
    return jsonify(result)

@cache.cached(timeout=600)
@movie_chat_bp.route('/movie_chat')
def movie_chat():
    global movie_rag
    movie_rag=MovieRecommendationRAG()
    return render_template('movie_chat.html')

@movie_chat_bp.route('/chat_movies', methods=['POST'])
def chat_movies():
    movie_chat = request.form.get('movieChat')
    return Response(movie_rag.chat(movie_chat), mimetype='text/event-stream')