import csv
import os
import random
from typing import List, Dict, Any
from helm.common.general import ensure_file_downloaded, ensure_directory_exists
from .scenario import Scenario, Instance, Reference, ALL_SPLITS, CORRECT_TAG, VALID_SPLIT, Input, Output

# TODO: Should I just get rid of the train/test split?

class EthicsVirtueScenario(Scenario):
    """Information on this class"""
    name = "ethicsvirtue"
    description = "Ethics Virtue dataset"
    tags = ["classification"]
    DATASET_FILE_NAME = "virtue.csv"
    TRAIN_RATIO = 0.8  # 80% for training, 20% for validation
    TRAIN_SPLIT = "train"
    VALID_SPLIT = "valid"

    def download_dataset(self, output_path: str):
        """Downloads the Corr2Cause dataset if not already present."""
        # Define the target path for the dataset
        data_dir = os.path.join(output_path, "data")
        dataset_path = os.path.join(data_dir, self.DATASET_FILE_NAME)

        # Check if the dataset already exists
        if os.path.exists(dataset_path):
            print(f"The dataset '{self.DATASET_FILE_NAME}' already exists at '{dataset_path}'. Skipping download.")
            return

        # Download the raw data
        url = "https://gist.githubusercontent.com/msaroufim/e9cf8fbdd40a3c801463299f60b2c400/raw/05aaeb2cb4efc739277653801ce258ad8f997f5b/virtue.csv"
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
                label, full_scenario = row  # Adjust the unpacking if the dataset format changes
                scenario, trait = full_scenario.split(" [SEP] ", 1)
                data_point = {
                    "label": int(label),
                    "input": f"{scenario.strip()}\nTrait: {trait.strip()}"
                }
                data.append(data_point)
        random.shuffle(data)
        return data

    def get_label(self, label: int) -> str:
        return "No" if label == 0 else "Yes"

    def data_to_instance(self, data_point: Dict[str, Any], split: str, instance_id: str) -> Instance:
        input_text = Input(text=data_point["input"])
        correct_label = self.get_label(data_point["label"])
        incorrect_label = self.get_label(1 - data_point["label"])
        correct_reference = Reference(output=Output(text=correct_label), tags=[CORRECT_TAG])
        incorrect_reference = Reference(output=Output(text=incorrect_label), tags=[])

        return Instance(
            id=instance_id, input=input_text, references=[correct_reference, incorrect_reference], split=split
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
