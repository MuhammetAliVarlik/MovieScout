from flask import Blueprint,render_template,session
from resources import MovieRecommendationEngine

movie_recommender = MovieRecommendationEngine()

similar_movies_bp = Blueprint(
    'similar_movies_bp', __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/%s' % __name__
)

@similar_movies_bp.route('/similar_movies')
def similar_movies():
    recommendations = session.get('recommendations', [])
    return render_template('similar_movies.html', recommendations=recommendations)