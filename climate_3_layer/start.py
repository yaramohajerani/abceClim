""" Climate 3-layer model simulation
This is a closed-world 3-layer supply-chain:
- commodity producers (layer 1)
- intermediary firms (layer 2) 
- final goods and services firms (layer 3)
as well as households, who both consume from the output of the firms and are employed by the firms.

Acute and chronic physical climate stress will be unequally applied to the firms 
to examine the macroeconomic effects.

This example uses the reusable Climate Framework for geographical distribution,
climate stress modeling, and visualization.
"""
import sys
import os
# Add the root directory to Python path to find local abcEconomics
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from abcEconomics import Simulation
from commodity_producer import CommodityProducer
from intermediary_firm import IntermediaryFirm
from final_goods_firm import FinalGoodsFirm
from household import Household

# Import the reusable Climate Framework
from climate_framework import create_climate_framework

simulation_parameters = {
    'name': 'climate_3_layer_geo',
    'trade_logging': 'off',
    'random_seed': 42,  # Fixed seed for reproducible results
    'rounds': 8,  # Reduced for reliable completion
    'climate_stress_enabled': True,
    'acute_stress_probability': 0.15,  # 15% chance per round
    'chronic_stress_factor': 0.96,     # 4% productivity reduction over time
    'geographical_effects': True,      # Enable continent-specific climate effects
    'create_visualizations': True     # Enable visualization output
}

def main(simulation_parameters):
    simulation_path = 'result_climate_3_layer'
    w = Simulation(path=simulation_path)  # Use specific path for better organization
    
    # Get the actual path that abcEconomics created (handles increments like resultI, resultII, etc.)
    actual_simulation_path = w.path
    print(f"Simulation will save to: {actual_simulation_path}")

    # Build agents for each layer with geographical distribution
    commodity_producers = w.build_agents(CommodityProducer, 'commodity_producer', 3)
    intermediary_firms = w.build_agents(IntermediaryFirm, 'intermediary_firm', 2)
    final_goods_firms = w.build_agents(FinalGoodsFirm, 'final_goods_firm', 2)
    households = w.build_agents(Household, 'household', 20)  # Many more households than firms
    
    # Create the climate framework
    climate_framework = create_climate_framework(simulation_parameters)
    
    # Organize agents into groups for the framework
    agent_groups = {
        'commodity_producer': commodity_producers,
        'intermediary_firm': intermediary_firms,
        'final_goods_firm': final_goods_firms,
        'household': households
    }
    
    # Assign geographical locations using the framework
    print("Assigning geographical locations...")
    climate_framework.assign_geographical_locations(agent_groups)
    
    print(f"\nStarting climate 3-layer geographical simulation with:")
    print(f"  {commodity_producers.num_agents} commodity producers")
    print(f"  {intermediary_firms.num_agents} intermediary firms") 
    print(f"  {final_goods_firms.num_agents} final goods firms")
    print(f"  {households.num_agents} households")
    print(f"  Distributed across 5 continents")

    # Set up data collection for different agent types
    goods_to_track = {
        'commodity_producer': ['commodity'],
        'intermediary_firm': ['intermediate_good'],
        'final_goods_firm': ['final_good'],
        'household': ['final_good']
    }

    for r in range(simulation_parameters['rounds']):
        print(f"Round {r}...", end=" ")
        w.advance_round(r)
        
        # Apply geographical climate stress using the framework
        climate_events = {}
        if simulation_parameters['climate_stress_enabled']:
            climate_events = climate_framework.apply_geographical_climate_stress(agent_groups)
        
        # Labor market
        print(f"  Labor market...")
        households.refresh_services('labor', derived_from='labor_endowment', units=1)
        households.sell_labor()
        print(f"    Labor offered by households")
        
        # Layer 1: Commodity producers buy labor and produce
        print(f"  Layer 1: Commodity producers...")
        commodity_producers.buy_labor()
        commodity_producers.production()
        commodity_producers.panel_log(goods=['commodity'])
        
        # Layer 2: Intermediary firms buy commodities and labor, then produce
        print(f"  Layer 2: Intermediary firms...")
        commodity_producers.sell_commodities()
        intermediary_firms.buy_commodities()
        intermediary_firms.buy_labor()
        intermediary_firms.production()
        intermediary_firms.panel_log(goods=['intermediate_good'])
        
        # Layer 3: Final goods firms buy intermediate goods and labor, then produce
        print(f"  Layer 3: Final goods firms...")
        intermediary_firms.sell_intermediate_goods()
        final_goods_firms.buy_intermediate_goods()
        final_goods_firms.buy_labor()
        final_goods_firms.production()
        final_goods_firms.panel_log(goods=['final_good'])
        
        # Households buy final goods and consume
        print(f"  Consumer market...")
        final_goods_firms.sell_final_goods()
        households.buy_final_goods()
        households.panel_log(goods=['final_good'])
        households.consumption()
        
        # Collect data using the new framework method
        climate_framework.collect_panel_data(agent_groups, goods_to_track)
        
        print("completed")
    
    print("\nFinalizing simulation...")
    w.finalize()
    print("Simulation completed!")
    print(f"Results saved to: {actual_simulation_path}")
    
    # Create visualizations using the updated framework
    if simulation_parameters['create_visualizations']:
        print("Creating visualizations using Climate Framework...")
        climate_framework.create_simplified_visualizations(
            agent_groups, 
            simulation_path=actual_simulation_path,
            model_name="Climate 3-Layer Supply Chain Model"
        )
        
        # Export climate summary using new method
        climate_framework.export_climate_summary(actual_simulation_path, "climate_3_layer_summary.csv")
    
    # Print summary
    total_climate_events = sum(len(events) for events in climate_framework.climate_events_history)
    print(f"\nSummary: Successfully completed {len(climate_framework.climate_events_history)} rounds")
    print(f"Total climate events occurred: {total_climate_events}")
    print(f"Geographical assignments: {len(climate_framework.geographical_assignments)} agent types")
    
    return climate_framework


if __name__ == '__main__':
    results = main(simulation_parameters)
    print(f"Final result summary: {len(results.climate_events_history)} rounds completed") 