from flask import Flask, render_template, request, jsonify
import pandas as pd
import os

base_dir = os.path.abspath(os.path.dirname(__file__))    
df = pd.read_csv(os.path.join(base_dir, "../data/processed/TMDB.csv"))
app = Flask(__name__)

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

@app.route('/find_similar_movies',methods=['POST'])
def find_similar_movies():
    movie_list=request.get("movie_list","")
    return render_template('similar_movies.html')

if __name__ =="__main__":
    app.run(debug =True)