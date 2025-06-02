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
        print(f"⚠️ Climate summary file not found: {climate_summary_file}")
        print(f"   Creating fallback geographical assignments...")
        
        # Create default geographical assignments based on typical configuration
        geographical_assignments = {
            'commodity_producer': {},
            'intermediary_firm': {},
            'final_goods_firm': {},
            'household': {}
        }
        
        # Try to infer agent counts from CSV files
        try:
            # Check commodity producers
            commodity_file = os.path.join(simulation_path, 'panel_commodity_producer_production.csv')
            if os.path.exists(commodity_file):
                df = pd.read_csv(commodity_file)
                unique_names = df['name'].unique()
                continents = ['Europe', 'Asia', 'Africa']
                for i, name in enumerate(unique_names):
                    agent_id = int(name.replace('commodity_producer', ''))
                    geographical_assignments['commodity_producer'][agent_id] = {
                        'continent': continents[i % len(continents)],
                        'vulnerability': 0.1 + (i * 0.02)
                    }
            
            # Check intermediary firms
            intermediary_file = os.path.join(simulation_path, 'panel_intermediary_firm_production.csv')
            if os.path.exists(intermediary_file):
                df = pd.read_csv(intermediary_file)
                unique_names = df['name'].unique()
                continents = ['North America', 'Europe']
                for i, name in enumerate(unique_names):
                    agent_id = int(name.replace('intermediary_firm', ''))
                    geographical_assignments['intermediary_firm'][agent_id] = {
                        'continent': continents[i % len(continents)],
                        'vulnerability': 0.08 + (i * 0.02)
                    }
            
            # Check final goods firms
            final_goods_file = os.path.join(simulation_path, 'panel_final_goods_firm_production.csv')
            if os.path.exists(final_goods_file):
                df = pd.read_csv(final_goods_file)
                unique_names = df['name'].unique()
                continents = ['North America', 'South America']
                for i, name in enumerate(unique_names):
                    agent_id = int(name.replace('final_goods_firm', ''))
                    geographical_assignments['final_goods_firm'][agent_id] = {
                        'continent': continents[i % len(continents)],
                        'vulnerability': 0.05 + (i * 0.01)
                    }
            
            # Check households
            household_file = os.path.join(simulation_path, 'panel_household_consumption.csv')
            if os.path.exists(household_file):
                df = pd.read_csv(household_file)
                unique_names = df['name'].unique()
                continents = ['North America', 'Europe', 'Asia', 'South America', 'Africa']
                for i, name in enumerate(unique_names):
                    agent_id = int(name.replace('household', ''))
                    geographical_assignments['household'][agent_id] = {
                        'continent': continents[i % len(continents)],
                        'vulnerability': 0.06 + (i * 0.005)
                    }
            
            print(f"✅ Created fallback geographical assignments for {len(geographical_assignments)} agent types")
            for agent_type, assignments in geographical_assignments.items():
                print(f"    {agent_type}: {len(assignments)} agents")
                
        except Exception as e:
            print(f"⚠️ Error creating fallback assignments: {e}")
        
        return geographical_assignments
    
    try:
        df = pd.read_csv(climate_summary_file)
        
        # Filter for geographical assignments
        geo_df = df[df['data_type'] == 'geographical_assignment']
        
        # Convert to the expected format
        geographical_assignments = {}
        
        for _, row in geo_df.iterrows():
            agent_type = row['agent_type']
            agent_id = int(row['agent_id'])
            continent = row['continent']
            vulnerability = row['vulnerability']
            
            if agent_type not in geographical_assignments:
                geographical_assignments[agent_type] = {}
            
            geographical_assignments[agent_type][agent_id] = {
                'continent': continent,
                'vulnerability': vulnerability
            }
        
        print(f"✅ Loaded geographical assignments for {len(geographical_assignments)} agent types")
        for agent_type, assignments in geographical_assignments.items():
            print(f"    {agent_type}: {len(assignments)} agents")
        
        return geographical_assignments
        
    except Exception as e:
        print(f"❌ Error loading geographical assignments: {e}")
        return {}

