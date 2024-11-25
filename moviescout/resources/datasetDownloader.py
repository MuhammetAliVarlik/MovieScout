import os
import pandas as pd
import zipfile
import yaml

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

class TMDBDatasetProcessor:
    def __init__(self, 
                 kaggle_dataset_name="asaniczka/tmdb-movies-dataset-2023-930k-movies",
                 download_dir=os.path.join(CURRENT_DIR, "..", "..", "data", "raw"),
                 processed_dir=os.path.join(CURRENT_DIR, "..", "..", "data", "processed"),
                 resources_file=os.path.join(CURRENT_DIR, "resources.yaml")):
        """
        Initialize the processor with dataset paths and parameters.
        
        :param kaggle_dataset_name: Kaggle dataset name (e.g., 'asaniczka/tmdb-movies-dataset-2023-930k-movies').
        :param download_dir: Directory where the dataset will be downloaded.
        :param processed_dir: Directory where the processed dataset will be saved.
        :param resources_file: Path to the resources.yaml file.
        """
        self.kaggle_dataset_name = kaggle_dataset_name
        self.download_dir = download_dir
        self.processed_dir = processed_dir
        self.resources_file = resources_file
        os.makedirs(self.download_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)

        self.load_resources()

    def load_resources(self):
        """
        Load the resources.yaml file and populate the attributes.
        """
        try:
            with open(self.resources_file, 'r') as file:
                resources = yaml.safe_load(file)

            # Load dataset paths and file names from the YAML
            self.zip_file_name = resources['dataset']['zip_file_name']
            self.csv_file_name = resources['dataset']['csv_file_name']
            self.processed_file_name = resources['dataset']['processed_file_name']
            self.dataset_name = resources['dataset']['name']
            self.download_path = resources['dataset']['download_path']
            self.processed_path = resources['dataset']['processed_path']

            print("Resources loaded from YAML.")

        except FileNotFoundError:
            print(f"Warning: {self.resources_file} not found. Using default settings.")
            self.zip_file_name = "tmdb-movies-dataset-2023-930k-movies.zip"
            self.csv_file_name = "TMDB_movie_dataset_v11.csv"
            self.processed_file_name = "TMDB.csv"
            self.dataset_name = self.kaggle_dataset_name
            self.download_path = self.download_dir
            self.processed_path = self.processed_dir

    def is_dataset_downloaded(self):
        """
        Check if the dataset ZIP file already exists in the download directory.
        """
        zip_path = os.path.join(self.download_dir, self.zip_file_name)
        return os.path.exists(zip_path)

    def download_dataset(self):
        """
        Download the dataset from Kaggle using the Kaggle API.
        """
        print("Downloading dataset from Kaggle...")
        os.system(f"kaggle datasets download {self.dataset_name} -p {self.download_dir}")
        print("Dataset downloaded.")

    def extract_dataset(self):
        """
        Extract the downloaded dataset ZIP file.
        """
        zip_path = os.path.join(self.download_dir, self.zip_file_name)
        print(f"Extracting dataset: {zip_path}")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(self.download_dir)
        print("Dataset extracted.")

    def process_dataset(self):
        """
        Process the dataset by filtering and selecting relevant columns.
        """
        csv_path = os.path.join(self.download_dir, self.csv_file_name)
        print(f"Loading dataset: {csv_path}")
        df = pd.read_csv(csv_path)

        print("Filtering and processing dataset...")
        # Filter conditions
        movies_db = df[df["popularity"] > 20]
        movies_db = movies_db[movies_db["adult"] == False]
        movies_db = movies_db[movies_db['spoken_languages'].str.contains("English") == True]
        movies_db = movies_db[movies_db['vote_average'] != 0]

        # Select relevant columns
        movies_db = movies_db[['title', 'vote_average', 'vote_count', 'status',
                               'release_date', 'runtime', 'overview',
                               'poster_path', 'genres', 'backdrop_path']]
        movies_db.reset_index(drop=True, inplace=True)
        print(f"Dataset processed. Shape: {movies_db.shape}")
        return movies_db

    def save_processed_dataset(self, df):
        """
        Save the processed dataset to a CSV file.
        """
        output_path = os.path.join(self.processed_dir, self.processed_file_name)
        print(f"Saving processed dataset to: {output_path}")
        df.to_csv(output_path, index=False)
        print("Processed dataset saved.")

    def run_pipeline(self):
        """
        Run the full pipeline: download, extract, process, and save the dataset.
        """
        # Check if the dataset is already downloaded
        if not self.is_dataset_downloaded():
            print("Dataset not found. Downloading...")
            self.download_dataset()
        else:
            print(f"Dataset already downloaded: {os.path.join(self.download_dir, self.zip_file_name)}")

        # Extract, process, and save the dataset
        self.extract_dataset()
        processed_df = self.process_dataset()
        self.save_processed_dataset(processed_df)
