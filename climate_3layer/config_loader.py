"""
Configuration Loader for Climate 3-Layer Model

This module handles loading and validation of model configuration from JSON files,
making the simulation flexible and parameterizable.
"""

import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path


class ConfigLoader:
    """Loads and validates configuration for the climate 3-layer model."""
    
    def __init__(self, config_path: str = "model_config.json"):
        """
        Initialize the config loader.
        
        Args:
            config_path: Path to the JSON configuration file
        """
        self.config_path = config_path
        self.config = None
        self.agent_configs = {}
        
    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from JSON file with validation.
        
        Returns:
            Dictionary containing all configuration parameters
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
        
        # Validate configuration structure
        self._validate_config()
        
        # Process agent configurations
        self._process_agent_configs()
        
        print(f"✅ Configuration loaded successfully from {self.config_path}")
        self._print_config_summary()
        
        return self.config
    
    def _validate_config(self):
        """Validate that required configuration sections exist."""
        required_sections = ['simulation', 'climate', 'agents', 'data_collection', 'visualization']
        
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing required configuration section: {section}")
        
        # Validate simulation section
        required_sim_keys = ['name', 'rounds']
        for key in required_sim_keys:
            if key not in self.config['simulation']:
                raise ValueError(f"Missing required simulation parameter: {key}")
        
        # Validate agent configurations
        if not self.config['agents']:
            raise ValueError("No agent types configured")
        
        for agent_type, agent_config in self.config['agents'].items():
            self._validate_agent_config(agent_type, agent_config)
    
    def _validate_agent_config(self, agent_type: str, config: Dict[str, Any]):
        """Validate individual agent configuration."""
        required_keys = ['count', 'initial_money']
        
        for key in required_keys:
            if key not in config:
                raise ValueError(f"Missing required parameter '{key}' for agent type '{agent_type}'")
        
        if config['count'] <= 0:
            raise ValueError(f"Agent count must be positive for '{agent_type}': {config['count']}")
        
        if config['initial_money'] < 0:
            raise ValueError(f"Initial money cannot be negative for '{agent_type}': {config['initial_money']}")
    
    def _process_agent_configs(self):
        """Process and prepare agent configurations for easier access."""
        # Extract coordination parameters for cross-agent communication
        household_config = self.config['agents'].get('household', {})
        household_survival_consumption = household_config.get('consumption', {}).get('minimum_survival_consumption', 0.0)
        
        # Count agents for coordination
        agent_counts = {agent_type: config['count'] for agent_type, config in self.config['agents'].items()}
        
        # Calculate cascading minimum production requirements through supply chain
        # Level 1: Household survival needs
        total_household_survival_needs = household_survival_consumption * agent_counts.get('household', 0)
        
        # Level 2: Final goods firms minimum production (with safety buffer applied per-firm)
        final_goods_firm_count = agent_counts.get('final_goods_firm', 1)
        
        # Get safety buffer from configuration (optional - defaults to 1.0 for no buffer)
        safety_buffer = self.config.get('supply_chain', {}).get('safety_buffer', 1.0)
        
        final_goods_minimum_per_firm = (total_household_survival_needs / final_goods_firm_count) * safety_buffer
        total_final_goods_minimum = final_goods_minimum_per_firm * final_goods_firm_count
        
        # Level 3: Intermediary firms minimum production (based on final goods needs)
        # Read actual exponents from configuration instead of hardcoding
        intermediary_firm_count = agent_counts.get('intermediary_firm', 1)
        intermediary_config = self.config['agents'].get('intermediary_firm', {})
        intermediary_inputs = intermediary_config.get('production', {}).get('inputs', {})
        
        # For final goods firms, find what proportion of their production uses intermediate goods
        final_goods_config = self.config['agents'].get('final_goods_firm', {})
        final_goods_inputs = final_goods_config.get('production', {}).get('inputs', {})
        intermediate_good_exponent = final_goods_inputs.get('intermediate_good', 0.5)  # fallback to 0.5
        total_exponents_final_goods = sum(final_goods_inputs.values()) if final_goods_inputs else 1.0
        intermediate_goods_needed_ratio = intermediate_good_exponent / total_exponents_final_goods
        
        total_intermediate_goods_minimum = total_final_goods_minimum * intermediate_goods_needed_ratio * safety_buffer
        intermediary_minimum_per_firm = total_intermediate_goods_minimum / intermediary_firm_count
        
        # Level 4: Commodity producers minimum production (based on intermediary needs)
        # Read actual exponents from configuration instead of hardcoding
        commodity_producer_count = agent_counts.get('commodity_producer', 1)
        commodity_config = self.config['agents'].get('commodity_producer', {})
        commodity_inputs = commodity_config.get('production', {}).get('inputs', {})
        
        # For intermediary firms, find what proportion of their production uses commodities
        commodity_exponent = intermediary_inputs.get('commodity', 0.5)  # fallback to 0.5
        total_exponents_intermediary = sum(intermediary_inputs.values()) if intermediary_inputs else 1.0
        commodities_needed_ratio = commodity_exponent / total_exponents_intermediary
        
        total_commodities_minimum = total_intermediate_goods_minimum * commodities_needed_ratio * safety_buffer
        commodity_minimum_per_producer = total_commodities_minimum / commodity_producer_count
        
        print(f"🔗 SUPPLY CHAIN MINIMUM PRODUCTION COORDINATION:")
        print(f"   Level 1 - Household survival: {household_survival_consumption:.3f} per household × {agent_counts.get('household', 0)} = {total_household_survival_needs:.3f} total")
        print(f"   Level 2 - Final goods firms: {final_goods_minimum_per_firm:.3f} per firm × {final_goods_firm_count} = {total_final_goods_minimum:.3f} total")
        print(f"   Level 3 - Intermediary firms: {intermediary_minimum_per_firm:.3f} per firm × {intermediary_firm_count} = {total_intermediate_goods_minimum:.3f} total")
        print(f"     ↳ Final goods input ratios: {final_goods_inputs} → intermediate_good ratio: {intermediate_goods_needed_ratio:.3f}")
        print(f"   Level 4 - Commodity producers: {commodity_minimum_per_producer:.3f} per producer × {commodity_producer_count} = {total_commodities_minimum:.3f} total")
        print(f"     ↳ Intermediary input ratios: {intermediary_inputs} → commodity ratio: {commodities_needed_ratio:.3f}")
        print(f"   Safety buffer: {safety_buffer:.1f} (applied per-firm for all levels)")
        
        for agent_type, config in self.config['agents'].items():
            self.agent_configs[agent_type] = {
                'count': config['count'],
                'initial_money': config['initial_money'],
                'initial_inventory': config.get('initial_inventory', {}),
                'production': config.get('production', {}),
                'consumption': config.get('consumption', {}),
                'labor': config.get('labor', {}),
                'climate': config.get('climate', {}),
                'geographical_distribution': config.get('geographical_distribution', ['Unknown']),
                
                # Supply chain coordination parameters
                'household_minimum_survival_consumption': household_survival_consumption,
                'household_count': agent_counts.get('household', 0),
                'final_goods_firm_count': final_goods_firm_count,
                'intermediary_firm_count': intermediary_firm_count,
                'commodity_producer_count': commodity_producer_count,
                
                # Cascading minimum production responsibilities
                'final_goods_minimum_per_firm': final_goods_minimum_per_firm,
                'intermediary_minimum_per_firm': intermediary_minimum_per_firm,
                'commodity_minimum_per_producer': commodity_minimum_per_producer,
                
                # Legacy support (for final goods firms)
                'final_goods_count': final_goods_firm_count,
                'intermediary_count': intermediary_firm_count
            }
    
    def _print_config_summary(self):
        """Print a summary of the loaded configuration."""
        print("\n📋 Configuration Summary:")
        print(f"  Simulation: {self.config['simulation']['name']}")
        print(f"  Rounds: {self.config['simulation']['rounds']}")
        print(f"  Climate stress: {'Enabled' if self.config['climate']['stress_enabled'] else 'Disabled'}")
        
        print(f"\n👥 Agent Configuration:")
        for agent_type, config in self.agent_configs.items():
            print(f"  {agent_type.replace('_', ' ').title()}: {config['count']} agents")
            print(f"    Initial money: ${config['initial_money']}")
            if config['production']:
                print(f"    Production capacity: {config['production'].get('base_output_quantity', 'N/A')}")
        
        if self.config['climate']['shock_rules']:
            print(f"\n🌪️ Climate Shock Rules: {len(self.config['climate']['shock_rules'])} defined")
            for rule in self.config['climate']['shock_rules']:
                print(f"  {rule['name']}: {rule['probability']:.1%} probability")
    
    def get_simulation_parameters(self) -> Dict[str, Any]:
        """Get simulation parameters in the format expected by the main simulation."""
        sim_config = self.config['simulation']
        climate_config = self.config['climate']
        viz_config = self.config['visualization']
        
        return {
            'name': sim_config['name'],
            'trade_logging': sim_config.get('trade_logging', 'off'),
            'random_seed': sim_config.get('random_seed', 42),
            'rounds': sim_config['rounds'],
            'climate_stress_enabled': climate_config['stress_enabled'],
            'chronic_rules': climate_config.get('chronic_rules', []),  # not actually currently used for 3layer
            'geographical_effects': climate_config.get('geographical_effects', True),
            'create_visualizations': viz_config.get('create_visualizations', True),
            'create_dynamic_visualization': viz_config.get('create_dynamic_visualization', True),
            'shock_rules': climate_config.get('shock_rules', []),
            'result_path': sim_config.get('result_path', 'result_climate_3_layer')
        }
    
    def get_agent_config(self, agent_type: str) -> Dict[str, Any]:
        """Get configuration for a specific agent type."""
        if agent_type not in self.agent_configs:
            raise ValueError(f"No configuration found for agent type: {agent_type}")
        return self.agent_configs[agent_type]
    
    def get_geographical_distribution_rules(self) -> Dict[str, List[str]]:
        """Get geographical distribution rules for all agent types."""
        distribution_rules = {}
        
        for agent_type, config in self.agent_configs.items():
            distribution = config['geographical_distribution']
            if 'all' in distribution:
                # Use all continents if 'all' is specified
                from climate_framework import CONTINENTS
                distribution_rules[agent_type] = list(CONTINENTS.keys())
            else:
                distribution_rules[agent_type] = distribution
                
        return distribution_rules
    
    def get_goods_to_track(self) -> Dict[str, List[str]]:
        """Get goods tracking configuration for data collection."""
        return self.config['data_collection'].get('track_goods', {})
    
    def get_climate_shock_rules(self) -> List[Dict[str, Any]]:
        """Get climate shock rules configuration."""
        return self.config['climate'].get('shock_rules', [])


