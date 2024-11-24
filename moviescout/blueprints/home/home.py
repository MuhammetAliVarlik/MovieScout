from flask import Blueprint,render_template,request,jsonify
from resources import MovieRecommendationEngine

movie_recommender = MovieRecommendationEngine()

home_bp = Blueprint(
    'home_bp', __name__,
    template_folder='templates',
    static_folder='./static',
    static_url_path='/%s' % __name__
)

@home_bp.route('/')
def home():
    return render_template('index.html')

@home_bp.route('/find_similar_movies', methods=['POST'])
def find_similar_movies():
    movie_list = request.form.getlist('movies[]')
    recommendations = movie_recommender.get_recommendations(movie_list)
    return jsonify({
        'status': 'success',
        'recommendations': recommendations,
        'total_similar_movies': len(recommendations)
    })