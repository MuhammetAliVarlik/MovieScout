import os
import yaml
from huggingface_hub import hf_hub_download

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

class HuggingFaceModelDownloader:
    def __init__(self, config_file="resources.yaml"):
        """
        Initialize the downloader with model repository details and output directory from a YAML config file.

        :param config_file: Path to the YAML configuration file (default is 'resources.yaml').
        """
        self.config_file = config_file
        self.load_config()

    def load_config(self):
        """
        Load the configuration from the YAML file.
        """
        try:
            with open(self.config_file, 'r') as file:
                config = yaml.safe_load(file)
            
            # Set model configuration from YAML
            self.repo_id = config['model']['repo_id']
            self.file_name = config['model']['file_name']
            self.output_dir = os.path.join(CURRENT_DIR, "..", "..", config['model']['output_dir'])
            os.makedirs(self.output_dir, exist_ok=True)  # Ensure the output directory exists
            
            print(f"Configuration loaded from {self.config_file}")
        except FileNotFoundError:
            print(f"Error: {self.config_file} not found. Using default settings.")
            # Default values if config file is missing
            self.repo_id = "bartowski/Llama-3.2-1B-Instruct-GGUF"
            self.file_name = "Llama-3.2-1B-Instruct-Q6_K_L.gguf"
            self.output_dir = os.path.join(CURRENT_DIR, "..", "..", "models")
            os.makedirs(self.output_dir, exist_ok=True)

    def model_exists(self):
        """
        Check if the model file already exists in the output directory.

        :return: True if the file exists, False otherwise.
        """
        file_path = os.path.join(self.output_dir, self.file_name)
        return os.path.exists(file_path)

    def download_model(self):
        """
        Download the model file from the specified Hugging Face repository, if it doesn't already exist.

        :return: The full path to the downloaded file, or a message indicating it already exists.
        """
        # Check if the model already exists
        file_path = os.path.join(self.output_dir, self.file_name)
        if self.model_exists():
            print(f"The model already exists at: {file_path}")
            return file_path

        # Download the model if it doesn't exist
        try:
            model_path = hf_hub_download(
                repo_id=self.repo_id,
                filename=self.file_name,
                local_dir=self.output_dir
            )
            print(f"Model downloaded to: {model_path}")
            return model_path
        except Exception as e:
            print(f"An error occurred while downloading the model: {e}")
            return None
