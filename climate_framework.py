"""
Climate Economics Framework
"""

import random
import os
from copy import copy
from typing import Dict, List, Any

# Define continents and their climate characteristics
continent_list: List[str] = ['North America', 'Europe',  'Asia', 'South America',  'Africa', 'Oceania']


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
                                    distribution_rules: Dict[str, List]):
        """
        Assign agents to continents and store the assignment plan.
        """
        for agent_type, agent_group in agent_groups.items():
            if agent_type in distribution_rules:
                target_continents = distribution_rules[agent_type]
            else:
                target_continents = copy(continent_list)
            
            num_agents = agent_group.num_agents
            print(f"  Assigning {num_agents} {agent_type.replace('_', ' ')}s to continents...")
            
            # Store geographical assignments for later use
            self.geographical_assignments[agent_type] = {}
            
            for i in range(num_agents):
                continent = target_continents[i % len(target_continents)]
                self.geographical_assignments[agent_type][i] = {'continent': continent}
                
                print(f"    {agent_type.replace('_', ' ').title()} {i} assigned to {continent}.")
            
            print(f"    Geographical assignment completed for {agent_type}")
    
    def apply_geographical_climate_stress(self, agent_groups: Dict[str, List]) -> Dict[str, str]:
        """
        Apply climate stress events by continent using group-level method calls.
        """
        climate_events = {}
        
        # Apply climate stress based on configured rules
        shock_rules = self.params['shock_rules']
        chronic_rules = self.params['chronic_rules']
        
        # Apply chronic stress first (if configured)
        if len(chronic_rules) != 0:
            print(f"\nApplying chronic stress...")
            self._apply_chronic_stress(agent_groups, chronic_rules)
        
        # Apply acute shocks
        if len(shock_rules) != 0:
            print(f"\nChecking for acute climate shocks...")
            climate_events = self._apply_shock_rules(agent_groups, shock_rules)
        
        # Store climate events
        self.climate_events_history.append(climate_events)
        return climate_events
    
    def _apply_chronic_stress(self, agent_groups: Dict[str, List], chronic_rules: List[Dict]):
        """Apply chronic climate stress based on rules."""
        for rule in chronic_rules:
            overhead_factor = rule['overhead_stress_factor'] if 'overhead_stress_factor' in rule else None
            productivity_factor = rule['productivity_stress_factor'] if 'productivity_stress_factor' in rule else None

            # apply overhead stress if applicable
            if overhead_factor is not None:
                print(f"  Applying overhead chronic stress: {rule.get('name', 'unnamed')} (factor: {rule['overhead_stress_factor']})")
                self._apply_stress_to_agents(agent_groups, rule['agent_types'], rule['continents'], rule['overhead_stress_factor'], 'chronic', 'overhead')
            
            # apply productivity stress if applicable
            if productivity_factor is not None:
                print(f"  Applying productivity chronic stress: {rule.get('name', 'unnamed')} (factor: {rule['productivity_stress_factor']})")
                self._apply_stress_to_agents(agent_groups, rule['agent_types'], rule['continents'], rule['productivity_stress_factor'], 'chronic', 'productivity')
    
    def _apply_shock_rules(self, agent_groups: Dict[str, List], shock_rules: List[Dict]) -> Dict[str, str]:
        """Apply acute climate shocks based on configured rules."""
        climate_events = {}
        
        for rule in shock_rules:
            probability = rule['probability']
            
            if random.random() < probability:
                rule_name = rule.get('name', 'unnamed_shock')
                agent_types = rule['agent_types']
                continents = rule['continents']
                overhead_factor = rule['overhead_stress_factor'] if 'overhead_stress_factor' in rule else None
                productivity_factor = rule['productivity_stress_factor'] if 'productivity_stress_factor' in rule else None
                
                print(f"  CLIMATE SHOCK: {rule_name} (overhead factor: {overhead_factor}, productivity factor: {productivity_factor})")
                
                if overhead_factor:
                    self._apply_stress_to_agents(agent_groups, agent_types, continents, overhead_factor, 'acute', 'overhead')
                
                if productivity_factor:
                    self._apply_stress_to_agents(agent_groups, agent_types, continents, productivity_factor, 'acute', 'productivity')

                climate_events[rule_name] = {
                    'type': 'shock',
                    'agent_types': agent_types,
                    'continents': continents,
                    'overhead_stress_factor': overhead_factor,
                    'productivity_stress_factor': productivity_factor
                }
        
        return climate_events
    
    def _apply_stress_to_agents(self, agent_groups: Dict[str, List], 
                              target_agent_types: List[str], 
                              target_continents: List[str], 
                              stress_factor: float,
                              stress_type: str,
                              stress_target: str):
        """Apply stress to specific agent types in specific continents."""
        if 'all' in target_continents:
            target_continents = copy(continent_list)
        
        for agent_type in target_agent_types:
            if agent_type not in agent_groups:
                print(f"    Warning: Agent type '{agent_type}' not found")
                continue
                
            agent_group = agent_groups[agent_type]
            
            # Apply stress using appropriate method
            method_name = 'apply_chronic_stress' if stress_type == 'chronic' else 'apply_acute_stress'
            
            if hasattr(agent_group, method_name):
                try:
                    method = getattr(agent_group, method_name)
                    method(stress_factor, stress_target)
                    print(f"    Applied {stress_target} {stress_type} stress to {agent_type} (factor: {stress_factor})")
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
                continents = event_data['continents']

                if 'all' in continents:
                    continents = copy(continent_list)
                
                for continent in continents:
                    summary_data.append({
                        'agent_type': 'climate_event',
                        'agent_id': event_key,
                        'round': round_num,
                        'continent': continent,
                        'data_type': 'climate_shock',
                        'event_name': event_key,
                        'stress_factor': event_data['stress_factor']
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
            if not hasattr(self, 'base_output_quantity'):
                current_output = getattr(self, 'current_output_quantity', 1.0)
                self.base_output_quantity = current_output
            if not hasattr(self, 'chronic_stress_accumulated'):
                self.chronic_stress_accumulated = 1.0
            if not hasattr(self, 'climate_stressed'):
                self.climate_stressed = False

        return new_init
    
    def apply_acute_stress(self, stress_factor, stress_target):
        """Apply climate stress to productivity."""
        self.climate_stressed = True
        if stress_target == 'productivity':
            self.current_output_quantity = self.base_output_quantity * stress_factor * self.chronic_stress_accumulated
            print(f"  {self.__class__.__name__} {self.id}: CLIMATE STRESS! Production: {self.base_output_quantity:.2f} -> {self.current_output_quantity:.2f}")
        # TODO apply overhead stress
    
    def reset_climate_stress(self):
        """Reset climate stress to chronic level."""
        if self.climate_stressed:
            self.climate_stressed = False
            if hasattr(self, 'current_output_quantity'):
                self.current_output_quantity = self.base_output_quantity * self.chronic_stress_accumulated
            # TODO: reset overhead
            print(f"  {self.__class__.__name__} {self.id}: Climate stress cleared")
    
    def apply_chronic_stress(self, stress_factor, stress_target):
        """Apply chronic climate stress (permanent degradation)."""
        # TODO keep track of acumlated chronic stress separately over overhead and productivity
        self.chronic_stress_accumulated *= stress_factor
        if stress_target == 'productivity':
            if hasattr(self, 'current_output_quantity'):
                self.current_output_quantity = self.base_output_quantity * self.chronic_stress_accumulated
                print(f"  {self.__class__.__name__} {self.id}: Chronic stress applied")
        # TODO apply overhead stress
    
    # Wrap the original __init__ method
    if hasattr(agent_class, '__init__'):
        agent_class.__init__ = init_wrapper(agent_class.__init__)

    # Add climate methods
    agent_class.apply_acute_stress = apply_acute_stress
    agent_class.reset_climate_stress = reset_climate_stress
    agent_class.apply_chronic_stress = apply_chronic_stress
    
    return agent_class