"""
Climate Economics Framework
"""

import random
import os
from typing import Dict, List, Any, Optional

# Define continents and their climate characteristics
CONTINENTS = {
    'North America': {'climate_risk': 0.8},
    'Europe': {'climate_risk': 0.6},
    'Asia': {'climate_risk': 1.2},
    'South America': {'climate_risk': 1.0},
    'Africa': {'climate_risk': 1.1}
}


class ClimateFramework:
    """
    Simplified framework for climate economics modeling with geographical distribution.
    Supports climate stress application to agents based on geographical location.
    """
    
    def __init__(self, simulation_parameters: Dict[str, Any]):
        self.params = simulation_parameters
        self.climate_events_history = []
        self.geographical_assignments = {}
        
        print(f"Climate Framework initialized")
    
    def assign_geographical_locations(self, agent_groups: Dict[str, List], 
                                    distribution_rules: Optional[Dict] = None):
        """
        Assign agents to continents and store the assignment plan.
        """
        if distribution_rules is None:
            distribution_rules = self._get_default_distribution_rules()
        
        continents = list(CONTINENTS.keys())
        
        for agent_type, agent_group in agent_groups.items():
            if agent_type in distribution_rules:
                target_continents = distribution_rules[agent_type]
            else:
                target_continents = continents
            
            num_agents = agent_group.num_agents
            print(f"  Assigning {num_agents} {agent_type.replace('_', ' ')}s to continents...")
            
            # Store geographical assignments for later use
            self.geographical_assignments[agent_type] = {}
            
            for i in range(num_agents):
                continent = target_continents[i % len(target_continents)]
                base_vulnerability = 0.1
                new_vulnerability = base_vulnerability * CONTINENTS[continent]['climate_risk']
                
                self.geographical_assignments[agent_type][i] = {
                    'continent': continent,
                    'vulnerability': new_vulnerability
                }
                
                print(f"    {agent_type.replace('_', ' ').title()} {i} assigned to {continent} (vulnerability: {new_vulnerability:.2f})")
            
            print(f"    Geographical assignment completed for {agent_type}")
    
    def apply_geographical_climate_stress(self, agent_groups: Dict[str, List]) -> Dict[str, str]:
        """
        Apply climate stress events by continent using group-level method calls.
        """
        climate_events = {}
        
        # Apply climate stress based on configured rules
        shock_rules = self.params.get('shock_rules', [])
        chronic_rules = self.params.get('chronic_rules', [])
        
        # Apply chronic stress first (if configured)
        if chronic_rules:
            print(f"\nApplying chronic stress...")
            self._apply_chronic_stress(agent_groups, chronic_rules)
        
        # Apply acute shocks
        if shock_rules:
            print(f"\nChecking for acute climate shocks...")
            climate_events = self._apply_shock_rules(agent_groups, shock_rules)
        
        # Store climate events
        self.climate_events_history.append(climate_events)
        return climate_events
    
    def _apply_chronic_stress(self, agent_groups: Dict[str, List], chronic_rules: List[Dict]):
        """Apply chronic climate stress based on rules."""
        for rule in chronic_rules:
            agent_types = rule.get('agent_types', [])
            continents = rule.get('continents', ['all'])
            stress_factor = rule.get('stress_factor', 0.99)
            
            print(f"  Applying chronic stress: {rule.get('name', 'unnamed')} (factor: {stress_factor})")
            
            self._apply_stress_to_agents(agent_groups, agent_types, continents, stress_factor, 'chronic')
    
    def _apply_shock_rules(self, agent_groups: Dict[str, List], shock_rules: List[Dict]) -> Dict[str, str]:
        """Apply acute climate shocks based on configured rules."""
        climate_events = {}
        
        for rule in shock_rules:
            probability = rule.get('probability', 0.1)
            
            if random.random() < probability:
                rule_name = rule.get('name', 'climate_shock')
                agent_types = rule.get('agent_types', [])
                continents = rule.get('continents', ['all'])
                stress_factor = rule.get('stress_factor', 0.7)
                
                print(f"  CLIMATE SHOCK: {rule_name} (factor: {stress_factor})")
                
                self._apply_stress_to_agents(agent_groups, agent_types, continents, stress_factor, 'acute')
                
                climate_events[rule_name] = {
                    'type': 'shock',
                    'agent_types': agent_types,
                    'continents': continents,
                    'stress_factor': stress_factor
                }
        
        return climate_events
    
    def _apply_stress_to_agents(self, agent_groups: Dict[str, List], 
                              target_agent_types: List[str], 
                              target_continents: List[str], 
                              stress_factor: float,
                              stress_type: str):
        """Apply stress to specific agent types in specific continents."""
        if 'all' in target_continents:
            target_continents = list(CONTINENTS.keys())
        
        for agent_type in target_agent_types:
            if agent_type not in agent_groups:
                print(f"    Warning: Agent type '{agent_type}' not found")
                continue
                
            agent_group = agent_groups[agent_type]
            
            # Apply stress using appropriate method
            method_name = 'apply_chronic_stress' if stress_type == 'chronic' else 'apply_climate_stress'
            
            if hasattr(agent_group, method_name):
                try:
                    method = getattr(agent_group, method_name)
                    method(stress_factor)
                    print(f"    Applied {stress_type} stress to {agent_type} (factor: {stress_factor})")
                except Exception as e:
                    print(f"    Could not apply {stress_type} stress to {agent_type}: {e}")
            else:
                print(f"    Warning: {agent_type} does not support {method_name}")
    
    def export_climate_summary(self, simulation_path: str = None, filename: str = "climate_summary.csv"):
        """Export a summary of climate events and geographical assignments."""
        import pandas as pd
        
        summary_data = []
        
        # Add geographical assignments
        for agent_type, assignments in self.geographical_assignments.items():
            for agent_id, info in assignments.items():
                summary_data.append({
                    'agent_type': agent_type,
                    'agent_id': agent_id,
                    'continent': info['continent'],
                    'vulnerability': info['vulnerability'],
                    'data_type': 'geographical_assignment'
                })
        
        # Add climate events
        for round_num, events in enumerate(self.climate_events_history):
            for event_key, event_data in events.items():
                if isinstance(event_data, dict):
                    # New format with event details
                    continents = event_data.get('continents', ['all'])
                    if 'all' in continents:
                        continents = list(CONTINENTS.keys())
                    
                    for continent in continents:
                        summary_data.append({
                            'agent_type': 'climate_event',
                            'agent_id': event_key,
                            'round': round_num,
                            'continent': continent,
                            'vulnerability': CONTINENTS[continent]['climate_risk'],
                            'data_type': 'climate_shock',
                            'event_name': event_key,
                            'stress_factor': event_data.get('stress_factor', 1.0)
                        })
                else:
                    # Simple format
                    summary_data.append({
                        'agent_type': 'climate_event',
                        'agent_id': event_key,
                        'round': round_num,
                        'continent': 'all',
                        'vulnerability': 1.0,
                        'data_type': 'simple_stress',
                        'event_name': event_key,
                        'stress_factor': 1.0
                    })
        
        if summary_data:
            df = pd.DataFrame(summary_data)
            
            if simulation_path:
                if not os.path.exists(simulation_path):
                    os.makedirs(simulation_path, exist_ok=True)
                save_path = os.path.join(simulation_path, filename)
            else:
                save_path = filename
                
            df.to_csv(save_path, index=False)
            print(f"Climate summary exported to '{save_path}'")
            return df
        else:
            print("No climate data to export")
            return None
    
    def _get_default_distribution_rules(self) -> Dict[str, List[str]]:
        """Default geographical distribution rules for common agent types."""
        return {
            'commodity_producer': ['Asia', 'South America', 'Africa'],
            'intermediary_firm': ['Asia', 'Europe'],
            'final_goods_firm': ['North America', 'Europe'],
            'household': list(CONTINENTS.keys()),
            'firm': ['North America', 'Europe', 'Asia']
        }


