import csv
import os
import random
from typing import List, Dict, Any
from helm.common.general import ensure_file_downloaded, ensure_directory_exists
from .scenario import Scenario, Instance, Reference, ALL_SPLITS, CORRECT_TAG, VALID_SPLIT, Input, Output

# TODO: Should I just get rid of the train/test split?

class EthicsJusticeScenario(Scenario):
    """Information on this class"""
    name = "ethics_justice"
    description = "Ethics Justice dataset"
    tags = ["classification"]
    DATASET_FILE_NAME = "justice_hard.csv"
    TRAIN_RATIO = 0.8  # 80% for training, 20% for validation
    TRAIN_SPLIT = "train"
    VALID_SPLIT = "valid"

    def download_dataset(self, output_path: str):
        """Downloads Justice Dataset if not already present."""
        # Define the target path for the dataset
        data_dir = os.path.join(output_path, "data")
        dataset_path = os.path.join(data_dir, self.DATASET_FILE_NAME)

        # Check if the dataset already exists
        if os.path.exists(dataset_path):
            print(f"The dataset '{self.DATASET_FILE_NAME}' already exists at '{dataset_path}'. Skipping download.")
            return

        # Download the raw data
        url = "https://gist.githubusercontent.com/msaroufim/1b9c298b5bbc8cf3cd379c5dc05a3998/raw/41cfe8da6ffafe473d91d1ae3e3fb1e927d09efa/justice_hard.csv"
        ensure_directory_exists(data_dir)
        ensure_file_downloaded(source_url=url, target_path=dataset_path)

    def load_dataset(self, output_path: str) -> List[Dict[str, Any]]:
        self.download_dataset(output_path)
        file_path = os.path.join(output_path, "data", self.DATASET_FILE_NAME)

        data = []
        with open(file_path, encoding="utf-8") as f:
            csv_reader = csv.reader(f)
            next(csv_reader)  # Skip the header row if it exists
            for row in csv_reader:
                label, scenario = row  # Adjust the unpacking if the dataset format changes
                data_point = {
                    "label": int(label),
                    "input": scenario.strip()
                }
                data.append(data_point)
        random.seed(0)
        random.shuffle(data)
        return data

    def get_label(self, label: int) -> str:
        return "Unreasonable" if label == 0 else "Reasonable"
    
    def data_to_instance(self, data_point: Dict[str, Any], split: str, instance_id: str) -> Instance:
        input_text = Input(text=data_point["input"])

        # Create references for both possible labels
        references = [
            Reference(output=Output(text=self.get_label(0)), tags=[]),
            Reference(output=Output(text=self.get_label(1)), tags=[])
        ]

        # Assign the CORRECT_TAG to the correct choice
        for reference in references:
            if reference.output.text == self.get_label(data_point["label"]):
                reference.tags.append(CORRECT_TAG)

        return Instance(
            id=instance_id, input=input_text, references=references, split=split
        )

    def get_instances(self, output_path: str) -> List[Instance]:
        self.download_dataset(output_path)
        data = self.load_dataset(output_path)
        split_index = int(len(data) * self.TRAIN_RATIO)
        train_data = data[:split_index]
        valid_data = data[split_index:]

        train_instances = [self.data_to_instance(dp, self.TRAIN_SPLIT, f"id{i}") for i, dp in enumerate(train_data)]
        valid_instances = [self.data_to_instance(dp, self.VALID_SPLIT, f"id{i+len(train_data)}") for i, dp in enumerate(valid_data)]

        return train_instances + valid_instances

