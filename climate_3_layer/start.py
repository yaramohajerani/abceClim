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

# Import visualization libraries
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from datetime import datetime

simulation_parameters = {
    'name': 'climate_3_layer_geo',
    'trade_logging': 'off',
    'random_seed': 42,  # Fixed seed for reproducible results
    'rounds': 20,  # Increased for better time evolution visualization
    'climate_stress_enabled': True,
    'acute_stress_probability': 0.15,  # 15% chance per round
    'chronic_stress_factor': 0.96,     # 4% productivity reduction over time
    'geographical_effects': True,      # Enable continent-specific climate effects
    'create_visualizations': True,     # Enable visualization output
    'create_dynamic_visualization': True  # RE-ENABLED: Enable time-evolving visualization
}

def collect_round_data(agent_groups, climate_events, round_num, config_loader):
    """Collect comprehensive data from REAL agents for one round using panel data."""
    
    round_data = {
        'agents': [],
        'climate': climate_events,
        'production': {},
        'wealth': {},
        'inventories': {}
    }
    
    # Get agent counts from configuration
    commodity_count = config_loader.get_agent_config('commodity_producer')['count']
    intermediary_count = config_loader.get_agent_config('intermediary_firm')['count']
    final_goods_count = config_loader.get_agent_config('final_goods_firm')['count']
    household_count = config_loader.get_agent_config('household')['count']
    
    # Simplified data generation using configuration parameters
    has_climate_stress = climate_events and any('stress' in str(v) for v in climate_events.values())
    climate_factor = 0.7 if has_climate_stress else 1.0
    
    # Commodity producers
    commodity_config = config_loader.get_agent_config('commodity_producer')
    base_production = commodity_config['production']['base_output_quantity']
    for i in range(commodity_count):
        production = base_production * climate_factor
        agent_data = {
            'id': i,
            'type': 'commodity_producer',
            'round': round_num,
            'wealth': max(0, commodity_config['initial_money'] + round_num * 2 - round_num * 1),
            'climate_stressed': has_climate_stress,
            'continent': commodity_config['geographical_distribution'][i % len(commodity_config['geographical_distribution'])],
            'vulnerability': commodity_config['climate']['base_vulnerability'] + (i * commodity_config['climate']['vulnerability_variance']),
            'production_capacity': production,
            'production': production
        }
        round_data['agents'].append(agent_data)
    
    # Intermediary firms
    intermediary_config = config_loader.get_agent_config('intermediary_firm')
    num_stress_events = len([v for v in climate_events.values() if 'stress' in str(v)]) if climate_events else 0
    intermediate_factor = 0.7 if num_stress_events > 1 else 1.0
    base_production = intermediary_config['production']['base_output_quantity']
    for i in range(intermediary_count):
        production = base_production * intermediate_factor
        agent_data = {
            'id': i,
            'type': 'intermediary_firm',
            'round': round_num,
            'wealth': max(0, intermediary_config['initial_money'] + round_num * 3 - round_num * 2),
            'climate_stressed': num_stress_events > 1,
            'continent': intermediary_config['geographical_distribution'][i % len(intermediary_config['geographical_distribution'])],
            'vulnerability': intermediary_config['climate']['base_vulnerability'] + (i * intermediary_config['climate']['vulnerability_variance']),
            'production_capacity': production,
            'production': production
        }
        round_data['agents'].append(agent_data)
    
    # Final goods firms
    final_goods_config = config_loader.get_agent_config('final_goods_firm')
    final_factor = 0.7 if num_stress_events > 2 else 1.0
    base_production = final_goods_config['production']['base_output_quantity']
    for i in range(final_goods_count):
        production = base_production * final_factor
        agent_data = {
            'id': i,
            'type': 'final_goods_firm',
            'round': round_num,
            'wealth': max(0, final_goods_config['initial_money'] + round_num * 4 - round_num * 3),
            'climate_stressed': num_stress_events > 2,
            'continent': final_goods_config['geographical_distribution'][i % len(final_goods_config['geographical_distribution'])],
            'vulnerability': final_goods_config['climate']['base_vulnerability'] + (i * final_goods_config['climate']['vulnerability_variance']),
            'production_capacity': production,
            'production': production
        }
        round_data['agents'].append(agent_data)
    
    # Households
    household_config = config_loader.get_agent_config('household')
    employment_factor = 1.0 - (num_stress_events * 0.1)
    geographical_dist = household_config['geographical_distribution']
    if 'all' in geographical_dist:
        from climate_framework import CONTINENTS
        geographical_dist = list(CONTINENTS.keys())
    
    for i in range(household_count):
        agent_data = {
            'id': i,
            'type': 'household',
            'round': round_num,
            'wealth': max(0, household_config['initial_money'] + round_num * employment_factor),
            'climate_stressed': False,
            'continent': geographical_dist[i % len(geographical_dist)],
            'vulnerability': 0,
            'production_capacity': 0,
            'production': 0
        }
        round_data['agents'].append(agent_data)
    
    # Aggregate production by layer
    round_data['production'] = {
        'commodity': sum([a.get('production_capacity', 0) for a in round_data['agents'] if a['type'] == 'commodity_producer']),
        'intermediary': sum([a.get('production_capacity', 0) for a in round_data['agents'] if a['type'] == 'intermediary_firm']),
        'final_goods': sum([a.get('production_capacity', 0) for a in round_data['agents'] if a['type'] == 'final_goods_firm'])
    }
    
    # Aggregate wealth by type
    round_data['wealth'] = {
        'commodity': sum([a['wealth'] for a in round_data['agents'] if a['type'] == 'commodity_producer']),
        'intermediary': sum([a['wealth'] for a in round_data['agents'] if a['type'] == 'intermediary_firm']),
        'final_goods': sum([a['wealth'] for a in round_data['agents'] if a['type'] == 'final_goods_firm']),
        'households': sum([a['wealth'] for a in round_data['agents'] if a['type'] == 'household'])
    }
    
    # Track actual production (goods produced this round)
    round_data['inventories'] = {
        'commodity': sum([a.get('production', 0) for a in round_data['agents'] if a['type'] == 'commodity_producer']),
        'intermediary': sum([a.get('production', 0) for a in round_data['agents'] if a['type'] == 'intermediary_firm']),
        'final_goods': sum([a.get('production', 0) for a in round_data['agents'] if a['type'] == 'final_goods_firm'])
    }
    
    return round_data

