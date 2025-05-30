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
    'rounds': 15,
    'climate_stress_enabled': True,
    'acute_stress_probability': 0.15,  # 15% chance per round
    'chronic_stress_factor': 0.96,     # 4% productivity reduction over time
    'geographical_effects': True,      # Enable continent-specific climate effects
    'create_visualizations': True     # Enable visualization output
}

def main(simulation_parameters):
    w = Simulation(path='auto')  # Re-enable logging to get results

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
    print(f"  {len(commodity_producers)} commodity producers")
    print(f"  {len(intermediary_firms)} intermediary firms") 
    print(f"  {len(final_goods_firms)} final goods firms")
    print(f"  {len(households)} households")
    print(f"  Distributed across 5 continents")

    for r in range(simulation_parameters['rounds']):
        print(f"Round {r}...", end=" ")
        w.advance_round(r)
        
        # Apply geographical climate stress using the framework
        climate_events = {}
        if simulation_parameters['climate_stress_enabled']:
            climate_events = climate_framework.apply_geographical_climate_stress(agent_groups)
        
        # Labor market
        households.refresh_services('labor', derived_from='labor_endowment', units=1)
        households.sell_labor()
        
        # Layer 1: Commodity producers buy labor and produce
        commodity_producers.buy_labor()
        commodity_producers.production()
        commodity_producers.panel_log(goods=['commodity'])
        
        # Layer 2: Intermediary firms buy commodities and labor, then produce
        commodity_producers.sell_commodities()
        intermediary_firms.buy_commodities()
        intermediary_firms.buy_labor()
        intermediary_firms.production()
        intermediary_firms.panel_log(goods=['intermediate_good'])
        
        # Layer 3: Final goods firms buy intermediate goods and labor, then produce
        intermediary_firms.sell_intermediate_goods()
        final_goods_firms.buy_intermediate_goods()
        final_goods_firms.buy_labor()
        final_goods_firms.production()
        final_goods_firms.panel_log(goods=['final_good'])
        
        # Households buy final goods and consume
        final_goods_firms.sell_final_goods()
        households.buy_final_goods()
        households.panel_log(goods=['final_good'])
        households.consumption()
        
        # Collect data using the framework
        climate_framework.collect_round_data(r, agent_groups, climate_events)
        
        print("completed")
    
    print("\nFinalizing simulation...")
    w.finalize()
    print("Simulation completed!")
    print(f"Results saved to: {w.path}")
    
    # Create visualizations using the framework
    if simulation_parameters['create_visualizations']:
        print("Creating visualizations using Climate Framework...")
        climate_framework.create_visualizations(
            agent_groups, 
            model_name="Climate 3-Layer Supply Chain Model",
            save_path="climate_3_layer_geographical_analysis.png"
        )
        
        # Export data for further analysis
        climate_framework.export_data("climate_3_layer_simulation_data.csv")
    
    # Print summary
    total_climate_events = sum(len(events) for events in climate_framework.results['climate_events'])
    print(f"\nSummary: Successfully completed {len(climate_framework.results['round'])} rounds")
    print(f"Total climate events occurred: {total_climate_events}")
    
    return climate_framework.results


if __name__ == '__main__':
    results = main(simulation_parameters)
    print(f"Final result summary: {len(results['round'])} rounds completed") 