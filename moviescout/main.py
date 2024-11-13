from flask import Flask, render_template, request, jsonify,url_for,session
import pandas as pd
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from config import Config
import pickle

# Base directory tanımlaması
base_dir = os.path.abspath(os.path.dirname(__file__))    
print(base_dir)

# CSV dosyasını okuma
csv_path = os.path.join(base_dir, "..", "data", "processed", "TMDB.csv")
df = pd.read_csv(csv_path)
df['genres'] = df['genres'].fillna('')

# TF-IDF matrisini yükleme
tfidf_path = os.path.join(base_dir, "../models", "content.pkl")
with open(tfidf_path, 'rb') as file:
    tfidf_matrix = pickle.load(file)

print("TF-IDF matrisi yüklendi.")

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

from flask import session, jsonify, request
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

@app.route('/find_similar_movies', methods=['POST'])
def find_similar_movies():
    # Kullanıcıdan gelen seçilen film başlıklarını alıyoruz
    movie_list = request.form.getlist('movies[]')
    if not movie_list:
        return jsonify({"error": "No movies selected"}), 400

    # Seçilen filmleri DataFrame'den bulup indekslerini alıyoruz
    user_history_indices = []
    for movie_name in movie_list:
        # Tam eşleşen film başlıklarını buluyoruz
        matched_rows = df[df['title']==movie_name]
        
        if matched_rows.empty:
            return jsonify({"error": f"Movie '{movie_name}' not found in dataset"}), 400
        
        user_history_indices.extend(matched_rows.index.tolist())  # İndeksleri alıyoruz

    if not user_history_indices:
        return jsonify({"error": "No valid movies selected from dataset"}), 400

    # Kullanıcı profilini, seçilen filmlerin tür vektörlerinin ortalaması olarak hesaplıyoruz
    user_profile = np.mean(tfidf_matrix[user_history_indices], axis=0)

    # Kullanıcı profili ile tüm filmler arasındaki benzerlik puanlarını hesaplıyoruz
    similarity_scores = cosine_similarity([user_profile], tfidf_matrix).flatten()

    # Benzerlik puanlarını DataFrame'e ekliyoruz ve benzerliğe göre sıralıyoruz
    df['similarity_score'] = similarity_scores

    # Seçilen filmleri önerilenler listesinden çıkarıyoruz
    recommended_movies = df[~df['title'].isin(movie_list)]

    # Önerilen filmleri benzerlik puanına göre sıralıyoruz
    recommended_movies = recommended_movies.sort_values(by='similarity_score', ascending=False)

    # İlk 10 önerilen filmi alıyoruz (ilk film zaten kullanıcı tarafından seçilen filmler)
    recommended_movies = recommended_movies.head(10)

    # Önerilen filmleri JSON formatına çeviriyoruz
    recommendations = recommended_movies[['title','vote_average','vote_count','status','release_date','runtime','overview','poster_path', 'genres','backdrop_path', 'similarity_score']].to_dict(orient='records')

    # Önerilen film sayısını hesaplıyoruz
    total_similar_movies = len(recommended_movies)

    # Önerileri ve benzer film sayısını session'a kaydediyoruz
    session['recommendations'] = recommendations
    session['total_similar_movies'] = total_similar_movies

    # Başarı durumu döndürüyoruz
    return jsonify({
        'status': 'success',
        'recommendations': recommendations,
        'total_similar_movies': total_similar_movies
    })




@app.route('/similar_movies')
def similar_movies():
    # Fetch recommendations from the session
    recommendations = session.get('recommendations', [])
    
    # Render the page with recommendations
    return render_template('similar_movies.html', recommendations=recommendations)

if __name__ =="__main__":
    app.run(debug =True)