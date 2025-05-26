from unittest import TestCase

from toml_utilities import config_list_to_str_for_console_output


class TestConfigListToStrForConsoleOutput(TestCase):
    def test_config_list_to_str_for_console_output(self):
        test_list = ['dir1', 'dir2', 'dir3']
        expected_result = 'dir1:dir2:dir3'
        result = config_list_to_str_for_console_output(test_list)
        self.assertEqual(result, expected_result)
