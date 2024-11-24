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
<a target="_blank" href="https://sass-lang.com/">
    <img src="https://img.shields.io/badge/SCSS-CC6699?logo=sass&logoColor=white" />
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
<a target="_blank" href="https://www.langchain.com/">
    <img src="https://img.shields.io/badge/Langchain-1B1D29?logo=langchain&logoColor=white" />
</a>

--
A modern web application that helps you find and explore movies based on your interests. By leveraging the TMDB dataset and semantic search, this app allows you to swipe through movie recommendations and store your favorites locally. Additionally, the app utilizes a custom-built large language model (LLM) for personalized film suggestions.

---

## 🚀 Features

- **Search Movies**: Search for movies using the TMDB dataset through an intuitive search input on the homepage.
- **Swipe to Like**: A swipe interface to like/dislike movies and store favorites in local storage.
- **Semantic Search**: Find similar movies using semantic search for a more personalized recommendation experience.
- **Personalized Recommendations**: Receive additional movie suggestions via a recommender system built with a custom LLM and retrieval-augmented generation (RAG).
- **Responsive Design**: Optimized for both desktop and mobile viewing.

---

## 🧑‍💻 Technologies Used

This project utilizes a range of modern web technologies for both the frontend and backend. Below are the key technologies and their roles in the application:

### Frontend

<p>
  <strong>HTML5</strong>: The foundation of the project, used to structure the web pages and define semantic content.
</p>

<p>
  <strong>CSS3</strong>: Used for styling the pages with custom layouts, colors, and visual effects.
</p>

<p>
  <strong>SCSS</strong>: CSS preprocessor used for writing more maintainable and reusable styles.
</p>

<p>
  <strong>JavaScript</strong>: Handles dynamic functionality, including movie search, semantic search, and swipe actions.
</p>

<p>
  <strong>Bootstrap 5</strong>: A CSS framework used for responsive design and quick UI development, making the app mobile-friendly.
</p>

### Backend

<p>
  
  <strong>Flask</strong>: A lightweight Python web framework used to serve the application and manage backend logic.
</p>

### Datasets & Libraries

<p>
  <strong>TMDB Dataset</strong>: Provides access to a vast database of movies, which is used to fetch movie data (e.g., titles, descriptions, images). 
  <a href="https://www.kaggle.com/datasets/asaniczka/tmdb-movies-dataset-2023-930k-movies">Full TMDB Movies Dataset 2024 (1M Movies) ~ asaniczka</a>
</p>

<p>
  <strong>Langchain</strong>: A library used for building advanced language model-powered systems. In this project, it is used to generate personalized movie recommendations with retrieval-augmented generation (RAG).
</p>

---

📸 Media

Here are some screenshots to give you a glimpse of the app's interface:

Homepage:

![Alt text](docs/demo/home.png?raw=true "Home")
![Alt text](docs/demo/movie_details.png?raw=true "Movie Details")

Similar Movies:
![Alt text](docs/demo/similar_movies.png?raw=true "Similar Movies")

Movies Chat:
![Alt text](docs/demo/movies_chat.png?raw=true "Movies Chat")

## 📦 Installation

To run the project locally, follow these steps:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/username/moviescout.git
   cd moviescout
   ```
