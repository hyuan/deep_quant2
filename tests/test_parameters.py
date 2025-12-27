"""Tests for parameter utilities."""

import unittest
from utils.parameters import (
    set_nested_dict_value,
    map_cli_parameters_to_config,
    merge_configs
)


class TestParameterUtils(unittest.TestCase):
    """Test cases for parameter utility functions."""
    
    def test_set_nested_dict_value(self):
        """Test setting nested dictionary values."""
        d = {}
        
        # Simple key
        set_nested_dict_value(d, 'key', 'value')
        self.assertEqual(d['key'], 'value')
        
        # Nested key
        set_nested_dict_value(d, 'level1.level2', 'nested_value')
        self.assertEqual(d['level1']['level2'], 'nested_value')
        
        # Deep nesting
        set_nested_dict_value(d, 'a.b.c.d', 'deep')
        self.assertEqual(d['a']['b']['c']['d'], 'deep')
    
    def test_set_nested_dict_value_overwrite(self):
        """Test overwriting existing nested values."""
        d = {'existing': {'key': 'old_value'}}
        
        set_nested_dict_value(d, 'existing.key', 'new_value')
        self.assertEqual(d['existing']['key'], 'new_value')
    
    def test_map_cli_parameters_to_config(self):
        """Test mapping CLI parameters to config."""
        config = {
            'indicators': {
                'sma': {
                    'period': 10
                }
            }
        }
        
        dynamic_params = {
            'indicators.sma.period': '20'
        }
        
        result = map_cli_parameters_to_config(config, dynamic_params)
        
        self.assertEqual(result['indicators']['sma']['period'], 20)
    
    def test_map_cli_parameters_type_inference(self):
        """Test type inference when mapping parameters."""
        config = {}
        
        # Integer
        dynamic_params = {'int_param': '42'}
        result = map_cli_parameters_to_config(config, dynamic_params)
        self.assertEqual(result['int_param'], 42)
        self.assertIsInstance(result['int_param'], int)
        
        # Float
        dynamic_params = {'float_param': '3.14'}
        result = map_cli_parameters_to_config(config, dynamic_params)
        self.assertEqual(result['float_param'], 3.14)
        self.assertIsInstance(result['float_param'], float)
        
        # Boolean
        dynamic_params = {'bool_param': 'true'}
        result = map_cli_parameters_to_config(config, dynamic_params)
        self.assertTrue(result['bool_param'])
        self.assertIsInstance(result['bool_param'], bool)
        
        # String
        dynamic_params = {'str_param': 'hello'}
        result = map_cli_parameters_to_config(config, dynamic_params)
        self.assertEqual(result['str_param'], 'hello')
        self.assertIsInstance(result['str_param'], str)
    
    def test_merge_configs(self):
        """Test merging configurations."""
        base = {
            'key1': 'value1',
            'nested': {
                'key2': 'value2',
                'key3': 'value3'
            }
        }
        
        override = {
            'key1': 'new_value1',
            'nested': {
                'key3': 'new_value3',
                'key4': 'value4'
            },
            'new_key': 'new_value'
        }
        
        result = merge_configs(base, override)
        
        self.assertEqual(result['key1'], 'new_value1')
        self.assertEqual(result['nested']['key2'], 'value2')  # Preserved from base
        self.assertEqual(result['nested']['key3'], 'new_value3')  # Overridden
        self.assertEqual(result['nested']['key4'], 'value4')  # Added from override
        self.assertEqual(result['new_key'], 'new_value')  # Added from override
    
    def test_merge_configs_deep_nesting(self):
        """Test merging deeply nested configs."""
        base = {
            'level1': {
                'level2': {
                    'level3': {
                        'key': 'old'
                    }
                }
            }
        }
        
        override = {
            'level1': {
                'level2': {
                    'level3': {
                        'key': 'new'
                    }
                }
            }
        }
        
        result = merge_configs(base, override)
        self.assertEqual(result['level1']['level2']['level3']['key'], 'new')


if __name__ == '__main__':
    unittest.main()
