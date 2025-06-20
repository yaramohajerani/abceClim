""" Animation Visualizer for Climate 3-Layer Model
Standalone script for creating time-evolving animations and visualizations
from simulation output CSV files. Can be run independently after simulation completion.

Usage:
    python animation_visualizer.py <simulation_path>
"""
import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from datetime import datetime

def load_geographical_assignments(simulation_path):
    """Load geographical assignments from the climate summary CSV file."""
    climate_summary_file = os.path.join(simulation_path, 'climate_3_layer_summary.csv')
    
    if not os.path.exists(climate_summary_file):
        print(f"ERROR: Climate summary file not found: {climate_summary_file}")
        raise FileNotFoundError(f"Climate summary file missing: {climate_summary_file}")
    
    try:
        df = pd.read_csv(climate_summary_file)
        
        # Filter for geographical assignments
        geo_df = df[df['data_type'] == 'geographical_assignment']
        
        if len(geo_df) == 0:
            raise ValueError("No geographical assignments found in climate summary")
        
        # Convert to the expected format
        geographical_assignments = {}
        
        for _, row in geo_df.iterrows():
            agent_type = row['agent_type']
            agent_id = int(row['agent_id'])
            continent = row['continent']
            
            if agent_type not in geographical_assignments:
                geographical_assignments[agent_type] = {}
            
            geographical_assignments[agent_type][agent_id] = {
                'continent': continent
            }
        
        print(f"SUCCESS: Loaded geographical assignments for {len(geographical_assignments)} agent types")
        for agent_type, assignments in geographical_assignments.items():
            print(f"    {agent_type}: {len(assignments)} agents")
        
        return geographical_assignments
        
    except Exception as e:
        print(f"ERROR: Error loading geographical assignments: {e}")
        raise

def load_climate_events(simulation_path):
    """Load climate events from the climate summary CSV file."""
    climate_summary_file = os.path.join(simulation_path, 'climate_3_layer_summary.csv')
    
    if not os.path.exists(climate_summary_file):
        print(f"ERROR: Climate summary file not found: {climate_summary_file}")
        raise FileNotFoundError(f"Climate summary file missing: {climate_summary_file}")
    
    try:
        df = pd.read_csv(climate_summary_file)
        
        # Filter for climate events (exclude geographical assignments)
        events_df = df[df['data_type'] != 'geographical_assignment']
        
        if len(events_df) == 0:
            print("INFO: No climate events found in simulation")
            return []
        
        # Group events by round
        climate_events_history = []
        max_round = int(events_df['round'].max()) if len(events_df) > 0 else -1
        
        for round_num in range(max_round + 1):
            round_events = events_df[events_df['round'] == round_num]
            
            if len(round_events) > 0:
                # Convert to the expected format - group by event_name
                events_dict = {}
                
                for event_name in round_events['event_name'].unique():
                    event_rows = round_events[round_events['event_name'] == event_name]
                    
                    if len(event_rows) > 0:
                        first_row = event_rows.iloc[0]
                        continents_affected = list(event_rows['continent'].unique())
                        
                        # Extract agent types from the agent_types field
                        agent_types = []
                        if 'agent_types' in first_row and pd.notna(first_row['agent_types']) and first_row['agent_types'] != '':
                            agent_types = first_row['agent_types'].split(',')
                        
                        events_dict[event_name] = {
                            'type': 'configurable_shock',
                            'rule_name': first_row['data_type'],
                            'agent_types': agent_types,
                            'continents': continents_affected,
                            'productivity_stress_factor': float(first_row['productivity_stress_factor']),
                            'overhead_stress_factor': float(first_row['overhead_stress_factor']),
                            'affected_agents': {}
                        }
                
                climate_events_history.append(events_dict)
            else:
                climate_events_history.append({})
        
        total_events = sum(len(events) for events in climate_events_history)
        print(f"SUCCESS: Loaded climate events: {total_events} events across {len(climate_events_history)} rounds")
        
        # Show event summary
        for round_num, events in enumerate(climate_events_history):
            if events:
                event_names = list(events.keys())
                print(f"    Round {round_num}: {event_names}")
        
        return climate_events_history
        
    except Exception as e:
        print(f"ERROR: Error loading climate events: {e}")
        import traceback
        traceback.print_exc()
        raise

class ClimateFrameworkFromData:
    """Simple climate framework that loads data from CSV files."""
    def __init__(self, geographical_assignments, climate_events_history):
        self.geographical_assignments = geographical_assignments
        self.climate_events_history = climate_events_history

def collect_simulation_data(simulation_path, round_num, climate_framework):
    """Collect data from the simulation CSV files for one round."""
    
    round_data = {
        'agents': [],
        'climate': {},
        'production': {},
        'wealth': {},
        'inventories': {},
        'overhead_costs': {},
        'debt': {},
        'pricing': {}
    }
    
    # Get actual climate events for this round from climate framework
    if round_num < len(climate_framework.climate_events_history):
        round_data['climate'] = climate_framework.climate_events_history[round_num]
    
    # Read production data from CSV files
    production_files = {
        'commodity_producer': 'panel_commodity_producer_production.csv',
        'intermediary_firm': 'panel_intermediary_firm_production.csv', 
        'final_goods_firm': 'panel_final_goods_firm_production.csv',
        'household': 'panel_household_consumption.csv'
    }
    
    # Initialize storage
    round_data['production'] = {}
    round_data['inventories'] = {}
    round_data['overhead_costs'] = {}
    round_data['debt'] = {}
    round_data['pricing'] = {}
    
    # Read data from CSV files for all agent types
    for agent_type, filename in production_files.items():
        file_path = os.path.join(simulation_path, filename)
        if os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path)
                
                # Filter for this specific round
                round_df = df[df['round'] == round_num]
                
                if len(round_df) > 0:
                    # Create agent data entries for each agent
                    for _, row in round_df.iterrows():
                        agent_id = int(row['name'].replace(agent_type, ''))
                        
                        # Check if agent is climate stressed
                        is_climate_stressed = is_agent_climate_stressed(
                            agent_type, agent_id, round_data['climate'], climate_framework
                        )
                        
                        # Get wealth (money) data
                        if agent_type == 'household':
                            wealth = row['consumption_money'] if 'consumption_money' in row else row['money']
                            debt = row['consumption_debt'] if 'consumption_debt' in row else row['debt']
                            production = 0  # Households don't produce
                            consumption = row['consumption_consumption'] if 'consumption_consumption' in row else row['consumption']
                            inventory = row['cumulative_inventory']
                            overhead = 0  # Households don't have overhead
                            price = 0     # Households don't set prices
                        else:
                            wealth = row['money']
                            debt = row['debt_created_this_round'] if 'debt_created_this_round' in row else row['debt']
                            production = row['production']
                            consumption = 0  # Firms don't consume
                            inventory = row['cumulative_inventory']
                            overhead = row['current_overhead'] if 'current_overhead' in row else row['overhead']
                            price = row['price']
                        
                        agent_data = {
                            'id': agent_id,
                            'type': agent_type,
                            'round': round_num,
                            'production': production,
                            'consumption': consumption,
                            'inventory': inventory,
                            'production_capacity': production,  # Use actual production as capacity
                            'climate_stressed': is_climate_stressed,
                            'wealth': wealth,
                            'debt': debt,
                            'overhead': overhead,
                            'price': price,
                            'continent': get_agent_continent(agent_type, agent_id, climate_framework)
                        }
                        
                        round_data['agents'].append(agent_data)
                    
                    # Aggregate data by layer - ONLY from actual data, no hardcoding
                    if agent_type == 'household':
                        # Household data
                        total_consumption = round_df['consumption'].sum()
                        total_inventory = round_df['cumulative_inventory'].sum()
                        total_debt = round_df['debt'].sum()
                        
                        round_data['production']['household'] = total_consumption  # Track consumption as "production" for households
                        round_data['inventories']['household'] = total_inventory
                        round_data['overhead_costs']['household'] = 0  # Households have no overhead
                        round_data['debt']['households'] = total_debt
                        round_data['pricing']['household'] = 0  # Households don't set prices
                    else:
                        # Production agent data
                        total_production = round_df['production'].sum()
                        total_inventory = round_df['cumulative_inventory'].sum()
                        total_overhead = round_df['current_overhead'].sum() if 'current_overhead' in round_df.columns else round_df['overhead'].sum()
                        total_debt = round_df['debt_created_this_round'].sum() if 'debt_created_this_round' in round_df.columns else round_df['debt'].sum()
                        avg_price = round_df['price'].mean()
                        
                        # Map to simplified names for visualization
                        if agent_type == 'commodity_producer':
                            layer_name = 'commodity'
                        elif agent_type == 'intermediary_firm':
                            layer_name = 'intermediary'
                        elif agent_type == 'final_goods_firm':
                            layer_name = 'final_goods'
                        
                        round_data['production'][layer_name] = total_production
                        round_data['inventories'][layer_name] = total_inventory
                        round_data['overhead_costs'][layer_name] = total_overhead
                        round_data['debt'][f'{layer_name}_firms'] = total_debt
                        round_data['pricing'][layer_name] = avg_price
                        
            except Exception as e:
                print(f"Warning: Could not read {filename}: {e}")
    
    # Calculate wealth data by summing money from all agents of each type
    round_data['wealth'] = {}
    for agent_type in ['commodity_producer', 'intermediary_firm', 'final_goods_firm', 'household']:
        total_wealth = sum([agent['wealth'] for agent in round_data['agents'] if agent['type'] == agent_type])
        
        if agent_type == 'commodity_producer':
            round_data['wealth']['commodity'] = total_wealth
        elif agent_type == 'intermediary_firm':
            round_data['wealth']['intermediary'] = total_wealth
        elif agent_type == 'final_goods_firm':
            round_data['wealth']['final_goods'] = total_wealth
        elif agent_type == 'household':
            round_data['wealth']['households'] = total_wealth
    
    # Aggregate debt data
    total_firm_debt = sum([agent['debt'] for agent in round_data['agents'] if agent['type'] != 'household'])
    round_data['debt']['firms'] = total_firm_debt
    
    return round_data

