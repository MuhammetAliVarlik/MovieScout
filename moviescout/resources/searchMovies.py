class MovieSearchService:
    def __init__(self, movie_recommender):
        self.movie_recommender = movie_recommender

    def search_movies(self, movie_name):
        """Search for movies containing the given name."""
        filtered_df = self.movie_recommender.df[self.movie_recommender.df['title'].str.contains(movie_name, case=False, na=False)]
        result = filtered_df[['title', 'vote_average', 'vote_count', 'status', 'release_date', 'runtime', 'overview', 'poster_path', 'genres', 'backdrop_path']].to_dict(orient='records')
        return result

    def search_chat_movies(self, movie_name):
        """Search for movies matching the exact given name."""
        movie_name = movie_name.strip()
        filtered_df = self.movie_recommender.df[self.movie_recommender.df['title'].str.strip().str.lower() == movie_name.lower()]
        result = filtered_df[['title', 'vote_average', 'vote_count', 'status', 'release_date', 'runtime', 'overview', 'poster_path', 'genres', 'backdrop_path']].to_dict(orient='records')
        return result