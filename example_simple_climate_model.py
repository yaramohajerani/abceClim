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
        self.base_output_quantity = 10.0     # Store base production
        self.create('goods', self.current_output_quantity)
        self.climate_stressed = False        # Track if currently stressed
        print(f"    SimpleFirm {self.id} initialized with {self.possession('money')} money and {self.possession('goods')} goods")
    
    def apply_climate_stress(self, stress_factor):
        """Apply climate stress by reducing production capacity"""
        self.climate_stressed = True
        self.current_output_quantity = self.base_output_quantity * stress_factor
        print(f"    Firm {self.id}: CLIMATE STRESS applied! Production reduced to {self.current_output_quantity:.1f} (was {self.base_output_quantity})")
    
    def reset_climate_stress(self):
        """Reset production to normal levels"""
        if self.climate_stressed:
            self.climate_stressed = False
            self.current_output_quantity = self.base_output_quantity
            print(f"    Firm {self.id}: Climate stress cleared, production restored to {self.current_output_quantity}")
    
    def produce(self):
        # Production based on current climate-adjusted capacity
        print(f"    Firm {self.id} producing {self.current_output_quantity} goods (stressed: {self.climate_stressed})")
        self.create('goods', self.current_output_quantity)
    
    def sell_goods(self):
        # Simple selling mechanism
        goods_to_sell = self.possession('goods')
        if goods_to_sell > 0:
            # In a real model, this would be to other agents
            sell_amount = goods_to_sell * 0.5
            print(f"    Firm {self.id} selling {sell_amount} goods (had {goods_to_sell})")
            self.destroy('goods', sell_amount)  # Simulate selling half
    
    def pay_wages_to_employees(self, wage_multiplier):
        """Pay wages to employees based on current production level"""
        # Calculate wage multiplier based on current vs normal production
        base_wage = 5.0
        actual_wage = base_wage * wage_multiplier
        
        # Store wage info for group-level payment
        self.current_wage_payment = actual_wage
        
        # Firm pays out wages (costs) 
        # In a simplified model, assume 2.5 employees per firm on average
        employees_per_firm = 2.5  
        total_wages = actual_wage * employees_per_firm
        if self.possession('money') >= total_wages:
            self.destroy('money', total_wages)
            
        print(f"    Firm {self.id} set wage rate: {actual_wage:.1f} (production factor: {wage_multiplier:.1f})")
        return actual_wage

class SimpleHousehold(Agent):
    def init(self):
        print(f"    Initializing SimpleHousehold {self.id}")
        self.create('money', 20)
        self.employer_firm_id = None  # Will be assigned an employer
        self.base_wage = 5            # Base wage per round
        self.current_wage = 5         # Current wage (affected by firm performance)
        print(f"    SimpleHousehold {self.id} initialized with {self.possession('money')} money")
    
    def assign_employer(self, firm_id):
        """Assign this household to work for a specific firm"""
        self.employer_firm_id = firm_id
        print(f"    Household {self.id} assigned to work for Firm {firm_id}")
    
    def receive_wages(self, wage_amount):
        """Receive wages from employer firm"""
        self.current_wage = wage_amount
        self.create('money', wage_amount)
        print(f"    Household {self.id} received {wage_amount:.1f} wages (total money: {self.possession('money'):.1f})")
    
    def receive_average_wages(self, average_wage):
        """Receive wages based on the average wage in the economy (group-level)"""
        # Add some randomness for individual variation
        import random
        individual_wage = average_wage * random.uniform(0.8, 1.2)
        self.current_wage = individual_wage
        self.create('money', individual_wage)
        print(f"    Household {self.id} received {individual_wage:.1f} wages from economy-wide average {average_wage:.1f}")

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
    simulation_path = 'result_simple_climate_simulation'
    w = Simulation(path=simulation_path)
    
    # Get the actual path that abcEconomics created (handles increments like resultI, resultII, etc.)
    actual_simulation_path = w.path
    print(f"Simulation will save to: {actual_simulation_path}")
    
    print("Building agents...")
    # Build agents
    firms = w.build_agents(SimpleFirm, 'firm', 8)
    households = w.build_agents(SimpleHousehold, 'household', 20)
    
    print(f"Built agents: {firms.num_agents} firms, {households.num_agents} households")
    
    # Simplified employment: households work in the general economy
    # No need for individual assignments - we'll use economy-wide wage averages
    print("Setting up simplified employment relationships...")
    print(f"Economy setup: {households.num_agents} households work in economy with {firms.num_agents} firms")
    
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
        
        # Simple economic activities - production happens AFTER climate stress
        print(f"  Firms producing...")
        firms.produce()
        
        # Collect data RIGHT AFTER production to capture climate impact
        print(f"  Collecting post-production data...")
        climate_framework.collect_panel_data(agent_groups, goods_to_track)
        
        print(f"  Firms selling...")
        firms.sell_goods()
        
        # Pay wages based on economy-wide average production (climate-affected)
        print(f"  Calculating economy-wide wages...")
        # Calculate average production level across all firms
        total_firms = firms.num_agents
        # Use group-level method to get average production impact
        total_wage_multiplier = 0
        
        # Calculate wage multipliers using group approach
        for i in range(total_firms):
            # Use production factor: current/base output
            # Since all firms have same logic, calculate average stress effect
            pass
        
        # Simplified: Use climate stress to affect economy-wide wages
        economy_stress_factor = 1.0
        if climate_events:
            # If there are climate events, reduce wages economy-wide
            economy_stress_factor = 0.75  # 25% wage reduction during climate stress
            print(f"    Climate stress detected! Economy-wide wage factor: {economy_stress_factor}")
        else:
            print(f"    No climate stress. Normal wage factor: {economy_stress_factor}")
        
        # Pay wages using group methods
        base_wage = 5.0
        economy_wage = base_wage * economy_stress_factor
        
        # Apply wage payments to firm costs
        firms.pay_wages_to_employees(economy_stress_factor)
        
        # Apply wage income to households
        households.receive_average_wages(economy_wage)
        
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
                simulation_path=actual_simulation_path,
                model_name="Simple Climate Economic Model"
            )
            
            # Export climate summary
            climate_framework.export_climate_summary(actual_simulation_path, "simple_climate_summary.csv")
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