def is_agent_climate_stressed(agent_type, agent_id, climate_events, climate_framework):
    """Determine if a specific agent is affected by climate stress in this round."""
    if not climate_events:
        return False
    
    for event_key, event_data in climate_events.items():
        if isinstance(event_data, dict):
            # New configurable shock format
            affected_continents = event_data['continents']
            affected_agent_types = event_data.get('agent_types', [])
            
            # Check if this agent's type is affected
            if agent_type not in affected_agent_types:
                continue  # Skip this event if agent type is not affected
            
            # Check if this agent's continent is affected
            if 'all' in affected_continents:
                return True
            
            agent_continent = get_agent_continent(agent_type, agent_id, climate_framework)
            if agent_continent in affected_continents:
                return True
        
        elif event_key in ['North America', 'Europe', 'Asia', 'South America', 'Africa']:
            # Old format where event key is continent name
            # This format doesn't specify agent types, so we assume it affects all agent types
            agent_continent = get_agent_continent(agent_type, agent_id, climate_framework)
            if agent_continent == event_key:
                return True
    
    return False

def get_agent_continent(agent_type, agent_id, climate_framework):
    """Get the continent assignment for a specific agent."""
    assignments = climate_framework.geographical_assignments[agent_type]
    return assignments[agent_id]['continent']

