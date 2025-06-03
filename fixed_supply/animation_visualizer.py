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
    climate_summary_file = os.path.join(simulation_path, 'fixed_supply_climate_summary.csv')
    
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
    climate_summary_file = os.path.join(simulation_path, 'fixed_supply_climate_summary.csv')
    
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
        
        # Group events by round using the correct 'round' column
        climate_events_history = []
        max_round = int(events_df['round'].max()) if len(events_df) > 0 else -1
        
        for round_num in range(max_round + 1):
            round_events = events_df[events_df['round'] == round_num]
            
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
    
    # Load climate events for this round FIRST
    climate_events = {}
    if hasattr(climate_framework, 'climate_events_history') and round_num < len(climate_framework.climate_events_history):
        climate_events = climate_framework.climate_events_history[round_num]
    
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
            
            # Fixed supply model uses 'name' column instead of 'id'
            unique_agents = round_data['name'].unique()
            
            for agent_name in unique_agents:
                # Extract agent ID from name (e.g., 'commodity_producer0' -> 0)
                agent_id = int(agent_name.replace(agent_type, ''))
                agent_round_data = round_data[round_data['name'] == agent_name].iloc[0]
                
                # Fixed supply model uses prefixed column names
                if agent_type == 'household':
                    wealth = agent_round_data.get('consumption_money', 0)
                    debt = agent_round_data.get('consumption_debt', 0)
                    profit = 0  # Households don't have profit
                    actual_margin = 0
                    target_margin = 0
                    climate_cost_absorbed = 0
                    price = 0
                else:
                    wealth = agent_round_data.get('production_money', 0)
                    debt = agent_round_data.get('production_debt', 0)
                    profit = agent_round_data.get('production_profit', 0)
                    actual_margin = agent_round_data.get('production_actual_margin', 0)
                    target_margin = agent_round_data.get('production_target_margin', 0)
                    climate_cost_absorbed = agent_round_data.get('production_climate_cost_absorbed', 0)
                    price = agent_round_data.get('production_price', 0)
                
                # Basic agent data
                agent_info = {
                    'id': agent_id,
                    'type': agent_type,
                    'round': round_num,
                    'wealth': wealth,
                    'debt': debt,
                    'net_worth': wealth - debt,
                    'profit': profit,
                    'actual_margin': actual_margin,
                    'target_margin': target_margin,
                    'climate_cost_absorbed': climate_cost_absorbed,
                    'dynamic_price': price,
                    'climate_stressed': False,  # Will be updated from climate events
                    'continent': get_agent_continent(agent_type, agent_id, climate_framework),
                    'vulnerability': get_agent_vulnerability(agent_type, agent_id, climate_framework)
                }
                
                # Check if agent is climate stressed (ONLY acute events, not chronic)
                is_climate_stressed = is_agent_climate_stressed(
                    agent_type, agent_id, climate_events, climate_framework
                )
                
                # Note: We deliberately do NOT check for chronic stress effects here
                # because the red color in geography plot should only indicate acute events
                
                agent_info['climate_stressed'] = is_climate_stressed
                
                agent_data.append(agent_info)
    
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
            
            # Fixed supply model uses prefixed column names
            if 'production_production' in round_data.columns:
                production_data[good_type] = round_data['production_production'].sum()
            
            if 'production_cumulative_inventory' in round_data.columns:
                inventory_data[good_type] = round_data['production_cumulative_inventory'].sum()
            
            # Collect financial metrics with prefixed names
            if 'production_debt' in round_data.columns:
                financial_data['total_debt'] += round_data['production_debt'].sum()
            
            if 'production_profit' in round_data.columns:
                financial_data['total_profit'] += round_data['production_profit'].sum()
                
            if 'production_actual_margin' in round_data.columns and 'production_target_margin' in round_data.columns:
                margin_deviations = abs(round_data['production_actual_margin'] - round_data['production_target_margin'])
                financial_data['avg_margin_deviation'] += margin_deviations.mean()
                
            if 'production_climate_cost_absorbed' in round_data.columns:
                financial_data['climate_cost_total'] += round_data['production_climate_cost_absorbed'].sum()
    
    # Add household consumption data
    household_file = os.path.join(simulation_path, 'panel_household_consumption.csv')
    if os.path.exists(household_file):
        df = pd.read_csv(household_file)
        round_data = df[df['round'] == round_num]
        
        # Add household debt to total (with prefixed name)
        if 'consumption_debt' in round_data.columns:
            financial_data['total_debt'] += round_data['consumption_debt'].sum()
    
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
    
    # Get agent's continent for checking
    agent_continent = get_agent_continent(agent_type, agent_id, climate_framework)
    
    for event_key, event_data in climate_events.items():
        if isinstance(event_data, dict):
            # New configurable shock format (both acute and chronic)
            affected_agent_types = event_data.get('agent_types', [])
            affected_continents = event_data.get('continents', [])
            
            # Check if this agent type is affected
            if agent_type in affected_agent_types:
                # Check if this agent's continent is affected
                if 'all' in affected_continents:
                    return True
                
                if agent_continent in affected_continents:
                    return True
        
        elif event_key in ['North America', 'Europe', 'Asia', 'South America', 'Africa']:
            # Old format where event key is continent name
            if agent_continent == event_key:
                return True
        
        # Handle any other event format that might indicate stress
        elif event_key == agent_continent:
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
    
    # 2. Wealth & Debt by Sector (enhanced plot)
    ax2.set_title('Wealth & Debt Evolution by Sector')
    commodity_wealth = [visualization_data['wealth_data'][i]['commodity'] for i in range(len(rounds))]
    intermediary_wealth = [visualization_data['wealth_data'][i]['intermediary'] for i in range(len(rounds))]
    final_goods_wealth = [visualization_data['wealth_data'][i]['final_goods'] for i in range(len(rounds))]
    household_wealth = [visualization_data['wealth_data'][i]['households'] for i in range(len(rounds))]
    
    # Calculate debt by sector
    commodity_debt = []
    intermediary_debt = []
    final_goods_debt = []
    household_debt = []
    
    for i in range(len(rounds)):
        # Extract debt for each sector from agent data
        agents = visualization_data['agents'][i]
        commodity_debt.append(sum(a['debt'] for a in agents if a['type'] == 'commodity_producer'))
        intermediary_debt.append(sum(a['debt'] for a in agents if a['type'] == 'intermediary_firm'))
        final_goods_debt.append(sum(a['debt'] for a in agents if a['type'] == 'final_goods_firm'))
        household_debt.append(sum(a['debt'] for a in agents if a['type'] == 'household'))
    
    # Plot wealth (solid lines)
    ax2.plot(rounds, commodity_wealth, 'o-', label='Commodity Wealth', color='#8B4513', linewidth=2)
    ax2.plot(rounds, intermediary_wealth, 's-', label='Intermediary Wealth', color='#DAA520', linewidth=2)
    ax2.plot(rounds, final_goods_wealth, '^-', label='Final Goods Wealth', color='#00FF00', linewidth=2)
    ax2.plot(rounds, household_wealth, 'd-', label='Households Wealth', color='#4169E1', linewidth=2)
    
    # Plot debt (dashed lines with transparency)
    ax2.plot(rounds, commodity_debt, 'o--', label='Commodity Debt', color='#8B4513', linewidth=1.5, alpha=0.7)
    ax2.plot(rounds, intermediary_debt, 's--', label='Intermediary Debt', color='#DAA520', linewidth=1.5, alpha=0.7)
    ax2.plot(rounds, final_goods_debt, '^--', label='Final Goods Debt', color='#00FF00', linewidth=1.5, alpha=0.7)
    ax2.plot(rounds, household_debt, 'd--', label='Households Debt', color='#4169E1', linewidth=1.5, alpha=0.7)
    
    ax2.set_xlabel('Round')
    ax2.set_ylabel('Amount ($)')
    ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
    ax2.grid(True, alpha=0.3)
    
    # 3. Inventory Levels (existing plot)
    ax3.set_title('Inventory Accumulation')
    commodity_inv = [visualization_data['inventories'][i]['commodity'] for i in range(len(rounds))]
    intermediary_inv = [visualization_data['inventories'][i]['intermediary'] for i in range(len(rounds))]
    final_goods_inv = [visualization_data['inventories'][i]['final_goods'] for i in range(len(rounds))]
    
    ax3.plot(rounds, commodity_inv, 'o-', label='Commodity', color='#8B4513', linewidth=2)
    ax3.plot(rounds, intermediary_inv, 's-', label='Intermediary', color='#DAA520', linewidth=2)
    ax3.plot(rounds, final_goods_inv, '^-', label='Final Goods', color='#00FF00', linewidth=2)
    ax3.set_xlabel('Round')
    ax3.set_ylabel('Cumulative Inventory')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. Total Debt Evolution (NEW)
    ax4.set_title('Total System Debt')
    total_debt = [visualization_data['financial'][i]['total_debt'] for i in range(len(rounds))]
    ax4.plot(rounds, total_debt, 'o-', color='red', linewidth=2, markersize=6)
    ax4.fill_between(rounds, 0, total_debt, alpha=0.3, color='red')
    ax4.set_xlabel('Round')
    ax4.set_ylabel('Total Debt ($)')
    ax4.grid(True, alpha=0.3)
    
    # 5. Price Evolution by Sector (NEW - replacing redundant net worth)
    ax5.set_title('Dynamic Price Evolution by Sector')
    
    # Collect price data by sector over time
    commodity_prices = []
    intermediary_prices = []
    final_goods_prices = []
    
    for i in range(len(rounds)):
        agents = visualization_data['agents'][i]
        
        # Get average price for each sector (agents may have different prices)
        commodity_price_sum = sum(a.get('dynamic_price', 0) for a in agents if a['type'] == 'commodity_producer')
        commodity_count = len([a for a in agents if a['type'] == 'commodity_producer'])
        commodity_avg_price = commodity_price_sum / commodity_count if commodity_count > 0 else 0
        
        intermediary_price_sum = sum(a.get('dynamic_price', 0) for a in agents if a['type'] == 'intermediary_firm')
        intermediary_count = len([a for a in agents if a['type'] == 'intermediary_firm'])
        intermediary_avg_price = intermediary_price_sum / intermediary_count if intermediary_count > 0 else 0
        
        final_goods_price_sum = sum(a.get('dynamic_price', 0) for a in agents if a['type'] == 'final_goods_firm')
        final_goods_count = len([a for a in agents if a['type'] == 'final_goods_firm'])
        final_goods_avg_price = final_goods_price_sum / final_goods_count if final_goods_count > 0 else 0
        
        commodity_prices.append(commodity_avg_price)
        intermediary_prices.append(intermediary_avg_price)
        final_goods_prices.append(final_goods_avg_price)
    
    # Plot price evolution
    ax5.plot(rounds, commodity_prices, 'o-', label='Commodity Price', color='#8B4513', linewidth=2, markersize=4)
    ax5.plot(rounds, intermediary_prices, 's-', label='Intermediate Good Price', color='#DAA520', linewidth=2, markersize=4)
    ax5.plot(rounds, final_goods_prices, '^-', label='Final Good Price', color='#00FF00', linewidth=2, markersize=4)
    
    # Add baseline reference lines (initial prices)
    if len(commodity_prices) > 0 and commodity_prices[0] > 0:
        ax5.axhline(y=commodity_prices[0], color='#8B4513', linestyle=':', alpha=0.5, label='Commodity Baseline')
    if len(intermediary_prices) > 0 and intermediary_prices[0] > 0:
        ax5.axhline(y=intermediary_prices[0], color='#DAA520', linestyle=':', alpha=0.5, label='Intermediate Baseline')
    if len(final_goods_prices) > 0 and final_goods_prices[0] > 0:
        ax5.axhline(y=final_goods_prices[0], color='#00FF00', linestyle=':', alpha=0.5, label='Final Good Baseline')
    
    ax5.set_xlabel('Round')
    ax5.set_ylabel('Price per Unit ($)')
    ax5.legend(fontsize=9)
    ax5.grid(True, alpha=0.3)
    
    # 6. Profit and Climate Cost (NEW)
    ax6.set_title('System Profitability and Climate Costs')
    total_profit = [visualization_data['financial'][i]['total_profit'] for i in range(len(rounds))]
    climate_cost = [visualization_data['financial'][i]['climate_cost_total'] for i in range(len(rounds))]
    
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
    for i, events in enumerate(visualization_data['climate']):
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
    
    # Create simpler figure with 4 subplots to avoid matplotlib issues
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Fixed Supply Model - Animated Analysis', fontsize=16)
    
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
        for ax in [ax1, ax2, ax3, ax4]:
            ax.clear()
        # Clear the twin axis as well
        ax2_twin.clear()
        
        if frame >= len(visualization_data['rounds']):
            return
        
        round_num = visualization_data['rounds'][frame]
        agent_data = visualization_data['agents'][frame]
        production_data = visualization_data['production_data'][frame]
        wealth_data = visualization_data['wealth_data'][frame]
        climate_events = visualization_data['climate'][frame]
        
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
            'commodity_producer': '#8B4513',  # Dark brown
            'intermediary_firm': '#DAA520',   # Goldenrod  
            'final_goods_firm': '#00FF00',    # Green
            'household': '#4169E1'            # Blue
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
        commodity_inv = [visualization_data['inventories'][i]['commodity'] for i in range(frame+1)]
        intermediary_inv = [visualization_data['inventories'][i]['intermediary'] for i in range(frame+1)]
        final_goods_inv = [visualization_data['inventories'][i]['final_goods'] for i in range(frame+1)]
        
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
            if shock_round < len(visualization_data['climate']):
                events = visualization_data['climate'][shock_round]
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
        ax2.legend(lines1 + lines2, labels1 + labels2, fontsize=7)
        
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
            
            # Check if this continent has any climate events this round
            continent_has_events = False
            if climate_events:
                for event_key, event_data in climate_events.items():
                    if isinstance(event_data, dict):
                        affected_continents = event_data.get('continents', [])
                        if 'all' in affected_continents or continent in affected_continents:
                            continent_has_events = True
                            break
                    elif continent in str(event_key):
                        continent_has_events = True
                        break
            
            # Color continent based on climate events
            if continent_has_events:
                base_color = '#FFB6C1'  # Light red/pink for affected continents
            
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
        stressed_agents_by_continent = {}
        
        for agent in agent_data:
            continent = agent['continent']
            if continent not in agent_counts_by_continent:
                agent_counts_by_continent[continent] = {
                    'commodity_producer': 0,
                    'intermediary_firm': 0, 
                    'final_goods_firm': 0,
                    'household': 0
                }
                stressed_agents_by_continent[continent] = {
                    'commodity_producer': 0,
                    'intermediary_firm': 0, 
                    'final_goods_firm': 0,
                    'household': 0
                }
            
            agent_counts_by_continent[continent][agent['type']] += 1
            
            # Count stressed agents
            if agent['climate_stressed']:
                stressed_agents_by_continent[continent][agent['type']] += 1
        
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
                        
                        # Check if any agents of this type in this continent are stressed
                        stressed_count = stressed_agents_by_continent[continent][agent_type]
                        is_stressed = stressed_count > 0
                        
                        # Choose color and size based on stress status
                        if is_stressed:
                            color = '#FF0000'  # Bright red for stressed agents
                            size = 200  # Larger for stressed
                            edge_color = 'black'
                            edge_width = 2
                        else:
                            color = agent_colors[i]  # Normal sector color
                            size = 100  # Normal size
                            edge_color = 'black'
                            edge_width = 1
                        
                        ax3.scatter(pos_x, pos_y, c=color, s=size, marker=agent_symbols[i], 
                                  alpha=0.9, edgecolors=edge_color, linewidth=edge_width)
                        
                        # Add count label (show stressed/total if there are stressed agents)
                        if is_stressed:
                            label_text = f"{stressed_count}/{counts[agent_type]}"
                            label_color = 'red'
                            fontweight = 'bold'
                        else:
                            label_text = str(counts[agent_type])
                            label_color = 'black'
                            fontweight = 'normal'
                        
                        ax3.text(pos_x, pos_y - 0.15, label_text, 
                               ha='center', va='center', fontsize=6, 
                               fontweight=fontweight, color=label_color)
        
        # Add legend for agent types
        legend_elements = []
        agent_type_names = ['Commodity Producers', 'Intermediary Firms', 'Final Goods Firms', 'Households']
        agent_colors = ['#8B4513', '#DAA520', '#00FF00', '#4169E1']  # Consistent with agent_type_colors
        agent_symbols = ['o', 's', '^', 'D']
        
        for i, (name, color, symbol) in enumerate(zip(agent_type_names, agent_colors, agent_symbols)):
            legend_elements.append(plt.Line2D([0], [0], marker=symbol, color='w', 
                                            markerfacecolor=color, markersize=8, 
                                            label=name, markeredgecolor='black', markeredgewidth=0.5))
        
        # Add stress indicator to legend
        legend_elements.append(plt.Line2D([0], [0], marker='o', color='w', 
                                        markerfacecolor='#FF0000', markersize=12, 
                                        label='Climate Stressed (Acute Events)', markeredgecolor='black', markeredgewidth=2))
        
        # Add continent stress indicator to legend
        legend_elements.append(plt.Rectangle((0, 0), 1, 1, facecolor='#FFB6C1', 
                                           label='Affected Continent', alpha=0.6))
        
        ax3.legend(handles=legend_elements, loc='lower center', fontsize=7, 
                  title='Agent Types & Climate Status', title_fontsize=8, framealpha=0.8)
        
        ax3.axis('off')  # Remove axes for cleaner world map look
        
        # Plot 4: Wealth & Debt time-series by sector
        ax4.set_title('Wealth & Debt Evolution by Sector')
        
        # Collect wealth data over time up to current frame
        commodity_wealth_series = [visualization_data['wealth_data'][i]['commodity'] for i in range(frame+1)]
        intermediary_wealth_series = [visualization_data['wealth_data'][i]['intermediary'] for i in range(frame+1)]
        final_goods_wealth_series = [visualization_data['wealth_data'][i]['final_goods'] for i in range(frame+1)]
        household_wealth_series = [visualization_data['wealth_data'][i]['households'] for i in range(frame+1)]
        
        # Collect debt data over time up to current frame
        commodity_debt_series = []
        intermediary_debt_series = []
        final_goods_debt_series = []
        household_debt_series = []
        
        for i in range(frame+1):
            agents = visualization_data['agents'][i]
            commodity_debt_series.append(sum(a['debt'] for a in agents if a['type'] == 'commodity_producer'))
            intermediary_debt_series.append(sum(a['debt'] for a in agents if a['type'] == 'intermediary_firm'))
            final_goods_debt_series.append(sum(a['debt'] for a in agents if a['type'] == 'final_goods_firm'))
            household_debt_series.append(sum(a['debt'] for a in agents if a['type'] == 'household'))
        
        # Plot wealth (solid lines)
        ax4.plot(rounds_so_far, commodity_wealth_series, 'o-', label='Commodity Wealth', color='#8B4513', linewidth=2, markersize=4)
        ax4.plot(rounds_so_far, intermediary_wealth_series, 's-', label='Intermediary Wealth', color='#DAA520', linewidth=2, markersize=4)
        ax4.plot(rounds_so_far, final_goods_wealth_series, '^-', label='Final Goods Wealth', color='#00FF00', linewidth=2, markersize=4)
        ax4.plot(rounds_so_far, household_wealth_series, 'd-', label='Households Wealth', color='#4169E1', linewidth=2, markersize=4)
        
        # Plot debt (dashed lines with transparency)
        ax4.plot(rounds_so_far, commodity_debt_series, 'o--', label='Commodity Debt', color='#8B4513', linewidth=1.5, alpha=0.7, markersize=3)
        ax4.plot(rounds_so_far, intermediary_debt_series, 's--', label='Intermediary Debt', color='#DAA520', linewidth=1.5, alpha=0.7, markersize=3)
        ax4.plot(rounds_so_far, final_goods_debt_series, '^--', label='Final Goods Debt', color='#00FF00', linewidth=1.5, alpha=0.7, markersize=3)
        ax4.plot(rounds_so_far, household_debt_series, 'd--', label='Households Debt', color='#4169E1', linewidth=1.5, alpha=0.7, markersize=3)
        
        # Add climate shock indicators as vertical lines (same as production plot)
        climate_shock_legend_added_wealth = False
        for shock_round in range(frame + 1):
            if shock_round < len(visualization_data['climate']):
                events = visualization_data['climate'][shock_round]
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
        ax4.set_ylabel('Amount ($)')
        ax4.legend(fontsize=7)
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
    
    # Create animation
    num_frames = len(visualization_data['rounds'])
    anim = animation.FuncAnimation(fig, animate, frames=num_frames, interval=1500, repeat=True)
    
    # Save animation
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{simulation_path}/fixed_supply_animation_{timestamp}.gif"
    
    print(f"💾 Saving animation as {filename}...")
    anim.save(filename, writer='pillow', fps=1.5, dpi=72)
    print(f"✅ Animation saved: {filename}")
    
    plt.close()
    
    return filename

def collect_all_visualization_data(simulation_path, climate_framework, num_rounds):
    """Collect visualization data for all rounds including financial metrics."""
    
    print("📊 Collecting visualization data from simulation results...")
    visualization_data = {
        'rounds': [],
        'agents': [],
        'climate': [],
        'production_data': [],
        'wealth_data': [],
        'inventories': [],
        'net_worth': [],
        'financial': []
    }
    
    # Read data for each round from the CSV files
    for r in range(num_rounds):
        round_data = collect_simulation_data(simulation_path, r, climate_framework)
        
        visualization_data['rounds'].append(r)
        visualization_data['agents'].append(round_data['agents'])
        visualization_data['climate'].append(round_data['climate'])
        visualization_data['production_data'].append(round_data['production'])
        visualization_data['wealth_data'].append(round_data['wealth'])
        visualization_data['inventories'].append(round_data['inventories'])
        visualization_data['net_worth'].append(round_data['net_worth'])
        visualization_data['financial'].append(round_data['financial'])
        
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