# Utility functions for easy integration
def create_climate_framework(simulation_parameters: Dict[str, Any]) -> ClimateFramework:
    """Create a new climate framework instance."""
    return ClimateFramework(simulation_parameters)


def add_climate_capabilities(agent_class):
    """
    Decorator to add basic climate stress capabilities to agent classes.
    """
    def init_wrapper(original_init):
        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            # Add climate attributes if not present
            if not hasattr(self, 'climate_vulnerability'):
                self.climate_vulnerability = 0.1
            if not hasattr(self, 'base_output_quantity'):
                current_output = getattr(self, 'current_output_quantity', 1.0)
                self.base_output_quantity = current_output
            if not hasattr(self, 'chronic_stress_accumulated'):
                self.chronic_stress_accumulated = 1.0
            if not hasattr(self, 'climate_stressed'):
                self.climate_stressed = False
        return new_init
    
    def apply_climate_stress(self, stress_factor):
        """Apply climate stress to productivity."""
        self.climate_stressed = True
        if hasattr(self, 'current_output_quantity'):
            self.current_output_quantity = self.base_output_quantity * stress_factor * self.chronic_stress_accumulated
            print(f"  {self.__class__.__name__} {self.id}: CLIMATE STRESS! Production: {self.base_output_quantity:.2f} -> {self.current_output_quantity:.2f}")
    
    def reset_climate_stress(self):
        """Reset climate stress to chronic level."""
        if self.climate_stressed:
            self.climate_stressed = False
            if hasattr(self, 'current_output_quantity'):
                self.current_output_quantity = self.base_output_quantity * self.chronic_stress_accumulated
            print(f"  {self.__class__.__name__} {self.id}: Climate stress cleared")
    
    def apply_chronic_stress(self, stress_factor):
        """Apply chronic climate stress (permanent degradation)."""
        self.chronic_stress_accumulated *= stress_factor
        if hasattr(self, 'current_output_quantity'):
            self.current_output_quantity = self.base_output_quantity * self.chronic_stress_accumulated
            print(f"  {self.__class__.__name__} {self.id}: Chronic stress applied")
    
    # Wrap the original __init__ method
    if hasattr(agent_class, '__init__'):
        agent_class.__init__ = init_wrapper(agent_class.__init__)
    
    # Add climate methods
    agent_class.apply_climate_stress = apply_climate_stress
    agent_class.reset_climate_stress = reset_climate_stress
    agent_class.apply_chronic_stress = apply_chronic_stress
    
    return agent_class