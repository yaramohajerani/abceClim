"""
Simple Climate Economic Model Example

This demonstrates how the Climate Framework can be easily integrated
with any agent-based economic model to add geographical distribution,
climate stress modeling, and visualization capabilities.
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
        # Households don't need climate capabilities in this simple model

def run_simple_climate_model():
    """Run a simple climate economic model using the Climate Framework."""
    
    # Simulation parameters
    simulation_parameters = {
        'name': 'simple_climate_model',
        'trade_logging': 'off',
        'random_seed': 42,
        'rounds': 3,  # Reduce rounds for debugging
        'climate_stress_enabled': True,
        'acute_stress_probability': 0.2,  # 20% chance per round
        'chronic_stress_factor': 0.95,   # 5% productivity reduction over time
        'create_visualizations': True
    }
    
    print("Creating simulation...")
    # Create simulation
    w = Simulation(path='auto')
    
    print("Building agents...")
    # Build agents
    firms = w.build_agents(SimpleFirm, 'firm', 5)
    households = w.build_agents(SimpleHousehold, 'household', 15)
    
    print(f"Built agents: firms={type(firms)}, households={type(households)}")
    
    # Debug: Check what we actually have
    print(f"Firms num_agents: {firms.num_agents}")
    print(f"Households num_agents: {households.num_agents}")
    
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
    try:
        climate_framework.assign_geographical_locations(agent_groups)
        print("Geographical assignment completed successfully!")
    except Exception as e:
        print(f"Error in geographical assignment: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    # Get agent counts for display
    firm_count = firms.num_agents
    household_count = households.num_agents
    
    print(f"\nStarting simple climate model with:")
    print(f"  {firm_count} firms")
    print(f"  {household_count} households")
    print(f"  Distributed across 5 continents")
    
    # Run simulation
    for r in range(simulation_parameters['rounds']):
        print(f"\nRound {r}...")
        
        try:
            print(f"  Advancing round {r}...")
            w.advance_round(r)
            print(f"  Round {r} advanced successfully")
            
            # Apply climate stress using the framework
            climate_events = {}
            if simulation_parameters['climate_stress_enabled']:
                print(f"  Applying climate stress...")
                climate_events = climate_framework.apply_geographical_climate_stress(agent_groups)
                print(f"  Climate events: {climate_events}")
            
            # Simple economic activities
            print(f"  Firms producing...")
            firms.produce()
            print(f"  Firms selling...")
            firms.sell_goods()
            
            # Collect data using the framework
            print(f"  Collecting data...")
            climate_framework.collect_round_data(r, agent_groups, climate_events)
            
            print(f"Round {r} completed successfully!")
            
        except Exception as e:
            print(f"Error in round {r}: {e}")
            import traceback
            traceback.print_exc()
            break
    
    # Finalize simulation
    print("\nFinalizing simulation...")
    try:
        w.finalize()
        print("Simulation finalized successfully!")
    except Exception as e:
        print(f"Error finalizing simulation: {e}")
        import traceback
        traceback.print_exc()
    
    # Create visualizations
    if simulation_parameters['create_visualizations']:
        try:
            print("Creating visualizations using Climate Framework...")
            climate_framework.create_visualizations(
                agent_groups,
                model_name="Simple Climate Economic Model",
                save_path="simple_climate_model_analysis.png"
            )
            
            # Export data
            climate_framework.export_data("simple_climate_model_data.csv")
            print("Visualizations and data export completed!")
        except Exception as e:
            print(f"Error creating visualizations: {e}")
            import traceback
            traceback.print_exc()
    
    # Print summary
    try:
        total_climate_events = sum(len(events) for events in climate_framework.results['climate_events'])
        print(f"\nSummary: Successfully completed {len(climate_framework.results['round'])} rounds")
        print(f"Total climate events occurred: {total_climate_events}")
    except Exception as e:
        print(f"Error creating summary: {e}")
    
    return climate_framework.results

if __name__ == '__main__':
    results = run_simple_climate_model()
    print(f"Simple model completed with {len(results['round'])} rounds!")
    print("\nThis demonstrates how any economic model can easily use the Climate Framework!")
    print("Key benefits:")
    print("  ✓ Automatic geographical distribution")
    print("  ✓ Built-in climate stress modeling")
    print("  ✓ Comprehensive visualizations")
    print("  ✓ Data export for analysis")
    print("  ✓ Reusable across different models") 