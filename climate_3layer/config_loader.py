"""
Configuration Loader for Climate 3-Layer Model
"""

import json
import os
from typing import Dict, Any, List


class ConfigLoader:
    """ config loader for the climate 3-layer model."""

    def __init__(self, config_path: str = "model_config.json"):
        self.config_path = config_path
        self.config = None
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            self.config = json.load(f)
        
        print(f"Configuration loaded from {self.config_path}")
        return self.config
    
    def get_simulation_parameters(self) -> Dict[str, Any]:
        """Get simulation parameters."""
        sim_config = self.config['simulation']
        climate_config = self.config['climate']
        
        return {
            'name': sim_config['name'],
            'rounds': sim_config['rounds'],
            'result_path': sim_config['result_path'],
            'climate_stress_enabled': climate_config['stress_enabled'],
            'shock_rules': climate_config['shock_rules'],
            'chronic_rules': climate_config['chronic_rules'],
            'create_visualizations': self.config['visualization'].get('create_visualizations'),
            'create_dynamic_visualization': self.config['visualization'].get('create_dynamic_visualization')
        }
    
    def get_agent_config(self, agent_type: str) -> Dict[str, Any]:
        """Get configuration for a specific agent type."""
        return self.config['agents'][agent_type]
    
    def get_geographical_distribution_rules(self) -> Dict[str, List[str]]:
        """Get geographical distribution rules."""
        return self.config.get('geographical_distribution', {})
    
    def get_goods_to_track(self) -> Dict[str, List[str]]:
        """Get goods to track for data collection."""
        return self.config['data_collection'].get('goods_to_track', {})


def load_model_config(config_path: str = "model_config.json") -> ConfigLoader:
    """Load and return a simple config loader."""
    loader = ConfigLoader(config_path)
    loader.load_config()
    return loader 