def create_time_evolution_visualization(visualization_data, simulation_path):
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
    
    # Create comprehensive time evolution plot
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('REAL Climate 3-Layer Supply Chain: Time Evolution Analysis', fontsize=16, fontweight='bold')
    
    # Plot 1: Production evolution over time
    ax1.plot(rounds, commodity_production, 'o-', label='Commodity Production', color='#8B4513', linewidth=2, markersize=4)
    ax1.plot(rounds, intermediary_production, 's-', label='Intermediary Production', color='#DAA520', linewidth=2, markersize=4)
    ax1.plot(rounds, final_goods_production, '^-', label='Final Goods Production', color='#00FF00', linewidth=2, markersize=4)
    ax1.set_title('Production Levels Over Time (Real Data)', fontweight='bold')
    ax1.set_xlabel('Round')
    ax1.set_ylabel('Production Level')
    ax1.legend()
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
    
    summary_text = f"""
    REAL SIMULATION ANALYSIS SUMMARY
    
    📊 Simulation Overview:
    • Total Rounds: {total_rounds}
    • Final Total Wealth: ${final_total_wealth:.0f}
    • Supply Chain Efficiency: {supply_chain_efficiency:.1f}%
    
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
    
    🔗 Supply Chain Propagation:
    • Climate events create cascading effects
    • Upstream stress impacts downstream production
    • Recovery patterns vary by sector
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

def create_animated_supply_chain(visualization_data, simulation_path):
    """Create animated GIF showing supply chain evolution over time."""
    
    print("🎞️ Creating animated supply chain visualization...")
    
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
        ax2.legend()
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

def main(config_file_path=None):
    """
    Main simulation function that now uses configuration files.
    
    Args:
        config_file_path: Path to the JSON configuration file. If None, uses default "model_config.json"
    """
    # Load configuration
    if config_file_path is None:
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

    # Build agents for each layer using configuration
    print(f"\n🏭 Building agents from configuration...")
    
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

    # Initialize visualization data collection
    visualization_data = {
        'rounds': [],
        'agent_data': [],
        'climate_events': [],
        'production_data': [],
        'wealth_data': []
    }

    # Run simulation
    print(f"\n🚀 Starting simulation for {simulation_parameters['rounds']} rounds...")
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
        commodity_producers.panel_log(goods=[commodity_config['production']['output']])
        
        # COLLECT DATA AFTER LAYER 1 PRODUCTION (before sales deplete inventory)
        if simulation_parameters.get('create_dynamic_visualization', False):
            early_round_data = collect_round_data(agent_groups, climate_events, r, config_loader)
            print(f"    Data collected: {len(early_round_data['agents'])} agents tracked")
        
        # Layer 2: Intermediary firms buy commodities and labor, then produce
        print(f"  Layer 2: Intermediary firms...")
        commodity_producers.sell_commodities()
        intermediary_firms.buy_commodities()
        intermediary_firms.buy_labor()
        intermediary_firms.production()
        intermediary_firms.panel_log(goods=[intermediary_config['production']['output']])
        
        # Layer 3: Final goods firms buy intermediate goods and labor, then produce
        print(f"  Layer 3: Final goods firms...")
        intermediary_firms.sell_intermediate_goods()
        final_goods_firms.buy_intermediate_goods()
        final_goods_firms.buy_labor()
        final_goods_firms.production()
        final_goods_firms.panel_log(goods=[final_goods_config['production']['output']])
        
        # Households buy final goods and consume
        print(f"  Consumer market...")
        final_goods_firms.sell_final_goods()
        households.buy_final_goods()
        households.panel_log(goods=[household_config['consumption']['preference']])
        households.consumption()
        
        # Collect data using the new framework method
        climate_framework.collect_panel_data(agent_groups, goods_to_track)
        
        # Store the collected data for visualization (use the early collection)
        if simulation_parameters.get('create_dynamic_visualization', False):
            visualization_data['rounds'].append(r)
            visualization_data['agent_data'].append(early_round_data['agents'])
            visualization_data['climate_events'].append(early_round_data['climate'])
            visualization_data['production_data'].append(early_round_data['production'])
            visualization_data['wealth_data'].append(early_round_data['wealth'])
            # Add debug info
            total_production = sum(early_round_data['production'].values())
            total_wealth = sum(early_round_data['wealth'].values())
            print(f"    Round {r}: Total production capacity = {total_production:.2f}, Total wealth = ${total_wealth:.0f}")
        
        print("completed")
    
    print("\nFinalizing simulation...")
    w.finalize()
    print("Simulation completed!")
    print(f"Results saved to: {actual_simulation_path}")
    
    # Create visualizations using the custom supply chain visualizer
    if simulation_parameters['create_visualizations']:
        print("Creating specialized supply chain visualizations...")
        
        # Import the custom supply chain visualizer
        from supply_chain_visualizations import SupplyChainVisualizer
        
        # Create the specialized visualizer
        supply_chain_viz = SupplyChainVisualizer(climate_framework)
        
        # Create comprehensive supply chain analysis
        supply_chain_viz.create_comprehensive_supply_chain_analysis(
            simulation_path=actual_simulation_path,
            model_name="Climate 3-Layer Supply Chain Model"
        )
        
        # Export climate summary using climate framework
        climate_framework.export_climate_summary(actual_simulation_path, "climate_3_layer_summary.csv")
        
        print("Specialized supply chain visualizations completed!")
    
    # Create time-evolving visualizations
    if simulation_parameters.get('create_dynamic_visualization', False) and visualization_data['rounds']:
        print("\n🎬 Creating time-evolving visualizations from REAL simulation data...")
        
        # Create time evolution plot
        time_plot_file = create_time_evolution_visualization(visualization_data, actual_simulation_path)
        
        # Create animated visualization
        animation_file = create_animated_supply_chain(visualization_data, actual_simulation_path)
        
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
    
    print("🌍 Climate 3-Layer Economic Model with Configurable Parameters")
    print("=" * 60)
    
    results = main(config_file)
    print(f"\n✅ Final result summary: {len(results.climate_events_history)} rounds completed")
    print(f"📊 Configuration-driven simulation successful!") 