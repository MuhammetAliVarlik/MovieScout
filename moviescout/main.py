from flask import Flask, render_template, request, jsonify, session,Response
from flask_caching import Cache
from func.moviesRecommendationEngine import MovieRecommendationEngine
from func.moviesRAG import MovieRecommendationRAG
from config import Config
 # Assuming the class is in this file

# Initialize Flask app and cache
app = Flask(__name__)
app.config.from_object(Config)
cache = Cache(config={'CACHE_TYPE': 'simple'})  # Use simple in-memory cache for development
cache.init_app(app)

# Instantiate the recommendation system
movie_recommender = MovieRecommendationEngine()
movie_rag=None
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search_movies', methods=['POST'])
def search_movies():
    movie_name = request.form.get('movieName', '')
    filtered_df = movie_recommender.df[movie_recommender.df['title'].str.contains(movie_name, case=False, na=False)]
    result = filtered_df[['title', 'vote_average', 'vote_count', 'status', 'release_date', 'runtime', 'overview', 'poster_path', 'genres', 'backdrop_path']].to_dict(orient='records')
    return jsonify(result)

@app.route('/search_chat_movies', methods=['POST'])
def search_chat_movies():
    movie_name = request.form.get('movieName', '').strip()
    filtered_df = movie_recommender.df[movie_recommender.df['title'].str.strip().str.lower() == movie_name.lower()]
    result = filtered_df[['title', 'vote_average', 'vote_count', 'status', 'release_date', 'runtime', 'overview', 'poster_path', 'genres', 'backdrop_path']].to_dict(orient='records')
    return jsonify(result)

    

@app.route('/find_similar_movies', methods=['POST'])
def find_similar_movies():
    movie_list = request.form.getlist('movies[]')
    recommendations = movie_recommender.get_recommendations(movie_list)
    return jsonify({
        'status': 'success',
        'recommendations': recommendations,
        'total_similar_movies': len(recommendations)
    })

@app.route('/similar_movies')
def similar_movies():
    recommendations = session.get('recommendations', [])
    print(recommendations)
    return render_template('similar_movies.html', recommendations=recommendations)
@cache.cached(timeout=600)
@app.route('/movie_chat')
def movie_chat():
    global movie_rag
    movie_rag=MovieRecommendationRAG()
    return render_template('movie_chat.html')

@app.route('/chat_movies', methods=['POST'])
def chat_movies():
    movie_chat = request.form.get('movieChat')
    return Response(movie_rag.chat(movie_chat), mimetype='text/event-stream')

if __name__ == "__main__":
    app.run(debug=True)
