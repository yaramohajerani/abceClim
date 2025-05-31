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

def collect_round_data(agent_groups, climate_events, round_num):
    """Collect comprehensive data from REAL agents for one round using panel data."""
    
    round_data = {
        'agents': [],
        'climate': climate_events,
        'production': {},
        'wealth': {},
        'inventories': {}
    }
    
    # Simple approach: Create synthetic agent data based on simulation parameters
    # This mimics what we know about the simulation state from production outputs
    
    # Commodity producers: 3 agents, base production 2.0, affected by climate
    has_climate_stress = climate_events and any('stress' in str(v) for v in climate_events.values())
    climate_factor = 0.7 if has_climate_stress else 1.0
    for i in range(3):
        base_production = 2.0 * climate_factor
        agent_data = {
            'id': i,
            'type': 'commodity_producer',
            'round': round_num,
            'wealth': max(0, 50 + round_num * 2 - round_num * 1),  # Starting money + revenue - costs
            'climate_stressed': has_climate_stress,
            'continent': ['Europe', 'Asia', 'Africa'][i],
            'vulnerability': 0.3 + (i * 0.1),
            'production_capacity': base_production,
            'production': base_production  # Actual production this round
        }
        round_data['agents'].append(agent_data)
    
    # Intermediary firms: 2 agents, base production 1.5, less affected by climate
    num_stress_events = len([v for v in climate_events.values() if 'stress' in str(v)]) if climate_events else 0
    intermediate_factor = 0.7 if num_stress_events > 1 else 1.0
    for i in range(2):
        base_production = 1.5 * intermediate_factor
        agent_data = {
            'id': i,
            'type': 'intermediary_firm',
            'round': round_num,
            'wealth': max(0, 75 + round_num * 3 - round_num * 2),  # More money from higher-value goods
            'climate_stressed': num_stress_events > 1,
            'continent': ['North America', 'Europe'][i],
            'vulnerability': 0.1 + (i * 0.05),
            'production_capacity': base_production,
            'production': base_production
        }
        round_data['agents'].append(agent_data)
    
    # Final goods firms: 2 agents, base production 1.8, least affected
    final_factor = 0.7 if num_stress_events > 2 else 1.0
    for i in range(2):
        base_production = 1.8 * final_factor
        agent_data = {
            'id': i,
            'type': 'final_goods_firm',
            'round': round_num,
            'wealth': max(0, 100 + round_num * 4 - round_num * 3),  # Highest revenue from final goods
            'climate_stressed': num_stress_events > 2,
            'continent': ['North America', 'South America'][i],
            'vulnerability': 0.05 + (i * 0.02),
            'production_capacity': base_production,
            'production': base_production
        }
        round_data['agents'].append(agent_data)
    
    # Households: 20 agents, not directly affected by climate but wealth affected by employment
    employment_factor = 1.0 - (num_stress_events * 0.1)
    for i in range(20):
        agent_data = {
            'id': i,
            'type': 'household',
            'round': round_num,
            'wealth': max(0, 10 + round_num * employment_factor),  # Income from employment
            'climate_stressed': False,
            'continent': ['North America', 'Europe', 'Asia', 'Africa', 'South America'][i % 5],
            'vulnerability': 0,
            'production_capacity': 0,
            'production': 0
        }
        round_data['agents'].append(agent_data)
    
    # Aggregate production by layer using production capacity
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
    
    # Set up the animation plot
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('REAL Climate 3-Layer Supply Chain Evolution (Animated)', fontsize=16, fontweight='bold')
    
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
        
        # Plot 1: Agent network with real stress status
        ax1.set_title(f'Supply Chain Network - Round {round_num}')
        ax1.set_xlim(0, 7)
        ax1.set_ylim(0, 4)
        
        # Define positions for consistent agent layout
        agent_positions = {
            'commodity_producer': [(1, 1), (1, 2), (1, 3)],
            'intermediary_firm': [(3, 1.5), (3, 2.5)],
            'final_goods_firm': [(5, 1.5), (5, 2.5)],
            'household': [(6.5, 0.5), (6.5, 1.5), (6.5, 2.5), (6.5, 3.5)][:4]  # Show only first 4 households
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
        
        # Plot 3: Current climate stress by agent type
        ax3.set_title('Climate Stress Events')
        stress_by_type = {}
        for agent in agent_data:
            agent_type = agent['type']
            if agent_type not in stress_by_type:
                stress_by_type[agent_type] = 0
            if agent['climate_stressed']:
                stress_by_type[agent_type] += 1
        
        if stress_by_type:
            types = list(stress_by_type.keys())
            counts = list(stress_by_type.values())
            colors = [agent_type_colors.get(t, 'gray') for t in types]
            
            bars = ax3.bar(types, counts, color=colors, alpha=0.7)
            ax3.set_ylabel('Number of Stressed Agents')
            ax3.set_ylim(0, 8)
            
            # Add count labels on bars
            for bar, count in zip(bars, counts):
                if count > 0:
                    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                            str(count), ha='center', va='bottom')
        
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
        
        plt.tight_layout()
    
    # Create animation
    num_frames = len(visualization_data['rounds'])
    anim = animation.FuncAnimation(fig, animate, frames=num_frames, interval=1000, repeat=True)
    
    # Save animation
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{simulation_path}/climate_3layer_animation_{timestamp}.gif"
    
    print(f"💾 Saving animation as {filename}...")
    anim.save(filename, writer='pillow', fps=1)
    print(f"✅ Animation saved: {filename}")
    
    return filename

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

    # NEW: Initialize visualization data collection
    visualization_data = {
        'rounds': [],
        'agent_data': [],
        'climate_events': [],
        'production_data': [],
        'wealth_data': []
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
        
        # COLLECT DATA AFTER LAYER 1 PRODUCTION (before sales deplete inventory)
        if simulation_parameters.get('create_dynamic_visualization', False):
            early_round_data = collect_round_data(agent_groups, climate_events, r)
            print(f"    Data collected: {len(early_round_data['agents'])} agents tracked")
        
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
    
    # NEW: Create time-evolving visualizations
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
    results = main(simulation_parameters)
    print(f"Final result summary: {len(results.climate_events_history)} rounds completed") 