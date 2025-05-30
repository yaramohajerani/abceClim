""" Agents are now build according
to the line in agents_parameter.csv
"""
import sys
import os
# Add the root directory to Python path to find local abcEconomics
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from abcEconomics import Simulation
from firm import Firm
from household import Household


simulation_parameters = {'name': 'name',
                         'trade_logging': 'off',
                         'random_seed': None,
                         'rounds': 10}

def main(simulation_parameters):
    w = Simulation(path='auto')  # Re-enable logging to get results

    firms = w.build_agents(Firm, 'firm', 2)
    households = w.build_agents(Household, 'household', 2)
    
    print(f"Starting simulation with {len(firms)} firms and {len(households)} households")
    
    # Manual result tracking
    results = {
        'round': [],
        'firm_money': [],
        'firm_goods': [],
        'household_money': [],
        'household_goods': []
    }

    for r in range(simulation_parameters['rounds']):
        print(f"Round {r}...", end=" ")
        w.advance_round(r)
        
        households.refresh_services('labor', derived_from='labor_endowment', units=5)
        households.sell_labor()
        firms.buy_inputs()
        firms.production()
        firms.panel_log(goods=['consumption_good', 'intermediate_good'])
        firms.sell_intermediary_goods()
        households.buy_intermediary_goods()
        households.panel_log(goods=['consumption_good'])
        households.consumption()
        
        # Collect manual results (this requires accessing individual agents)
        # For now, let's just track that the round completed
        results['round'].append(r)
        print("completed")
    
    print("\nFinalizing simulation...")
    w.finalize()
    print("Simulation completed!")
    print(f"Results saved to: {w.path}")
    
    # Print summary
    print(f"\nSummary: Successfully completed {len(results['round'])} rounds")
    
    return results


if __name__ == '__main__':
    results = main(simulation_parameters)
    print(f"Final result: {results}")