def create_time_evolution_visualization(visualization_data, simulation_path, baseline_data=None):
    """Create time-evolving visualization from simulation data."""
    
    print("Creating time-evolving visualization from simulation data...")
    
    rounds = visualization_data['rounds']
    
    # Extract time series data - no defaults, crash if missing
    def safe_extract(data_list, key):
        return [data[key] for data in data_list]
    
    # Production data
    commodity_production = safe_extract(visualization_data['production_data'], 'commodity')
    intermediary_production = safe_extract(visualization_data['production_data'], 'intermediary')
    final_goods_production = safe_extract(visualization_data['production_data'], 'final_goods')
    
    # Inventory data
    commodity_inventory = safe_extract(visualization_data['inventories'], 'commodity')
    intermediary_inventory = safe_extract(visualization_data['inventories'], 'intermediary')
    final_goods_inventory = safe_extract(visualization_data['inventories'], 'final_goods')
    
    # Wealth data
    commodity_wealth = safe_extract(visualization_data['wealth_data'], 'commodity')
    intermediary_wealth = safe_extract(visualization_data['wealth_data'], 'intermediary')
    final_goods_wealth = safe_extract(visualization_data['wealth_data'], 'final_goods')
    household_wealth = safe_extract(visualization_data['wealth_data'], 'households')
    
    # Overhead costs data
    commodity_overhead = safe_extract(visualization_data['overhead_costs'], 'commodity')
    intermediary_overhead = safe_extract(visualization_data['overhead_costs'], 'intermediary')
    final_goods_overhead = safe_extract(visualization_data['overhead_costs'], 'final_goods')
    
    # Pricing data
    commodity_price = safe_extract(visualization_data['pricing'], 'commodity')
    intermediary_price = safe_extract(visualization_data['pricing'], 'intermediary')
    final_goods_price = safe_extract(visualization_data['pricing'], 'final_goods')
    
    # Debt data
    household_debt = safe_extract(visualization_data['debt'], 'households')
    firm_debt = safe_extract(visualization_data['debt'], 'firms')
    
    # Extract baseline data if available
    baseline_commodity_production = None
    baseline_intermediary_production = None
    baseline_final_goods_production = None
    baseline_commodity_inventory = None
    baseline_intermediary_inventory = None
    baseline_final_goods_inventory = None
    baseline_commodity_wealth = None
    baseline_intermediary_wealth = None
    baseline_final_goods_wealth = None
    baseline_household_wealth = None
    baseline_commodity_overhead = None
    baseline_intermediary_overhead = None
    baseline_final_goods_overhead = None
    baseline_commodity_price = None
    baseline_intermediary_price = None
    baseline_final_goods_price = None
    baseline_household_debt = None
    baseline_firm_debt = None
    
    if baseline_data:
        try:
            baseline_commodity_production = safe_extract(baseline_data['production_data'], 'commodity')
            baseline_intermediary_production = safe_extract(baseline_data['production_data'], 'intermediary')
            baseline_final_goods_production = safe_extract(baseline_data['production_data'], 'final_goods')
            baseline_commodity_inventory = safe_extract(baseline_data['inventories'], 'commodity')
            baseline_intermediary_inventory = safe_extract(baseline_data['inventories'], 'intermediary')
            baseline_final_goods_inventory = safe_extract(baseline_data['inventories'], 'final_goods')
            baseline_commodity_wealth = safe_extract(baseline_data['wealth_data'], 'commodity')
            baseline_intermediary_wealth = safe_extract(baseline_data['wealth_data'], 'intermediary')
            baseline_final_goods_wealth = safe_extract(baseline_data['wealth_data'], 'final_goods')
            baseline_household_wealth = safe_extract(baseline_data['wealth_data'], 'households')
            baseline_commodity_overhead = safe_extract(baseline_data['overhead_costs'], 'commodity')
            baseline_intermediary_overhead = safe_extract(baseline_data['overhead_costs'], 'intermediary')
            baseline_final_goods_overhead = safe_extract(baseline_data['overhead_costs'], 'final_goods')
            baseline_commodity_price = safe_extract(baseline_data['pricing'], 'commodity')
            baseline_intermediary_price = safe_extract(baseline_data['pricing'], 'intermediary')
            baseline_final_goods_price = safe_extract(baseline_data['pricing'], 'final_goods')
            baseline_household_debt = safe_extract(baseline_data['debt'], 'households')
            baseline_firm_debt = safe_extract(baseline_data['debt'], 'firms')
            print("Baseline data extracted successfully")
        except Exception as e:
            print(f"Warning: Could not extract baseline data: {e}")
            baseline_data = None
    
    # Count climate events by round
    climate_stress_counts = []
    for round_agents in visualization_data['agent_data']:
        stress_count = sum([1 for agent in round_agents if agent['climate_stressed']])
        climate_stress_counts.append(stress_count)
    
    # Create comprehensive time evolution plot with 3x3 grid (separated dual y-axis plot)
    fig, ((ax1, ax2, ax3), (ax4, ax5, ax6), (ax7, ax8, ax9)) = plt.subplots(3, 3, figsize=(24, 18))
    fig.suptitle('Climate 3-Layer Supply Chain: Time Evolution Analysis', fontsize=18, fontweight='bold')
    
    # Helper function to add climate shock indicators
    def add_climate_shocks(ax, legend_suffix=""):
        shock_colors = {
            'commodity_producer': '#8B4513',
            'intermediary_firm': '#DAA520', 
            'final_goods_firm': '#00FF00',
            'household': '#4169E1',
            'all_sectors': '#FF0000'
        }
        
        climate_shock_legend_added = False
        for shock_round in rounds:
            if shock_round < len(visualization_data['climate_events']):
                events = visualization_data['climate_events'][shock_round]
                if events:
                    affected_sectors = set()
                    for event_name, event_data in events.items():
                        if isinstance(event_data, dict) and 'agent_types' in event_data:
                            affected_sectors.update(event_data['agent_types'])
                    
                    if len(affected_sectors) > 1:
                        line_color = shock_colors['all_sectors']
                        line_label = 'Multi-Sector Climate Shock'
                    elif len(affected_sectors) == 1:
                        sector = list(affected_sectors)[0]
                        line_color = shock_colors.get(sector, '#FF0000')
                        sector_names = {
                            'commodity_producer': 'Commodity',
                            'intermediary_firm': 'Intermediary', 
                            'final_goods_firm': 'Final Goods',
                            'household': 'Household'
                        }
                        line_label = f'{sector_names.get(sector, sector)} Climate Shock'
                    else:
                        line_color = '#FF0000'
                        line_label = 'Climate Shock'
                    
                    ax.axvline(x=shock_round, color=line_color, linestyle='--', 
                               alpha=0.8, linewidth=2, 
                               label=line_label if not climate_shock_legend_added else "")
                    climate_shock_legend_added = True
    
    # Plot 1: Production evolution over time
    if baseline_data:
        ax1.plot(rounds, baseline_commodity_production, 'o--', label='Baseline Commodity', color='#8B4513', linewidth=1, markersize=3, alpha=0.6)
        ax1.plot(rounds, baseline_intermediary_production, 's--', label='Baseline Intermediary', color='#DAA520', linewidth=1, markersize=3, alpha=0.6)
        ax1.plot(rounds, baseline_final_goods_production, '^--', label='Baseline Final Goods', color='#00FF00', linewidth=1, markersize=3, alpha=0.6)
    
    ax1.plot(rounds, commodity_production, 'o-', label='Climate Commodity', color='#8B4513', linewidth=2, markersize=4)
    ax1.plot(rounds, intermediary_production, 's-', label='Climate Intermediary', color='#DAA520', linewidth=2, markersize=4)
    ax1.plot(rounds, final_goods_production, '^-', label='Climate Final Goods', color='#00FF00', linewidth=2, markersize=4)
    add_climate_shocks(ax1)
    ax1.set_title('Production Levels Over Time', fontweight='bold')
    ax1.set_xlabel('Round')
    ax1.set_ylabel('Production Level')
    ax1.legend(loc='center right', fontsize=8)
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Inventory evolution over time
    if baseline_data:
        ax2.plot(rounds, baseline_commodity_inventory, 'o--', label='Baseline Commodity', color='#8B4513', linewidth=1, markersize=3, alpha=0.6)
        ax2.plot(rounds, baseline_intermediary_inventory, 's--', label='Baseline Intermediary', color='#DAA520', linewidth=1, markersize=3, alpha=0.6)
        ax2.plot(rounds, baseline_final_goods_inventory, '^--', label='Baseline Final Goods', color='#00FF00', linewidth=1, markersize=3, alpha=0.6)
    
    ax2.plot(rounds, commodity_inventory, 'o-', label='Climate Commodity', color='#8B4513', linewidth=2, markersize=4)
    ax2.plot(rounds, intermediary_inventory, 's-', label='Climate Intermediary', color='#DAA520', linewidth=2, markersize=4)
    ax2.plot(rounds, final_goods_inventory, '^-', label='Climate Final Goods', color='#00FF00', linewidth=2, markersize=4)
    add_climate_shocks(ax2)
    ax2.set_title('Inventory Levels Over Time', fontweight='bold')
    ax2.set_xlabel('Round')
    ax2.set_ylabel('Inventory Level')
    ax2.legend(loc='center right', fontsize=8)
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Overhead Costs evolution over time
    if baseline_data:
        ax3.plot(rounds, baseline_commodity_overhead, 'o--', label='Baseline Commodity', color='#8B4513', linewidth=1, markersize=3, alpha=0.6)
        ax3.plot(rounds, baseline_intermediary_overhead, 's--', label='Baseline Intermediary', color='#DAA520', linewidth=1, markersize=3, alpha=0.6)
        ax3.plot(rounds, baseline_final_goods_overhead, '^--', label='Baseline Final Goods', color='#00FF00', linewidth=1, markersize=3, alpha=0.6)
    
    ax3.plot(rounds, commodity_overhead, 'o-', label='Climate Commodity', color='#8B4513', linewidth=2, markersize=4)
    ax3.plot(rounds, intermediary_overhead, 's-', label='Climate Intermediary', color='#DAA520', linewidth=2, markersize=4)
    ax3.plot(rounds, final_goods_overhead, '^-', label='Climate Final Goods', color='#00FF00', linewidth=2, markersize=4)
    add_climate_shocks(ax3)
    ax3.set_title('Overhead Costs Over Time', fontweight='bold')
    ax3.set_xlabel('Round')
    ax3.set_ylabel('Overhead Cost ($)')
    ax3.legend(loc='center right', fontsize=8)
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Pricing evolution over time
    if baseline_data:
        ax4.plot(rounds, baseline_commodity_price, 'o--', label='Baseline Commodity', color='#8B4513', linewidth=1, markersize=3, alpha=0.6)
        ax4.plot(rounds, baseline_intermediary_price, 's--', label='Baseline Intermediary', color='#DAA520', linewidth=1, markersize=3, alpha=0.6)
        ax4.plot(rounds, baseline_final_goods_price, '^--', label='Baseline Final Goods', color='#00FF00', linewidth=1, markersize=3, alpha=0.6)
    
    ax4.plot(rounds, commodity_price, 'o-', label='Climate Commodity', color='#8B4513', linewidth=2, markersize=4)
    ax4.plot(rounds, intermediary_price, 's-', label='Climate Intermediary', color='#DAA520', linewidth=2, markersize=4)
    ax4.plot(rounds, final_goods_price, '^-', label='Climate Final Goods', color='#00FF00', linewidth=2, markersize=4)
    add_climate_shocks(ax4)
    ax4.set_title('Pricing Evolution Over Time', fontweight='bold')
    ax4.set_xlabel('Round')
    ax4.set_ylabel('Price ($)')
    ax4.legend(loc='center right', fontsize=8)
    ax4.grid(True, alpha=0.3)
    
    # Plot 5: Wealth evolution by sector (including debt)
    if baseline_data:
        ax5.plot(rounds, baseline_commodity_wealth, 'o--', label='Baseline Commodity', color='#8B4513', linewidth=1, markersize=3, alpha=0.6)
        ax5.plot(rounds, baseline_intermediary_wealth, 's--', label='Baseline Intermediary', color='#DAA520', linewidth=1, markersize=3, alpha=0.6)
        ax5.plot(rounds, baseline_final_goods_wealth, '^--', label='Baseline Final Goods', color='#00FF00', linewidth=1, markersize=3, alpha=0.6)
        ax5.plot(rounds, baseline_household_wealth, 'd--', label='Baseline Household', color='#4169E1', linewidth=1, markersize=3, alpha=0.6)
    
    ax5.plot(rounds, commodity_wealth, 'o-', label='Climate Commodity', color='#8B4513', linewidth=2, markersize=4)
    ax5.plot(rounds, intermediary_wealth, 's-', label='Climate Intermediary', color='#DAA520', linewidth=2, markersize=4)
    ax5.plot(rounds, final_goods_wealth, '^-', label='Climate Final Goods', color='#00FF00', linewidth=2, markersize=4)
    ax5.plot(rounds, household_wealth, 'd-', label='Climate Household', color='#4169E1', linewidth=2, markersize=4)
    add_climate_shocks(ax5)
    ax5.set_title('Wealth Evolution by Sector', fontweight='bold')
    ax5.set_xlabel('Round')
    ax5.set_ylabel('Wealth ($)')
    ax5.legend(loc='center right', fontsize=8)
    ax5.grid(True, alpha=0.3)
    
    # Plot 6: Debt evolution
    if baseline_data:
        ax6.plot(rounds, baseline_household_debt, 'd--', label='Baseline Household Debt', color='#4169E1', linewidth=1, markersize=3, alpha=0.6)
        ax6.plot(rounds, baseline_firm_debt, 's--', label='Baseline All Firms Debt', color='#666666', linewidth=1, markersize=3, alpha=0.6)
    
    ax6.plot(rounds, household_debt, 'd-', label='Climate Household Debt', color='#4169E1', linewidth=2, markersize=4, alpha=0.8)
    ax6.plot(rounds, firm_debt, 's-', label='Climate All Firms Debt', color='#666666', linewidth=2, markersize=4, alpha=0.8)
    add_climate_shocks(ax6)
    ax6.set_title('Debt Levels Over Time', fontweight='bold')
    ax6.set_xlabel('Round')
    ax6.set_ylabel('Debt ($)')
    ax6.legend(loc='center right', fontsize=8)
    ax6.grid(True, alpha=0.3)
    
    # Plot 7: Climate stress events count
    ax7.bar(rounds, climate_stress_counts, color='red', alpha=0.6, label='Climate Stressed Agents')
    ax7.set_title('Climate Stress Events', fontweight='bold')
    ax7.set_xlabel('Round')
    ax7.set_ylabel('Number of Stressed Agents')
    ax7.legend(loc='upper right', fontsize=8)
    ax7.grid(True, alpha=0.3)
    
    # Plot 8: Total Production (separated from dual y-axis)
    total_production = [c + i + f for c, i, f in zip(commodity_production, intermediary_production, final_goods_production)]
    if baseline_data:
        baseline_total_production = [c + i + f for c, i, f in zip(baseline_commodity_production, baseline_intermediary_production, baseline_final_goods_production)]
        ax8.plot(rounds, baseline_total_production, 'g--', label='Baseline Total Production', linewidth=2, alpha=0.6)
    
    ax8.plot(rounds, total_production, 'g-', label='Climate Total Production', linewidth=3, alpha=0.8)
    add_climate_shocks(ax8)
    ax8.set_title('Total Production', fontweight='bold')
    ax8.set_xlabel('Round')
    ax8.set_ylabel('Total Production')
    ax8.legend(loc='upper right', fontsize=8)
    ax8.grid(True, alpha=0.3)
    
    # Plot 9: Total Overhead and Average Price (separated from dual y-axis)
    total_overhead = [c + i + f for c, i, f in zip(commodity_overhead, intermediary_overhead, final_goods_overhead)]
    avg_price = [(c + i + f) / 3 for c, i, f in zip(commodity_price, intermediary_price, final_goods_price)]
    
    if baseline_data:
        baseline_total_overhead = [c + i + f for c, i, f in zip(baseline_commodity_overhead, baseline_intermediary_overhead, baseline_final_goods_overhead)]
        baseline_avg_price = [(c + i + f) / 3 for c, i, f in zip(baseline_commodity_price, baseline_intermediary_price, baseline_final_goods_price)]
        ax9.plot(rounds, baseline_total_overhead, 'r--', label='Baseline Total Overhead', linewidth=1, alpha=0.6)
        ax9.plot(rounds, baseline_avg_price, 'b--', label='Baseline Average Price', linewidth=1, alpha=0.6)
    
    ax9.plot(rounds, total_overhead, 'r-', label='Climate Total Overhead', linewidth=2, alpha=0.8)
    ax9.plot(rounds, avg_price, 'b-', label='Climate Average Price', linewidth=2, alpha=0.8)
    add_climate_shocks(ax9)
    ax9.set_title('Total Overhead & Average Price', fontweight='bold')
    ax9.set_xlabel('Round')
    ax9.set_ylabel('Cost/Price ($)')
    ax9.legend(loc='upper right', fontsize=8)
    ax9.grid(True, alpha=0.3)
    
    # Save the time evolution plot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{simulation_path}/climate_3layer_time_evolution_{timestamp}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"SUCCESS: Time evolution visualization saved: {filename}")
    
    plt.close()
    return filename