def load_climate_events(simulation_path):
    """Load climate events from the climate summary CSV file."""
    climate_summary_file = os.path.join(simulation_path, 'climate_3_layer_summary.csv')
    
    if not os.path.exists(climate_summary_file):
        print(f"⚠️ Climate summary file not found: {climate_summary_file}")
        return []
    
    try:
        df = pd.read_csv(climate_summary_file)
        
        # Filter for climate events
        events_df = df[df['data_type'] != 'geographical_assignment']
        
        if len(events_df) == 0:
            print("ℹ️ No climate events found in simulation")
            return []
        
        # Group events by round
        climate_events_history = []
        max_round = events_df['agent_id'].max() if len(events_df) > 0 else -1
        
        for round_num in range(max_round + 1):
            round_events = events_df[events_df['agent_id'] == round_num]
            
            if len(round_events) > 0:
                # Convert to the expected format
                events_dict = {}
                
                # Group by event name
                for event_name in round_events['event_name'].unique():
                    event_rows = round_events[round_events['event_name'] == event_name]
                    
                    if len(event_rows) > 0:
                        first_row = event_rows.iloc[0]
                        
                        events_dict[event_name] = {
                            'type': 'configurable_shock',
                            'rule_name': first_row['data_type'],
                            'agent_types': first_row['affected_agent_types'].split(',') if pd.notna(first_row['affected_agent_types']) else [],
                            'continents': list(event_rows['continent'].unique()),
                            'stress_factor': first_row['stress_factor'] if pd.notna(first_row['stress_factor']) else 1.0,
                            'duration': first_row['duration'] if pd.notna(first_row['duration']) else 1,
                            'affected_agents': {}
                        }
                
                climate_events_history.append(events_dict)
            else:
                climate_events_history.append({})
        
        total_events = sum(len(events) for events in climate_events_history)
        print(f"✅ Loaded climate events: {total_events} events across {len(climate_events_history)} rounds")
        
        # Show event summary
        for round_num, events in enumerate(climate_events_history):
            if events:
                event_names = list(events.keys())
                print(f"    Round {round_num}: {event_names}")
        
        return climate_events_history
        
    except Exception as e:
        print(f"❌ Error loading climate events: {e}")
        return []

class ClimateFrameworkFromData:
    """Simple climate framework that loads data from CSV files."""
    def __init__(self, geographical_assignments, climate_events_history):
        self.geographical_assignments = geographical_assignments
        self.climate_events_history = climate_events_history

def collect_simulation_data(simulation_path, round_num, climate_framework):
    """Collect and process data for a specific round from CSV files."""
    
    agent_data = []
    climate_events = {}
    
    # Enhanced agent types with potential financial metrics
    agent_types = ['commodity_producer', 'intermediary_firm', 'final_goods_firm', 'household']
    
    # Collect agent data from CSV files
    for agent_type in agent_types:
        # Try production file first, then consumption for households
        filename = f'panel_{agent_type}_production.csv'
        if agent_type == 'household':
            filename = f'panel_{agent_type}_consumption.csv'
        
        filepath = os.path.join(simulation_path, filename)
        if os.path.exists(filepath):
            df = pd.read_csv(filepath)
            
            # Filter for the specific round
            round_data = df[df['round'] == round_num]
            
            # Collect all agents of this type
            unique_agents = round_data['id'].unique()
            
            for agent_id in unique_agents:
                agent_round_data = round_data[round_data['id'] == agent_id].iloc[0]
                
                # Basic agent data
                agent_info = {
                    'id': agent_id,
                    'type': agent_type,
                    'round': round_num,
                    'wealth': agent_round_data.get('money', 0),
                    'climate_stressed': False,  # Will be updated from climate events
                    'continent': get_agent_continent(agent_type, agent_id, climate_framework),
                    'vulnerability': get_agent_vulnerability(agent_type, agent_id, climate_framework)
                }
                
                # Add financial metrics if available
                if 'debt' in agent_round_data:
                    agent_info['debt'] = agent_round_data['debt']
                    agent_info['net_worth'] = agent_info['wealth'] - agent_info['debt']
                else:
                    agent_info['debt'] = 0
                    agent_info['net_worth'] = agent_info['wealth']
                
                if 'profit' in agent_round_data:
                    agent_info['profit'] = agent_round_data['profit']
                
                if 'actual_margin' in agent_round_data:
                    agent_info['actual_margin'] = agent_round_data['actual_margin']
                    
                if 'target_margin' in agent_round_data:
                    agent_info['target_margin'] = agent_round_data['target_margin']
                
                if 'climate_cost_absorbed' in agent_round_data:
                    agent_info['climate_cost_absorbed'] = agent_round_data['climate_cost_absorbed']
                
                if 'price' in agent_round_data:
                    agent_info['dynamic_price'] = agent_round_data['price']
                
                # Check if agent is climate stressed
                agent_info['climate_stressed'] = is_agent_climate_stressed(
                    agent_type, agent_id, climate_events, climate_framework
                )
                
                agent_data.append(agent_info)
    
    # Load climate events for this round
    if hasattr(climate_framework, 'climate_events_history') and round_num < len(climate_framework.climate_events_history):
        climate_events = climate_framework.climate_events_history[round_num]
    
    # Collect production data
    production_data = {
        'commodity': 0,
        'intermediary': 0, 
        'final_goods': 0
    }
    
    # Collect inventory data
    inventory_data = {
        'commodity': 0,
        'intermediary': 0,
        'final_goods': 0
    }
    
    # Collect financial data
    financial_data = {
        'total_debt': 0,
        'total_profit': 0,
        'avg_margin_deviation': 0,  # Deviation from target margins
        'climate_cost_total': 0
    }
    
    # Read production data from CSV files for each agent type
    for agent_type, good_type in [('commodity_producer', 'commodity'), 
                                   ('intermediary_firm', 'intermediary'),
                                   ('final_goods_firm', 'final_goods')]:
        filename = f'panel_{agent_type}_production.csv'
        filepath = os.path.join(simulation_path, filename)
        
        if os.path.exists(filepath):
            df = pd.read_csv(filepath)
            round_data = df[df['round'] == round_num]
            
            if 'production' in round_data.columns:
                production_data[good_type] = round_data['production'].sum()
            
            if 'cumulative_inventory' in round_data.columns:
                inventory_data[good_type] = round_data['cumulative_inventory'].sum()
            
            # Collect financial metrics
            if 'debt' in round_data.columns:
                financial_data['total_debt'] += round_data['debt'].sum()
            
            if 'profit' in round_data.columns:
                financial_data['total_profit'] += round_data['profit'].sum()
                
            if 'actual_margin' in round_data.columns and 'target_margin' in round_data.columns:
                margin_deviations = abs(round_data['actual_margin'] - round_data['target_margin'])
                financial_data['avg_margin_deviation'] += margin_deviations.mean()
                
            if 'climate_cost_absorbed' in round_data.columns:
                financial_data['climate_cost_total'] += round_data['climate_cost_absorbed'].sum()
    
    # Add household consumption data
    household_file = os.path.join(simulation_path, 'panel_household_consumption.csv')
    if os.path.exists(household_file):
        df = pd.read_csv(household_file)
        round_data = df[df['round'] == round_num]
        
        # Add household debt to total
        if 'debt' in round_data.columns:
            financial_data['total_debt'] += round_data['debt'].sum()
    
    # Collect wealth data by sector
    wealth_data = {
        'commodity': sum(a['wealth'] for a in agent_data if a['type'] == 'commodity_producer'),
        'intermediary': sum(a['wealth'] for a in agent_data if a['type'] == 'intermediary_firm'),
        'final_goods': sum(a['wealth'] for a in agent_data if a['type'] == 'final_goods_firm'),
        'households': sum(a['wealth'] for a in agent_data if a['type'] == 'household')
    }
    
    # Collect net worth data by sector  
    net_worth_data = {
        'commodity': sum(a['net_worth'] for a in agent_data if a['type'] == 'commodity_producer'),
        'intermediary': sum(a['net_worth'] for a in agent_data if a['type'] == 'intermediary_firm'),
        'final_goods': sum(a['net_worth'] for a in agent_data if a['type'] == 'final_goods_firm'),
        'households': sum(a['net_worth'] for a in agent_data if a['type'] == 'household')
    }
    
    return {
        'agents': agent_data,
        'climate': climate_events,
        'production': production_data,
        'inventories': inventory_data,
        'wealth': wealth_data,
        'net_worth': net_worth_data,
        'financial': financial_data
    }

