import argparse
import os
from collections import defaultdict
from typing import List

import toml
import yaml
from yaml.representer import Representer


def config_list_to_str_for_console_output(data_ops_config_list: List[str]) -> str:
    return ":".join(data_ops_config_list)


def _parse_individual_data_ops_config(directory: str) -> dict:
    try:
        with open(os.path.join(directory, "pyproject.toml"), "r") as toml_file:
            toml_data = toml.load(toml_file)
            return toml_data["data-ops-config"]
    except Exception as e:
        print(f"Error parsing TOML file in {directory}: {e}")
        return {}


def _toml_file_has_matching_type(directory: str, ops_type: str) -> bool:
    with open(os.path.join(directory, "pyproject.toml"), "r") as toml_file:
        toml_data = toml.load(toml_file)
        if "data-ops-config" in toml_data.keys():
            if ops_type:
                return toml_data["data-ops-config"].get("type") == ops_type
            else:
                return True
        return False


class TomlUtilities:
    def __init__(self, root_dir: str, ops_type: str):
        self.root_dir = root_dir
        self.ops_type = ops_type
        if self.ops_type == "all":
            self.ops_type = None

    def parse_data_ops_configurations(self) -> List[str]:
        return [root for root, dirs, files in os.walk(self.root_dir)
                if "pyproject.toml" in files and root != self.root_dir
                and _toml_file_has_matching_type(root, self.ops_type)]

    def generate_yaml_config(self) -> str:
        yaml.add_representer(defaultdict, Representer.represent_dict)
        data_ops_configurations = self.parse_data_ops_configurations()
        parsed_configs = {}
        for directory in data_ops_configurations:
            parsed_config = _parse_individual_data_ops_config(directory)
            ops_type = parsed_config.pop("type")
            parsed_config["name"] = directory.split("/")[-1]
            if ops_type not in parsed_configs:
                parsed_configs[ops_type] = []
            parsed_configs[ops_type].append(parsed_config)
        return yaml.dump(parsed_configs, default_flow_style=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=["directory_types", "terraform_yaml_config"])
    parser.add_argument("directory")
    parser.add_argument("--ops_type", choices=["tdv_ddl", "tdv_dml", "dml_with_dag", "ddl", "dml", "all", "stored_proc"])
    args = parser.parse_args()

    toml_utils = TomlUtilities(args.directory, args.ops_type)
    if args.operation == "directory_types":
        print(config_list_to_str_for_console_output(toml_utils.parse_data_ops_configurations()))
    if args.operation == "terraform_yaml_config":
        print(toml_utils.generate_yaml_config())


if __name__ == "__main__":
    main()
