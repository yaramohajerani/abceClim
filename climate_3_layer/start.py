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

Now supports configurable parameters through JSON configuration files.
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

# Import the configuration loader
from config_loader import load_model_config

# Import the simulation logger
from simulation_logger import SimulationLogger, replace_agent_prints_with_logging

# Import visualization libraries
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from datetime import datetime

def collect_simulation_data(simulation_path, round_num, config_loader, climate_framework):
    """Collect data from the simulation CSV files for one round."""
    
    round_data = {
        'agents': [],
        'climate': {},
        'production': {},
        'wealth': {},
        'inventories': {}
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
    
    production_goods = {
        'commodity_producer': 'commodity',
        'intermediary_firm': 'intermediate_good',
        'final_goods_firm': 'final_good',
        'household': 'final_good'  # households consume final goods
    }
    
    # Initialize production totals
    round_data['production'] = {
        'commodity': 0,
        'intermediary': 0,
        'final_goods': 0
    }
    
    # Read data from CSV files for all agent types including households
    for agent_type, filename in production_files.items():
        file_path = os.path.join(simulation_path, filename)
        if os.path.exists(file_path):
            try:
                import pandas as pd
                df = pd.read_csv(file_path)
                
                # Filter for this specific round
                round_df = df[df['round'] == round_num]
                
                if len(round_df) > 0:
                    # Create agent data entries for each agent
                    for _, row in round_df.iterrows():
                        agent_id = int(row['name'].replace(agent_type, ''))
                        
                        # Determine if this specific agent is climate stressed
                        is_climate_stressed = is_agent_climate_stressed(
                            agent_type, agent_id, round_data['climate'], climate_framework
                        )
                        
                        # Get wealth (money) data if available
                        wealth = row.get('money', 0)
                        
                        # Get production/consumption data
                        if agent_type == 'household':
                            # For households, track consumption, not production
                            consumption = row.get(production_goods[agent_type], 0)
                            agent_data = {
                                'id': agent_id,
                                'type': agent_type,
                                'round': round_num,
                                'production': 0,  # Households don't produce
                                'consumption': consumption,
                                'production_capacity': 0,
                                'climate_stressed': is_climate_stressed,
                                'wealth': wealth,
                                'continent': get_agent_continent(agent_type, agent_id, climate_framework),
                                'vulnerability': get_agent_vulnerability(agent_type, agent_id, climate_framework)
                            }
                        else:
                            # For production agents
                            production = row.get(production_goods[agent_type], 0)
                            agent_data = {
                                'id': agent_id,
                                'type': agent_type,
                                'round': round_num,
                                'production': production,
                                'production_capacity': production,  # Use actual production as capacity for now
                                'climate_stressed': is_climate_stressed,
                                'wealth': wealth,
                                'continent': get_agent_continent(agent_type, agent_id, climate_framework),
                                'vulnerability': get_agent_vulnerability(agent_type, agent_id, climate_framework)
                            }
                        
                        round_data['agents'].append(agent_data)
                    
                    # Sum total production for production layers (not households)
                    if agent_type != 'household':
                        good_column = production_goods[agent_type]
                        total_production = round_df[good_column].sum()
                        
                        if agent_type == 'commodity_producer':
                            round_data['production']['commodity'] = total_production
                        elif agent_type == 'intermediary_firm':
                            round_data['production']['intermediary'] = total_production
                        elif agent_type == 'final_goods_firm':
                            round_data['production']['final_goods'] = total_production
                        
            except Exception as e:
                print(f"Warning: Could not read {filename}: {e}")
    
    # Calculate wealth data by summing money from all agents of each type
    round_data['wealth'] = {
        'commodity': sum([agent['wealth'] for agent in round_data['agents'] if agent['type'] == 'commodity_producer']),
        'intermediary': sum([agent['wealth'] for agent in round_data['agents'] if agent['type'] == 'intermediary_firm']),
        'final_goods': sum([agent['wealth'] for agent in round_data['agents'] if agent['type'] == 'final_goods_firm']),
        'households': sum([agent['wealth'] for agent in round_data['agents'] if agent['type'] == 'household'])
    }
    
    # Copy production to inventories
    round_data['inventories'] = round_data['production'].copy()
    
    return round_data

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

def create_time_evolution_visualization(visualization_data, simulation_path, config_loader):
    """Create time-evolving visualization from real simulation data."""
    
    print("🎬 Creating time-evolving visualization from REAL simulation data...")
    
    rounds = visualization_data['rounds']
    
    # Extract time series data
    commodity_production = [data['commodity'] for data in visualization_data['production_data']]
    intermediary_production = [data['intermediary'] for data in visualization_data['production_data']]
    final_goods_production = [data['final_goods'] for data in visualization_data['production_data']]
    
    commodity_wealth = [data['commodity'] for data in visualization_data['wealth_data']]
    intermediary_wealth = [data['intermediary'] for data in visualization_data['wealth_data']]
    final_goods_wealth = [data['final_goods'] for data in visualization_data['wealth_data']]
    household_wealth = [data['households'] for data in visualization_data['wealth_data']]
    
    # Count climate events by round
    climate_stress_counts = []
    for round_agents in visualization_data['agent_data']:
        stress_count = sum([1 for agent in round_agents if agent['climate_stressed']])
        climate_stress_counts.append(stress_count)
    
    # Calculate production capacities dynamically from configuration
    commodity_config = config_loader.get_agent_config('commodity_producer')
    intermediary_config = config_loader.get_agent_config('intermediary_firm')
    final_goods_config = config_loader.get_agent_config('final_goods_firm')
    
    commodity_capacity = commodity_config['count'] * commodity_config['production']['base_output_quantity']
    intermediary_capacity = intermediary_config['count'] * intermediary_config['production']['base_output_quantity']
    final_goods_capacity = final_goods_config['count'] * final_goods_config['production']['base_output_quantity']
    
    # Create comprehensive time evolution plot
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('REAL Climate 3-Layer Supply Chain: Time Evolution Analysis', fontsize=16, fontweight='bold')
    
    # Plot 1: Production evolution over time WITH CAPACITY LINES
    ax1.plot(rounds, commodity_production, 'o-', label='Commodity Production', color='#8B4513', linewidth=2, markersize=4)
    ax1.plot(rounds, intermediary_production, 's-', label='Intermediary Production', color='#DAA520', linewidth=2, markersize=4)
    ax1.plot(rounds, final_goods_production, '^-', label='Final Goods Production', color='#00FF00', linewidth=2, markersize=4)
    
    # Add capacity lines
    ax1.axhline(y=commodity_capacity, color='#8B4513', linestyle='--', alpha=0.7, linewidth=2, label=f'Commodity Capacity ({commodity_capacity})')
    ax1.axhline(y=intermediary_capacity, color='#DAA520', linestyle='--', alpha=0.7, linewidth=2, label=f'Intermediary Capacity ({intermediary_capacity})')
    ax1.axhline(y=final_goods_capacity, color='#00FF00', linestyle='--', alpha=0.7, linewidth=2, label=f'Final Goods Capacity ({final_goods_capacity})')
    
    # Add capacity utilization annotations
    if commodity_production:
        commodity_utilization = (commodity_production[-1] / commodity_capacity) * 100
        ax1.text(0.02, 0.98, f'Final Utilization:\nCommodity: {commodity_utilization:.1f}%\nIntermediary: {(intermediary_production[-1] / intermediary_capacity) * 100:.1f}%\nFinal Goods: {(final_goods_production[-1] / final_goods_capacity) * 100:.1f}%', 
                transform=ax1.transAxes, fontsize=9, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    ax1.set_title('Production Levels vs Capacity Over Time (Real Data)', fontweight='bold')
    ax1.set_xlabel('Round')
    ax1.set_ylabel('Production Level')
    ax1.legend(loc='center right', fontsize=9)
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Wealth evolution by sector
    ax2.plot(rounds, commodity_wealth, 'o-', label='Commodity Producers', color='#8B4513', linewidth=2, markersize=4)
    ax2.plot(rounds, intermediary_wealth, 's-', label='Intermediary Firms', color='#DAA520', linewidth=2, markersize=4)
    ax2.plot(rounds, final_goods_wealth, '^-', label='Final Goods Firms', color='#00FF00', linewidth=2, markersize=4)
    ax2.plot(rounds, household_wealth, 'd-', label='Households', color='#4169E1', linewidth=2, markersize=4)
    ax2.set_title('Wealth Evolution by Sector (Real Data)', fontweight='bold')
    ax2.set_xlabel('Round')
    ax2.set_ylabel('Total Wealth ($)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Climate stress events over time
    ax3.plot(rounds, climate_stress_counts, 'ro-', linewidth=3, markersize=6)
    ax3.fill_between(rounds, climate_stress_counts, alpha=0.3, color='red')
    ax3.set_title('Climate Stress Events Over Time (Real Data)', fontweight='bold')
    ax3.set_xlabel('Round')
    ax3.set_ylabel('Number of Stressed Agents')
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Supply chain resilience analysis
    # Calculate production volatility as resilience metric
    commodity_volatility = np.std(commodity_production)
    intermediary_volatility = np.std(intermediary_production)
    final_goods_volatility = np.std(final_goods_production)
    
    # Calculate correlation between climate events and production drops
    production_changes = np.diff(commodity_production)
    climate_changes = np.diff(climate_stress_counts)
    
    ax4.axis('off')
    
    # Summary statistics from REAL simulation
    total_rounds = len(rounds)
    avg_climate_events = np.mean(climate_stress_counts)
    max_climate_events = np.max(climate_stress_counts)
    final_total_wealth = sum([commodity_wealth[-1], intermediary_wealth[-1], 
                             final_goods_wealth[-1], household_wealth[-1]])
    
    # Calculate supply chain impact propagation
    max_commodity_stress = max(climate_stress_counts) if climate_stress_counts else 0
    supply_chain_efficiency = (final_goods_production[-1] / final_goods_production[0] * 100) if final_goods_production[0] > 0 else 100
    
    # Calculate average capacity utilization
    avg_commodity_util = np.mean(commodity_production) / commodity_capacity * 100
    avg_intermediary_util = np.mean(intermediary_production) / intermediary_capacity * 100
    avg_final_goods_util = np.mean(final_goods_production) / final_goods_capacity * 100
    
    summary_text = f"""
    REAL SIMULATION ANALYSIS SUMMARY
    
    📊 Simulation Overview:
    • Total Rounds: {total_rounds}
    • Final Total Wealth: ${final_total_wealth:.0f}
    • Supply Chain Efficiency: {supply_chain_efficiency:.1f}%
    
    🏭 Capacity Utilization:
    • Commodity avg: {avg_commodity_util:.1f}% (cap: {commodity_capacity})
    • Intermediary avg: {avg_intermediary_util:.1f}% (cap: {intermediary_capacity})
    • Final Goods avg: {avg_final_goods_util:.1f}% (cap: {final_goods_capacity})
    
    🌪️ Climate Impact Analysis:
    • Average climate events per round: {avg_climate_events:.1f}
    • Maximum climate events in one round: {max_climate_events}
    • Total climate stress events: {sum(climate_stress_counts)}
    
    📈 Production Volatility (Resilience):
    • Commodity layer: {commodity_volatility:.2f}
    • Intermediary layer: {intermediary_volatility:.2f}
    • Final goods layer: {final_goods_volatility:.2f}
    
    💰 Final Production Levels:
    • Commodity: {commodity_production[-1]:.2f}
    • Intermediary: {intermediary_production[-1]:.2f}
    • Final Goods: {final_goods_production[-1]:.2f}
    """
    
    ax4.text(0.05, 0.95, summary_text, transform=ax4.transAxes, fontsize=10,
             verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
    
    plt.tight_layout()
    
    # Save the time evolution plot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{simulation_path}/climate_3layer_time_evolution_{timestamp}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"✅ Time evolution visualization saved: {filename}")
    
    #plt.show()
    plt.close()
    return filename

def create_animated_supply_chain(visualization_data, simulation_path, config_loader):
    """Create animated GIF showing supply chain evolution over time."""
    
    print("🎞️ Creating animated supply chain visualization...")
    
    # Calculate production capacities dynamically from configuration
    commodity_config = config_loader.get_agent_config('commodity_producer')
    intermediary_config = config_loader.get_agent_config('intermediary_firm')
    final_goods_config = config_loader.get_agent_config('final_goods_firm')
    
    commodity_capacity = commodity_config['count'] * commodity_config['production']['base_output_quantity']
    intermediary_capacity = intermediary_config['count'] * intermediary_config['production']['base_output_quantity']
    final_goods_capacity = final_goods_config['count'] * final_goods_config['production']['base_output_quantity']
    
    # Set up the animation plot with more subplots including geographical map
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 14))
    fig.suptitle('Climate 3-Layer Supply Chain Evolution (Animated)', fontsize=16, fontweight='bold')
    
    # Define continent positions for the world map (simplified layout)
    continent_positions = {
        'North America': (1, 3, 1.5, 1),     # (x, y, width, height)
        'South America': (1.2, 1.5, 1, 1.2),
        'Europe': (3, 3.2, 0.8, 0.6),
        'Africa': (3.2, 2, 0.8, 1.5),
        'Asia': (4.5, 2.5, 2, 1.8)
    }
    
    def animate(frame):
        # Clear all subplots
        for ax in [ax1, ax2, ax3, ax4]:
            ax.clear()
        
        if frame >= len(visualization_data['rounds']):
            return
        
        round_num = visualization_data['rounds'][frame]
        agent_data = visualization_data['agent_data'][frame]
        production_data = visualization_data['production_data'][frame]
        wealth_data = visualization_data['wealth_data'][frame]
        climate_events = visualization_data['climate_events'][frame]
        
        # Plot 1: Agent network with real stress status
        ax1.set_title(f'Supply Chain Network - Round {round_num}')
        ax1.set_xlim(0, 7)
        ax1.set_ylim(0, 4)
        
        # Define positions for consistent agent layout
        agent_positions = {
            'commodity_producer': [(1, 1), (1, 2), (1, 3)],
            'intermediary_firm': [(3, 1.5), (3, 2.5)],
            'final_goods_firm': [(5, 1.5), (5, 2.5)],
            'household': [(6.5, 0.5), (6.5, 1.5), (6.5, 2.5), (6.5, 3.5)]#[:4]  # Show only first 4 households
        }
        
        agent_type_colors = {
            'commodity_producer': '#8B4513',
            'intermediary_firm': '#DAA520',
            'final_goods_firm': '#00FF00',
            'household': '#4169E1'
        }
        
        pos_idx = {'commodity_producer': 0, 'intermediary_firm': 0, 'final_goods_firm': 0, 'household': 0}
        
        for agent in agent_data:
            agent_type = agent['type']
            if agent_type in agent_positions and pos_idx[agent_type] < len(agent_positions[agent_type]):
                pos = agent_positions[agent_type][pos_idx[agent_type]]
                pos_idx[agent_type] += 1
                
                color = '#FF0000' if agent['climate_stressed'] else agent_type_colors[agent_type]
                size = 200 if agent['climate_stressed'] else 100
                
                ax1.scatter(pos[0], pos[1], c=color, s=size, alpha=0.8)
                ax1.text(pos[0], pos[1]-0.2, f"${agent['wealth']:.0f}", 
                        ha='center', fontsize=8)
        
        # Add supply chain flow arrows
        ax1.annotate('', xy=(2.8, 2), xytext=(1.2, 2), 
                    arrowprops=dict(arrowstyle='->', lw=2, color='gray'))
        ax1.annotate('', xy=(4.8, 2), xytext=(3.2, 2), 
                    arrowprops=dict(arrowstyle='->', lw=2, color='gray'))
        ax1.annotate('', xy=(6.3, 2), xytext=(5.2, 2), 
                    arrowprops=dict(arrowstyle='->', lw=2, color='gray'))
        
        ax1.text(1, 3.7, 'Layer 1\nCommodity', ha='center', fontsize=10, fontweight='bold')
        ax1.text(3, 3.7, 'Layer 2\nIntermediary', ha='center', fontsize=10, fontweight='bold')
        ax1.text(5, 3.7, 'Layer 3\nFinal Goods', ha='center', fontsize=10, fontweight='bold')
        ax1.text(6.5, 3.7, 'Households', ha='center', fontsize=10, fontweight='bold')
        
        # Plot 2: Production levels up to current frame
        ax2.set_title('Production Levels Over Time')
        rounds_so_far = visualization_data['rounds'][:frame+1]
        
        commodity_prod = [visualization_data['production_data'][i]['commodity'] for i in range(frame+1)]
        intermediary_prod = [visualization_data['production_data'][i]['intermediary'] for i in range(frame+1)]
        final_goods_prod = [visualization_data['production_data'][i]['final_goods'] for i in range(frame+1)]
        
        ax2.plot(rounds_so_far, commodity_prod, 'o-', label='Commodity', color='#8B4513')
        ax2.plot(rounds_so_far, intermediary_prod, 's-', label='Intermediary', color='#DAA520')
        ax2.plot(rounds_so_far, final_goods_prod, '^-', label='Final Goods', color='#00FF00')
        
        # Add capacity lines (use dynamically calculated values)
        ax2.axhline(y=commodity_capacity, color='#8B4513', linestyle='--', alpha=0.6, linewidth=1.5, label=f'Commodity Cap ({commodity_capacity})')
        ax2.axhline(y=intermediary_capacity, color='#DAA520', linestyle='--', alpha=0.6, linewidth=1.5, label=f'Intermediary Cap ({intermediary_capacity})')
        ax2.axhline(y=final_goods_capacity, color='#00FF00', linestyle='--', alpha=0.6, linewidth=1.5, label=f'Final Goods Cap ({final_goods_capacity})')
        
        # Add current utilization text
        if commodity_prod and intermediary_prod and final_goods_prod:
            current_commodity_util = (commodity_prod[-1] / commodity_capacity) * 100
            current_intermediary_util = (intermediary_prod[-1] / intermediary_capacity) * 100  
            current_final_goods_util = (final_goods_prod[-1] / final_goods_capacity) * 100
            
            ax2.text(0.02, 0.98, f'Round {round_num} Utilization:\nCommodity: {current_commodity_util:.1f}%\nIntermediary: {current_intermediary_util:.1f}%\nFinal Goods: {current_final_goods_util:.1f}%', 
                    transform=ax2.transAxes, fontsize=8, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='lightcyan', alpha=0.8))
        
        ax2.legend(fontsize=8, loc='upper left')
        ax2.set_xlabel('Round')
        ax2.set_ylabel('Production Level')
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
        
        # Plot 4: Wealth distribution
        ax4.set_title('Wealth by Sector')
        wealth_types = list(wealth_data.keys())
        wealth_amounts = list(wealth_data.values())
        colors = ['#8B4513', '#DAA520', '#00FF00', '#4169E1']
        
        bars = ax4.bar(wealth_types, wealth_amounts, color=colors, alpha=0.7)
        ax4.set_ylabel('Total Wealth ($)')
        
        # Add wealth labels
        for bar, amount in zip(bars, wealth_amounts):
            ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(wealth_amounts)*0.01, 
                    f'${amount:.0f}', ha='center', va='bottom', fontsize=9)
        
        # NEW 
        plt.tight_layout()
    
    # Create animation
    num_frames = len(visualization_data['rounds'])
    anim = animation.FuncAnimation(fig, animate, frames=num_frames, interval=1500, repeat=True)
    
    # Save animation
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{simulation_path}/climate_3layer_animation_{timestamp}.gif"
    
    print(f"💾 Saving animation as {filename}...")
    anim.save(filename, writer='pillow', fps=0.67)  # Slower fps for better readability
    print(f"✅ Animation saved: {filename}")
    
    plt.close()  # Clean up memory
    
    return filename