def create_animated_supply_chain(visualization_data, simulation_path, baseline_data=None):
    """Create animated GIF showing supply chain evolution over time."""
    print("Creating animated supply chain visualization...")
    
    fig = plt.figure(figsize=(18 , 14)) 
    fig.suptitle('Climate 3-Layer Supply Chain Evolution', fontsize=16, fontweight='bold')
    
    # Create custom subplot layout
    ax1 = plt.subplot2grid((3, 3), (0, 0), rowspan=2)  # Network plot (big, left side)
    ax2 = plt.subplot2grid((3, 3), (0, 1))             # Production 
    ax3 = plt.subplot2grid((3, 3), (0, 2))             # Inventory 
    ax4 = plt.subplot2grid((3, 3), (1, 1))             # Pricing 
    ax5 = plt.subplot2grid((3, 3), (1, 2))             # Production
    ax6 = plt.subplot2grid((3, 3), (2, 0))             # Geography 
    ax7 = plt.subplot2grid((3, 3), (2, 1))             # Wealth 
    ax8 = plt.subplot2grid((3, 3), (2, 2))             # debt
    
    num_frames = len(visualization_data['rounds'])

    def animate(frame):
        # Clear all subplots
        for ax in [ax1, ax2, ax3, ax4, ax5, ax6, ax7, ax8]:
            ax.clear()
        
        if frame >= len(visualization_data['rounds']):
            return
        
        round_num = visualization_data['rounds'][frame]
        agent_data = visualization_data['agent_data'][frame]
        
        ###################################################
        # NETWORK PLOT Agent network with stress status
        ###################################################
        ax1.set_title(f'Supply Chain Network - Round {round_num}', fontweight='bold')
        ax1.set_xlim(0, 8)
        ax1.set_ylim(0, 6)
         
        # Count actual agents by type from data
        agent_counts = {}
        for agent in agent_data:
            agent_type = agent['type']
            if agent_type not in agent_counts:
                agent_counts[agent_type] = 0
            agent_counts[agent_type] += 1
        
        # Dynamically create positions based on actual agent counts
        def create_agent_positions(agent_counts):
            positions = {}
            
            # Column positions for each agent type
            commodity_x = 1
            intermediary_x = 3
            final_goods_x = 5
            household_x = 7
            
            # Create positions for each agent type based on actual counts
            for agent_type, count in agent_counts.items():
                positions[agent_type] = []
                
                if agent_type == 'commodity_producer':
                    # Vertical spacing for commodity producers
                    y_spacing = 5.0 / max(count, 1)
                    for i in range(count):
                        y = 0.5 + i * y_spacing
                        positions[agent_type].append((commodity_x, y))
                        
                elif agent_type == 'intermediary_firm':
                    # Vertical spacing for intermediary firms
                    y_spacing = 5.0 / max(count, 1)
                    for i in range(count):
                        y = 0.5 + i * y_spacing
                        positions[agent_type].append((intermediary_x, y))
                        
                elif agent_type == 'final_goods_firm':
                    # Vertical spacing for final goods firms
                    y_spacing = 5.0 / max(count, 1)
                    for i in range(count):
                        y = 0.5 + i * y_spacing
                        positions[agent_type].append((final_goods_x, y))
                        
                elif agent_type == 'household':
                    # Grid layout for households (can be many)
                    if count <= 6:
                        # Single column
                        y_spacing = 5.0 / max(count, 1)
                        for i in range(count):
                            y = 0.5 + i * y_spacing
                            positions[agent_type].append((household_x, y))
                    else:
                        # Multiple columns if many households
                        cols = 2 if count <= 12 else 3
                        rows_per_col = (count + cols - 1) // cols  # Ceiling division
                        
                        for i in range(count):
                            col = i // rows_per_col
                            row = i % rows_per_col
                            x = household_x + col * 0.3  # Slightly offset columns
                            y = 0.5 + row * (5.0 / rows_per_col)
                            positions[agent_type].append((x, y))
            
            return positions
        
        agent_positions = create_agent_positions(agent_counts)

        agent_type_colors = {
            'commodity_producer': '#8B4513',
            'intermediary_firm': '#DAA520',
            'final_goods_firm': '#00FF00',
            'household': '#4169E1'
        }

        # Plot each agent using data and dynamic positions
        pos_idx = {'commodity_producer': 0, 'intermediary_firm': 0, 'final_goods_firm': 0, 'household': 0}

        for agent in agent_data:
            agent_type = agent['type']
            if agent_type in agent_positions and pos_idx[agent_type] < len(agent_positions[agent_type]):
                pos = agent_positions[agent_type][pos_idx[agent_type]]
                pos_idx[agent_type] += 1
                
                # Determine color based on climate stress
                base_color = agent_type_colors[agent_type]
                color = '#FF0000' if agent['climate_stressed'] else base_color
                size = 200 if agent['climate_stressed'] else 100
                
                # Determine if agent is in debt and add debt indicator
                is_in_debt = agent.get('debt', 0) > 0
                
                if is_in_debt and not agent['climate_stressed']:
                    # Agent in debt but not climate stressed - use orange border
                    ax1.scatter(pos[0], pos[1], c=color, s=size, alpha=0.8, 
                               edgecolors='#FFA500', linewidths=3)
                elif is_in_debt and agent['climate_stressed']:
                    # Agent both in debt and climate stressed - use black border
                    ax1.scatter(pos[0], pos[1], c=color, s=size, alpha=0.8, 
                               edgecolors='black', linewidths=3)
                else:
                    # Normal agent - no special border
                    ax1.scatter(pos[0], pos[1], c=color, s=size, alpha=0.8)
                
                # Show wealth with debt indicator if applicable
                if is_in_debt:
                    debt_amount = agent.get('debt', 0)
                    wealth_text = f"-${debt_amount-agent['wealth']:.0f}"
                else: 
                    wealth_text = f"${agent['wealth']:.0f}"

                ax1.text(pos[0], pos[1]-0.2, wealth_text, 
                        ha='center', fontsize=10) 
        
        # Add supply chain flow arrows (dynamic positioning)
        if 'commodity_producer' in agent_counts and 'intermediary_firm' in agent_counts:
            ax1.annotate('', xy=(2.8, 2.5), xytext=(1.2, 2.5), 
                        arrowprops=dict(arrowstyle='->', lw=2, color='gray'))
        if 'intermediary_firm' in agent_counts and 'final_goods_firm' in agent_counts:
            ax1.annotate('', xy=(4.8, 2.5), xytext=(3.2, 2.5), 
                        arrowprops=dict(arrowstyle='->', lw=2, color='gray'))
        if 'final_goods_firm' in agent_counts and 'household' in agent_counts:
            ax1.annotate('', xy=(6.8, 2.5), xytext=(5.2, 2.5), 
                        arrowprops=dict(arrowstyle='->', lw=2, color='gray'))
        
        # Add layer labels with actual counts
        if 'commodity_producer' in agent_counts:
            ax1.text(1, 5.2, f'Layer 1\nCommodity\n({agent_counts["commodity_producer"]})', ha='center', fontsize=10, fontweight='bold')
        if 'intermediary_firm' in agent_counts:
            ax1.text(3, 5.2, f'Layer 2\nIntermediary\n({agent_counts["intermediary_firm"]})', ha='center', fontsize=10, fontweight='bold')
        if 'final_goods_firm' in agent_counts:
            ax1.text(5, 5.2, f'Layer 3\nFinal Goods\n({agent_counts["final_goods_firm"]})', ha='center', fontsize=10, fontweight='bold')
        if 'household' in agent_counts:
            ax1.text(7, 5.2, f'Households\n({agent_counts["household"]})', ha='center', fontsize=10, fontweight='bold')
        
        # Add legend for network plot indicators - positioned to avoid blocking content
        legend_elements = []
        legend_elements.append(plt.Line2D([0], [0], marker='o', color='w', 
                                        markerfacecolor='#8B4513', markersize=8, 
                                        label='Normal Agent', markeredgecolor='none'))
        legend_elements.append(plt.Line2D([0], [0], marker='o', color='w', 
                                        markerfacecolor='#FF0000', markersize=10, 
                                        label='Climate Stressed', markeredgecolor='none'))
        legend_elements.append(plt.Line2D([0], [0], marker='o', color='w', 
                                        markerfacecolor='#8B4513', markersize=8, 
                                        label='Agent in Debt', markeredgecolor='#FFA500', markeredgewidth=2))
        
        ax1.legend(handles=legend_elements, loc='upper left', fontsize=7, 
                  title='Agent Status', title_fontsize=8, framealpha=0.8, bbox_to_anchor=(0.8, 1))
        
        ax1.axis('off')
        
        ###################################################
        # PRODUCTION PLOT
        ###################################################
        ax2.set_title('Production Levels', fontweight='bold')
        ax2.set_ylabel('Production')
        
        # Get data up to current frame
        current_rounds = visualization_data['rounds'][:frame+1]
        
        # Stressed production data
        commodity_prod = [visualization_data['production_data'][i].get('commodity', 0) for i in range(frame+1)]
        intermediary_prod = [visualization_data['production_data'][i].get('intermediary', 0) for i in range(frame+1)]
        final_goods_prod = [visualization_data['production_data'][i].get('final_goods', 0) for i in range(frame+1)]
        
        ax2.plot(current_rounds, commodity_prod, 'o-', color='#8B4513', label='Stressed Commodity', linewidth=2)
        ax2.plot(current_rounds, intermediary_prod, 's-', color='#DAA520', label='Stressed Intermediary', linewidth=2)
        ax2.plot(current_rounds, final_goods_prod, '^-', color='#00FF00', label='Stressed Final Goods', linewidth=2)
        
        # Baseline production data
        if baseline_data:
            baseline_commodity_prod = [baseline_data['production_data'][i].get('commodity', 0) for i in range(frame+1)]
            baseline_intermediary_prod = [baseline_data['production_data'][i].get('intermediary', 0) for i in range(frame+1)]
            baseline_final_goods_prod = [baseline_data['production_data'][i].get('final_goods', 0) for i in range(frame+1)]
            
            ax2.plot(current_rounds, baseline_commodity_prod, 'o--', color='#8B4513', alpha=0.5, label='Baseline Commodity')
            ax2.plot(current_rounds, baseline_intermediary_prod, 's--', color='#DAA520', alpha=0.5, label='Baseline Intermediary')
            ax2.plot(current_rounds, baseline_final_goods_prod, '^--', color='#00FF00', alpha=0.5, label='Baseline Final Goods')
        
        ax2.legend(fontsize=7)
        ax2.grid(True, alpha=0.3)
        ax2.set_xlim(0, num_frames)
        
        ###################################################
        # Overhead plot
        ###################################################
        ax4.set_title('Overhead Costs', fontweight='bold')
        ax4.set_xlabel('Round')
        ax4.set_ylabel('Overhead ($)')
        
        # Stressed overhead data
        commodity_overhead = [visualization_data['overhead_costs'][i].get('commodity', 0) for i in range(frame+1)]
        intermediary_overhead = [visualization_data['overhead_costs'][i].get('intermediary', 0) for i in range(frame+1)]
        final_goods_overhead = [visualization_data['overhead_costs'][i].get('final_goods', 0) for i in range(frame+1)]
        
        ax4.plot(current_rounds, commodity_overhead, 'o-', color='#8B4513', label='Stressed Commodity', linewidth=2)
        ax4.plot(current_rounds, intermediary_overhead, 's-', color='#DAA520', label='Stressed Intermediary', linewidth=2)
        ax4.plot(current_rounds, final_goods_overhead, '^-', color='#00FF00', label='Stressed Final Goods', linewidth=2)
        
        # Baseline overhead data
        if baseline_data:
            baseline_commodity_overhead = [baseline_data['overhead_costs'][i].get('commodity', 0) for i in range(frame+1)]
            baseline_intermediary_overhead = [baseline_data['overhead_costs'][i].get('intermediary', 0) for i in range(frame+1)]
            baseline_final_goods_overhead = [baseline_data['overhead_costs'][i].get('final_goods', 0) for i in range(frame+1)]
            
            ax4.plot(current_rounds, baseline_commodity_overhead, 'o--', color='#8B4513', alpha=0.5, label='Baseline Commodity')
            ax4.plot(current_rounds, baseline_intermediary_overhead, 's--', color='#DAA520', alpha=0.5, label='Baseline Intermediary')
            ax4.plot(current_rounds, baseline_final_goods_overhead, '^--', color='#00FF00', alpha=0.5, label='Baseline Final Goods')
        
        ax4.legend(fontsize=7)
        ax4.grid(True, alpha=0.3)
        ax4.set_xlim(0, num_frames)
        
        ###################################################
        # WEALTH PLOT 
        ###################################################
        ax7.set_title('Average Wealth', fontweight='bold')
        ax7.set_xlabel('Round')
        ax7.set_ylabel('Wealth ($)')
        
        # Stressed wealth data
        household_wealth = [visualization_data['wealth_data'][i].get('households', 0) for i in range(frame+1)]
        firm_wealth = [visualization_data['wealth_data'][i].get('commodity', 0) + 
                      visualization_data['wealth_data'][i].get('intermediary', 0) + 
                      visualization_data['wealth_data'][i].get('final_goods', 0) for i in range(frame+1)]
        
        ax7.plot(current_rounds, household_wealth, 'o-', color='blue', label='Stressed Households', linewidth=2)
        ax7.plot(current_rounds, firm_wealth, 's-', color='green', label='Stressed Firms', linewidth=2)
        
        # Baseline wealth data
        if baseline_data:
            baseline_household_wealth = [baseline_data['wealth_data'][i].get('households', 0) for i in range(frame+1)]
            baseline_firm_wealth = [baseline_data['wealth_data'][i].get('commodity', 0) + 
                                  baseline_data['wealth_data'][i].get('intermediary', 0) + 
                                  baseline_data['wealth_data'][i].get('final_goods', 0) for i in range(frame+1)]
            
            ax7.plot(current_rounds, baseline_household_wealth, 'o--', color='blue', alpha=0.5, label='Baseline Households')
            ax7.plot(current_rounds, baseline_firm_wealth, 's--', color='green', alpha=0.5, label='Baseline Firms')
        
        ax7.legend(fontsize=7)
        ax7.grid(True, alpha=0.3)
        ax7.set_xlim(0, num_frames)
        
        ###################################################
        # INVENTORY PLOT
        ###################################################
        ax3.set_title('Inventory Levels', fontweight='bold')
        ax3.set_ylabel('Inventory')
        
        # Stressed inventory data
        commodity_inv = [visualization_data['inventories'][i].get('commodity', 0) for i in range(frame+1)]
        intermediary_inv = [visualization_data['inventories'][i].get('intermediary', 0) for i in range(frame+1)]
        final_goods_inv = [visualization_data['inventories'][i].get('final_goods', 0) for i in range(frame+1)]
        
        ax3.plot(current_rounds, commodity_inv, 'o-', color='#8B4513', label='Stressed Commodity', linewidth=2)
        ax3.plot(current_rounds, intermediary_inv, 's-', color='#DAA520', label='Stressed Intermediary', linewidth=2)
        ax3.plot(current_rounds, final_goods_inv, '^-', color='#00FF00', label='Stressed Final Goods', linewidth=2)
        
        # Baseline inventory data
        if baseline_data:
            baseline_commodity_inv = [baseline_data['inventories'][i].get('commodity', 0) for i in range(frame+1)]
            baseline_intermediary_inv = [baseline_data['inventories'][i].get('intermediary', 0) for i in range(frame+1)]
            baseline_final_goods_inv = [baseline_data['inventories'][i].get('final_goods', 0) for i in range(frame+1)]
            
            ax3.plot(current_rounds, baseline_commodity_inv, 'o--', color='#8B4513', alpha=0.5, label='Baseline Commodity')
            ax3.plot(current_rounds, baseline_intermediary_inv, 's--', color='#DAA520', alpha=0.5, label='Baseline Intermediary')
            ax3.plot(current_rounds, baseline_final_goods_inv, '^--', color='#00FF00', alpha=0.5, label='Baseline Final Goods')
        
        ax3.legend(fontsize=7)
        ax3.grid(True, alpha=0.3)
        ax3.set_xlim(0, num_frames)
        
        ###################################################
        # PRICE PLOT
        ###################################################
        ax5.set_title('Average Prices', fontweight='bold') 
        ax5.set_ylabel('Price ($)')
        
        # Stressed price data
        commodity_price = [visualization_data['pricing'][i].get('commodity', 0) for i in range(frame+1)]
        intermediary_price = [visualization_data['pricing'][i].get('intermediary', 0) for i in range(frame+1)]
        final_goods_price = [visualization_data['pricing'][i].get('final_goods', 0) for i in range(frame+1)]
        
        ax5.plot(current_rounds, commodity_price, 'o-', color='#8B4513', label='Stressed Commodity', linewidth=2)
        ax5.plot(current_rounds, intermediary_price, 's-', color='#DAA520', label='Stressed Intermediary', linewidth=2)
        ax5.plot(current_rounds, final_goods_price, '^-', color='#00FF00', label='Stressed Final Goods', linewidth=2)
        
        # Baseline price data
        if baseline_data:
            baseline_commodity_price = [baseline_data['pricing'][i].get('commodity', 0) for i in range(frame+1)]
            baseline_intermediary_price = [baseline_data['pricing'][i].get('intermediary', 0) for i in range(frame+1)]
            baseline_final_goods_price = [baseline_data['pricing'][i].get('final_goods', 0) for i in range(frame+1)]
            
            ax5.plot(current_rounds, baseline_commodity_price, 'o--', color='#8B4513', alpha=0.5, label='Baseline Commodity')
            ax5.plot(current_rounds, baseline_intermediary_price, 's--', color='#DAA520', alpha=0.5, label='Baseline Intermediary')
            ax5.plot(current_rounds, baseline_final_goods_price, '^--', color='#00FF00', alpha=0.5, label='Baseline Final Goods')
        
        ax5.legend(fontsize=7)
        ax5.grid(True, alpha=0.3)
        ax5.set_xlim(0, num_frames)
        
        ###################################################
        # DEBT PLOT 
        ###################################################
        ax8.set_title('Total Debt', fontweight='bold')
        ax8.set_xlabel('Round')
        ax8.set_ylabel('Debt ($)')
        
        # Stressed debt data
        household_debt = [visualization_data['debt'][i].get('households', 0) for i in range(frame+1)]
        firm_debt = [visualization_data['debt'][i].get('firms', 0) for i in range(frame+1)]
        
        ax8.plot(current_rounds, household_debt, 'o-', color='red', label='Stressed Households', linewidth=2)
        ax8.plot(current_rounds, firm_debt, 's-', color='orange', label='Stressed Firms', linewidth=2)
        
        # Baseline debt data
        if baseline_data:
            baseline_household_debt = [baseline_data['debt'][i].get('households', 0) for i in range(frame+1)]
            baseline_firm_debt = [baseline_data['debt'][i].get('firms', 0) for i in range(frame+1)]
            
            ax8.plot(current_rounds, baseline_household_debt, 'o--', color='red', alpha=0.5, label='Baseline Households')
            ax8.plot(current_rounds, baseline_firm_debt, 's--', color='orange', alpha=0.5, label='Baseline Firms')
        
        ax8.legend(fontsize=7)
        ax8.grid(True, alpha=0.3)
        ax8.set_xlim(0, num_frames)
        
        ###################################################
        # GEOGRAPHY PLOT
        ###################################################
        ax6.set_title('Geographical Distribution', fontweight='bold')
        ax6.set_xlim(0, 7)
        ax6.set_ylim(0, 5)
        ax6.set_aspect('equal')
        
        # Define continent positions for the world map (simplified layout)
        continent_positions = {
            'North America': (1, 3.5, 1.5, 1),
            'South America': (1, 1, 1.5, 1.5),
            'Europe': (3, 3.5, 1, 1),
            'Asia': (4.5, 3, 1.5, 1.5),
            'Africa': (3, 1.5, 1, 1.5),
            'Oceania': (5.5, 0.5, 1, 1)
        }
        
        # Get climate events for current round
        climate_events = {}
        if round_num < len(visualization_data['climate_events']):
            climate_events = visualization_data['climate_events'][round_num]
        
        # Draw continent shapes (simplified rectangles)
        continent_colors = {}
        for continent in continent_positions.keys():
            # Default color
            base_color = '#90EE90'  # Light green for normal
            
            # Check if this continent has climate stress
            if climate_events:
                for event_name, event_data in climate_events.items():
                    if isinstance(event_data, dict) and 'continents' in event_data:
                        if continent in event_data['continents'] or 'all' in event_data['continents']:
                            base_color = '#FF6B6B'  # Red for climate stress
                            break
            
            continent_colors[continent] = base_color
            
            # Draw continent rectangle
            x, y, width, height = continent_positions[continent]
            continent_rect = plt.Rectangle((x, y), width, height, 
                                         facecolor=base_color, 
                                         edgecolor='black', 
                                         alpha=0.6)
            ax6.add_patch(continent_rect)
            
            # Add continent label
            ax6.text(x + width/2, y + height/2, continent.replace(' ', '\n'), 
                    ha='center', va='center', fontsize=8, fontweight='bold')

        # Place agents on their continents
        agent_counts_by_continent = {}
        for agent in agent_data:
            continent = agent['continent']
            if continent not in agent_counts_by_continent:
                agent_counts_by_continent[continent] = {
                    'commodity_producer': 0,
                    'intermediary_firm': 0, 
                    'final_goods_firm': 0,
                    'household': 0
                }
            agent_counts_by_continent[continent][agent['type']] += 1
        
        # Draw agent indicators on continents
        for continent, counts in agent_counts_by_continent.items():
            if continent in continent_positions:
                x, y, width, height = continent_positions[continent]
                
                # Position agents within continent bounds
                agent_positions_in_continent = [
                    (x + 0.2, y + height - 0.2),  # Top-left: commodity
                    (x + width - 0.2, y + height - 0.2),  # Top-right: intermediary
                    (x + 0.2, y + 0.2),  # Bottom-left: final goods
                    (x + width - 0.2, y + 0.2)   # Bottom-right: households
                ]
                
                agent_types = ['commodity_producer', 'intermediary_firm', 'final_goods_firm', 'household']
                agent_colors = ['#8B4513', '#DAA520', '#00FF00', '#4169E1']
                agent_symbols = ['o', 's', '^', 'D']
                
                for i, agent_type in enumerate(agent_types):
                    if counts[agent_type] > 0:
                        pos_x, pos_y = agent_positions_in_continent[i]
                        
                        # Check if agents of this type in this continent are stressed
                        stressed_agents = [a for a in agent_data 
                                         if a['continent'] == continent 
                                         and a['type'] == agent_type 
                                         and a['climate_stressed']]
                        
                        color = '#FF0000' if stressed_agents else agent_colors[i]
                        size = 150 if stressed_agents else 80
                        
                        ax6.scatter(pos_x, pos_y, c=color, s=size, marker=agent_symbols[i], 
                                  alpha=0.9, edgecolors='black', linewidth=1)
                        
                        # Add count label
                        ax6.text(pos_x, pos_y - 0.15, str(int(counts[agent_type])), 
                               ha='center', va='center', fontsize=6, fontweight='bold')
        
        # Add legend for agent types - positioned to avoid blocking content
        legend_elements = []
        agent_type_names = ['Commodity', 'Intermediary', 'Final Goods', 'Households']
        legend_agent_colors = ['#8B4513', '#DAA520', '#00FF00', '#4169E1']
        agent_symbols = ['o', 's', '^', 'D']

        for i, (name, color, symbol) in enumerate(zip(agent_type_names, legend_agent_colors, agent_symbols)):
            legend_elements.append(plt.Line2D([0], [0], marker=symbol, color='w', 
                                            markerfacecolor=color, markersize=6, 
                                            label=name, markeredgecolor='black', markeredgewidth=0.5))
        
        # Add stress indicator to legend
        legend_elements.append(plt.Line2D([0], [0], marker='o', color='w', 
                                        markerfacecolor='#FF0000', markersize=8, 
                                        label='Stressed', markeredgecolor='black', markeredgewidth=0.5))
        
        ax6.legend(handles=legend_elements, loc='upper right', fontsize=6, 
                  title='Agent Types', title_fontsize=7, framealpha=0.8, bbox_to_anchor=(0.5, 0 ))
         
        ax6.axis('off')  # Remove axes for cleaner world map look
        
    # Create animation
    anim = animation.FuncAnimation(fig, animate, frames=num_frames, interval=800, repeat=True)
    
    # Save animation
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(simulation_path, f"climate_3layer_animation_{timestamp}.gif")
    print(f"Saving animation as {filename}...")
    anim.save(filename, writer='pillow', fps=1.5, dpi=72)
    plt.close()
    print(f"SUCCESS: Animation saved: {filename}")
    return filename

