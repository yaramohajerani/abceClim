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
        self.agent_climate_data: Dict[tuple, Dict[str, float]] = {}
        
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
        """Reset all acute climate stress effects for all agents."""
        print("  Resetting acute climate stress...")
        
        for agent_type, agent_group in agent_groups.items():
            try:
                agent_count = agent_group.num_agents
                scheduler = agent_group._scheduler
                
                for i in range(agent_count):
                    # Get agent name and access real agent object
                    agent_name = (agent_group.agent_name_prefix, i)
                    
                    if hasattr(scheduler, 'agents') and agent_name in scheduler.agents:
                        real_agent = scheduler.agents[agent_name]
                    else:
                        real_agent = agent_group[i]
                    
                    agent_key = (agent_type, i)
                    
                    if agent_key in self.agent_climate_data:
                        climate_data = self.agent_climate_data[agent_key]
                        
                        if climate_data.get('climate_stressed', False):
                            climate_data['climate_stressed'] = False
                            
                            # Reset to chronic level
                            if hasattr(real_agent, 'current_output_quantity'):
                                base_output = climate_data['base_output_quantity']
                                chronic_accumulated = climate_data['chronic_productivity_stress_accumulated']
                                real_agent.current_output_quantity = base_output * chronic_accumulated
                                    
                            if hasattr(real_agent, 'current_overhead'):
                                base_overhead = climate_data['base_overhead']
                                chronic_accumulated = climate_data['chronic_overhead_stress_accumulated']
                                real_agent.current_overhead = base_overhead * chronic_accumulated
                                
                            print(f"      {agent_type} {i}: Climate stress cleared")
                            
            except Exception as e:
                print(f"    Could not reset climate stress for {agent_type}: {e}")
                raise  # Re-raise to see the actual error
    
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
                
                # Access real agents through the scheduler's agent storage
                scheduler = agent_group._scheduler
                
                for i in range(agent_count):
                    # Get agent name using the group's naming convention
                    agent_name = (agent_group.agent_name_prefix, i)
                    
                    # Access the real agent object from the scheduler
                    if hasattr(scheduler, 'agents') and agent_name in scheduler.agents:
                        real_agent = scheduler.agents[agent_name]
                    else:
                        # Fallback to the Action object approach if direct access fails
                        real_agent = agent_group[i]
                    
                    # Initialize climate capabilities if not present
                    self._initialize_agent_climate_capabilities(agent_type, i, real_agent)
                    
                    # Apply stress
                    if stress_type == 'chronic':
                        self._apply_chronic_stress_to_agent(agent_type, i, real_agent, stress_factor, stress_target)
                    else:
                        self._apply_acute_stress_to_agent(agent_type, i, real_agent, stress_factor, stress_target)
                
                print(f"    Applied {stress_target} {stress_type} stress to {agent_count} {agent_type} agents (factor: {stress_factor})")
            except Exception as e:
                print(f"    Could not apply {stress_type} stress to {agent_type}: {e}")
                raise  # Re-raise to see the actual error

    def _initialize_agent_climate_capabilities(self, agent_type, agent_id, agent):
        """Initialize climate stress capabilities for an individual agent."""
        # Use the agent type and index directly to avoid Action object issues
        agent_key = (agent_type, agent_id)
        
        if agent_key not in self.agent_climate_data:
            # Get the base values from the agent directly
            try:
                base_output = getattr(agent, 'base_output_quantity', getattr(agent, 'current_output_quantity'))
                base_overhead = getattr(agent, 'base_overhead', getattr(agent, 'current_overhead'))
                
                # Convert to float to avoid Action objects
                if hasattr(base_output, '__float__'):
                    base_output = float(base_output)
                else:
                    base_output = 1.0  # Default fallback
                    
                if hasattr(base_overhead, '__float__'):
                    base_overhead = float(base_overhead)  
                else:
                    base_overhead = 0.0  # Default fallback
                
                self.agent_climate_data[agent_key] = {
                    'base_output_quantity': base_output,
                    'base_overhead': base_overhead,
                    'chronic_productivity_stress_accumulated': 1.0,
                    'chronic_overhead_stress_accumulated': 1.0,
                    'climate_stressed': False
                }
                
                print(f"        Initialized climate data for {agent_type} {agent_id}: output={base_output:.2f}, overhead={base_overhead:.2f}")
                
            except Exception as e:
                print(f"        Could not initialize {agent_type} {agent_id}: {e}")

    def _apply_acute_stress_to_agent(self, agent_type, agent_id, agent, stress_factor: float, stress_target: str):
        """Apply acute climate stress to an individual agent."""
        agent_key = (agent_type, agent_id)
        if agent_key not in self.agent_climate_data:
            return
            
        climate_data = self.agent_climate_data[agent_key]
        climate_data['climate_stressed'] = True
        
        if stress_target == 'productivity':
            base_output = climate_data['base_output_quantity']
            chronic_accumulated = climate_data['chronic_productivity_stress_accumulated']
            new_output = base_output * float(stress_factor) * chronic_accumulated
            
            # Apply to agent - crash if it fails so we can see the error
            agent.current_output_quantity = new_output
            print(f"      {agent_type} {agent_id}: CLIMATE STRESS! Production: {base_output:.2f} -> {new_output:.2f}")
                
        elif stress_target == 'overhead':
            if hasattr(agent, 'current_overhead'):
                base_overhead = climate_data['base_overhead']
                chronic_accumulated = climate_data['chronic_overhead_stress_accumulated']
                new_overhead = base_overhead * float(stress_factor) * chronic_accumulated
                
                agent.current_overhead = new_overhead
                print(f"      {agent_type} {agent_id}: CLIMATE STRESS! Overhead: {base_overhead:.2f} -> {new_overhead:.2f}")
            else:
                print(f"      {agent_type} {agent_id}: No overhead attribute to apply stress to")

    def _apply_chronic_stress_to_agent(self, agent_type, agent_id, agent, stress_factor: float, stress_target: str):
        """Apply chronic climate stress to an individual agent."""
        agent_key = (agent_type, agent_id)
        if agent_key not in self.agent_climate_data:
            return
            
        climate_data = self.agent_climate_data[agent_key]
        
        if stress_target == 'productivity':
            climate_data['chronic_productivity_stress_accumulated'] *= stress_factor
            
            # Apply to agent's actual attributes if possible
            if hasattr(agent, 'current_output_quantity'):
                base_output = climate_data['base_output_quantity']
                chronic_stress = climate_data['chronic_productivity_stress_accumulated']
                agent.current_output_quantity = base_output * chronic_stress
                print(f"      {agent_type} {agent_id}: Chronic productivity stress applied (factor: {stress_factor:.2f})")
                    
        elif stress_target == 'overhead':
            climate_data['chronic_overhead_stress_accumulated'] *= stress_factor
            
            if hasattr(agent, 'current_overhead'):
                base_overhead = climate_data['base_overhead']
                chronic_stress = climate_data['chronic_overhead_stress_accumulated']
                agent.current_overhead = base_overhead * chronic_stress
                print(f"      {agent_type} {agent_id}: Chronic overhead stress applied (factor: {stress_factor:.2f})")

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
                        'productivity_stress_factor': event_data['productivity_stress_factor'],
                        'overhead_stress_factor': event_data['overhead_stress_factor']
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