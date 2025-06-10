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
                        
                        # Extract agent types from the data_type field (which contains the rule name)
                        # The agent types affected are implicit from which agents are in the targeted continents
                        agent_types = []  # We'll determine this from the geographical assignments
                        
                        events_dict[event_name] = {
                            'type': 'configurable_shock',
                            'rule_name': first_row['data_type'],
                            'agent_types': agent_types,  # Will be filled later
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
            
            # Check if this agent's continent is affected
            if 'all' in affected_continents:
                return True
            
            agent_continent = get_agent_continent(agent_type, agent_id, climate_framework)
            if agent_continent in affected_continents:
                return True
        
        elif event_key in ['North America', 'Europe', 'Asia', 'South America', 'Africa']:
            # Old format where event key is continent name
            agent_continent = get_agent_continent(agent_type, agent_id, climate_framework)
            if agent_continent == event_key:
                return True
    
    return False

def get_agent_continent(agent_type, agent_id, climate_framework):
    """Get the continent assignment for a specific agent."""
    assignments = climate_framework.geographical_assignments[agent_type]
    return assignments[agent_id]['continent']

def create_time_evolution_visualization(visualization_data, simulation_path):
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
    
    # Count climate events by round
    climate_stress_counts = []
    for round_agents in visualization_data['agent_data']:
        stress_count = sum([1 for agent in round_agents if agent['climate_stressed']])
        climate_stress_counts.append(stress_count)
    
    # Create comprehensive time evolution plot with 2x4 grid
    fig, ((ax1, ax2, ax3, ax4), (ax5, ax6, ax7, ax8)) = plt.subplots(2, 4, figsize=(24, 12))
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
    ax1.plot(rounds, commodity_production, 'o-', label='Commodity Production', color='#8B4513', linewidth=2, markersize=4)
    ax1.plot(rounds, intermediary_production, 's-', label='Intermediary Production', color='#DAA520', linewidth=2, markersize=4)
    ax1.plot(rounds, final_goods_production, '^-', label='Final Goods Production', color='#00FF00', linewidth=2, markersize=4)
    add_climate_shocks(ax1)
    ax1.set_title('Production Levels Over Time', fontweight='bold')
    ax1.set_xlabel('Round')
    ax1.set_ylabel('Production Level')
    ax1.legend(loc='center right', fontsize=8)
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Inventory evolution over time
    ax2.plot(rounds, commodity_inventory, 'o-', label='Commodity Inventory', color='#8B4513', linewidth=2, markersize=4)
    ax2.plot(rounds, intermediary_inventory, 's-', label='Intermediary Inventory', color='#DAA520', linewidth=2, markersize=4)
    ax2.plot(rounds, final_goods_inventory, '^-', label='Final Goods Inventory', color='#00FF00', linewidth=2, markersize=4)
    add_climate_shocks(ax2)
    ax2.set_title('Inventory Levels Over Time', fontweight='bold')
    ax2.set_xlabel('Round')
    ax2.set_ylabel('Inventory Level')
    ax2.legend(loc='center right', fontsize=8)
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Overhead Costs evolution over time
    ax3.plot(rounds, commodity_overhead, 'o-', label='Commodity Overhead', color='#8B4513', linewidth=2, markersize=4)
    ax3.plot(rounds, intermediary_overhead, 's-', label='Intermediary Overhead', color='#DAA520', linewidth=2, markersize=4)
    ax3.plot(rounds, final_goods_overhead, '^-', label='Final Goods Overhead', color='#00FF00', linewidth=2, markersize=4)
    add_climate_shocks(ax3)
    ax3.set_title('Overhead Costs Over Time', fontweight='bold')
    ax3.set_xlabel('Round')
    ax3.set_ylabel('Overhead Cost ($)')
    ax3.legend(loc='center right', fontsize=8)
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Pricing evolution over time
    ax4.plot(rounds, commodity_price, 'o-', label='Commodity Price', color='#8B4513', linewidth=2, markersize=4)
    ax4.plot(rounds, intermediary_price, 's-', label='Intermediary Price', color='#DAA520', linewidth=2, markersize=4)
    ax4.plot(rounds, final_goods_price, '^-', label='Final Goods Price', color='#00FF00', linewidth=2, markersize=4)
    add_climate_shocks(ax4)
    ax4.set_title('Pricing Evolution Over Time', fontweight='bold')
    ax4.set_xlabel('Round')
    ax4.set_ylabel('Price ($)')
    ax4.legend(loc='center right', fontsize=8)
    ax4.grid(True, alpha=0.3)
    
    # Plot 5: Wealth evolution by sector (including debt)
    ax5.plot(rounds, commodity_wealth, 'o-', label='Commodity Wealth', color='#8B4513', linewidth=2, markersize=4)
    ax5.plot(rounds, intermediary_wealth, 's-', label='Intermediary Wealth', color='#DAA520', linewidth=2, markersize=4)
    ax5.plot(rounds, final_goods_wealth, '^-', label='Final Goods Wealth', color='#00FF00', linewidth=2, markersize=4)
    ax5.plot(rounds, household_wealth, 'd-', label='Household Wealth', color='#4169E1', linewidth=2, markersize=4)
    add_climate_shocks(ax5)
    ax5.set_title('Wealth Evolution by Sector', fontweight='bold')
    ax5.set_xlabel('Round')
    ax5.set_ylabel('Wealth ($)')
    ax5.legend(loc='center right', fontsize=8)
    ax5.grid(True, alpha=0.3)
    
    # Plot 6: Debt evolution
    ax6.plot(rounds, household_debt, 'd--', label='Household Debt', color='#4169E1', linewidth=2, markersize=4, alpha=0.6)
    ax6.plot(rounds, firm_debt, 's--', label='All Firms Debt', color='#666666', linewidth=2, markersize=4, alpha=0.6)
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
    
    # Plot 8: Summary statistics with overhead and pricing on twin axis
    total_production = [c + i + f for c, i, f in zip(commodity_production, intermediary_production, final_goods_production)]
    total_overhead = [c + i + f for c, i, f in zip(commodity_overhead, intermediary_overhead, final_goods_overhead)]
    avg_price = [(c + i + f) / 3 for c, i, f in zip(commodity_price, intermediary_price, final_goods_price)]
    
    ax8.plot(rounds, total_production, 'g-', label='Total Production', linewidth=3, alpha=0.8)
    ax8_twin = ax8.twinx()
    ax8_twin.plot(rounds, total_overhead, 'r--', label='Total Overhead', linewidth=2, alpha=0.8)
    ax8_twin.plot(rounds, avg_price, 'b:', label='Avg Price', linewidth=2, alpha=0.8)
    
    add_climate_shocks(ax8)
    ax8.set_title('Economic Summary', fontweight='bold')
    ax8.set_xlabel('Round')
    ax8.set_ylabel('Production', color='green')
    ax8_twin.set_ylabel('Overhead ($) & Price ($)', color='red')
    ax8.legend(loc='upper left', fontsize=8)
    ax8_twin.legend(loc='upper right', fontsize=8)
    ax8.grid(True, alpha=0.3)
    
    # Save the time evolution plot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{simulation_path}/climate_3layer_time_evolution_{timestamp}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"SUCCESS: Time evolution visualization saved: {filename}")
    
    plt.close()
    return filename

def create_animated_supply_chain(visualization_data, simulation_path):
    """Create animated GIF showing supply chain evolution over time."""
    
    print("Creating animated supply chain visualization...")
    
    # Set up the animation plot with 5 subplots in a custom layout
    # Layout: Network (big left), Production/Inventory (top right), Overhead/Pricing (middle right), 
    #         Geography (bottom left), Wealth (bottom right)
    fig = plt.figure(figsize=(16 , 15)) 
    fig.suptitle('Climate 3-Layer Supply Chain Evolution', fontsize=16, fontweight='bold')
    
    # Create custom subplot layout
    ax1 = plt.subplot2grid((3, 2), (0, 0), rowspan=2)  # Network plot (big, left side)
    ax2 = plt.subplot2grid((3, 2), (0, 1))             # Production/Inventory (top right)
    ax3 = plt.subplot2grid((3, 2), (1, 1))             # Overhead/Pricing (middle right)
    ax4 = plt.subplot2grid((3, 2), (2, 0))             # Geography (bottom left)
    ax5 = plt.subplot2grid((3, 2), (2, 1))             # Wealth (bottom right)
    
    # Create the twin axis outside the animate function to avoid overlapping axes
    ax3_twin = ax3.twinx()
    
    # Define continent positions for the world map (simplified layout)
    continent_positions = {
        'North America': (0.5, 3, 1.5, 1.5),
        'South America': (0.5, 1, 1.5, 1.5),
        'Europe': (3, 3.5, 1, 1),
        'Asia': (4.5, 3, 1.5, 1.5),
        'Africa': (3, 1.5, 1, 1.5),
        'Oceania': (5.5, 0.5, 1, 1)
    }
    def animate(frame):
        # Clear all subplots
        for ax in [ax1, ax2, ax3, ax4, ax5]:
            ax.clear()
        # Clear the twin axis as well
        ax3_twin.clear()
        
        if frame >= len(visualization_data['rounds']):
            return
        
        round_num = visualization_data['rounds'][frame]
        agent_data = visualization_data['agent_data'][frame]
        production_data = visualization_data['production_data'][frame]
        wealth_data = visualization_data['wealth_data'][frame]
        climate_events = visualization_data['climate_events'][frame]
        
        # Plot 1: Agent network with stress status
        ax1.set_title(f'Supply Chain Network - Round {round_num}')
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
        
        # Add legend for network plot indicators
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
        
        ax1.legend(handles=legend_elements, loc='upper right', fontsize=8, 
                  title='Agent Status', title_fontsize=9, framealpha=0.8)
        
        # Plot 2: Production & Inventory Levels Over Time
        ax2.set_title('Production & Inventory Levels Over Time')
        rounds_so_far = visualization_data['rounds'][:frame+1]
        
        commodity_prod = [visualization_data['production_data'][i].get('commodity', 0) for i in range(frame+1)]
        intermediary_prod = [visualization_data['production_data'][i].get('intermediary', 0) for i in range(frame+1)]
        final_goods_prod = [visualization_data['production_data'][i].get('final_goods', 0) for i in range(frame+1)]
        
        # Add inventory data
        commodity_inventory = [visualization_data['inventories'][i].get('commodity', 0) for i in range(frame+1)]
        intermediary_inventory = [visualization_data['inventories'][i].get('intermediary', 0) for i in range(frame+1)]
        final_goods_inventory = [visualization_data['inventories'][i].get('final_goods', 0) for i in range(frame+1)]
        
        # Plot production (solid lines)
        ax2.plot(rounds_so_far, commodity_prod, 'o-', label='Commodity Prod', color='#8B4513', linewidth=2, markersize=3)
        ax2.plot(rounds_so_far, intermediary_prod, 's-', label='Intermediary Prod', color='#DAA520', linewidth=2, markersize=3)
        ax2.plot(rounds_so_far, final_goods_prod, '^-', label='Final Goods Prod', color='#00FF00', linewidth=2, markersize=3)
        
        # Plot inventory (dashed lines)
        ax2.plot(rounds_so_far, commodity_inventory, 'o--', label='Commodity Inv', color='#8B4513', linewidth=1, alpha=0.7, markersize=2)
        ax2.plot(rounds_so_far, intermediary_inventory, 's--', label='Intermediary Inv', color='#DAA520', linewidth=1, alpha=0.7, markersize=2)
        ax2.plot(rounds_so_far, final_goods_inventory, '^--', label='Final Goods Inv', color='#00FF00', linewidth=1, alpha=0.7, markersize=2)
        
        ax2.set_ylabel('Production & Inventory', color='black')
        ax2.legend(fontsize=8)
        ax2.set_xlabel('Round')
        ax2.grid(True, alpha=0.3)
        
        # Add climate shock indicators
        for shock_round in range(frame + 1):
            if shock_round < len(visualization_data['climate_events']):
                events = visualization_data['climate_events'][shock_round]
                if events:
                    ax2.axvline(x=shock_round, color='red', linestyle='--', alpha=0.6, linewidth=1)
        
        # Plot 3: Overhead Costs & Pricing Over Time
        ax3.set_title('Overhead Costs & Pricing Over Time')
        
        # Get overhead and pricing data
        commodity_overhead = [visualization_data['overhead_costs'][i].get('commodity', 0) for i in range(frame+1)]
        intermediary_overhead = [visualization_data['overhead_costs'][i].get('intermediary', 0) for i in range(frame+1)]
        final_goods_overhead = [visualization_data['overhead_costs'][i].get('final_goods', 0) for i in range(frame+1)]
        
        commodity_price = [visualization_data['pricing'][i].get('commodity', 0) for i in range(frame+1)]
        intermediary_price = [visualization_data['pricing'][i].get('intermediary', 0) for i in range(frame+1)]
        final_goods_price = [visualization_data['pricing'][i].get('final_goods', 0) for i in range(frame+1)]
        
        # Plot overhead (solid lines) - LEFT Y-AXIS
        ax3.plot(rounds_so_far, commodity_overhead, 'o-', label='Commodity Overhead', color='#8B4513', linewidth=2, markersize=3)
        ax3.plot(rounds_so_far, intermediary_overhead, 's-', label='Intermediary Overhead', color='#DAA520', linewidth=2, markersize=3)
        ax3.plot(rounds_so_far, final_goods_overhead, '^-', label='Final Goods Overhead', color='#00FF00', linewidth=2, markersize=3)
        ax3.set_ylabel('Overhead Costs ($)', color='black')
        
        # Plot pricing (dashed lines) - RIGHT Y-AXIS using the pre-created twin axis
        ax3_twin.plot(rounds_so_far, commodity_price, 'o--', label='Commodity Price', color='#8B4513', alpha=0.7, linewidth=1, markersize=2)
        ax3_twin.plot(rounds_so_far, intermediary_price, 's--', label='Intermediary Price', color='#DAA520', alpha=0.7, linewidth=1, markersize=2)
        ax3_twin.plot(rounds_so_far, final_goods_price, '^--', label='Final Goods Price', color='#00FF00', alpha=0.7, linewidth=1, markersize=2)
        ax3_twin.set_ylabel('Prices ($)', color='gray')
        ax3_twin.tick_params(axis='y', labelcolor='gray')
        ax3_twin.yaxis.set_label_position('right')
        
        # Add climate shock indicators
        for shock_round in range(frame + 1):
            if shock_round < len(visualization_data['climate_events']):
                events = visualization_data['climate_events'][shock_round]
                if events:
                    ax3.axvline(x=shock_round, color='red', linestyle='--', alpha=0.6, linewidth=1)
        
        # Combine legends
        lines1, labels1 = ax3.get_legend_handles_labels()
        lines2, labels2 = ax3_twin.get_legend_handles_labels()
        ax3.legend(lines1 + lines2, labels1 + labels2, fontsize=8)
        
        ax3.set_xlabel('Round')
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Geographical Distribution World Map
        ax4.set_title(f'Global Climate Impact Map - Round {round_num}')
        ax4.set_xlim(0, 7)
        ax4.set_ylim(0, 5)
        ax4.set_aspect('equal')
        
        # Draw continent shapes (simplified rectangles)
        continent_colors = {}
        for continent in continent_positions.keys():
            # Default color
            base_color = '#90EE90'  # Light green for normal
            
            # Check if this continent has climate stress
            if climate_events and continent in climate_events:
                if 'stress' in str(climate_events[continent]):
                    base_color = '#FF6B6B'  # Red for climate stress
            
            continent_colors[continent] = base_color
            
            # Draw continent rectangle
            x, y, width, height = continent_positions[continent]
            continent_rect = plt.Rectangle((x, y), width, height, 
                                         facecolor=base_color, 
                                         edgecolor='black', 
                                         alpha=0.6)
            ax4.add_patch(continent_rect)
            
            # Add continent label
            ax4.text(x + width/2, y + height/2, continent.replace(' ', '\n'), 
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
                        
                        ax4.scatter(pos_x, pos_y, c=color, s=size, marker=agent_symbols[i], 
                                  alpha=0.9, edgecolors='black', linewidth=1)
                        
                        # Add count label
                        ax4.text(pos_x, pos_y - 0.15, str(counts[agent_type]), 
                               ha='center', va='center', fontsize=6, fontweight='bold')
        
        # Add legend for agent types
        legend_elements = []
        agent_type_names = ['Commodity Producers', 'Intermediary Firms', 'Final Goods Firms', 'Households']
        legend_agent_colors = ['#8B4513', '#DAA520', '#00FF00', '#4169E1']
        agent_symbols = ['o', 's', '^', 'D']
        
        for i, (name, color, symbol) in enumerate(zip(agent_type_names, legend_agent_colors, agent_symbols)):
            legend_elements.append(plt.Line2D([0], [0], marker=symbol, color='w', 
                                            markerfacecolor=color, markersize=8, 
                                            label=name, markeredgecolor='black', markeredgewidth=0.5))
        
        # Add stress indicator to legend
        legend_elements.append(plt.Line2D([0], [0], marker='o', color='w', 
                                        markerfacecolor='#FF0000', markersize=10, 
                                        label='Climate Stressed', markeredgecolor='black', markeredgewidth=0.5))
        
        ax4.legend(handles=legend_elements, loc='lower center', fontsize=8, 
                  title='Agent Types', title_fontsize=9, framealpha=0.8)
         
        ax4.axis('off')  # Remove axes for cleaner world map look
        
        # Plot 5: Wealth time-series by sector
        ax5.set_title('Wealth Evolution by Sector')
        
        # Collect wealth data over time up to current frame
        commodity_wealth_series = [visualization_data['wealth_data'][i].get('commodity', 0) for i in range(frame+1)]
        intermediary_wealth_series = [visualization_data['wealth_data'][i].get('intermediary', 0) for i in range(frame+1)]
        final_goods_wealth_series = [visualization_data['wealth_data'][i].get('final_goods', 0) for i in range(frame+1)]
        household_wealth_series = [visualization_data['wealth_data'][i].get('households', 0) for i in range(frame+1)]
        
        # Collect debt data over time up to current frame
        household_debt_series = [visualization_data['debt'][i].get('households', 0) for i in range(frame+1)]
        firm_debt_series = [visualization_data['debt'][i].get('firms', 0) for i in range(frame+1)]
        
        # Define consistent colors for agent types
        agent_colors = {
            'commodity': '#8B4513',
            'intermediary': '#DAA520', 
            'final_goods': '#00FF00',
            'households': '#4169E1'
        }
        
        # Plot wealth time-series lines (solid lines)
        ax5.plot(rounds_so_far, commodity_wealth_series, 'o-', label='Commodity Wealth', 
                color=agent_colors['commodity'], linewidth=2, markersize=4)
        ax5.plot(rounds_so_far, intermediary_wealth_series, 's-', label='Intermediary Wealth', 
                color=agent_colors['intermediary'], linewidth=2, markersize=4)
        ax5.plot(rounds_so_far, final_goods_wealth_series, '^-', label='Final Goods Wealth', 
                color=agent_colors['final_goods'], linewidth=2, markersize=4)
        ax5.plot(rounds_so_far, household_wealth_series, 'd-', label='Household Wealth', 
                color=agent_colors['households'], linewidth=2, markersize=4)
        
        # Plot debt lines (dashed lines with same colors but lighter alpha)
        ax5.plot(rounds_so_far, household_debt_series, 'd--', label='Household Debt', 
                color=agent_colors['households'], linewidth=2, markersize=4, alpha=0.6)
        
        # Calculate and plot total firm debt (combination of all firm types)
        ax5.plot(rounds_so_far, firm_debt_series, 's--', label='All Firms Debt', 
                color='#666666', linewidth=2, markersize=4, alpha=0.6)
        
        ax5.set_xlabel('Round')
        ax5.set_ylabel('Total Wealth ($)')
        ax5.legend(fontsize=8)
        ax5.grid(True, alpha=0.3)
        
        plt.tight_layout()
    
    # Create animation
    num_frames = len(visualization_data['rounds'])
    anim = animation.FuncAnimation(fig, animate, frames=num_frames, interval=1500, repeat=True)
    
    # Save animation
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{simulation_path}/climate_3layer_animation_{timestamp}.gif"
    
    print(f"Saving animation as {filename}...")
    anim.save(filename, writer='pillow', fps=1.5, dpi=72)
    print(f"SUCCESS: Animation saved: {filename}")
    
    plt.close()  # Clean up memory
    
    return filename

def collect_all_visualization_data(simulation_path, climate_framework, num_rounds):
    """Collect visualization data for all rounds from the simulation CSV files."""
    
    print("Collecting visualization data from simulation results...")
    visualization_data = {
        'rounds': [],
        'agent_data': [],
        'climate_events': [],
        'production_data': [],
        'wealth_data': [],
        'inventories': [],
        'overhead_costs': [],
        'pricing': [],
        'debt': []
    }
    
    # Read data for each round from the CSV files
    for r in range(num_rounds):
        round_data = collect_simulation_data(simulation_path, r, climate_framework)
        
        visualization_data['rounds'].append(r)
        visualization_data['agent_data'].append(round_data['agents'])
        visualization_data['climate_events'].append(round_data['climate'])
        visualization_data['production_data'].append(round_data['production'])
        visualization_data['wealth_data'].append(round_data['wealth'])
        visualization_data['inventories'].append(round_data['inventories'])
        visualization_data['overhead_costs'].append(round_data['overhead_costs'])
        visualization_data['pricing'].append(round_data['pricing'])
        visualization_data['debt'].append(round_data['debt'])
        
        # Add debug info
        total_production = sum(round_data['production'].values())
        total_inventory = sum(round_data['inventories'].values())
        print(f"    Round {r}: Production = {total_production:.2f}, Inventory = {total_inventory:.2f}")
    
    print("SUCCESS: Visualization data collection completed!")
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
    
    # Collect visualization data
    visualization_data = collect_all_visualization_data(
        simulation_path, climate_framework, num_rounds
    )
    
    if not visualization_data['rounds']:
        print("ERROR: No visualization data collected!")
        return
    
    # Create visualizations
    print("\nCreating time-evolving visualizations...")
    
    # Create time evolution plot
    time_plot_file = create_time_evolution_visualization(
        visualization_data, simulation_path
    )
    
    # Create animated visualization
    animation_file = create_animated_supply_chain(
        visualization_data, simulation_path
    )
    
    print(f"\nAnimation visualizations completed!")
    print(f"Time evolution plot: {time_plot_file}")
    print(f"Animation: {animation_file}")
    
    return {
        'time_plot': time_plot_file,
        'animation': animation_file,
        'visualization_data': visualization_data
    }

def main():
    """Command line interface for the animation visualizer."""
    
    if len(sys.argv) < 1:
        print("Usage: python animation_visualizer.py <simulation_path>")
        print("  simulation_path: Path to the simulation output directory")
        sys.exit(1)
    
    simulation_path = sys.argv[1]
    
    if not os.path.exists(simulation_path):
        print(f"ERROR: Simulation path does not exist: {simulation_path}")
        sys.exit(1)
    
    results = run_animation_visualizations(simulation_path)
    
    if results:
        print("\nSUCCESS: Animation visualization completed successfully!")
    else:
        print("\nERROR: Animation visualization failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()
