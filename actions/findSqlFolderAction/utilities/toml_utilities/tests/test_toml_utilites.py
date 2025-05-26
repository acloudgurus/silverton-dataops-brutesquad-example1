import os
from unittest import TestCase

import yaml

from toml_utilities import TomlUtilities


class TestTomlUtilities(TestCase):
    def setUp(self):
        self.test_dir = os.path.abspath("test_dir")
        os.makedirs(self.test_dir, exist_ok=True)

        self.dir_with_pyproject = os.path.join(self.test_dir, "dir_with_pyproject")
        os.makedirs(self.dir_with_pyproject, exist_ok=True)
        self.pyproject_content_with_section = """
                                                [tool.poetry]
                                                name = "test_package"
                                                version = "0.1.0"
                                            
                                                [data-ops-config]
                                                type = "test_type"
                                                s3-prefix = "test_prefix"
                                                path-to-sql = "test_sql"
                                                path-to-changelog = "test_changelog"
                                                """
        with open(os.path.join(self.dir_with_pyproject, "pyproject.toml"), "w") as f:
            f.write(self.pyproject_content_with_section)

        self.dir_with_pyproject_different_type = os.path.join(
            self.test_dir, "dir_with_pyproject_different_type"
        )
        os.makedirs(self.dir_with_pyproject_different_type, exist_ok=True)
        self.pyproject_content_no_type = """
                                        [tool.poetry]
                                        name = "yet_another_package"
                                        version = "0.2.0"

                                        [data-ops-config]
                                        type = "different_type"
                                        s3-prefix = "test_prefix"
                                        path-to-sql = "test_sql"
                                        path-to-changelog = "test_changelog"
                                        """
        with open(
            os.path.join(self.dir_with_pyproject_different_type, "pyproject.toml"), "w"
        ) as f:
            f.write(self.pyproject_content_no_type)

        self.dir_with_pyproject_no_section = os.path.join(
            self.test_dir, "dir_with_pyproject_no_section"
        )
        os.makedirs(self.dir_with_pyproject_no_section, exist_ok=True)
        self.pyproject_content_no_section = """
                                            [tool.poetry]
                                            name = "another_package"
                                            version = "0.3.0"
                                            """
        with open(
            os.path.join(self.dir_with_pyproject_no_section, "pyproject.toml"), "w"
        ) as f:
            f.write(self.pyproject_content_no_section)

        self.dir_without_pyproject = os.path.join(
            self.test_dir, "dir_without_pyproject"
        )
        os.makedirs(self.dir_without_pyproject, exist_ok=True)

    def tearDown(self):
        for root, dirs, files in os.walk(self.test_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.test_dir)

    def test_given_toml_file_with_data_ops_config_when_parse_data_ops_config_called_then_list_with_correct_dir_returned(
        self,
    ):
        toml_utils = TomlUtilities(self.test_dir, "test_type")
        result = toml_utils.parse_data_ops_configurations()
        self.assertIn(self.dir_with_pyproject, result)

    def test_given_a_toml_file_with_no_data_ops_config_section_when_parse_data_ops_config_called_then_empty_list_returned(
        self,
    ):
        toml_utils = TomlUtilities(self.test_dir, "test_type")
        result = toml_utils.parse_data_ops_configurations()
        self.assertNotIn(self.dir_with_pyproject_no_section, result)

    def test_given_a_toml_file_with_wrong_type_in_data_ops_config_section_when_parse_data_ops_config_called_then_empty_list_returned(
        self,
    ):
        toml_utils = TomlUtilities(self.test_dir, "wrong_type")
        result = toml_utils.parse_data_ops_configurations()
        self.assertEqual([], result)

    def test_given_a_directory_without_a_pyproject_toml_file_then_when_parse_data_ops_config_called_then_empty_list_returned(
        self,
    ):
        toml_utils = TomlUtilities(self.test_dir, "test_type")
        result = toml_utils.parse_data_ops_configurations()
        self.assertNotIn(self.dir_without_pyproject, result)

    def test_given_a_toml_file_with_different_type_in_data_ops_config_section_when_parse_data_ops_config_called_with_ops_type_then_different_type_not_returned(
        self,
    ):
        toml_utils = TomlUtilities(self.test_dir, "test_type")
        result = toml_utils.parse_data_ops_configurations()
        self.assertNotIn(self.dir_with_pyproject_different_type, result)

    def test_given_option_all_then_when_parse_data_ops_config_called_then_all_drectories_with_pyproject_toml_files_with_data_ops_config_returned(
        self,
    ):
        toml_utils = TomlUtilities(self.test_dir, "all")
        result = toml_utils.parse_data_ops_configurations()
        self.assertIn(self.dir_with_pyproject, result)
        self.assertIn(self.dir_with_pyproject_different_type, result)
        self.assertNotIn(self.dir_with_pyproject_no_section, result)
        self.assertNotIn(self.dir_without_pyproject, result)

    def test_given_toml_file_with_data_ops_config_when_generate_yaml_config_called_then_yaml_stream_returned(
        self,
    ):
        expected_result = {
            "test_type": [
                {
                    "name": "dir_with_pyproject",
                    "s3-prefix": "test_prefix",
                    "path-to-sql": "test_sql",
                    "path-to-changelog": "test_changelog",
                }
            ]
        }
        expected_result = yaml.dump(expected_result, default_flow_style=False)
        toml_utils = TomlUtilities(self.test_dir, "test_type")
        result = toml_utils.generate_yaml_config()
        self.assertEqual(expected_result, result)

    def test_given_a_toml_file_with_wrong_type_in_data_ops_config_section_when_generate_yaml_config_called_then_yaml_stream_not_returned(
        self,
    ):
        toml_utils = TomlUtilities(self.test_dir, "wrong_type")
        result = toml_utils.generate_yaml_config()
        self.assertEqual(yaml.dump({}, default_flow_style=False), result)

    def test_given_option_all_then_when_generate_yaml_config_called_then_yaml_stream_for_all_drectories_with_pyproject_toml_files_with_data_ops_config_returned(
        self,
    ):
        expected_result = {
            "different_type": [
                {
                    "name": "dir_with_pyproject_different_type",
                    "path-to-changelog": "test_changelog",
                    "path-to-sql": "test_sql",
                    "s3-prefix": "test_prefix",
                }
            ],
            "test_type": [
                {
                    "name": "dir_with_pyproject",
                    "path-to-changelog": "test_changelog",
                    "path-to-sql": "test_sql",
                    "s3-prefix": "test_prefix",
                }
            ],
        }
        toml_utils = TomlUtilities(self.test_dir, "all")
        result = yaml.full_load(toml_utils.generate_yaml_config())
        self.assertTrue([i for i in expected_result if i not in result] == [])