def is_agent_climate_stressed(agent_type, agent_id, climate_events, climate_framework):
    """Determine if a specific agent is affected by climate stress in this round."""
    if not climate_events:
        return False
    
    for event_key, event_data in climate_events.items():
        if isinstance(event_data, dict):
            # New configurable shock format
            affected_agent_types = event_data.get('agent_types', [])
            affected_continents = event_data.get('continents', [])
            
            # Check if this agent type is affected
            if agent_type in affected_agent_types:
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
    if agent_type in climate_framework.geographical_assignments:
        assignments = climate_framework.geographical_assignments[agent_type]
        if agent_id in assignments:
            return assignments[agent_id]['continent']
    return 'Unknown'

def get_agent_vulnerability(agent_type, agent_id, climate_framework):
    """Get the vulnerability for a specific agent."""
    if agent_type in climate_framework.geographical_assignments:
        assignments = climate_framework.geographical_assignments[agent_type]
        if agent_id in assignments:
            return assignments[agent_id]['vulnerability']
    return 0.0

def create_time_evolution_visualization(visualization_data, simulation_path):
    """Create static time-series visualizations of key metrics with financial tracking."""
    
    print("📊 Creating time evolution visualization...")
    
    # Enhanced figure with 6 subplots (2x3 grid)
    fig, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle('Fixed Supply Model - Time Evolution Analysis', fontsize=16)
    
    rounds = visualization_data['rounds']
    
    # 1. Production Over Time (existing plot)
    ax1.set_title('Production Levels Over Time')
    commodity_prod = [visualization_data['production_data'][i]['commodity'] for i in range(len(rounds))]
    intermediary_prod = [visualization_data['production_data'][i]['intermediary'] for i in range(len(rounds))]
    final_goods_prod = [visualization_data['production_data'][i]['final_goods'] for i in range(len(rounds))]
    
    ax1.plot(rounds, commodity_prod, 'o-', label='Commodity', color='#8B4513', linewidth=2)
    ax1.plot(rounds, intermediary_prod, 's-', label='Intermediary', color='#DAA520', linewidth=2)
    ax1.plot(rounds, final_goods_prod, '^-', label='Final Goods', color='#00FF00', linewidth=2)
    ax1.set_xlabel('Round')
    ax1.set_ylabel('Production')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Wealth by Sector (existing plot)
    ax2.set_title('Wealth Evolution by Sector')
    commodity_wealth = [visualization_data['wealth_data'][i]['commodity'] for i in range(len(rounds))]
    intermediary_wealth = [visualization_data['wealth_data'][i]['intermediary'] for i in range(len(rounds))]
    final_goods_wealth = [visualization_data['wealth_data'][i]['final_goods'] for i in range(len(rounds))]
    household_wealth = [visualization_data['wealth_data'][i]['households'] for i in range(len(rounds))]
    
    ax2.plot(rounds, commodity_wealth, 'o-', label='Commodity', color='#8B4513', linewidth=2)
    ax2.plot(rounds, intermediary_wealth, 's-', label='Intermediary', color='#DAA520', linewidth=2)
    ax2.plot(rounds, final_goods_wealth, '^-', label='Final Goods', color='#00FF00', linewidth=2)
    ax2.plot(rounds, household_wealth, 'd-', label='Households', color='#4169E1', linewidth=2)
    ax2.set_xlabel('Round')
    ax2.set_ylabel('Total Wealth ($)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Inventory Levels (existing plot)
    ax3.set_title('Inventory Accumulation')
    commodity_inv = [visualization_data['inventory_data'][i]['commodity'] for i in range(len(rounds))]
    intermediary_inv = [visualization_data['inventory_data'][i]['intermediary'] for i in range(len(rounds))]
    final_goods_inv = [visualization_data['inventory_data'][i]['final_goods'] for i in range(len(rounds))]
    
    ax3.plot(rounds, commodity_inv, 'o-', label='Commodity', color='#8B4513', linewidth=2)
    ax3.plot(rounds, intermediary_inv, 's-', label='Intermediary', color='#DAA520', linewidth=2)
    ax3.plot(rounds, final_goods_inv, '^-', label='Final Goods', color='#00FF00', linewidth=2)
    ax3.set_xlabel('Round')
    ax3.set_ylabel('Cumulative Inventory')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. Total Debt Evolution (NEW)
    ax4.set_title('Total System Debt')
    total_debt = [visualization_data['financial_data'][i]['total_debt'] for i in range(len(rounds))]
    ax4.plot(rounds, total_debt, 'o-', color='red', linewidth=2, markersize=6)
    ax4.fill_between(rounds, 0, total_debt, alpha=0.3, color='red')
    ax4.set_xlabel('Round')
    ax4.set_ylabel('Total Debt ($)')
    ax4.grid(True, alpha=0.3)
    
    # 5. Net Worth by Sector (NEW)
    ax5.set_title('Net Worth Evolution (Wealth - Debt)')
    commodity_net = [visualization_data['net_worth_data'][i]['commodity'] for i in range(len(rounds))]
    intermediary_net = [visualization_data['net_worth_data'][i]['intermediary'] for i in range(len(rounds))]
    final_goods_net = [visualization_data['net_worth_data'][i]['final_goods'] for i in range(len(rounds))]
    household_net = [visualization_data['net_worth_data'][i]['households'] for i in range(len(rounds))]
    
    ax5.plot(rounds, commodity_net, 'o-', label='Commodity', color='#8B4513', linewidth=2)
    ax5.plot(rounds, intermediary_net, 's-', label='Intermediary', color='#DAA520', linewidth=2)
    ax5.plot(rounds, final_goods_net, '^-', label='Final Goods', color='#00FF00', linewidth=2)
    ax5.plot(rounds, household_net, 'd-', label='Households', color='#4169E1', linewidth=2)
    ax5.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    ax5.set_xlabel('Round')
    ax5.set_ylabel('Net Worth ($)')
    ax5.legend()
    ax5.grid(True, alpha=0.3)
    
    # 6. Profit and Climate Cost (NEW)
    ax6.set_title('System Profitability and Climate Costs')
    total_profit = [visualization_data['financial_data'][i]['total_profit'] for i in range(len(rounds))]
    climate_cost = [visualization_data['financial_data'][i]['climate_cost_total'] for i in range(len(rounds))]
    
    ax6_twin = ax6.twinx()
    
    # Profit on left axis
    line1 = ax6.plot(rounds, total_profit, 'o-', color='green', linewidth=2, label='Total Profit')
    ax6.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    ax6.set_xlabel('Round')
    ax6.set_ylabel('Total Profit ($)', color='green')
    ax6.tick_params(axis='y', labelcolor='green')
    
    # Climate cost on right axis
    line2 = ax6_twin.plot(rounds, climate_cost, 's-', color='orange', linewidth=2, label='Climate Cost Absorbed')
    ax6_twin.set_ylabel('Climate Cost Absorbed ($)', color='orange')
    ax6_twin.tick_params(axis='y', labelcolor='orange')
    
    # Combined legend
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax6.legend(lines, labels, loc='upper left')
    ax6.grid(True, alpha=0.3)
    
    # Add climate event markers to all plots
    climate_events_rounds = []
    for i, events in enumerate(visualization_data['climate_events']):
        if events:
            climate_events_rounds.append(i)
    
    for ax in [ax1, ax2, ax3, ax4, ax5, ax6]:
        for event_round in climate_events_rounds:
            ax.axvline(x=event_round, color='red', linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    
    # Save the figure
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{simulation_path}/fixed_supply_time_evolution_{timestamp}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"✅ Time evolution plot saved: {filename}")
    
    plt.close()
    return filename

def create_animated_supply_chain(visualization_data, simulation_path):
    """Create animated visualization of supply chain dynamics with financial metrics."""
    
    print("🎬 Creating animated supply chain visualization...")
    
    # Create figure with 5 subplots (expanded layout)
    fig = plt.figure(figsize=(20, 12))
    
    # Define grid layout for 5 plots
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    ax1 = fig.add_subplot(gs[0:2, 0])     # Network view (tall)
    ax2 = fig.add_subplot(gs[0, 1:])      # Production & Inventory (wide)
    ax3 = fig.add_subplot(gs[1, 1])       # World map
    ax4 = fig.add_subplot(gs[1, 2])       # Wealth time-series
    ax5 = fig.add_subplot(gs[2, :])       # Financial metrics (wide bottom)
    
    # Create twin axis for production plot
    ax2_twin = ax2.twinx()
    
    # Store continent positions
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
        ax1.clear()
        ax2.clear()
        ax2_twin.clear()
        ax3.clear()
        ax4.clear()
        ax5.clear()
        
        round_num = visualization_data['rounds'][frame]
        agent_data = visualization_data['agent_data'][frame]
        climate_events = visualization_data['climate_events'][frame]
        
        # Plot 1: Agent network with financial status
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
                
                # Color based on financial health
                if agent.get('debt', 0) > agent.get('wealth', 0) * 0.5:  # High debt
                    color = '#FF6B6B'  # Red tint
                elif agent['climate_stressed']:
                    color = '#FFA500'  # Orange
                else:
                    color = agent_type_colors[agent_type]
                
                size = 200 if agent['climate_stressed'] else 100
                
                ax1.scatter(pos[0], pos[1], c=color, s=size, alpha=0.8)
                
                # Show net worth instead of just wealth
                net_worth = agent.get('net_worth', agent['wealth'])
                ax1.text(pos[0], pos[1]-0.2, f"${net_worth:.0f}", 
                        ha='center', fontsize=8)
                
                # Show debt indicator if in debt
                if agent.get('debt', 0) > 0:
                    ax1.text(pos[0], pos[1]-0.35, f"D:${agent['debt']:.0f}", 
                            ha='center', fontsize=6, color='red')
        
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
            ax1.text(1, 5.3, f'Layer 1\nCommodity\n({agent_counts["commodity_producer"]})', ha='center', fontsize=10, fontweight='bold')
        if 'intermediary_firm' in agent_counts:
            ax1.text(3, 5.3, f'Layer 2\nIntermediary\n({agent_counts["intermediary_firm"]})', ha='center', fontsize=10, fontweight='bold')
        if 'final_goods_firm' in agent_counts:
            ax1.text(5, 5.3, f'Layer 3\nFinal Goods\n({agent_counts["final_goods_firm"]})', ha='center', fontsize=10, fontweight='bold')
        if 'household' in agent_counts:
            ax1.text(7, 5.3, f'Households\n({agent_counts["household"]})', ha='center', fontsize=10, fontweight='bold')
        
        # Plot 2: Production & Inventory Levels Over Time
        ax2.set_title('Production & Inventory Levels Over Time')
        rounds_so_far = visualization_data['rounds'][:frame+1]
        
        commodity_prod = [visualization_data['production_data'][i]['commodity'] for i in range(frame+1)]
        intermediary_prod = [visualization_data['production_data'][i]['intermediary'] for i in range(frame+1)]
        final_goods_prod = [visualization_data['production_data'][i]['final_goods'] for i in range(frame+1)]
        
        # Add inventory data
        commodity_inv = [visualization_data['inventory_data'][i]['commodity'] for i in range(frame+1)]
        intermediary_inv = [visualization_data['inventory_data'][i]['intermediary'] for i in range(frame+1)]
        final_goods_inv = [visualization_data['inventory_data'][i]['final_goods'] for i in range(frame+1)]
        
        # Plot production (solid lines) - LEFT Y-AXIS
        ax2.plot(rounds_so_far, commodity_prod, 'o-', label='Commodity Prod', color='#8B4513', linewidth=2)
        ax2.plot(rounds_so_far, intermediary_prod, 's-', label='Intermediary Prod', color='#DAA520', linewidth=2)
        ax2.plot(rounds_so_far, final_goods_prod, '^-', label='Final Goods Prod', color='#00FF00', linewidth=2)
        ax2.set_ylabel('Production per Round', color='black')
        
        # Plot inventory (dashed lines) - RIGHT Y-AXIS using the pre-created twin axis
        ax2_twin.plot(rounds_so_far, commodity_inv, 'o--', label='Commodity Inv', color='#8B4513', alpha=0.7, linewidth=1)
        ax2_twin.plot(rounds_so_far, intermediary_inv, 's--', label='Intermediary Inv', color='#DAA520', alpha=0.7, linewidth=1)
        ax2_twin.plot(rounds_so_far, final_goods_inv, '^--', label='Final Goods Inv', color='#00FF00', alpha=0.7, linewidth=1)
        ax2_twin.set_ylabel('Cumulative Inventory', color='gray')
        ax2_twin.tick_params(axis='y', labelcolor='gray')
        # Explicitly set the label position to the right side
        ax2_twin.yaxis.set_label_position('right')
        
        # Add climate shock indicators as vertical lines
        shock_colors = {
            'commodity_producer': '#8B4513',
            'intermediary_firm': '#DAA520', 
            'final_goods_firm': '#00FF00',
            'household': '#4169E1',
            'all_sectors': '#FF0000'  # For multi-sector shocks
        }
        
        climate_shock_legend_added = False
        for shock_round in range(frame + 1):
            if shock_round < len(visualization_data['climate_events']):
                events = visualization_data['climate_events'][shock_round]
                if events:  # Climate events occurred in this round
                    # Determine which sectors were affected
                    affected_sectors = set()
                    for event_name, event_data in events.items():
                        if isinstance(event_data, dict) and 'agent_types' in event_data:
                            affected_sectors.update(event_data['agent_types'])
                    
                    # Choose line color based on affected sectors
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
                    
                    # Add vertical line at the shock round
                    ax2.axvline(x=shock_round, color=line_color, linestyle='--', 
                               alpha=0.8, linewidth=2, 
                               label=line_label if not climate_shock_legend_added else "")
                    
                    climate_shock_legend_added = True
        
        # Combine legends
        lines1, labels1 = ax2.get_legend_handles_labels()
        lines2, labels2 = ax2_twin.get_legend_handles_labels()
        ax2.legend(lines1 + lines2, labels1 + labels2, fontsize=7, loc='upper left')
        
        ax2.set_xlabel('Round')
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Geographical Distribution World Map
        ax3.set_title(f'Global Climate Impact Map - Round {round_num}')
        ax3.set_xlim(0, 7)
        ax3.set_ylim(0, 5)
        ax3.set_aspect('equal')
        
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
            ax3.add_patch(continent_rect)
            
            # Add continent label
            ax3.text(x + width/2, y + height/2, continent.replace(' ', '\n'), 
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
                        
                        ax3.scatter(pos_x, pos_y, c=color, s=size, marker=agent_symbols[i], 
                                  alpha=0.9, edgecolors='black', linewidth=1)
                        
                        # Add count label
                        ax3.text(pos_x, pos_y - 0.15, str(counts[agent_type]), 
                               ha='center', va='center', fontsize=6, fontweight='bold')
        
        # Add legend for agent types
        legend_elements = []
        agent_type_names = ['Commodity Producers', 'Intermediary Firms', 'Final Goods Firms', 'Households']
        agent_colors = ['#8B4513', '#DAA520', '#00FF00', '#4169E1']
        agent_symbols = ['o', 's', '^', 'D']
        
        for i, (name, color, symbol) in enumerate(zip(agent_type_names, agent_colors, agent_symbols)):
            legend_elements.append(plt.Line2D([0], [0], marker=symbol, color='w', 
                                            markerfacecolor=color, markersize=8, 
                                            label=name, markeredgecolor='black', markeredgewidth=0.5))
        
        # Add stress indicator to legend
        legend_elements.append(plt.Line2D([0], [0], marker='o', color='w', 
                                        markerfacecolor='#FF0000', markersize=10, 
                                        label='Climate Stressed', markeredgecolor='black', markeredgewidth=0.5))
        
        ax3.legend(handles=legend_elements, loc='lower right', fontsize=8, 
                  title='Agent Types', title_fontsize=9, framealpha=0.8)
        
        ax3.axis('off')  # Remove axes for cleaner world map look
        
        # Plot 4: Wealth time-series by sector
        ax4.set_title('Wealth Evolution by Sector')
        
        # Collect wealth data over time up to current frame
        commodity_wealth_series = [visualization_data['wealth_data'][i]['commodity'] for i in range(frame+1)]
        intermediary_wealth_series = [visualization_data['wealth_data'][i]['intermediary'] for i in range(frame+1)]
        final_goods_wealth_series = [visualization_data['wealth_data'][i]['final_goods'] for i in range(frame+1)]
        household_wealth_series = [visualization_data['wealth_data'][i]['households'] for i in range(frame+1)]
        
        # Plot time-series lines
        ax4.plot(rounds_so_far, commodity_wealth_series, 'o-', label='Commodity Producers', color='#8B4513', linewidth=2, markersize=4)
        ax4.plot(rounds_so_far, intermediary_wealth_series, 's-', label='Intermediary Firms', color='#DAA520', linewidth=2, markersize=4)
        ax4.plot(rounds_so_far, final_goods_wealth_series, '^-', label='Final Goods Firms', color='#00FF00', linewidth=2, markersize=4)
        ax4.plot(rounds_so_far, household_wealth_series, 'd-', label='Households', color='#4169E1', linewidth=2, markersize=4)
        
        # Add climate shock indicators as vertical lines (same as production plot)
        climate_shock_legend_added_wealth = False
        for shock_round in range(frame + 1):
            if shock_round < len(visualization_data['climate_events']):
                events = visualization_data['climate_events'][shock_round]
                if events:  # Climate events occurred in this round
                    # Determine which sectors were affected
                    affected_sectors = set()
                    for event_name, event_data in events.items():
                        if isinstance(event_data, dict) and 'agent_types' in event_data:
                            affected_sectors.update(event_data['agent_types'])
                    
                    # Choose line color based on affected sectors
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
                    
                    # Add vertical line at the shock round
                    ax4.axvline(x=shock_round, color=line_color, linestyle='--', 
                               alpha=0.8, linewidth=2, 
                               label=line_label if not climate_shock_legend_added_wealth else "")
                    
                    climate_shock_legend_added_wealth = True
        
        ax4.set_xlabel('Round')
        ax4.set_ylabel('Total Wealth ($)')
        ax4.legend(fontsize=8)
        ax4.grid(True, alpha=0.3)
        
        # Plot 5: Financial Metrics Dashboard (NEW)
        ax5.set_title('Financial Metrics Dashboard')
        
        # Collect financial metrics up to current frame
        rounds_so_far = visualization_data['rounds'][:frame+1]
        
        # Debt evolution
        debt_series = [visualization_data['financial_data'][i]['total_debt'] for i in range(frame+1)]
        profit_series = [visualization_data['financial_data'][i]['total_profit'] for i in range(frame+1)]
        climate_cost_series = [visualization_data['financial_data'][i]['climate_cost_total'] for i in range(frame+1)]
        
        # Create 3 sub-sections in the financial dashboard
        ax5_debt = plt.subplot2grid((1, 3), (0, 0), colspan=1, fig=fig)
        ax5_profit = plt.subplot2grid((1, 3), (0, 1), colspan=1, fig=fig)
        ax5_margins = plt.subplot2grid((1, 3), (0, 2), colspan=1, fig=fig)
        
        # Debt subplot
        ax5_debt.plot(rounds_so_far, debt_series, 'r-', linewidth=2)
        ax5_debt.fill_between(rounds_so_far, 0, debt_series, alpha=0.3, color='red')
        ax5_debt.set_title('System Debt')
        ax5_debt.set_xlabel('Round')
        ax5_debt.set_ylabel('Total Debt ($)')
        ax5_debt.grid(True, alpha=0.3)
        
        # Profit subplot
        ax5_profit.plot(rounds_so_far, profit_series, 'g-', linewidth=2)
        ax5_profit.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        ax5_profit.fill_between(rounds_so_far, 0, profit_series, 
                               where=[p >= 0 for p in profit_series],
                               alpha=0.3, color='green', label='Profit')
        ax5_profit.fill_between(rounds_so_far, 0, profit_series,
                               where=[p < 0 for p in profit_series],
                               alpha=0.3, color='red', label='Loss')
        ax5_profit.set_title('System Profitability')
        ax5_profit.set_xlabel('Round')
        ax5_profit.set_ylabel('Total Profit ($)')
        ax5_profit.grid(True, alpha=0.3)
        
        # Margin deviation subplot (bar chart for current round)
        if frame > 0:
            current_agents = [a for a in agent_data if a['type'] != 'household']
            agent_labels = [f"{a['type'][:4]}{a['id']}" for a in current_agents]
            margin_deviations = []
            
            for agent in current_agents:
                if 'actual_margin' in agent and 'target_margin' in agent:
                    deviation = (agent['actual_margin'] - agent['target_margin']) * 100
                    margin_deviations.append(deviation)
                else:
                    margin_deviations.append(0)
            
            if margin_deviations:
                colors = ['green' if d >= 0 else 'red' for d in margin_deviations]
                ax5_margins.bar(range(len(agent_labels)), margin_deviations, color=colors, alpha=0.7)
                ax5_margins.axhline(y=0, color='black', linestyle='-', alpha=0.5)
                ax5_margins.set_title('Profit Margin vs Target (%)')
                ax5_margins.set_ylabel('Deviation from Target (%)')
                ax5_margins.set_xticks(range(len(agent_labels)))
                ax5_margins.set_xticklabels(agent_labels, rotation=45, ha='right', fontsize=8)
                ax5_margins.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
    
    # Create animation
    num_frames = len(visualization_data['rounds'])
    anim = animation.FuncAnimation(fig, animate, frames=num_frames, interval=1500, repeat=True)
    
    # Save animation
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{simulation_path}/fixed_supply_animation_{timestamp}.gif"
    
    print(f"💾 Saving animation as {filename}...")
    anim.save(filename, writer='pillow', fps=0.67)  # Slower fps for better readability
    print(f"✅ Animation saved: {filename}")
    
    plt.close()
    
    return filename

def collect_all_visualization_data(simulation_path, climate_framework, num_rounds):
    """Collect visualization data for all rounds including financial metrics."""
    
    print("📊 Collecting visualization data from simulation results...")
    visualization_data = {
        'rounds': [],
        'agent_data': [],
        'climate_events': [],
        'production_data': [],
        'wealth_data': [],
        'inventory_data': [],
        'net_worth_data': [],
        'financial_data': []
    }
    
    # Read data for each round from the CSV files
    for r in range(num_rounds):
        round_data = collect_simulation_data(simulation_path, r, climate_framework)
        
        visualization_data['rounds'].append(r)
        visualization_data['agent_data'].append(round_data['agents'])
        visualization_data['climate_events'].append(round_data['climate'])
        visualization_data['production_data'].append(round_data['production'])
        visualization_data['wealth_data'].append(round_data['wealth'])
        visualization_data['inventory_data'].append(round_data['inventories'])
        visualization_data['net_worth_data'].append(round_data['net_worth'])
        visualization_data['financial_data'].append(round_data['financial'])
        
        # Add debug info
        total_production = sum(round_data['production'].values())
        total_inventory = sum(round_data['inventories'].values())
        total_debt = round_data['financial']['total_debt']
        print(f"    Round {r}: Production = {total_production:.2f}, Inventory = {total_inventory:.2f}, Debt = ${total_debt:.2f}")
    
    print("✅ Visualization data collection completed!")
    return visualization_data

def run_animation_visualizations(simulation_path):
    """Main function to run all animation visualizations for Fixed Supply Model."""
    
    print("🎬 Starting Animation Visualizer for Fixed Supply Model")
    print("=" * 60)
    
    # Try to detect number of rounds from CSV files
    production_file = os.path.join(simulation_path, 'panel_commodity_producer_production.csv')
    if not os.path.exists(production_file):
        print(f"❌ Simulation output not found in: {simulation_path}")
        print("Make sure you've run the simulation first!")
        return
    
    try:
        df = pd.read_csv(production_file)
        num_rounds = df['round'].max() + 1
        print(f"📊 Detected {num_rounds} rounds in simulation output")
    except Exception as e:
        print(f"❌ Error reading simulation data: {e}")
        return
    
    # Load geographical assignments and climate events from CSV files
    print("🌍 Loading geographical assignments from simulation data...")
    geographical_assignments = load_geographical_assignments(simulation_path)
    
    print("🌪️ Loading climate events from simulation data...")
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
        print("❌ No visualization data collected!")
        return
    
    # Create visualizations
    print("\n🎬 Creating time-evolving visualizations...")
    
    # Create time evolution plot
    time_plot_file = create_time_evolution_visualization(
        visualization_data, simulation_path
    )
    
    # Create animated visualization
    animation_file = create_animated_supply_chain(
        visualization_data, simulation_path
    )
    
    print(f"\n🎉 Animation visualizations completed!")
    print(f"📊 Time evolution plot: {time_plot_file}")
    print(f"🎞️ Animation: {animation_file}")
    print(f"💰 Financial metrics tracked: debt, profit, margins, climate costs")
    
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
        print(f"❌ Simulation path does not exist: {simulation_path}")
        sys.exit(1)
    
    results = run_animation_visualizations(simulation_path)
    
    if results:
        print("\n✅ Animation visualization completed successfully!")
    else:
        print("\n❌ Animation visualization failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()