def collect_all_visualization_data(simulation_path, climate_framework, num_rounds):
    """Collect all visualization data from simulation output."""
    
    # If num_rounds is None, detect it from CSV files
    if num_rounds is None:
        production_file = os.path.join(simulation_path, 'panel_commodity_producer_production.csv')
        if not os.path.exists(production_file):
            print(f"ERROR: Simulation output not found in: {simulation_path}")
            return None
        
        try:
            df = pd.read_csv(production_file)
            num_rounds = df['round'].max() + 1
            print(f"Detected {num_rounds} rounds in simulation output")
        except Exception as e:
            print(f"ERROR: Error reading simulation data: {e}")
            return None
    
    print(f"Collecting visualization data for {num_rounds} rounds...")
    
    visualization_data = {
        'rounds': [],
        'agent_data': [],
        'production_data': [],
        'inventories': [],
        'wealth_data': [],
        'overhead_costs': [],
        'pricing': [],
        'debt': [],
        'climate_events': []
    }
    
    for round_num in range(num_rounds):
        print(f"  Processing round {round_num}...")
        
        # Collect data for this round
        round_data = collect_simulation_data(simulation_path, round_num, climate_framework)
        
        # Store in visualization data structure
        visualization_data['rounds'].append(round_num)
        visualization_data['agent_data'].append(round_data['agents'])
        visualization_data['production_data'].append(round_data['production'])
        visualization_data['inventories'].append(round_data['inventories'])
        visualization_data['wealth_data'].append(round_data['wealth'])
        visualization_data['overhead_costs'].append(round_data['overhead_costs'])
        visualization_data['pricing'].append(round_data['pricing'])
        visualization_data['debt'].append(round_data['debt'])
        visualization_data['climate_events'].append(round_data['climate'])
    
    print(f"SUCCESS: Collected visualization data for {num_rounds} rounds")
    return visualization_data

