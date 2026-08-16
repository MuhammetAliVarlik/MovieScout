# 🎬 MovieScout - Movie Finder and Recommender

<a target="_blank" href="https://cookiecutter-data-science.drivendata.org/">
    <img src="https://img.shields.io/badge/CCDS-Project%20template-328F97?logo=cookiecutter" />
</a>
<a target="_blank" href="https://developer.mozilla.org/en-US/docs/Web/HTML">
    <img src="https://img.shields.io/badge/HTML5-E34F26?logo=html5&logoColor=white" />
</a>
<a target="_blank" href="https://www.w3.org/Style/CSS/">
    <img src="https://img.shields.io/badge/CSS3-1572B6?logo=css3&logoColor=white" />
</a>
<a target="_blank" href="https://developer.mozilla.org/en-US/docs/Web/JavaScript">
    <img src="https://img.shields.io/badge/JavaScript-F7DF1E?logo=javascript&logoColor=black" />
</a>
<a target="_blank" href="https://getbootstrap.com/">
    <img src="https://img.shields.io/badge/Bootstrap-7952B3?logo=bootstrap&logoColor=white" />
</a>
<a target="_blank" href="https://flask.palletsprojects.com/">
    <img src="https://img.shields.io/badge/Flask-000000?logo=flask&logoColor=white" />
</a>
<a target="_blank" href="https://www.themoviedb.org/documentation/api">
    <img src="https://img.shields.io/badge/TMDB-00B5E2?logo=themoviedb&logoColor=white" />
</a>
<a target="_blank" href="https://ollama.com">
    <img src="https://img.shields.io/badge/Ollama-000000?logo=ollama&logoColor=white" />
</a>

--
A web application that helps you find and explore movies based on your interests. By leveraging the TMDB dataset and semantic search, MovieScout lets you search for films, swipe through recommendations, import your Letterboxd ratings history, and chat with a local LLM for personalized suggestions.

---

## 🚀 Features

- **Search Movies**: Search for movies using the built-in TMDB dataset through an intuitive search input on the homepage.
- **Swipe to Discover**: A swipe interface to like/dislike movies and build up your favorites.
- **Semantic Search & Recommendations**: Find similar movies using a ChromaDB-backed embedding search.
- **Import your Letterboxd ratings**: Upload a Letterboxd export `.zip` (or a bare `ratings.csv`) at `/api/import` — MovieScout parses your ratings, enriches them against the local TMDB dataset, and excludes films you've already watched from future recommendations.
- **LLM Chat**: Ask a local LLM (via [Ollama](https://ollama.com)) for personalized recommendations, aware of your imported taste profile.
- **Responsive Design**: Optimized for both desktop and mobile viewing.

---

## 🧑‍💻 Technologies Used

### Frontend
HTML5, CSS3, JavaScript, Bootstrap 5.

### Backend
Flask, ChromaDB (semantic search), Sentence-Transformers (embeddings), Ollama (local LLM chat).

### Dataset
[TMDB Movies Dataset (asaniczka, Kaggle)](https://www.kaggle.com/datasets/asaniczka/tmdb-movies-dataset-2023-930k-movies) — a processed subset ships with this repo, so no separate download is needed for search/discover/recommendations/Letterboxd import.

---

## 📸 Media

### Homepage:

![Alt text](docs/demo/home.png?raw=true "Home")

### Movie Details:

![Alt text](docs/demo/movie_details.png?raw=true "Movie Details")

### Similar Movies:

![Alt text](docs/demo/similar_movies.png?raw=true "Similar Movies")

### Movies Chat:

![Alt text](docs/demo/movies_chat.png?raw=true "Movies Chat")

## 📦 Installation

To run the project locally:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/MuhammetAliVarlik/MovieScout.git
   cd MovieScout
   ```
2. **Install dependencies** (Python 3.10+):
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure environment variables**:
   ```bash
   cp .env.example .env
   ```
   The defaults work out of the box — `TMDB_API_KEY` is optional (only used to enrich Letterboxd imports for films missing from the local dataset).
4. **Run the app**:
   ```bash
   python run.py
   ```
   Visit `http://localhost:5000`. Search, discover, recommendations, and Letterboxd import all work immediately — the processed TMDB dataset ships in the repo, and the ChromaDB index is built automatically on first request.

### Optional: enable LLM chat

The `/chat` page needs a local LLM served by [Ollama](https://ollama.com). Every other feature works without it.

```bash
# Install Ollama from https://ollama.com, then:
ollama pull llama3.2:3b
```

Ollama typically starts its server automatically; if not, run `ollama serve`. Without it, `/chat` still loads and shows a clear inline message explaining what to do instead of failing.

## 🔒 Security notes

This is a portfolio/demo project. There are no user accounts, and the only state-changing endpoints (search, recommendations, Letterboxd import) are same-origin form/file submissions with no destructive cross-site action, so CSRF/CORS middleware was intentionally left out to keep the app simple. Treat it accordingly if you extend it toward a multi-user deployment.

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests to improve this project.

Enjoy exploring movies with MovieScout! 🍿
