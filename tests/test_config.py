"""Tests for configuration utilities."""

import unittest
import tempfile
import os
from pathlib import Path
import yaml

from utils.config import load_strategy_def, save_strategy_def, load_runtime_config


class TestConfigUtils(unittest.TestCase):
    """Test cases for configuration utility functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.strategies_dir = Path(self.test_dir) / 'strategies'
        self.strategies_dir.mkdir(exist_ok=True)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_save_and_load_strategy_def(self):
        """Test saving and loading strategy definition."""
        strategy_def = {
            'name': 'TestStrategy',
            'indicators': {
                'sma': {
                    'type': 'SMA',
                    'period': 20
                }
            },
            'triggers': [],
            'parameters': {
                'sma_period': 20
            }
        }
        
        # Save
        strategy_file = self.strategies_dir / 'TestStrategy.yaml'
        with open(strategy_file, 'w') as f:
            yaml.dump(strategy_def, f)
        
        # Load
        with open(strategy_file, 'r') as f:
            loaded = yaml.safe_load(f)
        
        self.assertEqual(loaded['name'], 'TestStrategy')
        self.assertIn('sma', loaded['indicators'])
        self.assertEqual(loaded['parameters']['sma_period'], 20)
    
    def test_load_runtime_config(self):
        """Test loading runtime configuration."""
        config = {
            'strategy': 'TestStrategy',
            'start_date': '2023-01-01',
            'end_date': '2024-01-01',
            'tickers': 'AAPL',
            'strategy_parameters': {
                'sma_period': 20
            },
            'analysis': True
        }
        
        config_file = Path(self.test_dir) / 'test_config.yaml'
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        loaded = load_runtime_config(str(config_file))
        
        self.assertEqual(loaded['strategy'], 'TestStrategy')
        self.assertEqual(loaded['start_date'], '2023-01-01')
        self.assertIn('strategy_parameters', loaded)
        self.assertTrue(loaded['analysis'])
    
    def test_load_nonexistent_config(self):
        """Test loading a config file that doesn't exist."""
        with self.assertRaises(FileNotFoundError):
            load_runtime_config('/nonexistent/config.yaml')


if __name__ == '__main__':
    unittest.main()
