## Project Organization

```
├── LICENSE            <- Open-source license if one is chosen
├── Makefile           <- Makefile with convenience commands like `make data` or `make train`
├── README.md          <- The top-level README for developers using this project. It usually contains project description, setup instructions, and usage.
├── data               <- Directory for handling all data files
│   ├── external       <- Data from third party sources (e.g., raw datasets, APIs)
│   ├── interim        <- Intermediate data that has been processed or transformed but is not final yet
│   ├── processed      <- The final, canonical data sets for modeling (cleaned and ready for use)
│   └── raw            <- The original, immutable data dump (data as received, unmodified)
│
├── docs               <- A default mkdocs project; documentation for project setup and usage, can be built into HTML for easy access
│
├── models             <- Directory containing trained models and model-related data
│   └── serialized     <- Trained and serialized models, model predictions, or model summaries
│
├── notebooks          <- Jupyter notebooks for data exploration, model testing, etc.
│                         Naming convention is a number (for ordering), the creator's initials, and a short `-` delimited description, e.g.
│                         `1.0-jqp-initial-data-exploration` for the first notebook by JQP that explores the data.
│
├── pyproject.toml     <- Project configuration file with package metadata for 'moviescout' and configuration for tools like `black` (Python code formatter)
│
├── references         <- Contains data dictionaries, manuals, and other explanatory materials
│   └── documentation  <- Any additional documentation or reference materials needed for understanding the project
│
├── reports            <- Generated reports from analysis (e.g., HTML, PDF, LaTeX)
│   └── figures        <- Directory for storing generated graphics and figures to be used in reporting or documentation
│
├── requirements.txt   <- The requirements file for reproducing the analysis environment, typically generated using `pip freeze > requirements.txt`
│
├── setup.cfg          <- Configuration file for tools like flake8 (for code style checks)
│
└── moviescout         <- Source code for use in this project; the main package directory
    │
    ├── __init__.py             <- Makes 'moviescout' a Python package
    │
    ├── run.py                 <- Stores useful variables and configuration (e.g., paths, setup parameters, etc.)
    │
    └── blueprints             <- Contains the blueprints for the web application (if using a framework like Flask)
        │
        ├── __init__.py         <- Makes the 'blueprints' directory a package
        │
        ├── blueprints          <- Main directory for defining application views or routes
        │   │
        │   ├── home            <- Home page blueprints
        │   │   │
        │   │   ├── static      <- Static assets (images, JS, CSS) related to the home page
        │   │   ├── templates   <- HTML templates for the home page
        │   │   └── home.py      <- Python file defining the route and logic for the home page
        │   │
        │   ├── movies_chat     <- Blueprint for the movie chat feature (e.g., chat interface for movie suggestions)
        │   │   │
        │   │   ├── static      <- Static assets (images, JS, CSS) related to movies chat
        │   │   ├── templates   <- HTML templates for movies chat
        │   │   └── movies_chat.py  <- Python file defining the route and logic for the movies chat
        │   │
        │   └── similar_movies  <- Blueprint for the similar movie recommendation feature
        │       │
        │       ├── static      <- Static assets (images, JS, CSS) related to similar movie recommendations
        │       ├── templates   <- HTML templates for similar movie recommendations
        │       └── similar_movies.py  <- Python file defining the route and logic for similar movies feature
        ├── resources           <- Contains reusable resources like utilities, data downloaders, and other logic
        │   │
        │   ├── __init__.py     <- Makes the 'resources' directory a package
        │   │
        │   ├── config.py       <- Configuration file for settings such as API keys, paths, etc.
        │   ├── datasetDownloader.py   <- Python module to handle downloading datasets
        │   ├── modelDownloader.py     <- Python module for downloading models
        │   ├── moviesRAG.py        <- Python module for movie-related Retrieval-Augmented Generation tasks
        │   ├── moviesRecommendationEngine.py  <- Python module for recommendation engine logic
        │   ├── searchMovies.py      <- Python module to search and retrieve movie data
        │   └── resources.yaml    <- YAML configuration file for resources used across the project
        │
        ├── static              <- Folder containing static assets for the app (CSS, images, JS, etc.)
        │   │
        │   ├── css             <- Stylesheets for styling the application
        │   ├── img             <- Images used across the application
        │   ├── js              <- JavaScript files for interactive functionality
        │   └── scss            <- SCSS files if using SASS for styling
        ├── templates           <- Folder containing HTML templates
        │   │
        │   └── partials        <- Folder for reusable HTML components or partials
        │       │
        │       ├── details_modal.html    <- Modal HTML for displaying movie details
        │       ├── liked_modal.html      <- Modal HTML for liked movies
        │       └── navbar.html           <- Navbar HTML component for site navigation
        │
        └── tests               <- Directory containing test cases for the project

```

---