def run_animation_visualizations(simulation_path):
    """Main function to run all animation visualizations from simulation output."""
    
    print("Starting Animation Visualizer for Climate 3-Layer Model")
    print("=" * 60)
    
    # Try to detect number of rounds from CSV files
    production_file = os.path.join(simulation_path, 'panel_commodity_producer_production.csv')
    if not os.path.exists(production_file):
        print(f"ERROR: Simulation output not found in: {simulation_path}")
        print("Make sure you've run the simulation first!")
        return
    
    try:
        df = pd.read_csv(production_file)
        num_rounds = df['round'].max() + 1
        print(f"Detected {num_rounds} rounds in simulation output")
    except Exception as e:
        print(f"ERROR: Error reading simulation data: {e}")
        return
    
    # Check if this is a climate simulation and look for baseline
    baseline_path = None
    is_climate_simulation = False
    
    # Check if this path contains "climate" in the name
    if "climate" in os.path.basename(simulation_path):
        is_climate_simulation = True
        # Look for baseline simulation in the same directory
        parent_dir = os.path.dirname(simulation_path)
        base_name = os.path.basename(simulation_path).replace("climate", "baseline")
        potential_baseline = os.path.join(parent_dir, base_name)
        
        if os.path.exists(potential_baseline):
            baseline_path = potential_baseline
            print(f"Found baseline simulation: {baseline_path}")
        else:
            # Try alternative naming patterns
            for item in os.listdir(parent_dir):
                if "baseline" in item and os.path.isdir(os.path.join(parent_dir, item)):
                    baseline_path = os.path.join(parent_dir, item)
                    print(f"Found baseline simulation: {baseline_path}")
                    break
    
    # Load geographical assignments and climate events from CSV files
    print("Loading geographical assignments from simulation data...")
    geographical_assignments = load_geographical_assignments(simulation_path)
    
    print("Loading climate events from simulation data...")
    climate_events_history = load_climate_events(simulation_path)
    
    # Ensure we have enough rounds in climate events (pad with empty events if needed)
    while len(climate_events_history) < num_rounds:
        climate_events_history.append({})
    
    # Create simple climate framework
    climate_framework = ClimateFrameworkFromData(geographical_assignments, climate_events_history)
    
    # Collect visualization data for current simulation
    visualization_data = collect_all_visualization_data(
        simulation_path, climate_framework, num_rounds
    )
    
    if not visualization_data['rounds']:
        print("ERROR: No visualization data collected!")
        return
    
    # If we found a baseline simulation, collect its data too
    baseline_data = None
    if baseline_path and is_climate_simulation:
        print("Collecting baseline simulation data for comparison...")
        try:
            baseline_geo = load_geographical_assignments(baseline_path)
            baseline_climate = load_climate_events(baseline_path)
            baseline_framework = ClimateFrameworkFromData(baseline_geo, baseline_climate)
            
            # Ensure baseline has enough rounds
            while len(baseline_climate) < num_rounds:
                baseline_climate.append({})
            
            baseline_data = collect_all_visualization_data(
                baseline_path, baseline_framework, num_rounds
            )
            print("Baseline data collected successfully")
        except Exception as e:
            print(f"Warning: Could not collect baseline data: {e}")
            baseline_data = None
    
    # Create visualizations
    print("\nCreating time-evolving visualizations...")
    
    # Create time evolution plot (with baseline if available)
    time_plot_file = create_time_evolution_visualization(
        visualization_data, simulation_path, baseline_data
    )
    
    # Create animated visualization (with baseline if available)
    animation_file = create_animated_supply_chain(
        visualization_data, simulation_path, baseline_data
    )
    
    print(f"\nAnimation visualizations completed!")
    print(f"Time evolution plot: {time_plot_file}")
    print(f"Animation: {animation_file}")
    
    return {
        'time_plot': time_plot_file,
        'animation': animation_file,
        'visualization_data': visualization_data
    }