def main(config_file_path):
    """
    Main simulation function that now uses configuration files.
    
    Args:
        config_file_path: Path to the JSON configuration file. If None, uses default "model_config.json"
    """
    # Load configuration
    config_file_path = os.path.join(os.path.dirname(__file__), "model_config.json")
    
    print(f"🔧 Loading configuration from: {config_file_path}")
    config_loader = load_model_config(config_file_path)
    
    # Get simulation parameters from configuration
    simulation_parameters = config_loader.get_simulation_parameters()
    
    # Set up simulation path
    simulation_path = simulation_parameters.get('result_path', 'result_climate_3_layer')
    w = Simulation(path=simulation_path)
    
    # Get the actual path that abcEconomics created (handles increments like resultI, resultII, etc.)
    actual_simulation_path = w.path
    print(f"Simulation will save to: {actual_simulation_path}")

    # Set up simulation logger
    logging_config = config_loader.config.get('logging', {})
    
    if logging_config.get('agent_activity_logging', True):
        log_filename = logging_config.get('log_filename', 'simulation_detailed_log.txt')
        log_file_path = os.path.join(actual_simulation_path, log_filename)
        console_level = logging_config.get('console_level', 'WARNING')
        
        sim_logger = SimulationLogger(log_file_path, console_level=console_level)
        
        # Replace agent print statements with structured logging
        replace_agent_prints_with_logging(sim_logger)
        
        print(f"📄 Detailed agent activity will be logged to: {log_file_path}")
    else:
        # Create a minimal logger that does nothing
        sim_logger = None
        print("📄 Agent activity logging is disabled")

    # Build agents for each layer using configuration
    print(f"\n Building agents from configuration...")
    
    # Get agent configurations
    commodity_config = config_loader.get_agent_config('commodity_producer')
    intermediary_config = config_loader.get_agent_config('intermediary_firm')
    final_goods_config = config_loader.get_agent_config('final_goods_firm')
    household_config = config_loader.get_agent_config('household')
    
    # Build agents with their configurations
    commodity_producers = w.build_agents(
        CommodityProducer, 
        'commodity_producer', 
        commodity_config['count'],
        config=commodity_config
    )
    
    intermediary_firms = w.build_agents(
        IntermediaryFirm, 
        'intermediary_firm', 
        intermediary_config['count'],
        config=intermediary_config
    )
    
    final_goods_firms = w.build_agents(
        FinalGoodsFirm, 
        'final_goods_firm', 
        final_goods_config['count'],
        config=final_goods_config
    )
    
    households = w.build_agents(
        Household, 
        'household', 
        household_config['count'],
        config=household_config
    )
    
    # Create the climate framework
    climate_framework = create_climate_framework(simulation_parameters)
    
    # Organize agents into groups for the framework
    agent_groups = {
        'commodity_producer': commodity_producers,
        'intermediary_firm': intermediary_firms,
        'final_goods_firm': final_goods_firms,
        'household': households
    }
    
    # Assign geographical locations using the framework with configuration rules
    print("🌍 Assigning geographical locations...")
    distribution_rules = config_loader.get_geographical_distribution_rules()
    climate_framework.assign_geographical_locations(agent_groups, distribution_rules)
    
    print(f"\nStarting climate 3-layer geographical simulation with:")
    print(f"  {commodity_producers.num_agents} commodity producers")
    print(f"  {intermediary_firms.num_agents} intermediary firms") 
    print(f"  {final_goods_firms.num_agents} final goods firms")
    print(f"  {households.num_agents} households")
    print(f"  Distributed across continents according to configuration")

    # Set up data collection using configuration
    goods_to_track = config_loader.get_goods_to_track()
    print("goods to track: ", goods_to_track)
    
    # Run simulation
    print(f"\n🚀 Starting simulation for {simulation_parameters['rounds']} rounds...")
    for r in range(simulation_parameters['rounds']):
        print(f"Round {r}...", end=" ")
        
        # Log the round start in the detailed log
        if sim_logger:
            sim_logger.set_round(r)
        
        w.advance_round(r)
        
        # Apply geographical climate stress using the framework
        climate_events = {}
        if simulation_parameters['climate_stress_enabled']:
            if sim_logger:
                sim_logger.set_phase("Climate Events")
            climate_events = climate_framework.apply_geographical_climate_stress(agent_groups)

        # Labor market
        print(f"  Labor market...")
        if sim_logger:
            sim_logger.set_phase("Labor Market")
        labor_endowment = household_config['labor']['endowment']
        households.refresh_services('labor', derived_from='labor_endowment', units=labor_endowment)
        households.sell_labor()
        if sim_logger:
            sim_logger.log_phase_summary(f"Labor offered by households (endowment: {labor_endowment} per household)")
        
        # Layer 1: Commodity producers buy labor and produce
        print(f"  Layer 1: Commodity producers...")
        if sim_logger:
            sim_logger.set_phase("Layer 1: Commodity Producers")
        commodity_producers.buy_labor()
        commodity_producers.production()
        commodity_producers.panel_log(goods=[commodity_config['production']['output'], 'money'])
        
        # Layer 2: Intermediary firms buy commodities and labor, then produce
        print(f"  Layer 2: Intermediary firms...")
        if sim_logger:
            sim_logger.set_phase("Layer 2: Intermediary Firms")
        commodity_producers.sell_commodities()
        intermediary_firms.buy_commodities()
        intermediary_firms.buy_labor()
        intermediary_firms.production()
        intermediary_firms.panel_log(goods=[intermediary_config['production']['output'], 'money'])
        
        # Layer 3: Final goods firms buy intermediate goods and labor, then produce
        print(f"  Layer 3: Final goods firms...")
        if sim_logger:
            sim_logger.set_phase("Layer 3: Final Goods Firms")
        intermediary_firms.sell_intermediate_goods()
        final_goods_firms.buy_intermediate_goods()
        final_goods_firms.buy_labor()
        final_goods_firms.production()
        final_goods_firms.panel_log(goods=[final_goods_config['production']['output'], 'money'])
        
        # Households buy final goods and consume
        print(f"  Consumer market...")
        if sim_logger:
            sim_logger.set_phase("Consumer Market")
        final_goods_firms.sell_final_goods()
        households.buy_final_goods()
        households.panel_log(goods=[household_config['consumption']['preference'], 'money'])
        households.consumption()
        
        # Collect data using the new framework method
        if sim_logger:
            sim_logger.set_phase("Data Collection")
        climate_framework.collect_panel_data(agent_groups, goods_to_track)
        
        print("completed")
    
    print("\nFinalizing simulation...")
    w.finalize()
    print("Simulation completed!")
    print(f"Results saved to: {actual_simulation_path}")
    
    # Log simulation end
    if sim_logger:
        summary_stats = {
            "Total rounds": simulation_parameters['rounds'],
            "Climate events": len([e for events in climate_framework.climate_events_history for e in events]),
            "Agent types": len(agent_groups),
            "Output directory": actual_simulation_path
        }
        sim_logger.log_simulation_end(summary_stats)
    
    # Collect visualization data 
    visualization_data = None
    if simulation_parameters.get('create_dynamic_visualization', False):
        print("\n📊 Collecting visualization data from simulation results...")
        visualization_data = {
            'rounds': [],
            'agent_data': [],
            'climate_events': [],
            'production_data': [],
            'wealth_data': []
        }
        
        # Read data for each round from the CSV files
        for r in range(simulation_parameters['rounds']):
            round_data = collect_simulation_data(actual_simulation_path, r, config_loader, climate_framework)
            
            visualization_data['rounds'].append(r)
            visualization_data['agent_data'].append(round_data['agents'])
            visualization_data['climate_events'].append(round_data['climate'])
            visualization_data['production_data'].append(round_data['production'])
            visualization_data['wealth_data'].append(round_data['wealth'])
            
            # Add debug info
            total_production = sum(round_data['production'].values())
            print(f"    Round {r}: Total production = {total_production:.2f} (commodity: {round_data['production']['commodity']:.2f}, intermediary: {round_data['production']['intermediary']:.2f}, final_goods: {round_data['production']['final_goods']:.2f})")
        
        print("✅ Visualization data collection completed!")
    
    # Create visualizations using the custom supply chain visualizer
    if simulation_parameters['create_visualizations']:
        print("Creating specialized supply chain visualizations...")
        
        # Import the custom supply chain visualizer
        from supply_chain_visualizations import SupplyChainVisualizer
        
        # Create the specialized visualizer with config_loader
        supply_chain_viz = SupplyChainVisualizer(climate_framework, config_loader)
        
        # Create comprehensive supply chain analysis
        supply_chain_viz.create_comprehensive_supply_chain_analysis(
            simulation_path=actual_simulation_path,
            model_name="Climate 3-Layer Supply Chain Model"
        )
        
        # Export climate summary using climate framework
        climate_framework.export_climate_summary(actual_simulation_path, "climate_3_layer_summary.csv")
        
        print("Specialized supply chain visualizations completed!")
    
    # Create time-evolving visualizations
    if simulation_parameters.get('create_dynamic_visualization', False) and visualization_data and visualization_data['rounds']:
        print("\n🎬 Creating time-evolving visualizations from REAL simulation data...")
        
        # Create time evolution plot
        time_plot_file = create_time_evolution_visualization(visualization_data, actual_simulation_path, config_loader)
        
        # Create animated visualization
        animation_file = create_animated_supply_chain(visualization_data, actual_simulation_path, config_loader)
        
        print(f"\n🎉 Dynamic visualizations completed!")
        print(f"📊 Time evolution plot: {time_plot_file}")
        print(f"🎞️ Animation: {animation_file}")
    
    # Print summary
    total_climate_events = sum(len(events) for events in climate_framework.climate_events_history)
    print(f"\nSummary: Successfully completed {len(climate_framework.climate_events_history)} rounds")
    print(f"Total climate events occurred: {total_climate_events}")
    print(f"Geographical assignments: {len(climate_framework.geographical_assignments)} agent types")
    
    return climate_framework


if __name__ == '__main__':
    import sys
    
    # Allow specifying config file as command line argument
    config_file = sys.argv[1] if len(sys.argv) > 1 else None
    
    if config_file is None:
        print("No configuration file provided.")
        sys.exit()
        
    print("🌍 Climate 3-Layer Economic Model with Configurable Parameters")
    print("=" * 60)
    
    results = main(config_file)
    print(f"\n✅ Final result summary: {len(results.climate_events_history)} rounds completed")
    print(f"📊 Configuration-driven simulation successful!") 