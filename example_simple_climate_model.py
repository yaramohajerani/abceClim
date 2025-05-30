"""
Simple Climate Economic Model Example

This demonstrates how the simplified Climate Framework can be easily integrated
with any agent-based economic model using abcEconomics' built-in functionality.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from abcEconomics import Simulation, Agent, Firm
from climate_framework import create_climate_framework, add_climate_capabilities

# Example: Simple firm with climate capabilities using the decorator
@add_climate_capabilities
class SimpleFirm(Agent, Firm):
    def init(self):
        print(f"    Initializing SimpleFirm {self.id}")
        self.create('money', 50)
        self.current_output_quantity = 10.0  # Will be used by climate framework
        self.create('goods', self.current_output_quantity)
        print(f"    SimpleFirm {self.id} initialized with {self.possession('money')} money and {self.possession('goods')} goods")
    
    def produce(self):
        # Simple production that can be affected by climate stress
        print(f"    Firm {self.id} producing {self.current_output_quantity} goods")
        self.create('goods', self.current_output_quantity)
    
    def sell_goods(self):
        # Simple selling mechanism
        goods_to_sell = self.possession('goods')
        if goods_to_sell > 0:
            # In a real model, this would be to other agents
            sell_amount = goods_to_sell * 0.5
            print(f"    Firm {self.id} selling {sell_amount} goods (had {goods_to_sell})")
            self.destroy('goods', sell_amount)  # Simulate selling half

class SimpleHousehold(Agent):
    def init(self):
        print(f"    Initializing SimpleHousehold {self.id}")
        self.create('money', 20)
        print(f"    SimpleHousehold {self.id} initialized with {self.possession('money')} money")

def run_simple_climate_model():
    """Run a simple climate economic model using the simplified Climate Framework."""
    
    # Simulation parameters
    simulation_parameters = {
        'name': 'simple_climate_model',
        'trade_logging': 'off',
        'random_seed': 42,
        'rounds': 5,
        'climate_stress_enabled': True,
        'acute_stress_probability': 0.3,  # 30% chance per round
        'create_visualizations': True
    }
    
    print("Creating simulation...")
    # Create simulation
    w = Simulation(path='simple_model_output')
    
    print("Building agents...")
    # Build agents
    firms = w.build_agents(SimpleFirm, 'firm', 8)
    households = w.build_agents(SimpleHousehold, 'household', 20)
    
    print(f"Built agents: {firms.num_agents} firms, {households.num_agents} households")
    
    # Create the climate framework
    print("Creating climate framework...")
    climate_framework = create_climate_framework(simulation_parameters)
    
    # Organize agents for the framework
    agent_groups = {
        'firm': firms,
        'household': households
    }
    
    # Assign geographical locations
    print("Assigning geographical locations...")
    climate_framework.assign_geographical_locations(agent_groups)
    
    print(f"\nStarting simple climate model with:")
    print(f"  {firms.num_agents} firms")
    print(f"  {households.num_agents} households")
    print(f"  Distributed across 5 continents")
    print(f"  Using abcEconomics' panel_log for data collection")
    
    # Set up data collection using abcEconomics' panel_log
    goods_to_track = {
        'firm': ['money', 'goods'],
        'household': ['money']
    }
    
    # Run simulation
    for r in range(simulation_parameters['rounds']):
        print(f"\nRound {r}...")
        
        print(f"  Advancing round...")
        w.advance_round(r)
        
        # Apply climate stress using the framework
        climate_events = {}
        if simulation_parameters['climate_stress_enabled']:
            print(f"  Applying climate stress...")
            climate_events = climate_framework.apply_geographical_climate_stress(agent_groups)
        
        # Simple economic activities
        print(f"  Firms producing...")
        firms.produce()
        print(f"  Firms selling...")
        firms.sell_goods()
        
        # Collect data using abcEconomics' panel_log (the proper way!)
        print(f"  Collecting data using abcEconomics panel_log...")
        climate_framework.collect_panel_data(agent_groups, goods_to_track)
        
        print(f"Round {r} completed successfully!")
    
    # Finalize simulation
    print("\nFinalizing simulation...")
    w.finalize()
    print("Simulation finalized successfully!")
    
    # Create simplified visualizations focused on climate aspects
    if simulation_parameters['create_visualizations']:
        try:
            print("Creating climate visualizations...")
            climate_framework.create_simplified_visualizations(
                agent_groups,
                simulation_path="simple_model_output",
                model_name="Simple Climate Economic Model"
            )
            
            # Export climate summary
            climate_framework.export_climate_summary("simple_climate_summary.csv")
            print("Climate visualizations and summary completed!")
        except Exception as e:
            print(f"Error creating visualizations: {e}")
            import traceback
            traceback.print_exc()
    
    # Print summary
    try:
        total_climate_events = sum(len(events) for events in climate_framework.climate_events_history)
        print(f"\nSummary: Successfully completed {len(climate_framework.climate_events_history)} rounds")
        print(f"Total climate events occurred: {total_climate_events}")
        print(f"Geographical assignments: {len(climate_framework.geographical_assignments)} agent types")
    except Exception as e:
        print(f"Error creating summary: {e}")
    
    return climate_framework

if __name__ == '__main__':
    climate_framework = run_simple_climate_model()
    print(f"\nSimple model completed with {len(climate_framework.climate_events_history)} rounds!")
    print("\nKey improvements in simplified approach:")
    print("  ✓ Uses abcEconomics' panel_log() for data collection")
    print("  ✓ Focuses on climate-specific capabilities")
    print("  ✓ Works with abcEconomics' group-based design")
    print("  ✓ Generates climate-focused visualizations")
    print("  ✓ Exports geographical and climate summaries")
    print("  ✓ Much more robust and compatible with abcEconomics")
    print("\nFor economic data analysis, check the abcEconomics output files in 'simple_model_output/'!") 