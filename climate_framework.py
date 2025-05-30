"""
Climate Economics Framework

A reusable framework for adding geographical distribution, climate stress,
and visualization capabilities to agent-based economic models.
"""

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from matplotlib.animation import FuncAnimation
import seaborn as sns
import random
from typing import Dict, List, Any, Tuple, Optional

# Define continents and their climate characteristics
CONTINENTS = {
    'North America': {'climate_risk': 0.8, 'position': (-100, 50), 'color': 'blue'},
    'Europe': {'climate_risk': 0.6, 'position': (10, 50), 'color': 'green'},
    'Asia': {'climate_risk': 1.2, 'position': (100, 30), 'color': 'red'},
    'South America': {'climate_risk': 1.0, 'position': (-60, -20), 'color': 'orange'},
    'Africa': {'climate_risk': 1.1, 'position': (20, 0), 'color': 'purple'}
}


class ClimateFramework:
    """
    Core framework for climate economics modeling with geographical distribution.
    """
    
    def __init__(self, simulation_parameters: Dict[str, Any]):
        self.params = simulation_parameters
        self.results = {
            'round': [],
            'climate_events': [],
            'production_by_continent': [],
            'agent_status': [],
            'trade_flows': []
        }
    
    def assign_geographical_locations(self, agent_groups: Dict[str, List], 
                                    distribution_rules: Optional[Dict] = None):
        """
        Assign agents to continents based on configurable distribution rules.
        
        Args:
            agent_groups: Dictionary mapping agent type names to abcEconomics agent groups
            distribution_rules: Custom rules for geographical distribution
        """
        if distribution_rules is None:
            distribution_rules = self._get_default_distribution_rules()
        
        continents = list(CONTINENTS.keys())
        
        for agent_type, agent_group in agent_groups.items():
            if agent_type in distribution_rules:
                target_continents = distribution_rules[agent_type]
            else:
                target_continents = continents  # Default to all continents
            
            # Use the correct abcEconomics API to access individual agents
            num_agents = agent_group.num_agents
            print(f"  Assigning {num_agents} {agent_type.replace('_', ' ')}s to continents...")
            
            for i in range(num_agents):
                # Access individual agent by name
                agent_name = f'{agent_type}_{i}'
                try:
                    agent = agent_group.by_name(agent_name)
                    continent = target_continents[i % len(target_continents)]
                    
                    # Set continent attribute directly on agent
                    agent.continent = continent
                    
                    # Apply geographical climate risk multiplier safely
                    base_vulnerability = 0.1  # Default vulnerability
                    if hasattr(agent, 'climate_vulnerability'):
                        try:
                            current_vulnerability = getattr(agent, 'climate_vulnerability')
                            if isinstance(current_vulnerability, (int, float)):
                                base_vulnerability = current_vulnerability
                        except:
                            pass  # Use default
                    
                    # Apply the continental risk multiplier
                    new_vulnerability = base_vulnerability * CONTINENTS[continent]['climate_risk']
                    agent.climate_vulnerability = new_vulnerability
                    
                    print(f"    {agent_type.replace('_', ' ').title()} {i} located in {continent} (vulnerability: {new_vulnerability:.2f})")
                    
                except Exception as e:
                    print(f"    Warning: Could not assign location to {agent_name}: {e}")
                    continue
    
    def _get_default_distribution_rules(self) -> Dict[str, List[str]]:
        """Default geographical distribution rules for common agent types."""
        return {
            'commodity_producer': ['Asia', 'South America', 'Africa'],  # Resource-rich
            'intermediary_firm': ['Asia', 'Europe'],  # Industrial
            'final_goods_firm': ['North America', 'Europe'],  # Developed markets
            'household': list(CONTINENTS.keys()),  # Distributed globally
            'firm': ['North America', 'Europe', 'Asia'],  # General firms
            'bank': ['North America', 'Europe', 'Asia'],  # Financial centers
            'government': list(CONTINENTS.keys())  # All continents
        }
    
    def apply_geographical_climate_stress(self, agent_groups: Dict[str, List]) -> Dict[str, str]:
        """
        Apply climate stress with geographical variation across all agent types.
        
        Args:
            agent_groups: Dictionary mapping agent type names to abcEconomics agent groups
            
        Returns:
            Dictionary of climate events by continent
        """
        climate_events = {}
        
        # Determine which continents experience acute stress
        for continent, info in CONTINENTS.items():
            continent_risk = info['climate_risk']
            adjusted_probability = self.params['acute_stress_probability'] * continent_risk
            
            if random.random() < adjusted_probability:
                climate_events[continent] = 'acute_stress'
                print(f"[ACUTE CLIMATE STRESS in {continent}]", end=" ")
        
        # Apply acute stress to affected agents
        for agent_type, agent_group in agent_groups.items():
            num_agents = agent_group.num_agents
            for i in range(num_agents):
                agent_name = f'{agent_type}_{i}'
                try:
                    agent = agent_group.by_name(agent_name)
                    if hasattr(agent, 'continent') and agent.continent in climate_events:
                        if hasattr(agent, 'apply_acute_stress'):
                            agent.apply_acute_stress()
                except Exception as e:
                    continue  # Skip failed agents
        
        # Apply chronic stress globally to all agents with the capability
        chronic_factor = self.params.get('chronic_stress_factor', 0.95)
        for agent_type, agent_group in agent_groups.items():
            num_agents = agent_group.num_agents
            for i in range(num_agents):
                agent_name = f'{agent_type}_{i}'
                try:
                    agent = agent_group.by_name(agent_name)
                    if hasattr(agent, 'apply_chronic_stress'):
                        agent.apply_chronic_stress(chronic_factor)
                except Exception as e:
                    continue  # Skip failed agents
        
        return climate_events
    
    def collect_round_data(self, round_num: int, agent_groups: Dict[str, List], 
                          climate_events: Dict[str, str], 
                          custom_metrics: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Collect comprehensive data for the current round.
        
        Args:
            round_num: Current simulation round
            agent_groups: Dictionary mapping agent type names to abcEconomics agent groups
            climate_events: Climate events for this round
            custom_metrics: Additional custom metrics to collect
            
        Returns:
            Dictionary containing all collected data
        """
        # Production by continent
        production_data = {continent: {} for continent in CONTINENTS.keys()}
        
        # Agent status data
        agent_data = []
        
        # Trade flow data
        trade_data = {}
        
        for agent_type, agent_group in agent_groups.items():
            # Initialize production tracking for this agent type
            for continent in CONTINENTS.keys():
                production_data[continent][agent_type] = 0
            
            # Initialize trade tracking
            trade_data[f"{agent_type}_trade"] = 0
            
            num_agents = agent_group.num_agents
            for i in range(num_agents):
                agent_name = f'{agent_type}_{i}'
                try:
                    agent = agent_group.by_name(agent_name)
                    continent = getattr(agent, 'continent', 'Unknown')
                    
                    # Collect production data (flexible goods detection)
                    total_production = 0
                    goods_possessed = self._get_agent_goods(agent)
                    
                    for good, quantity in goods_possessed.items():
                        if good != 'money' and good != 'labor':  # Exclude non-production goods
                            total_production += quantity
                            trade_data[f"{agent_type}_trade"] += quantity
                    
                    if continent in production_data:
                        production_data[continent][agent_type] += total_production
                    
                    # Collect agent status
                    agent_data.append({
                        'id': f"{agent_type}_{i}",
                        'type': agent_type,
                        'continent': continent,
                        'money': agent.possession('money') if hasattr(agent, 'possession') else 0,
                        'total_production': total_production,
                        'vulnerability': getattr(agent, 'climate_vulnerability', 0),
                        'stress_factor': getattr(agent, 'chronic_stress_accumulated', 1.0),
                        'round': round_num
                    })
                except Exception as e:
                    continue  # Skip failed agents
        
        # Add custom metrics if provided
        if custom_metrics:
            trade_data.update(custom_metrics)
        
        round_data = {
            'production': production_data,
            'agents': agent_data,
            'trades': trade_data,
            'climate_events': climate_events
        }
        
        # Store in results
        self.results['round'].append(round_num)
        self.results['climate_events'].append(climate_events)
        self.results['production_by_continent'].append(production_data)
        self.results['agent_status'].append(agent_data)
        self.results['trade_flows'].append(trade_data)
        
        return round_data
    
    def _get_agent_goods(self, agent) -> Dict[str, float]:
        """Get all goods possessed by an agent."""
        goods = {}
        if hasattr(agent, '_inventory'):
            if hasattr(agent._inventory, 'haves'):
                goods = dict(agent._inventory.haves)
        return goods
    
    def create_visualizations(self, agent_groups: Dict[str, List], 
                            model_name: str = "Climate Economic Model",
                            save_path: Optional[str] = None):
        """
        Create comprehensive visualizations of the geographical climate model.
        
        Args:
            agent_groups: Dictionary mapping agent type names to abcEconomics agent groups
            model_name: Name of the model for titles
            save_path: Optional custom save path for the visualization
        """
        if not self.results['round']:
            print("No data to visualize. Run simulation first.")
            return
        
        # Set up the visualization style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        # Create figure with subplots
        fig = plt.figure(figsize=(20, 15))
        fig.suptitle(f'{model_name} - Geographical Climate Analysis', fontsize=16, fontweight='bold')
        
        # 1. Geographical Network Visualization
        ax1 = plt.subplot(2, 3, 1)
        self._create_network_visualization(ax1, agent_groups)
        
        # 2. Production by Continent Over Time
        ax2 = plt.subplot(2, 3, 2)
        self._create_production_timeline(ax2)
        
        # 3. Climate Events Map
        ax3 = plt.subplot(2, 3, 3)
        self._create_climate_events_visualization(ax3)
        
        # 4. Agent Status Heatmap
        ax4 = plt.subplot(2, 3, 4)
        self._create_agent_status_heatmap(ax4)
        
        # 5. Supply Chain Flow
        ax5 = plt.subplot(2, 3, 5)
        self._create_supply_chain_flow(ax5)
        
        # 6. Economic Impact Analysis
        ax6 = plt.subplot(2, 3, 6)
        self._create_economic_impact_analysis(ax6)
        
        plt.tight_layout()
        
        # Save visualization
        if save_path is None:
            save_path = f'{model_name.lower().replace(" ", "_")}_geographical_analysis.png'
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"Visualizations saved as '{save_path}'")
    
    def _create_network_visualization(self, ax, agent_groups: Dict[str, List]):
        """Create a network graph showing agent locations and connections."""
        G = nx.Graph()
        pos = {}
        node_colors = []
        node_sizes = []
        
        # Color and size mapping for different agent types
        type_colors = {'commodity_producer': 'brown', 'intermediary_firm': 'blue', 
                      'final_goods_firm': 'green', 'household': 'gray', 'firm': 'purple'}
        type_sizes = {'commodity_producer': 300, 'intermediary_firm': 400, 
                     'final_goods_firm': 500, 'household': 100, 'firm': 350}
        
        # Add nodes for each agent
        for agent_type, agent_group in agent_groups.items():
            num_agents = agent_group.num_agents
            for i in range(num_agents):
                agent_name = f'{agent_type}_{i}'
                try:
                    agent = agent_group.by_name(agent_name)
                    continent = getattr(agent, 'continent', 'Unknown')
                    
                    # Only add node if we can successfully get continent info
                    if continent in CONTINENTS:
                        node_id = f"{agent_type}_{i}"
                        G.add_node(node_id)  # Only add node after successful agent retrieval
                        
                        # Offset agents of same type slightly
                        offset_x = (i % 3 - 1) * 3
                        offset_y = (i // 3) * 2
                        pos[node_id] = (CONTINENTS[continent]['position'][0] + offset_x, 
                                       CONTINENTS[continent]['position'][1] + offset_y)
                        node_colors.append(CONTINENTS[continent]['color'])
                        node_sizes.append(type_sizes.get(agent_type, 250))
                        
                except Exception as e:
                    print(f"    Warning: Could not add node for {agent_name}: {e}")
                    continue  # Skip failed agents
        
        # Add edges based on typical supply chain relationships
        self._add_supply_chain_edges(G, agent_groups)
        
        # Only draw if we have nodes with positions
        if len(pos) > 0:
            nx.draw(G, pos, ax=ax, node_color=node_colors, node_size=node_sizes, 
                    with_labels=True, font_size=6, font_weight='bold', 
                    edge_color='gray', alpha=0.7)
        else:
            ax.text(0.5, 0.5, 'No agent positions available', 
                    ha='center', va='center', transform=ax.transAxes)
        
        ax.set_title('Geographical Distribution of Agents', fontsize=14, fontweight='bold')
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
    
    def _add_supply_chain_edges(self, G, agent_groups: Dict[str, List]):
        """Add edges representing supply chain relationships."""
        # Standard supply chain connections
        if 'commodity_producer' in agent_groups and 'intermediary_firm' in agent_groups:
            cp_group = agent_groups['commodity_producer']
            inf_group = agent_groups['intermediary_firm']
            for i in range(cp_group.num_agents):
                for j in range(inf_group.num_agents):
                    node1 = f"commodity_producer_{i}"
                    node2 = f"intermediary_firm_{j}"
                    # Only add edge if both nodes exist in the graph
                    if node1 in G.nodes and node2 in G.nodes:
                        G.add_edge(node1, node2)
        
        if 'intermediary_firm' in agent_groups and 'final_goods_firm' in agent_groups:
            inf_group = agent_groups['intermediary_firm']
            fg_group = agent_groups['final_goods_firm']
            for i in range(inf_group.num_agents):
                for j in range(fg_group.num_agents):
                    node1 = f"intermediary_firm_{i}"
                    node2 = f"final_goods_firm_{j}"
                    # Only add edge if both nodes exist in the graph
                    if node1 in G.nodes and node2 in G.nodes:
                        G.add_edge(node1, node2)
        
        # General firm connections (if no specific supply chain)
        if 'firm' in agent_groups:
            firm_group = agent_groups['firm']
            num_firms = firm_group.num_agents
            for i in range(num_firms - 1):
                node1 = f"firm_{i}"
                node2 = f"firm_{i+1}"
                # Only add edge if both nodes exist in the graph
                if node1 in G.nodes and node2 in G.nodes:
                    G.add_edge(node1, node2)
    
    def _create_production_timeline(self, ax):
        """Create timeline showing production by continent."""
        rounds = self.results['round']
        
        # Aggregate production data by continent
        continent_production = {continent: [] for continent in CONTINENTS.keys()}
        
        for round_data in self.results['production_by_continent']:
            for continent in CONTINENTS.keys():
                total_production = sum(round_data.get(continent, {}).values())
                continent_production[continent].append(total_production)
        
        # Plot lines for each continent
        for continent, production in continent_production.items():
            if any(p > 0 for p in production):  # Only plot if there's production
                ax.plot(rounds, production, label=continent, 
                        color=CONTINENTS[continent]['color'], linewidth=2, marker='o')
        
        ax.set_title('Total Production by Continent Over Time', fontsize=14, fontweight='bold')
        ax.set_xlabel('Round')
        ax.set_ylabel('Total Production')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _create_climate_events_visualization(self, ax):
        """Visualize climate events across continents and time."""
        rounds = self.results['round']
        continents = list(CONTINENTS.keys())
        
        # Create a heatmap matrix
        climate_matrix = np.zeros((len(continents), len(rounds)))
        
        for round_idx, climate_events in enumerate(self.results['climate_events']):
            for continent_idx, continent in enumerate(continents):
                if continent in climate_events:
                    climate_matrix[continent_idx, round_idx] = 1
        
        im = ax.imshow(climate_matrix, cmap='Reds', aspect='auto', interpolation='nearest')
        
        ax.set_yticks(range(len(continents)))
        ax.set_yticklabels(continents)
        ax.set_xticks(range(0, len(rounds), max(1, len(rounds)//10)))
        ax.set_xticklabels(range(0, len(rounds), max(1, len(rounds)//10)))
        ax.set_title('Climate Events by Continent and Time', fontsize=14, fontweight='bold')
        ax.set_xlabel('Round')
        ax.set_ylabel('Continent')
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label('Climate Event Occurred')
    
    def _create_agent_status_heatmap(self, ax):
        """Create heatmap showing agent financial health over time."""
        if not self.results['agent_status']:
            ax.text(0.5, 0.5, 'No agent status data available', 
                    ha='center', va='center', transform=ax.transAxes)
            return
        
        # Get the latest round data
        latest_data = self.results['agent_status'][-1]
        
        # Create DataFrame for heatmap
        agent_df = pd.DataFrame(latest_data)
        
        if not agent_df.empty and 'money' in agent_df.columns:
            # Pivot data for heatmap
            heatmap_data = agent_df.pivot_table(values='money', index='continent', 
                                               columns='type', fill_value=0, aggfunc='mean')
            
            sns.heatmap(heatmap_data, annot=True, fmt='.1f', cmap='RdYlGn', ax=ax)
            ax.set_title('Agent Financial Status by Continent (Latest Round)', fontsize=14, fontweight='bold')
        else:
            ax.text(0.5, 0.5, 'No valid financial data', ha='center', va='center', transform=ax.transAxes)
    
    def _create_supply_chain_flow(self, ax):
        """Visualize the flow of goods through the supply chain."""
        rounds = self.results['round']
        
        # Extract trade flow data
        trade_types = set()
        for trade_data in self.results['trade_flows']:
            trade_types.update(trade_data.keys())
        
        # Plot each trade type
        for trade_type in sorted(trade_types):
            flows = [data.get(trade_type, 0) for data in self.results['trade_flows']]
            if any(f > 0 for f in flows):  # Only plot if there's flow
                ax.plot(rounds, flows, label=trade_type.replace('_', ' ').title(), 
                        linewidth=2, marker='o')
        
        ax.set_title('Economic Flow Over Time', fontsize=14, fontweight='bold')
        ax.set_xlabel('Round')
        ax.set_ylabel('Economic Activity')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _create_economic_impact_analysis(self, ax):
        """Analyze the economic impact of climate events."""
        rounds = self.results['round']
        
        # Calculate total production for each round
        total_production = []
        climate_event_rounds = []
        
        for i, round_data in enumerate(self.results['production_by_continent']):
            total = sum(
                sum(continent_data.values()) 
                for continent_data in round_data.values()
            )
            total_production.append(total)
            
            # Mark rounds with climate events
            if self.results['climate_events'][i]:
                climate_event_rounds.append(i)
        
        # Plot production with climate events highlighted
        ax.plot(rounds, total_production, 'b-', linewidth=2, label='Total Production')
        
        # Highlight climate event rounds
        for event_round in climate_event_rounds:
            if event_round < len(total_production):
                ax.axvline(x=event_round, color='red', linestyle='--', alpha=0.7)
                ax.scatter(event_round, total_production[event_round], 
                          color='red', s=100, zorder=5)
        
        ax.set_title('Economic Impact of Climate Events', fontsize=14, fontweight='bold')
        ax.set_xlabel('Round')
        ax.set_ylabel('Total Production')
        ax.legend(['Total Production', 'Climate Events'])
        ax.grid(True, alpha=0.3)
    
    def export_data(self, filename: str = "climate_simulation_data.csv"):
        """Export simulation data to CSV for further analysis."""
        # Flatten agent status data
        all_agent_data = []
        for round_agents in self.results['agent_status']:
            all_agent_data.extend(round_agents)
        
        df = pd.DataFrame(all_agent_data)
        df.to_csv(filename, index=False)
        print(f"Simulation data exported to {filename}")
        
        return df


# Utility functions for easy integration
def create_climate_framework(simulation_parameters: Dict[str, Any]) -> ClimateFramework:
    """Create a new climate framework instance."""
    return ClimateFramework(simulation_parameters)


def add_climate_capabilities(agent_class):
    """
    Decorator to add basic climate stress capabilities to agent classes.
    """
    def init_wrapper(original_init):
        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            # Add climate attributes if not present, using __dict__ to avoid interceptors
            if not hasattr(self, 'climate_vulnerability'):
                self.__dict__['climate_vulnerability'] = 0.1  # Default vulnerability
            if not hasattr(self, 'chronic_stress_accumulated'):
                self.__dict__['chronic_stress_accumulated'] = 1.0
            if not hasattr(self, 'base_output_quantity'):
                current_output = getattr(self, 'current_output_quantity', 1.0)
                self.__dict__['base_output_quantity'] = current_output
        return new_init
    
    def apply_acute_stress(self):
        """Apply acute climate stress (temporary productivity shock)."""
        import random
        
        # Safely get climate vulnerability
        vulnerability = getattr(self, 'climate_vulnerability', 0.1)
        if not isinstance(vulnerability, (int, float)):
            vulnerability = 0.1
            
        stress_factor = 1.0 - (vulnerability * random.uniform(0.2, 0.8))
        
        if hasattr(self, 'current_output_quantity'):
            original_quantity = self.current_output_quantity
            base_quantity = getattr(self, 'base_output_quantity', original_quantity)
            chronic_factor = getattr(self, 'chronic_stress_accumulated', 1.0)
            
            new_quantity = base_quantity * stress_factor * chronic_factor
            
            # Set new quantity safely
            if hasattr(self, '__dict__'):
                self.__dict__['current_output_quantity'] = new_quantity
            else:
                self.current_output_quantity = new_quantity
                
            print(f"  {self.__class__.__name__} {self.id}: Acute stress! Production: {original_quantity:.2f} -> {new_quantity:.2f}")
    
    def apply_chronic_stress(self, stress_factor):
        """Apply chronic climate stress (permanent productivity degradation)."""
        # Update chronic stress accumulation safely
        current_chronic = getattr(self, 'chronic_stress_accumulated', 1.0)
        if not isinstance(current_chronic, (int, float)):
            current_chronic = 1.0
            
        new_chronic = current_chronic * stress_factor
        self.__dict__['chronic_stress_accumulated'] = new_chronic
        
        # Update current output quantity if it exists
        if hasattr(self, 'current_output_quantity'):
            base_quantity = getattr(self, 'base_output_quantity', 1.0)
            new_quantity = base_quantity * new_chronic
            self.__dict__['current_output_quantity'] = new_quantity
    
    # Wrap the original __init__ method
    if hasattr(agent_class, '__init__'):
        agent_class.__init__ = init_wrapper(agent_class.__init__)
    
    # Add climate methods
    agent_class.apply_acute_stress = apply_acute_stress
    agent_class.apply_chronic_stress = apply_chronic_stress
    
    return agent_class 