def run_comparison_visualizations(baseline_path, climate_path):
    """
    Create comparison visualizations between baseline and climate simulations.
    
    Args:
        baseline_path: Path to baseline simulation results
        climate_path: Path to climate simulation results
    
    Returns:
        Dictionary with paths to created visualizations
    """
    print("🔔 Starting Comparison Visualizer for Baseline vs Climate Simulations")
    print("    ============================================================")
    
    try:
        # Load data from both simulations
        print("Loading baseline simulation data...")
        baseline_geo = load_geographical_assignments(baseline_path)
        baseline_climate = load_climate_events(baseline_path)
        baseline_framework = ClimateFrameworkFromData(baseline_geo, baseline_climate)
        
        print("Loading climate simulation data...")
        climate_geo = load_geographical_assignments(climate_path)
        climate_climate = load_climate_events(climate_path)
        climate_framework = ClimateFrameworkFromData(climate_geo, climate_climate)
        
        # Determine number of rounds (use the shorter simulation)
        baseline_rounds = len(baseline_climate)
        climate_rounds = len(climate_climate)
        num_rounds = min(baseline_rounds, climate_rounds)
        
        print(f"Detected {num_rounds} rounds in both simulations")
        
        # Collect data from both simulations
        print("Collecting baseline simulation data...")
        baseline_data = collect_all_visualization_data(baseline_path, baseline_framework, num_rounds)
        
        print("Collecting climate simulation data...")
        climate_data = collect_all_visualization_data(climate_path, climate_framework, num_rounds)
        
        # Create comparison visualizations
        print("Creating comparison visualizations...")
        
        # Create time evolution comparison
        time_plot_path = create_comparison_time_evolution(
            baseline_data, climate_data, baseline_path, climate_path, climate_framework
        )
        
        # Create comparison animation
        animation_path = create_comparison_animation(
            baseline_data, climate_data, baseline_path, climate_path
        )
        
        return {
            'time_plot': time_plot_path,
            'animation': animation_path
        }
        
    except Exception as e:
        print(f"ERROR: Failed to create comparison visualizations: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_comparison_time_evolution(baseline_data, climate_data, baseline_path, climate_path, climate_framework=None):
    """Create time evolution comparison plot showing baseline vs climate effects."""
    
    # Create a large figure with multiple subplots
    fig, axes = plt.subplots(3, 2, figsize=(20, 15))
    fig.suptitle('Baseline vs Climate Simulation Comparison', fontsize=16, fontweight='bold')
    
    # Plot 1: Total Production (separate plot to avoid clutter)
    ax1 = axes[0, 0]
    rounds = list(range(len(baseline_data)))
    
    # Extract production data
    baseline_production = [safe_extract(baseline_data, 'total_production')[i] for i in rounds]
    climate_production = [safe_extract(climate_data, 'total_production')[i] for i in rounds]
    
    ax1.plot(rounds, baseline_production, 'b--', linewidth=2, label='Baseline', alpha=0.8)
    ax1.plot(rounds, climate_production, 'b-', linewidth=3, label='Climate Stressed', alpha=0.9)
    ax1.set_title('Total Production Over Time', fontweight='bold')
    ax1.set_xlabel('Round')
    ax1.set_ylabel('Total Production')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Add climate events to production plot
    if climate_framework:
        add_climate_shocks_to_comparison(ax1, climate_framework, "Production")
    
    # Plot 2: Total Inventory (separate plot)
    ax2 = axes[0, 1]
    baseline_inventory = [safe_extract(baseline_data, 'total_inventory')[i] for i in rounds]
    climate_inventory = [safe_extract(climate_data, 'total_inventory')[i] for i in rounds]
    
    ax2.plot(rounds, baseline_inventory, 'g--', linewidth=2, label='Baseline', alpha=0.8)
    ax2.plot(rounds, climate_inventory, 'g-', linewidth=3, label='Climate Stressed', alpha=0.9)
    ax2.set_title('Total Inventory Over Time', fontweight='bold')
    ax2.set_xlabel('Round')
    ax2.set_ylabel('Total Inventory')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    if climate_framework:
        add_climate_shocks_to_comparison(ax2, climate_framework, "Inventory")
    
    # Plot 3: Average Wealth (separate plot)
    ax3 = axes[1, 0]
    baseline_wealth = [safe_extract(baseline_data, 'avg_wealth')[i] for i in rounds]
    climate_wealth = [safe_extract(climate_data, 'avg_wealth')[i] for i in rounds]
    
    ax3.plot(rounds, baseline_wealth, 'orange', linestyle='--', linewidth=2, label='Baseline', alpha=0.8)
    ax3.plot(rounds, climate_wealth, 'orange', linestyle='-', linewidth=3, label='Climate Stressed', alpha=0.9)
    ax3.set_title('Average Household Wealth', fontweight='bold')
    ax3.set_xlabel('Round')
    ax3.set_ylabel('Average Wealth ($)')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    if climate_framework:
        add_climate_shocks_to_comparison(ax3, climate_framework, "Wealth")
    
    # Plot 4: Total Debt (separate plot)
    ax4 = axes[1, 1]
    baseline_debt = [safe_extract(baseline_data, 'total_debt')[i] for i in rounds]
    climate_debt = [safe_extract(climate_data, 'total_debt')[i] for i in rounds]
    
    ax4.plot(rounds, baseline_debt, 'red', linestyle='--', linewidth=2, label='Baseline', alpha=0.8)
    ax4.plot(rounds, climate_debt, 'red', linestyle='-', linewidth=3, label='Climate Stressed', alpha=0.9)
    ax4.set_title('Total Household Debt', fontweight='bold')
    ax4.set_xlabel('Round')
    ax4.set_ylabel('Total Debt ($)')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    if climate_framework:
        add_climate_shocks_to_comparison(ax4, climate_framework, "Debt")
    
    # Plot 5: Average Overhead Costs (separate plot)
    ax5 = axes[2, 0]
    baseline_overhead = [safe_extract(baseline_data, 'avg_overhead')[i] for i in rounds]
    climate_overhead = [safe_extract(climate_data, 'avg_overhead')[i] for i in rounds]
    
    ax5.plot(rounds, baseline_overhead, 'purple', linestyle='--', linewidth=2, label='Baseline', alpha=0.8)
    ax5.plot(rounds, climate_overhead, 'purple', linestyle='-', linewidth=3, label='Climate Stressed', alpha=0.9)
    ax5.set_title('Average Firm Overhead Costs', fontweight='bold')
    ax5.set_xlabel('Round')
    ax5.set_ylabel('Average Overhead ($)')
    ax5.legend()
    ax5.grid(True, alpha=0.3)
    
    if climate_framework:
        add_climate_shocks_to_comparison(ax5, climate_framework, "Overhead")
    
    # Plot 6: Average Prices (separate plot)
    ax6 = axes[2, 1]
    baseline_prices = [safe_extract(baseline_data, 'avg_prices')[i] for i in rounds]
    climate_prices = [safe_extract(climate_data, 'avg_prices')[i] for i in rounds]
    
    ax6.plot(rounds, baseline_prices, 'brown', linestyle='--', linewidth=2, label='Baseline', alpha=0.8)
    ax6.plot(rounds, climate_prices, 'brown', linestyle='-', linewidth=3, label='Climate Stressed', alpha=0.9)
    ax6.set_title('Average Prices', fontweight='bold')
    ax6.set_xlabel('Round')
    ax6.set_ylabel('Average Price ($)')
    ax6.legend()
    ax6.grid(True, alpha=0.3)
    
    if climate_framework:
        add_climate_shocks_to_comparison(ax6, climate_framework, "Prices")
    
    plt.tight_layout()
    
    # Save the comparison plot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'baseline_vs_climate_comparison_{timestamp}.png'
    save_path = os.path.join(os.path.dirname(climate_path), filename)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"🔔 SUCCESS: Time evolution comparison saved: {save_path}")
    return save_path