def load_model_config(config_path: str = "model_config.json") -> ConfigLoader:
    """
    Convenience function to load model configuration.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Loaded and validated ConfigLoader instance
    """
    loader = ConfigLoader(config_path)
    loader.load_config()
    return loader


# Example configuration templates for different scenarios
EXAMPLE_CONFIGS = {
    "stress_test": {
        "description": "High-stress scenario with frequent climate shocks",
        "modifications": {
            "climate.acute_stress_probability": 0.3,
            "climate.shock_rules[0].probability": 0.2
        }
    },
    "stable_economy": {
        "description": "Stable economy with minimal climate disruption",
        "modifications": {
            "climate.stress_enabled": False,
            "simulation.rounds": 50
        }
    },
    "asia_focus": {
        "description": "Focus climate shocks on Asian production",
        "modifications": {
            "climate.shock_rules": [
                {
                    "name": "asia_commodity_disruption",
                    "probability": 0.15,
                    "agent_types": ["commodity_producer"],
                    "continents": ["Asia"],
                    "stress_factor": 0.6,
                    "duration": 1
                }
            ]
        }
    }
}


def create_example_config(scenario: str, output_path: str = None) -> str:
    """
    Create an example configuration file for a specific scenario.
    
    Args:
        scenario: One of the predefined scenarios in EXAMPLE_CONFIGS
        output_path: Path where to save the configuration file
        
    Returns:
        Path to the created configuration file
    """
    if scenario not in EXAMPLE_CONFIGS:
        raise ValueError(f"Unknown scenario: {scenario}. Available: {list(EXAMPLE_CONFIGS.keys())}")
    
    # Load base configuration
    loader = ConfigLoader()
    base_config = loader.load_config()
    
    # Apply modifications for the scenario
    modifications = EXAMPLE_CONFIGS[scenario]["modifications"]
    
    # This is a simplified implementation - in practice you'd want more sophisticated merging
    print(f"Creating example configuration for scenario: {scenario}")
    print(f"Description: {EXAMPLE_CONFIGS[scenario]['description']}")
    
    if output_path is None:
        output_path = f"config_{scenario}.json"
    
    # For now, just copy the base config and add a comment
    config_with_comment = {
        "_scenario": scenario,
        "_description": EXAMPLE_CONFIGS[scenario]["description"],
        **base_config
    }
    
    with open(output_path, 'w') as f:
        json.dump(config_with_comment, f, indent=2)
    
    print(f"Example configuration saved to: {output_path}")
    return output_path 