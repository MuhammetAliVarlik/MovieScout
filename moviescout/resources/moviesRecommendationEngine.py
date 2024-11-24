import os
import pickle
import pandas as pd
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from sklearn.metrics.pairwise import cosine_similarity
from flask import session

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

class MovieRecommendationEngine:
    def __init__(self,
                 csv_file_path=None, 
                 tfidf_file_path=None):

        # Set default paths relative to the current directory
        self.csv_file_path = csv_file_path or os.path.join(CURRENT_DIR,"..", "..", "data", "processed", "TMDB.csv")
        self.tfidf_file_path = tfidf_file_path or os.path.join(CURRENT_DIR,".." ,"..", "models", "content.pkl")

        self.db = None
        self.df = None
        self.tfidf_matrix = None
        self.llm = None
        self.chain = None
        
        self._load_csv()
        self._load_tfidf_matrix()
    
    def _load_csv(self):
        """Load the CSV file containing movie data"""
        self.df = pd.read_csv(self.csv_file_path)
        self.df['genres'] = self.df['genres'].fillna('')
        print("CSV file loaded.")
    
    def _load_tfidf_matrix(self):
        """Load the precomputed TF-IDF matrix"""
        with open(self.tfidf_file_path, 'rb') as file:
            self.tfidf_matrix = pickle.load(file)
        print("TF-IDF matrix loaded.")

    
    def get_recommendations(self, movie_list):
        """Get movie recommendations based on a list of selected movies"""
        if not movie_list:
            return {"error": "No movies selected"}

        user_history_indices = []
        for movie_name in movie_list:
            matched_rows = self.df[self.df['title'] == movie_name]
            if matched_rows.empty:
                return {"error": f"Movie '{movie_name}' not found in dataset"}
            user_history_indices.extend(matched_rows.index.tolist())
        
        if not user_history_indices:
            return {"error": "No valid movies selected from dataset"}

        user_profile = self.tfidf_matrix[user_history_indices].mean(axis=0)
        similarity_scores = cosine_similarity([user_profile], self.tfidf_matrix).flatten()
        
        self.df['similarity_score'] = similarity_scores
        recommended_movies = self.df[~self.df['title'].isin(movie_list)].sort_values(by='similarity_score', ascending=False)
        recommended_movies = recommended_movies.head(10)

        recommendations = recommended_movies[['title', 'vote_average', 'vote_count', 'status', 'release_date', 'runtime', 'overview', 'poster_path', 'genres', 'backdrop_path', 'similarity_score']].to_dict(orient='records')
        total_similar_movies = len(recommended_movies)
        session['recommendations'] = recommendations
        session['total_similar_movies'] = total_similar_movies
        return recommendations