def create_comparison_animation(baseline_data, climate_data, baseline_path, climate_path):
    """Create animated comparison showing baseline vs climate effects over time."""
    
    # Create figure with subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Baseline vs Climate Simulation Animation', fontsize=16, fontweight='bold')
    
    # Set up the animation
    num_rounds = len(baseline_data)
    
    def animate(frame):
        # Clear all subplots
        ax1.clear()
        ax2.clear()
        ax3.clear()
        ax4.clear()
        
        # Plot 1: Production comparison
        rounds = list(range(frame + 1))
        baseline_prod = [safe_extract(baseline_data, 'total_production')[i] for i in range(frame+1)]
        climate_prod = [safe_extract(climate_data, 'total_production')[i] for i in range(frame+1)]
        
        ax1.plot(rounds, baseline_prod, 'b--', linewidth=2, label='Baseline', alpha=0.8)
        ax1.plot(rounds, climate_prod, 'b-', linewidth=3, label='Climate Stressed', alpha=0.9)
        ax1.set_title('Total Production', fontweight='bold')
        ax1.set_xlabel('Round')
        ax1.set_ylabel('Production')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_xlim(0, num_rounds - 1)
        
        # Plot 2: Wealth comparison
        baseline_wealth = [safe_extract(baseline_data, 'avg_wealth')[i] for i in range(frame+1)]
        climate_wealth = [safe_extract(climate_data, 'avg_wealth')[i] for i in range(frame+1)]
        
        ax2.plot(rounds, baseline_wealth, 'orange', linestyle='--', linewidth=2, label='Baseline', alpha=0.8)
        ax2.plot(rounds, climate_wealth, 'orange', linestyle='-', linewidth=3, label='Climate Stressed', alpha=0.9)
        ax2.set_title('Average Wealth', fontweight='bold')
        ax2.set_xlabel('Round')
        ax2.set_ylabel('Wealth ($)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.set_xlim(0, num_rounds - 1)
        
        # Plot 3: Debt comparison
        baseline_debt = [safe_extract(baseline_data, 'total_debt')[i] for i in range(frame+1)]
        climate_debt = [safe_extract(climate_data, 'total_debt')[i] for i in range(frame+1)]
        
        ax3.plot(rounds, baseline_debt, 'red', linestyle='--', linewidth=2, label='Baseline', alpha=0.8)
        ax3.plot(rounds, climate_debt, 'red', linestyle='-', linewidth=3, label='Climate Stressed', alpha=0.9)
        ax3.set_title('Total Debt', fontweight='bold')
        ax3.set_xlabel('Round')
        ax3.set_ylabel('Debt ($)')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        ax3.set_xlim(0, num_rounds - 1)
        
        # Plot 4: Inventory comparison
        baseline_inv = [safe_extract(baseline_data, 'total_inventory')[i] for i in range(frame+1)]
        climate_inv = [safe_extract(climate_data, 'total_inventory')[i] for i in range(frame+1)]
        
        ax4.plot(rounds, baseline_inv, 'g--', linewidth=2, label='Baseline', alpha=0.8)
        ax4.plot(rounds, climate_inv, 'g-', linewidth=3, label='Climate Stressed', alpha=0.9)
        ax4.set_title('Total Inventory', fontweight='bold')
        ax4.set_xlabel('Round')
        ax4.set_ylabel('Inventory')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        ax4.set_xlim(0, num_rounds - 1)
        
        # Add round indicator
        fig.text(0.5, 0.02, f'Round {frame + 1} / {num_rounds}', ha='center', va='bottom', fontsize=14, fontweight='bold')
    
    # Create animation
    anim = animation.FuncAnimation(fig, animate, frames=num_rounds, interval=500, repeat=True)
    
    # Save animation
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'baseline_vs_climate_animation_{timestamp}.gif'
    save_path = os.path.join(os.path.dirname(climate_path), filename)
    
    print(f"🔔 Saving comparison animation as {save_path}...")
    anim.save(save_path, writer='pillow', fps=2)
    plt.close()
    
    print(f"🔔 SUCCESS: Comparison animation saved: {save_path}")
    return save_path


def add_climate_shocks_to_comparison(ax, climate_framework, plot_type):
    """Add climate shock indicators to comparison plots."""
    if not climate_framework or not climate_framework.climate_events_history:
        return
        
    for round_num, round_events in enumerate(climate_framework.climate_events_history):
        if round_events:  # If there are any events in this round
            # Add vertical line for climate events
            ax.axvline(x=round_num, color='red', linestyle='--', alpha=0.7, linewidth=1)
            
            # Add text label for first few events to avoid clutter
            if round_num < 5:  # Only label first 5 events
                ax.text(round_num, ax.get_ylim()[1] * 0.95, '🌪️', 
                       ha='center', va='top', fontsize=10, color='red')


def safe_extract(data_list, key):
    """Safely extract data from a list of dictionaries."""
    try:
        return [data.get(key, 0) for data in data_list]
    except (KeyError, IndexError, AttributeError):
        return [0] * len(data_list)


def main():
    """Main function to run animation visualizations from command line."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python animation_visualizer.py <results_parent_dir>")
        print("Example: python animation_visualizer.py results/expname/")
        return
    
    parent_dir = sys.argv[1]
    baseline_path = os.path.join(parent_dir, 'baseline')
    stressed_path = os.path.join(parent_dir, 'stressed')
    
    if not os.path.exists(baseline_path):
        print(f"ERROR: Baseline path does not exist: {baseline_path}")
        return
    if not os.path.exists(stressed_path):
        print(f"ERROR: Stressed path does not exist: {stressed_path}")
        return
    
    # Load climate framework and data for both runs
    print(f"Loading baseline data from: {baseline_path}")
    baseline_geo = load_geographical_assignments(baseline_path)
    baseline_climate = load_climate_events(baseline_path)
    baseline_framework = ClimateFrameworkFromData(baseline_geo, baseline_climate)
    baseline_data = collect_all_visualization_data(baseline_path, baseline_framework, num_rounds=None)
    
    print(f"Loading stressed data from: {stressed_path}")
    stressed_geo = load_geographical_assignments(stressed_path)
    stressed_climate = load_climate_events(stressed_path)
    stressed_framework = ClimateFrameworkFromData(stressed_geo, stressed_climate)
    stressed_data = collect_all_visualization_data(stressed_path, stressed_framework, num_rounds=None)
    
    # Run the animation visualizations with both datasets
    print("\nCreating combined animation with baseline and stressed data...")
    animation_file = create_animated_supply_chain(stressed_data, parent_dir, baseline_data=baseline_data)
    print(f"\n🎉 Animation created: {animation_file}")

# Update the animation layout to 3 rows × 4 columns, with the last column for inventory, prices, and debt
# (The rest of the create_animated_supply_chain function should be updated accordingly, see previous edits)

if __name__ == "__main__":
    main()
