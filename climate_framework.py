"""
Climate Economics Framework

A simplified, reusable framework for adding geographical distribution and climate stress
to agent-based economic models using abcEconomics' built-in functionality.
"""

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import seaborn as sns
import random
import os
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
    Simplified framework for climate economics modeling with geographical distribution.
    """
    
    def __init__(self, simulation_parameters: Dict[str, Any]):
        self.params = simulation_parameters
        self.climate_events_history = []
        self.geographical_assignments = {}
    
    def assign_geographical_locations(self, agent_groups: Dict[str, List], 
                                    distribution_rules: Optional[Dict] = None):
        """
        Assign agents to continents and store the assignment plan.
        """
        if distribution_rules is None:
            distribution_rules = self._get_default_distribution_rules()
        
        continents = list(CONTINENTS.keys())
        
        for agent_type, agent_group in agent_groups.items():
            if agent_type in distribution_rules:
                target_continents = distribution_rules[agent_type]
            else:
                target_continents = continents
            
            num_agents = agent_group.num_agents
            print(f"  Assigning {num_agents} {agent_type.replace('_', ' ')}s to continents...")
            
            # Store geographical assignments for later use
            self.geographical_assignments[agent_type] = {}
            
            for i in range(num_agents):
                continent = target_continents[i % len(target_continents)]
                base_vulnerability = 0.1
                new_vulnerability = base_vulnerability * CONTINENTS[continent]['climate_risk']
                
                self.geographical_assignments[agent_type][i] = {
                    'continent': continent,
                    'vulnerability': new_vulnerability
                }
                
                print(f"    {agent_type.replace('_', ' ').title()} {i} assigned to {continent} (vulnerability: {new_vulnerability:.2f})")
            
            print(f"    Geographical assignment completed for {agent_type}")
        
        print("Geographical assignment completed! Use panel_log() for data collection.")
    
    def apply_geographical_climate_stress(self, agent_groups: Dict[str, List]) -> Dict[str, str]:
        """
        Apply climate stress events by continent.
        """
        climate_events = {}
        
        # Determine which continents experience acute stress
        for continent, info in CONTINENTS.items():
            continent_risk = info['climate_risk']
            adjusted_probability = self.params['acute_stress_probability'] * continent_risk
            
            if random.random() < adjusted_probability:
                climate_events[continent] = 'acute_stress'
                print(f"[ACUTE CLIMATE STRESS in {continent}]", end=" ")
        
        # Store climate events
        self.climate_events_history.append(climate_events)
        
        print(f"Climate events: {climate_events}")
        return climate_events
    
    def collect_panel_data(self, agent_groups: Dict[str, List], goods_to_track: Dict[str, List]):
        """
        Use abcEconomics' built-in panel_log to collect data.
        
        Args:
            agent_groups: Dictionary mapping agent type names to abcEconomics agent groups
            goods_to_track: Dictionary mapping agent types to lists of goods to track
        """
        print("  Collecting data using abcEconomics panel_log...")
        
        for agent_type, agent_group in agent_groups.items():
            if agent_type in goods_to_track:
                goods = goods_to_track[agent_type]
                try:
                    agent_group.panel_log(goods=goods)
                    print(f"    Panel data collected for {agent_type}: {goods}")
                except Exception as e:
                    print(f"    Warning: Could not collect panel data for {agent_type}: {e}")
            else:
                # Default to money if no specific goods specified
                try:
                    agent_group.panel_log(goods=['money'])
                    print(f"    Panel data collected for {agent_type}: ['money']")
                except Exception as e:
                    print(f"    Warning: Could not collect panel data for {agent_type}: {e}")
    
    def create_simplified_visualizations(self, agent_groups: Dict[str, List], 
                                       simulation_path: str = None,
                                       model_name: str = "Climate Economic Model"):
        """
        Create simplified visualizations focusing on geographical and climate aspects.
        """
        # Set up the visualization style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        # Create figure with subplots
        fig = plt.figure(figsize=(15, 10))
        fig.suptitle(f'{model_name} - Climate Framework Analysis', fontsize=16, fontweight='bold')
        
        # 1. Geographical Distribution
        ax1 = plt.subplot(2, 2, 1)
        self._create_geographical_distribution_plot(ax1, agent_groups)
        
        # 2. Climate Events Timeline
        ax2 = plt.subplot(2, 2, 2)
        self._create_climate_events_timeline(ax2)
        
        # 3. Continental Risk Analysis
        ax3 = plt.subplot(2, 2, 3)
        self._create_continental_risk_analysis(ax3)
        
        # 4. Agent Distribution by Continent
        ax4 = plt.subplot(2, 2, 4)
        self._create_agent_distribution_chart(ax4)
        
        plt.tight_layout()
        
        # Save visualization
        save_path = f'{model_name.lower().replace(" ", "_")}_climate_analysis.png'
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"Climate visualizations saved as '{save_path}'")
        
        # Try to load and display abcEconomics data if available
        if simulation_path:
            self._try_load_abceconomics_data(simulation_path)
    
    def _create_geographical_distribution_plot(self, ax, agent_groups):
        """Create a plot showing geographical distribution of agents."""
        continent_counts = {continent: 0 for continent in CONTINENTS.keys()}
        
        for agent_type, assignments in self.geographical_assignments.items():
            for agent_info in assignments.values():
                continent_counts[agent_info['continent']] += 1
        
        continents = list(continent_counts.keys())
        counts = list(continent_counts.values())
        colors = [CONTINENTS[cont]['color'] for cont in continents]
        
        bars = ax.bar(continents, counts, color=colors, alpha=0.7)
        ax.set_title('Agent Distribution by Continent', fontweight='bold')
        ax.set_ylabel('Number of Agents')
        ax.tick_params(axis='x', rotation=45)
        
        # Add value labels on bars
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                   f'{count}', ha='center', va='bottom')
    
    def _create_climate_events_timeline(self, ax):
        """Create timeline of climate events."""
        if not self.climate_events_history:
            ax.text(0.5, 0.5, 'No climate events recorded', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Climate Events Timeline', fontweight='bold')
            return
        
        rounds = list(range(len(self.climate_events_history)))
        continents = list(CONTINENTS.keys())
        
        # Create a heatmap matrix
        climate_matrix = np.zeros((len(continents), len(rounds)))
        
        for round_idx, climate_events in enumerate(self.climate_events_history):
            for continent_idx, continent in enumerate(continents):
                if continent in climate_events:
                    climate_matrix[continent_idx, round_idx] = 1
        
        im = ax.imshow(climate_matrix, cmap='Reds', aspect='auto', interpolation='nearest')
        
        ax.set_yticks(range(len(continents)))
        ax.set_yticklabels(continents)
        ax.set_xticks(range(len(rounds)))
        ax.set_xticklabels(rounds)
        ax.set_title('Climate Events by Round', fontweight='bold')
        ax.set_xlabel('Round')
        ax.set_ylabel('Continent')
        
        # Add colorbar
        plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label='Climate Event')
    
    def _create_continental_risk_analysis(self, ax):
        """Create bar chart of continental climate risks."""
        continents = list(CONTINENTS.keys())
        risks = [CONTINENTS[cont]['climate_risk'] for cont in continents]
        colors = [CONTINENTS[cont]['color'] for cont in continents]
        
        bars = ax.bar(continents, risks, color=colors, alpha=0.7)
        ax.set_title('Climate Risk by Continent', fontweight='bold')
        ax.set_ylabel('Risk Multiplier')
        ax.tick_params(axis='x', rotation=45)
        ax.axhline(y=1.0, color='black', linestyle='--', alpha=0.5, label='Baseline')
        
        # Add value labels on bars
        for bar, risk in zip(bars, risks):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                   f'{risk:.1f}', ha='center', va='bottom')
        
        ax.legend()
    
    def _create_agent_distribution_chart(self, ax):
        """Create pie chart of agent type distribution."""
        agent_type_counts = {}
        for agent_type, assignments in self.geographical_assignments.items():
            agent_type_counts[agent_type.replace('_', ' ').title()] = len(assignments)
        
        if agent_type_counts:
            labels = list(agent_type_counts.keys())
            sizes = list(agent_type_counts.values())
            
            ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            ax.set_title('Agent Type Distribution', fontweight='bold')
        else:
            ax.text(0.5, 0.5, 'No agent data available', 
                   ha='center', va='center', transform=ax.transAxes)
    
    def _try_load_abceconomics_data(self, simulation_path):
        """Try to load and display data from abcEconomics output."""
        try:
            print(f"\nLooking for abcEconomics data in: {simulation_path}")
            
            # Look for CSV files in the simulation output directory
            if os.path.exists(simulation_path):
                csv_files = [f for f in os.listdir(simulation_path) if f.endswith('.csv')]
                if csv_files:
                    print(f"Found abcEconomics data files: {csv_files}")
                    for csv_file in csv_files[:3]:  # Show first 3 files
                        file_path = os.path.join(simulation_path, csv_file)
                        try:
                            df = pd.read_csv(file_path)
                            print(f"\n{csv_file} preview:")
                            print(df.head())
                        except Exception as e:
                            print(f"Could not read {csv_file}: {e}")
                else:
                    print("No CSV files found in simulation output")
            else:
                print("Simulation path does not exist")
                
        except Exception as e:
            print(f"Error loading abcEconomics data: {e}")
    
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
    
    def export_climate_summary(self, filename: str = "climate_summary.csv"):
        """Export a summary of climate events and geographical assignments."""
        # Create summary data
        summary_data = []
        
        # Add geographical assignments
        for agent_type, assignments in self.geographical_assignments.items():
            for agent_id, info in assignments.items():
                summary_data.append({
                    'agent_type': agent_type,
                    'agent_id': agent_id,
                    'continent': info['continent'],
                    'vulnerability': info['vulnerability'],
                    'data_type': 'geographical_assignment'
                })
        
        # Add climate events
        for round_num, events in enumerate(self.climate_events_history):
            for continent, event_type in events.items():
                summary_data.append({
                    'agent_type': 'climate_event',
                    'agent_id': round_num,
                    'continent': continent,
                    'vulnerability': CONTINENTS[continent]['climate_risk'],
                    'data_type': event_type
                })
        
        if summary_data:
            df = pd.DataFrame(summary_data)
            df.to_csv(filename, index=False)
            print(f"Climate summary exported to {filename}")
            return df
        else:
            print("No climate data to export")
            return None


# Utility functions for easy integration
def create_climate_framework(simulation_parameters: Dict[str, Any]) -> ClimateFramework:
    """Create a new climate framework instance."""
    return ClimateFramework(simulation_parameters)


def add_climate_capabilities(agent_class):
    """
    Simplified decorator to add basic climate stress capabilities to agent classes.
    """
    def init_wrapper(original_init):
        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            # Add climate attributes if not present
            if not hasattr(self, 'climate_vulnerability'):
                self.climate_vulnerability = 0.1  # Default vulnerability
            if not hasattr(self, 'base_output_quantity'):
                current_output = getattr(self, 'current_output_quantity', 1.0)
                self.base_output_quantity = current_output
        return new_init
    
    def apply_acute_stress(self):
        """Apply acute climate stress (temporary productivity shock)."""
        import random
        
        vulnerability = getattr(self, 'climate_vulnerability', 0.1)
        stress_factor = 1.0 - (vulnerability * random.uniform(0.2, 0.8))
        
        if hasattr(self, 'current_output_quantity'):
            base_quantity = getattr(self, 'base_output_quantity', self.current_output_quantity)
            new_quantity = base_quantity * stress_factor
            self.current_output_quantity = new_quantity
            print(f"  {self.__class__.__name__} {self.id}: Acute stress! Production reduced to {new_quantity:.2f}")
    
    # Wrap the original __init__ method
    if hasattr(agent_class, '__init__'):
        agent_class.__init__ = init_wrapper(agent_class.__init__)
    
    # Add climate methods
    agent_class.apply_acute_stress = apply_acute_stress
    
    return agent_class 