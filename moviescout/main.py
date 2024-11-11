from flask import Flask, render_template, request, jsonify,url_for,session
import pandas as pd
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from config import Config

base_dir = os.path.abspath(os.path.dirname(__file__))    
df = pd.read_csv(os.path.join(base_dir, "../data/processed/TMDB.csv"))
df['genres'] = df['genres'].fillna('')

app = Flask(__name__)
app.config.from_object(Config)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search_movies', methods=['POST'])
def search_movies():
    movie_name = request.form.get('movieName', '')  # Get the movie name from the form
    
    # Filter the DataFrame to match the search query (case-insensitive)
    filtered_df = df[df['title'].str.contains(movie_name, case=False, na=False)]
    
    # Create a list of dictionaries containing both 'title' and 'poster_url'
    result = filtered_df[['title', 'poster_path']].to_dict(orient='records')
    
    # Return the list as a JSON response
    return jsonify(result) # Converting to JSON for a proper response format

@app.route('/find_similar_movies', methods=['POST'])
def find_similar_movies():
    # Retrieve list of selected movie titles from the POST request
    movie_list = request.form.getlist('movies[]')
    
    if not movie_list:
        return jsonify({"error": "No movies selected"}), 400

    # Find row indices for movies in the DataFrame that match the selected titles
    user_history_indices = []
    for movie_name in movie_list:
        matched_rows = df[df['title'].str.contains(movie_name, case=False, na=False)]
        user_history_indices.extend(matched_rows.index.tolist())  # Use indices, not IDs

    if not user_history_indices:
        return jsonify({"error": "Selected movies not found in dataset"}), 400

    # Process genres column for TF-IDF
    tfidf_vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf_vectorizer.fit_transform(df['genres'])

    # Calculate the user profile by averaging the genre vectors of selected movies
    user_profile = np.mean(tfidf_matrix[user_history_indices].toarray(), axis=0)

    # Calculate similarity scores between user profile and all movie vectors
    similarity_scores = cosine_similarity([user_profile], tfidf_matrix).flatten()

    # Append similarity scores to the DataFrame and sort by similarity
    df['similarity_score'] = similarity_scores
    recommended_movies = df.sort_values(by='similarity_score', ascending=False).head(10)

    # Shuffle the DataFrame
    recommended_movies = recommended_movies.sample(frac=1).reset_index(drop=True)

    # Convert to JSON response with relevant columns
    response = recommended_movies.to_dict(orient='records')
    
    recommendations = recommended_movies[['title','vote_average','vote_count','status','release_date','runtime','overview','poster_path', 'genres','backdrop_path', 'similarity_score']].to_dict(orient='records')

    # Store the recommendations in the session for the next page
    session['recommendations'] = recommendations

    # Return a success response (will be handled by AJAX for redirect)
    return jsonify({'status': 'success'})

@app.route('/similar_movies')
def similar_movies():
    # Fetch recommendations from the session
    recommendations = session.get('recommendations', [])
    
    # Render the page with recommendations
    return render_template('similar_movies.html', recommendations=recommendations)

if __name__ =="__main__":
    app.run(debug =True)