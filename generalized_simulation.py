"""
Generalized Simulation Runner
Runs simulations with arbitrary heterogeneous agents in complex networks with climate stress.
"""

import sys
import os
import json
import random
import numpy as np
from typing import Dict, Any, Optional
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx

# Add the root directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from abcEconomics import Simulation
from generalized_agent import GeneralizedAgent
from generalized_network_framework import create_generalized_network_framework


class GeneralizedSimulationRunner:
    """
    A flexible simulation runner that can create and run economic simulations
    with arbitrary heterogeneous agents in complex networks.
    """
    
    def __init__(self, config_file: str):
        """
        Initialize the simulation runner with a configuration file.
        
        Args:
            config_file: Path to the JSON configuration file
        """
        self.config_file = config_file
        self.config = self._load_config(config_file)
        self.framework = create_generalized_network_framework(self.config)
        self.simulation = None
        self.agent_groups = {}
        
        # Set random seed
        seed = self.config.get('simulation', {}).get('random_seed', 42)
        if seed:
            random.seed(seed)
            np.random.seed(seed)
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            print(f"Configuration loaded from {config_file}")
            return config
        except Exception as e:
            print(f"Error loading configuration: {e}")
            raise
    
    def setup_simulation(self):
        """Set up the simulation with agents and network"""
        print("Setting up generalized simulation...")
        
        # Load agent types from configuration
        self.framework.load_agent_types_from_config(self.config)
        
        # Create simulation
        simulation_params = self.config.get('simulation', {})
        result_path = simulation_params.get('result_path', 'generalized_network_result')
        self.simulation = Simulation(path=result_path)
        
        # Assign geographical locations
        self.framework.assign_geographical_locations()
        
        # Generate network
        self.framework.generate_network()
        
        # Create agents
        self._create_agents()
        
        # Set up network connections
        self._setup_network_connections()
        
        print("Simulation setup completed")
    
    def _create_agents(self):
        """Create agents based on configuration"""
        agents_config = self.config.get('agents', {})
        
        for agent_type_name, agent_config in agents_config.items():
            count = agent_config['count']
            print(f"Creating {count} {agent_type_name} agents...")
            
            # Remove 'count' key from agent parameters
            base_params = agent_config.copy()
            base_params.pop('count', None)
            agent_parameters = [base_params.copy() for _ in range(count)]
            agent_group = self.simulation.build_agents(
                GeneralizedAgent,
                agent_type_name,
                agent_parameters=agent_parameters
            )
            
            self.agent_groups[agent_type_name] = agent_group
            self.framework.agent_groups = self.agent_groups
        
        print(f"Created {len(self.agent_groups)} agent groups")
    
    def _setup_network_connections(self):
        """Set up network connections between agents"""
        if not self.framework.network:
            return
        
        # Get all agent nodes from the network
        agent_nodes = {}
        for agent_type, agent_group in self.agent_groups.items():
            for i in range(agent_group.num_agents):
                node_id = f"{agent_type}_{i}"
                agent_nodes[node_id] = (agent_type, i)
        
        # Set up connections for each agent
        for node_id, (agent_type, agent_id) in agent_nodes.items():
            agent = self.agent_groups[agent_type][agent_id]
            
            # Get connected agents from network
            connected_nodes = list(self.framework.network.neighbors(node_id))
            connected_agents = []
            
            for connected_node in connected_nodes:
                if connected_node in agent_nodes:
                    connected_agent_type, connected_agent_id = agent_nodes[connected_node]
                    connected_agent = self.agent_groups[connected_agent_type][connected_agent_id]
                    connected_agents.append(connected_agent)
            
            # Set connected agents for this agent
            agent.connected_agents = connected_agents
            
            # Set network connectivity based on degree
            degree = self.framework.network.degree(node_id)
            agent.network_connectivity = min(1.0, degree / 10.0)  # Normalize to 0-1
        
        print(f"Network connections set up for {len(agent_nodes)} agents")
    
    def run_simulation(self, rounds: Optional[int] = None) -> Dict[str, Any]:
        """
        Run the simulation for the specified number of rounds.
        
        Args:
            rounds: Number of rounds to run (uses config default if None)
        
        Returns:
            Dictionary with simulation results
        """
        if not self.simulation:
            raise ValueError("Simulation not set up. Call setup_simulation() first.")
        
        simulation_params = self.config.get('simulation', {})
        total_rounds = rounds or simulation_params.get('rounds', 20)
        
        print(f"Running simulation for {total_rounds} rounds...")
        
        # Define simulation phases
        phases = ['production', 'labor_supply', 'trading', 'consumption']
        
        results = {
            'rounds': [],
            'total_wealth': [],
            'total_production': [],
            'total_consumption': [],
            'total_trades': [],
            'climate_events': []
        }
        
        for round_num in range(total_rounds):
            print(f"\n--- Round {round_num + 1} ---")
            
            # Advance to the next round
            self.simulation.advance_round(round_num)
            
            # Apply climate stress if enabled
            climate_enabled = self.config.get('climate', {}).get('stress_enabled', False)
            if climate_enabled:
                climate_events = self.framework.apply_climate_stress()
                if climate_events:
                    results['climate_events'].append(climate_events)
                    print(f"Climate events: {list(climate_events.keys())}")
            
            # Run simulation phases by calling agent group methods
            for phase in phases:
                for agent_type, agent_group in self.agent_groups.items():
                    phase_method = getattr(agent_group, phase, None)
                    if callable(phase_method):
                        phase_method()
            
            # Record performance for all agents
            self._record_round_performance(round_num)
            
            # Collect round statistics
            round_stats = self._collect_round_statistics()
            results['rounds'].append(round_num + 1)
            results['total_wealth'].append(round_stats['total_wealth'])
            results['total_production'].append(round_stats['total_production'])
            results['total_consumption'].append(round_stats['total_consumption'])
            results['total_trades'].append(round_stats['total_trades'])
            
            print(f"Round {round_num + 1} stats: Wealth={round_stats['total_wealth']:.2f}, "
                  f"Production={round_stats['total_production']:.2f}, "
                  f"Trades={round_stats['total_trades']}")
            
            # Reset climate stress for next round
            if climate_enabled:
                self.framework.reset_climate_stress()
        
        # Finalize the simulation
        self.simulation.finalize()
        
        print("Simulation completed")
        
        # Export results
        self._export_results(results)
        
        return results
    
    def _record_round_performance(self, round_num: int):
        """Record performance metrics for all agents"""
        for agent_type, agent_group in self.agent_groups.items():
            for i in range(agent_group.num_agents):
                agent = agent_group[i]
                agent.round = round_num
                agent.record_performance()
    
    def _collect_round_statistics(self) -> Dict[str, float]:
        """Collect statistics for the current round"""
        total_wealth = 0.0
        total_production = 0.0
        total_consumption = 0.0
        total_trades = 0
        
        for agent_type, agent_group in self.agent_groups.items():
            for i in range(agent_group.num_agents):
                # Always get the real agent object from the scheduler
                agent_name = (agent_group.agent_name_prefix, i)
                scheduler = agent_group._scheduler
                if hasattr(scheduler, 'agents') and agent_name in scheduler.agents:
                    agent = scheduler.agents[agent_name]
                else:
                    agent = agent_group[i]
                total_wealth += agent.calculate_wealth()
                total_production += agent.total_production
                total_consumption += agent.total_consumption
                total_trades += agent.total_trades
        
        return {
            'total_wealth': total_wealth,
            'total_production': total_production,
            'total_consumption': total_consumption,
            'total_trades': total_trades
        }
    
    def _export_results(self, results: Dict[str, Any], output_dir: str = None):
        """Export simulation results to files"""
        if not output_dir:
            output_dir = self.simulation.path if self.simulation else 'results'
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Export network summary
        if self.framework:
            self.framework.export_network_summary(output_dir, "network_summary.csv")
        
        # Export round-by-round results
        results_df = pd.DataFrame({
            'round': results['rounds'],
            'total_wealth': results['total_wealth'],
            'total_production': results['total_production'],
            'total_consumption': results['total_consumption'],
            'total_trades': results['total_trades']
        })
        results_df.to_csv(os.path.join(output_dir, 'simulation_results.csv'), index=False)
        
        # Export agent performance summaries
        agent_summaries = []
        for agent_type, agent_group in self.agent_groups.items():
            for i in range(agent_group.num_agents):
                agent = agent_group[i]
                summary = agent.get_performance_summary()
                agent_summaries.append(summary)
        
        if agent_summaries:
            agent_df = pd.DataFrame(agent_summaries)
            agent_df.to_csv(os.path.join(output_dir, 'agent_performance.csv'), index=False)
        
        # Export climate events
        if results['climate_events']:
            climate_events = []
            for round_num, events in enumerate(results['climate_events']):
                for event_name, event_data in events.items():
                    climate_events.append({
                        'round': round_num + 1,
                        'event_name': event_name,
                        'event_type': event_data.get('type', 'unknown'),
                        'agent_types': ','.join(event_data.get('agent_types', [])),
                        'continents': ','.join(event_data.get('continents', [])),
                        'productivity_stress_factor': event_data.get('productivity_stress_factor'),
                        'overhead_stress_factor': event_data.get('overhead_stress_factor')
                    })
            
            if climate_events:
                climate_df = pd.DataFrame(climate_events)
                climate_df.to_csv(os.path.join(output_dir, 'climate_events.csv'), index=False)
        
        print(f"Results exported to {output_dir}")
    
    def create_visualizations(self, results: Dict[str, Any], output_dir: str = None):
        """Create visualizations of simulation results"""
        if not output_dir:
            output_dir = self.simulation.path if self.simulation else 'results'
        
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # Create time series plots
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            
            # Wealth over time
            axes[0, 0].plot(results['rounds'], results['total_wealth'])
            axes[0, 0].set_title('Total Wealth Over Time')
            axes[0, 0].set_xlabel('Round')
            axes[0, 0].set_ylabel('Total Wealth')
            axes[0, 0].grid(True)
            
            # Production over time
            axes[0, 1].plot(results['rounds'], results['total_production'])
            axes[0, 1].set_title('Total Production Over Time')
            axes[0, 1].set_xlabel('Round')
            axes[0, 1].set_ylabel('Total Production')
            axes[0, 1].grid(True)
            
            # Consumption over time
            axes[1, 0].plot(results['rounds'], results['total_consumption'])
            axes[1, 0].set_title('Total Consumption Over Time')
            axes[1, 0].set_xlabel('Round')
            axes[1, 0].set_ylabel('Total Consumption')
            axes[1, 0].grid(True)
            
            # Trades over time
            axes[1, 1].plot(results['rounds'], results['total_trades'])
            axes[1, 1].set_title('Total Trades Over Time')
            axes[1, 1].set_xlabel('Round')
            axes[1, 1].set_ylabel('Total Trades')
            axes[1, 1].grid(True)
            
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'simulation_results.png'), dpi=300, bbox_inches='tight')
            plt.close()
            
            # Create network visualization if network exists
            if self.framework.network:
                plt.figure(figsize=(12, 8))
                pos = nx.spring_layout(self.framework.network, seed=42)
                
                # Color nodes by agent type
                node_colors = []
                for node in self.framework.network.nodes():
                    agent_type = node.split('_')[0]
                    if agent_type == 'producer':
                        node_colors.append('red')
                    elif agent_type == 'consumer':
                        node_colors.append('blue')
                    elif agent_type == 'intermediary':
                        node_colors.append('green')
                    else:
                        node_colors.append('gray')
                
                nx.draw(self.framework.network, pos, 
                       node_color=node_colors,
                       node_size=100,
                       with_labels=True,
                       font_size=8,
                       font_weight='bold')
                
                plt.title('Agent Network Structure')
                plt.savefig(os.path.join(output_dir, 'network_structure.png'), dpi=300, bbox_inches='tight')
                plt.close()
            
            print(f"Visualizations saved to {output_dir}")
            
        except Exception as e:
            print(f"Warning: Could not create visualizations: {e}")
            print("This might be due to missing matplotlib or networkx dependencies.")
    
    def run_complete_simulation(self, rounds: Optional[int] = None, 
                              create_visualizations: bool = True) -> Dict[str, Any]:
        """
        Run a complete simulation with setup, execution, and result export.
        
        Args:
            rounds: Number of rounds to run
            create_visualizations: Whether to create visualizations
        
        Returns:
            Simulation results
        """
        print("Starting complete simulation...")
        
        # Setup
        self.setup_simulation()
        
        # Run
        results = self.run_simulation(rounds)
        
        # Export results
        self._export_results(results)
        
        # Create visualizations
        if create_visualizations:
            self.create_visualizations(results)
        
        print("Complete simulation finished")
        return results


def main():
    """Main function to run a generalized simulation"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run a generalized economic network simulation')
    parser.add_argument('config_file', help='Path to the configuration JSON file')
    parser.add_argument('--rounds', type=int, help='Number of simulation rounds (overrides config)')
    parser.add_argument('--no-viz', action='store_true', help='Skip visualization creation')
    
    args = parser.parse_args()
    
    # Create and run simulation
    runner = GeneralizedSimulationRunner(args.config_file)
    results = runner.run_complete_simulation(
        rounds=args.rounds,
        create_visualizations=not args.no_viz
    )
    
    print("Simulation completed successfully!")


if __name__ == "__main__":
    main() 