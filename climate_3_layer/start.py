""" Climate 3-layer model simulation
This is a closed-world 3-layer supply-chain:
- commodity producers (layer 1)
- intermediary firms (layer 2) 
- final goods and services firms (layer 3)
as well as households, who both consume from the output of the firms and are employed by the firms.

Acute and chronic physical climate stress will be unequally applied to the firms 
to examine the macroeconomic effects.
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


simulation_parameters = {
    'name': 'climate_3_layer',
    'trade_logging': 'off',
    'random_seed': None,
    'rounds': 20,
    'climate_stress_enabled': True,
    'acute_stress_probability': 0.1,  # 10% chance per round
    'chronic_stress_factor': 0.95     # 5% productivity reduction over time
}

def main(simulation_parameters):
    w = Simulation(path='auto')  # Re-enable logging to get results

    # Build agents for each layer
    commodity_producers = w.build_agents(CommodityProducer, 'commodity_producer', 3)
    intermediary_firms = w.build_agents(IntermediaryFirm, 'intermediary_firm', 2)
    final_goods_firms = w.build_agents(FinalGoodsFirm, 'final_goods_firm', 2)
    households = w.build_agents(Household, 'household', 20)  # Many more households than firms
    
    print(f"Starting climate 3-layer simulation with:")
    print(f"  {len(commodity_producers)} commodity producers")
    print(f"  {len(intermediary_firms)} intermediary firms") 
    print(f"  {len(final_goods_firms)} final goods firms")
    print(f"  {len(households)} households")
    
    # Manual result tracking
    results = {
        'round': [],
        'total_production': [],
        'climate_events': []
    }

    for r in range(simulation_parameters['rounds']):
        print(f"Round {r}...", end=" ")
        w.advance_round(r)
        
        # Apply climate stress if enabled
        climate_event = None
        if simulation_parameters['climate_stress_enabled']:
            import random
            if random.random() < simulation_parameters['acute_stress_probability']:
                climate_event = 'acute_stress'
                print(f"[ACUTE CLIMATE STRESS]", end=" ")
            
            # Apply chronic stress
            commodity_producers.apply_chronic_stress(simulation_parameters['chronic_stress_factor'])
            intermediary_firms.apply_chronic_stress(simulation_parameters['chronic_stress_factor'])
            final_goods_firms.apply_chronic_stress(simulation_parameters['chronic_stress_factor'])
        
        # Labor market
        households.refresh_services('labor', derived_from='labor_endowment', units=1)
        households.sell_labor()
        
        # Layer 1: Commodity producers buy labor and produce
        commodity_producers.buy_labor()
        if climate_event == 'acute_stress':
            commodity_producers.apply_acute_stress()
        commodity_producers.production()
        commodity_producers.panel_log(goods=['commodity'])
        
        # Layer 2: Intermediary firms buy commodities and labor, then produce
        commodity_producers.sell_commodities()
        intermediary_firms.buy_commodities()
        intermediary_firms.buy_labor()
        if climate_event == 'acute_stress':
            intermediary_firms.apply_acute_stress()
        intermediary_firms.production()
        intermediary_firms.panel_log(goods=['intermediate_good'])
        
        # Layer 3: Final goods firms buy intermediate goods and labor, then produce
        intermediary_firms.sell_intermediate_goods()
        final_goods_firms.buy_intermediate_goods()
        final_goods_firms.buy_labor()
        if climate_event == 'acute_stress':
            final_goods_firms.apply_acute_stress()
        final_goods_firms.production()
        final_goods_firms.panel_log(goods=['final_good'])
        
        # Households buy final goods and consume
        final_goods_firms.sell_final_goods()
        households.buy_final_goods()
        households.panel_log(goods=['final_good'])
        households.consumption()
        
        # Track results
        results['round'].append(r)
        results['climate_events'].append(climate_event)
        print("completed")
    
    print("\nFinalizing simulation...")
    w.finalize()
    print("Simulation completed!")
    print(f"Results saved to: {w.path}")
    
    # Print summary
    climate_events_count = len([e for e in results['climate_events'] if e is not None])
    print(f"\nSummary: Successfully completed {len(results['round'])} rounds")
    print(f"Climate events occurred: {climate_events_count}")
    
    return results


if __name__ == '__main__':
    results = main(simulation_parameters)
    print(f"Final result summary: {len(results['round'])} rounds completed") 