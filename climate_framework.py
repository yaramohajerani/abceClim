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
    
    def reset_climate_stress(self, agent_groups: Dict[str, List]):
        """Reset all climate stress to chronic levels for all agents."""
        for agent_type, agent_group in agent_groups.items():
            try:
                agent_count = agent_group.num_agents
                
                # Access agents by index since abcEconomics groups are not directly iterable
                for i in range(agent_count):
                    agent = agent_group[i]
                    if hasattr(agent, 'climate_stressed'):
                        self._reset_agent_climate_stress(agent)
            except Exception as e:
                print(f"Could not reset climate stress for {agent_type}: {e}")
    
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
            
            # Apply stress to individual agents
            try:
                agent_count = agent_group.num_agents
                
                # Access agents by index since abcEconomics groups are not directly iterable
                for i in range(agent_count):
                    agent = agent_group[i]
                    # Initialize climate capabilities if not present
                    self._initialize_agent_climate_capabilities(agent)
                    
                    # Apply stress
                    if stress_type == 'chronic':
                        self._apply_chronic_stress_to_agent(agent, stress_factor, stress_target)
                    else:
                        self._apply_acute_stress_to_agent(agent, stress_factor, stress_target)
                
                print(f"    Applied {stress_target} {stress_type} stress to {agent_count} {agent_type} agents (factor: {stress_factor})")
            except Exception as e:
                print(f"    Could not apply {stress_type} stress to {agent_type}: {e}")

    def _initialize_agent_climate_capabilities(self, agent):
        """Initialize climate stress capabilities for an individual agent."""
        if not hasattr(agent, 'base_output_quantity'):
            current_output = getattr(agent, 'current_output_quantity')
            agent.base_output_quantity = current_output
        if not hasattr(agent, 'base_overhead'):
            current_overhead = getattr(agent, 'current_overhead')
            agent.base_overhead = current_overhead
        if not hasattr(agent, 'chronic_productivity_stress_accumulated'):
            agent.chronic_productivity_stress_accumulated = 1.0
        if not hasattr(agent, 'chronic_overhead_stress_accumulated'):
            agent.chronic_overhead_stress_accumulated = 1.0
        if not hasattr(agent, 'climate_stressed'):
            agent.climate_stressed = False

    def _apply_acute_stress_to_agent(self, agent, stress_factor: float, stress_target: str):
        """Apply acute climate stress to an individual agent."""
        agent.climate_stressed = True
        if stress_target == 'productivity':
            agent.current_output_quantity = agent.base_output_quantity * stress_factor * agent.chronic_productivity_stress_accumulated
            print(f"      {agent.__class__.__name__} {agent.id}: CLIMATE STRESS! Production: {agent.base_output_quantity:.2f} -> {agent.current_output_quantity:.2f}")
        elif stress_target == 'overhead':
            if hasattr(agent, 'current_overhead'):
                agent.current_overhead = agent.base_overhead * stress_factor * agent.chronic_overhead_stress_accumulated
                print(f"      {agent.__class__.__name__} {agent.id}: CLIMATE STRESS! Overhead: {agent.base_overhead:.2f} -> {agent.current_overhead:.2f}")
            else:
                print(f"      {agent.__class__.__name__} {agent.id}: No overhead attribute to apply stress to")

    def _apply_chronic_stress_to_agent(self, agent, stress_factor: float, stress_target: str):
        """Apply chronic climate stress to an individual agent."""
        if stress_target == 'productivity':
            agent.chronic_productivity_stress_accumulated *= stress_factor
            if hasattr(agent, 'current_output_quantity'):
                agent.current_output_quantity = agent.base_output_quantity * agent.chronic_productivity_stress_accumulated
                print(f"      {agent.__class__.__name__} {agent.id}: Chronic productivity stress applied (factor: {stress_factor:.2f})")
        elif stress_target == 'overhead':
            agent.chronic_overhead_stress_accumulated *= stress_factor
            if hasattr(agent, 'current_overhead'):
                agent.current_overhead = agent.base_overhead * agent.chronic_overhead_stress_accumulated
                print(f"      {agent.__class__.__name__} {agent.id}: Chronic overhead stress applied (factor: {stress_factor:.2f})")
            else:
                print(f"      {agent.__class__.__name__} {agent.id}: No overhead attribute to apply chronic stress to")

    def _reset_agent_climate_stress(self, agent):
        """Reset climate stress to chronic level for an individual agent."""
        if agent.climate_stressed:
            agent.climate_stressed = False
            if hasattr(agent, 'current_output_quantity'):
                agent.current_output_quantity = agent.base_output_quantity * agent.chronic_productivity_stress_accumulated
            if hasattr(agent, 'current_overhead'):
                agent.current_overhead = agent.base_overhead * agent.chronic_overhead_stress_accumulated
            print(f"      {agent.__class__.__name__} {agent.id}: Climate stress cleared")
    
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