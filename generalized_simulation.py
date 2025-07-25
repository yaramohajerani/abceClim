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

try:
    import imageio.v2 as imageio  # imageio <= v3 style import
except ImportError:  # pragma: no cover – optional dependency
    imageio = None


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
        # Debug flag (from config.simulation.debug)
        self.debug = self.config.get('simulation', {}).get('debug', False)
        
        # Optional network animation flag (from config.visualization.animate_network)
        self.animate_network: bool = self.config.get('visualization', {}).get('animate_network', False)
        # Internal helpers for animation
        self._frame_paths = []  # type: list[str]
        self._network_pos = None  # cached layout for consistent frames
        
        # Set random seed
        seed = self.config.get('simulation', {}).get('random_seed', 42)
        if seed:
            random.seed(seed)
            np.random.seed(seed)
        
        # Ensure real_agents exists even before setup to avoid attribute errors
        self.real_agents = []
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration, supporting optional inheritance via an `extends` field."""

        def _read(path: str) -> Dict[str, Any]:
            with open(path, 'r') as fh:
                return json.load(fh)

        def _deep_merge(base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
            """Recursively merge two dicts (updates overwrite base)."""
            result = dict(base)
            for k, v in updates.items():
                if k in result and isinstance(result[k], dict) and isinstance(v, dict):
                    result[k] = _deep_merge(result[k], v)
                else:
                    result[k] = v
            return result

        try:
            # First read the primary config
            config_dir = os.path.dirname(os.path.abspath(config_file))
            config = _read(config_file)

            # Handle inheritance chain (single string path)
            if 'extends' in config:
                base_rel_path = config.pop('extends')
                # Allow relative paths relative to current config file dir
                base_path = base_rel_path if os.path.isabs(base_rel_path) else os.path.join(config_dir, base_rel_path)

                base_config = self._load_config(base_path)  # recurse
                config = _deep_merge(base_config, config)

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
        print(f"DEBUG: Network generated with {self.framework.network.number_of_nodes()} nodes and {self.framework.network.number_of_edges()} edges")
        
        # Create agents
        self._create_agents()
        
        # Set up network connections
        self._dprint("DEBUG: About to call _setup_network_connections...")
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
        self._dprint("DEBUG: Setting up network connections...")
        
        if not self.framework.network:
            self._dprint("DEBUG: No network found, skipping connection setup")
            return
        
        self._dprint(f"DEBUG: Network has {self.framework.network.number_of_nodes()} nodes and {self.framework.network.number_of_edges()} edges")
        
        # Get all agent nodes from the network using the real agent objects in the scheduler
        agent_nodes = {}
        for agent_type, agent_group in self.agent_groups.items():
            for i in range(agent_group.num_agents):
                node_label = f"{agent_type}_{i}"  # Match the network node labels
                # Get the real agent object from the scheduler
                agent_name = (agent_group.agent_name_prefix, i)
                if agent_name in self.simulation.scheduler.agents:
                    agent = self.simulation.scheduler.agents[agent_name]
                    agent_nodes[node_label] = agent
                else:
                    self._dprint(f"DEBUG: Agent {agent_name} not found in scheduler")
        
        self._dprint(f"DEBUG: Found {len(agent_nodes)} agents to assign connections to")
        
        # Assign connections to agents
        for node_label, agent in agent_nodes.items():
            if node_label in self.framework.network:
                # Treat network as undirected when determining connections
                neighbors = set(self.framework.network.successors(node_label))
                neighbors.update(self.framework.network.predecessors(node_label))
                neighbors = list(neighbors)
                connected_agents = [agent_nodes[n] for n in neighbors if n in agent_nodes]
                agent.connected_agents = connected_agents
                agent.connections = connected_agents
                self._dprint(f"DEBUG: SETUP {node_label} connections: {len(connected_agents)}")
        
        self._dprint(f"Network connections set up for {len(agent_nodes)} agents")
        
        # Cache real agents list for faster access in run loop
        self.real_agents = list(self.simulation.scheduler.agents.values())
        
        # Provide each agent with a reference to the complete list so they
        # can pick overhead-service providers even if they lack direct
        # connections.
        for ag in self.real_agents:
            ag.all_agents = self.real_agents
    
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
        
        # Define simulation phases (including new overhead payment stage)
        phases = ['labor_supply', 'labor_contracting', 'overhead_payment', 'production', 'trading', 'consumption']
        
        results = {
            'rounds': [],
            'total_wealth': [],
            'total_production': [],
            'total_consumption': [],
            'total_trades': [],
            'total_overhead': [],
            'climate_events': [],
            'shock_rounds': [],
            # per-type time series
            'per_type': {}
        }
        # initialise per_type structure
        for t in self.agent_groups.keys():
            results['per_type'][t] = {
                'production': [],
                'wealth': [],
                'consumption': [],
                'trades': [],
                'overhead': []
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
                    results['shock_rounds'].append(round_num + 1)
                    print(f"Climate events: {list(climate_events.keys())}")
            
            self._dprint("DEBUG: Available agent groups:", list(self.agent_groups.keys()))
            
            # Run simulation phases using abcEconomics standard pattern
            for phase in phases:
                self._dprint(f"DEBUG: Running phase: {phase}")
                
                for agent in list(self.real_agents):
                    # Skip agents flagged as bankrupt before handling removal
                    if getattr(agent, "bankrupt", False):
                        continue

                    phase_method = getattr(agent, phase, None)
                    if callable(phase_method):
                        phase_method()
                    else:
                        self._dprint(f"DEBUG: {phase} method not found on agent {agent.name}")

                # After executing the overhead payment phase for all agents,
                # immediately process bankruptcies (removal + replacement)
                if phase == 'overhead_payment':
                    self._handle_bankruptcies()
            
            # Collect statistics directly from real_agents
            round_stats, per_type_stats = self._collect_round_statistics_inline()
            results['rounds'].append(round_num + 1)
            results['total_wealth'].append(round_stats['wealth'])
            results['total_production'].append(round_stats['production'])
            results['total_consumption'].append(round_stats['consumption'])
            results['total_trades'].append(round_stats['trades'])
            results['total_overhead'].append(round_stats['overhead'])
            
            # append per type
            for typ, stats in per_type_stats.items():
                for key, val in stats.items():
                    results['per_type'][typ][key].append(val)
            
            print(f"Round {round_num + 1} stats: Wealth={round_stats['wealth']:.2f}, "
                  f"Production={round_stats['production']:.2f}, "
                  f"Trades={round_stats['trades']}")
            
            # Optionally save a network frame BEFORE resetting acute stress
            if self.animate_network:
                self._save_network_frame(round_num, results_dir=self.simulation.path)

            # Reset climate stress for next round (clears acute effects after snapshot)
            if climate_enabled:
                self.framework.reset_climate_stress()
        
        # Finalize the simulation
        self.simulation.finalize()
        
        # Create GIF if animation frames were requested and at least two frames exist
        if self.animate_network:
            self._create_network_gif(results_dir=self.simulation.path)
        
        print("Simulation completed")
        
        # Export results
        self._export_results(results)
        
        return results
    
    def _collect_round_statistics_inline(self):
        """Collect totals and per-type stats from self.real_agents."""
        total = dict(wealth=0.0, production=0.0, consumption=0.0, trades=0, overhead=0.0)
        per_type = {}
        for agent in self.real_agents:
            typ = agent.group
            if typ not in per_type:
                per_type[typ] = dict(wealth=0.0, production=0.0, consumption=0.0, trades=0, overhead=0.0)
            w = agent.calculate_wealth()

            # --- per-round deltas instead of cumulative values ---
            prev_prod = getattr(agent, '_prev_total_production', 0.0)
            prev_cons = getattr(agent, '_prev_total_consumption', 0.0)
            prev_trades = getattr(agent, '_prev_total_trades', 0)

            p = agent.total_production - prev_prod
            c = agent.total_consumption - prev_cons
            tr = agent.total_trades - prev_trades

            # store current totals for next round
            agent._prev_total_production = agent.total_production
            agent._prev_total_consumption = agent.total_consumption
            agent._prev_total_trades = agent.total_trades

            over = getattr(agent, 'current_overhead', getattr(agent, 'base_overhead', 0.0))
            # totals
            total['wealth'] += w
            total['production'] += p
            total['consumption'] += c
            total['trades'] += tr
            total['overhead'] += over
            # per type
            per_type[typ]['wealth'] += w
            per_type[typ]['production'] += p
            per_type[typ]['consumption'] += c
            per_type[typ]['trades'] += tr
            per_type[typ]['overhead'] += over

        return total, per_type
    
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
            'total_trades': results['total_trades'],
            'total_overhead': results['total_overhead']
        })
        results_df.to_csv(os.path.join(output_dir, 'simulation_results.csv'), index=False)
        
        # Export agent performance summaries
        agent_summaries = []
        for agent in self.real_agents:
            agent_summaries.append(agent.get_performance_summary())
        
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
        
        if results['per_type']:
            # Flatten per-type time series into long-form DataFrame
            per_type_rows = []
            rounds = results['rounds']
            for agent_type, metrics in results['per_type'].items():
                for idx, rnd in enumerate(rounds):
                    per_type_rows.append({
                        'round': rnd,
                        'agent_type': agent_type,
                        'production': metrics['production'][idx],
                        'wealth': metrics['wealth'][idx],
                        'consumption': metrics['consumption'][idx],
                        'trades': metrics['trades'][idx],
                        'overhead': metrics['overhead'][idx]
                    })
            per_type_df = pd.DataFrame(per_type_rows)
            per_type_df.to_csv(os.path.join(output_dir, 'per_type_timeseries.csv'), index=False)
        
        # Export shock rounds as separate CSV for convenience
        if results.get('shock_rounds'):
            shock_df = pd.DataFrame({'round': results['shock_rounds']})
            shock_df.to_csv(os.path.join(output_dir, 'shock_rounds.csv'), index=False)
        
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
            # Mark shocks
            for sr in results.get('shock_rounds', []):
                axes[0, 0].axvline(sr, color='red', linestyle='--', alpha=0.4)
            axes[0, 0].set_title('Total Wealth Over Time')
            axes[0, 0].set_xlabel('Round')
            axes[0, 0].set_ylabel('Total Wealth')
            axes[0, 0].grid(True)
            
            # Production over time
            axes[0, 1].plot(results['rounds'], results['total_production'])
            # Mark shocks
            for sr in results.get('shock_rounds', []):
                axes[0, 1].axvline(sr, color='red', linestyle='--', alpha=0.4)
            axes[0, 1].set_title('Total Production Over Time')
            axes[0, 1].set_xlabel('Round')
            axes[0, 1].set_ylabel('Total Production')
            axes[0, 1].grid(True)
            
            # Consumption over time
            axes[1, 0].plot(results['rounds'], results['total_consumption'])
            # Mark shocks
            for sr in results.get('shock_rounds', []):
                axes[1, 0].axvline(sr, color='red', linestyle='--', alpha=0.4)
            axes[1, 0].set_title('Total Consumption Over Time')
            axes[1, 0].set_xlabel('Round')
            axes[1, 0].set_ylabel('Total Consumption')
            axes[1, 0].grid(True)
            
            # Trades over time
            axes[1, 1].plot(results['rounds'], results['total_trades'])
            # Mark shocks
            for sr in results.get('shock_rounds', []):
                axes[1, 1].axvline(sr, color='red', linestyle='--', alpha=0.4)
            axes[1, 1].set_title('Total Trades Over Time')
            axes[1, 1].set_xlabel('Round')
            axes[1, 1].set_ylabel('Total Trades')
            axes[1, 1].grid(True)
            
            # New figure for overhead
            fig_over, ax_over = plt.subplots(figsize=(7, 4))
            ax_over.plot(results['rounds'], results['total_overhead'])
            for sr in results.get('shock_rounds', []):
                ax_over.axvline(sr, color='red', linestyle='--', alpha=0.4)
            ax_over.set_title('Total Overhead Over Time')
            ax_over.set_xlabel('Round')
            ax_over.set_ylabel('Total Overhead')
            ax_over.grid(True)
            fig_over.tight_layout()
            fig_over.savefig(os.path.join(output_dir, 'total_overhead.png'), dpi=300, bbox_inches='tight')
            plt.close(fig_over)
            
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'simulation_results.png'), dpi=300, bbox_inches='tight')
            plt.close()
            
            # Combined 2x2 per-type metrics figure
            fig2, axes2 = plt.subplots(2, 2, figsize=(12, 8))

            # Helper to plot lines
            def _plot_metric(ax, metric_key, title, ylabel):
                for typ, ts in results['per_type'].items():
                    ax.plot(results['rounds'], ts[metric_key], label=typ)
                ax.set_title(title)
                ax.set_xlabel('Round')
                ax.set_ylabel(ylabel)
                ax.grid(True)

            _plot_metric(axes2[0, 0], 'production', 'Production by Type', 'Units')
            _plot_metric(axes2[0, 1], 'wealth', 'Wealth by Type', 'Wealth')
            _plot_metric(axes2[1, 0], 'consumption', 'Consumption by Type', 'Units')
            _plot_metric(axes2[1, 1], 'trades', 'Trades by Type', '# Trades')

            # Add shock lines to all subplots
            for ax in axes2.flatten():
                for sr in results.get('shock_rounds', []):
                    ax.axvline(sr, color='red', linestyle='--', alpha=0.4)

            # Consolidated legend
            handles, labels = axes2[0, 0].get_legend_handles_labels()
            fig2.legend(handles, labels, loc='lower center', ncol=len(labels))
            plt.tight_layout(rect=[0, 0.05, 1, 1])
            fig2.savefig(os.path.join(output_dir, 'metrics_by_type.png'), dpi=300, bbox_inches='tight')
            plt.close(fig2)
            
            # ------------------------------------------------------
            # Improved network visualization
            # ------------------------------------------------------
            if self.framework.network:
                plt.figure(figsize=(12, 8))

                # Use deterministic layout for reproducibility
                pos = nx.spring_layout(self.framework.network, seed=42, k=0.35)

                # Prepare node colors & legend handles
                type_color = {
                    'producer': 'red',
                    'intermediary': 'green',
                    'consumer': 'blue'
                }
                node_colors = [type_color.get(node.split('_')[0], 'gray') for node in self.framework.network.nodes]

                # Draw nodes (larger size for better visibility)
                nx.draw_networkx_nodes(
                    self.framework.network,
                    pos,
                    node_color=node_colors,
                    node_size=300,
                    alpha=0.9,
                    linewidths=0.5,
                    edgecolors='black')

                # Draw edges with transparency & width scaled by weight
                weights = [data.get('weight', 1.0) for _, _, data in self.framework.network.edges(data=True)]
                # Normalize edge widths between 0.5 and 3.0 for readability
                if weights:
                    w_min, w_max = min(weights), max(weights)
                    edge_widths = [0.5 + 2.5 * ((w - w_min) / (w_max - w_min + 1e-9)) for w in weights]
                else:
                    edge_widths = 1.0

                nx.draw_networkx_edges(
                    self.framework.network,
                    pos,
                    width=edge_widths,
                    arrows=False,
                    alpha=0.25,
                    edge_color='gray')

                # Draw node labels (agent id only) with small font to reduce clutter
                simple_labels = {n: n.split('_')[1] for n in self.framework.network.nodes}
                nx.draw_networkx_labels(
                    self.framework.network,
                    pos,
                    labels=simple_labels,
                    font_size=6,
                    font_color='black')

                # Create a custom legend
                from matplotlib.lines import Line2D
                legend_elements = [Line2D([0], [0], marker='o', color='w', label=typ.capitalize(),
                                            markerfacecolor=col, markersize=10, markeredgecolor='black')
                                    for typ, col in type_color.items()]
                plt.legend(handles=legend_elements, title='Agent Type', loc='best')

                plt.title('Agent Network Structure (Round 0)')
                plt.axis('off')
                plt.tight_layout()
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

    # --------------------------------------------------------------
    # Utility: conditional debug print
    # --------------------------------------------------------------

    def _dprint(self, *args, **kwargs):
        """Print only when self.debug flag is True."""
        if self.debug:
            print(*args, **kwargs)

    # ------------------------------------------------------------------
    # Network animation helpers
    # ------------------------------------------------------------------

    def _save_network_frame(self, round_num: int, results_dir: str):
        """Save a PNG snapshot of the current network state for the given round."""
        if imageio is None:
            # imageio not available – silently skip to avoid hard dependency
            self._dprint("imageio not installed; skipping network frame saving")
            return

        # Lazily compute deterministic layout once for all frames
        if self._network_pos is None:
            self._network_pos = nx.spring_layout(self.framework.network, seed=42)

        # --------------------------------------------------
        # Gather per-agent information: wealth & climate status
        # --------------------------------------------------
        wealths = {}
        acute_flags = {}
        chronic_flags = {}

        # Quick mapping to climate data for chronic status look-up
        climate_data_map = self.framework.agent_climate_data

        for agent in self.real_agents:
            key = f"{agent.group}_{agent.agent_id}"
            w = max(0.0, agent.calculate_wealth())  # avoid negatives for size scaling
            wealths[key] = w

            # Determine climate status (acute and/or chronic independently)
            acute_flags[key] = getattr(agent, "climate_stressed", False)

            cdata = climate_data_map.get((agent.group, agent.agent_id), None)
            chronic = False
            if cdata:
                chronic_prod = cdata.get("chronic_productivity_stress_accumulated", 1.0)
                chronic_over = cdata.get("chronic_overhead_stress_accumulated", 1.0)
                chronic = (chronic_prod > 1.0) or (chronic_over > 1.0)
            chronic_flags[key] = chronic
        
        # Scaling for node sizes
        if wealths:
            max_wealth = max(wealths.values()) or 1.0
        else:
            max_wealth = 1.0
        min_size, max_size = 100, 1500  # visual bounds

        node_sizes = []
        node_colors = []

        # Base colours for agent types (fallback)
        type_color_fallback = {
            'producer': '#d62728',
            'intermediary': '#2ca02c',
            'consumer': '#1f77b4'
        }

        for node in self.framework.network.nodes:
            # Size scaling
            size = min_size
            if node in wealths and max_wealth > 0:
                size = min_size + (wealths[node] / max_wealth) * (max_size - min_size)
            node_sizes.append(size)

            # Colour determination
            agent_type = node.split("_")[0]
            node_colors.append(type_color_fallback.get(agent_type, "gray"))

        # --------------------------------------------------
        # Plot
        # --------------------------------------------------
        plt.figure(figsize=(10, 7))

        nx.draw(
            self.framework.network,
            pos=self._network_pos,
            node_size=node_sizes,
            node_color=node_colors,
            edge_color="k",
            alpha=0.8,
            width=0.4,
        )
        plt.title(f"Network – Round {round_num + 1}")
        plt.axis("off")

        # --------------------------------------------------
        # Overlay outlines for stress indicators
        # --------------------------------------------------
        acute_nodes = [n for n in self.framework.network.nodes if acute_flags.get(n, False)]
        chronic_nodes = [n for n in self.framework.network.nodes if chronic_flags.get(n, False)]

        # Map node -> size for convenience
        size_map = {n: s for n, s in zip(self.framework.network.nodes, node_sizes)}

        # Chronic outline (orange, solid, thinner)
        if chronic_nodes:
            sizes_chronic = [size_map[n] * 1.15 for n in chronic_nodes]  # slightly larger to be visible
            coll_chronic = nx.draw_networkx_nodes(
                self.framework.network,
                pos=self._network_pos,
                nodelist=chronic_nodes,
                node_size=sizes_chronic,
                node_color='none',
                edgecolors='#FFA500',
                linewidths=2.0,
            )
            # ensure solid line style
            coll_chronic.set_linestyle('solid')

        # Acute outline (red, dashed, thicker)
        if acute_nodes:
            sizes_acute = [size_map[n] * 1.25 for n in acute_nodes]  # slightly larger than chronic
            coll_acute = nx.draw_networkx_nodes(
                self.framework.network,
                pos=self._network_pos,
                nodelist=acute_nodes,
                node_size=sizes_acute,
                node_color='none',
                edgecolors='#FF0000',
                linewidths=3.0,
            )
            try:
                coll_acute.set_linestyle('dashed')
            except Exception:
                pass  # some matplotlib versions may not support dashed nodes

        # Custom legend reflecting outlines
        from matplotlib.lines import Line2D
        legend_elems = [
            Line2D([0], [0], marker='o', color='w', label='Producer', markerfacecolor=type_color_fallback['producer'], markersize=10, markeredgecolor='black'),
            Line2D([0], [0], marker='o', color='w', label='Intermediary', markerfacecolor=type_color_fallback['intermediary'], markersize=10, markeredgecolor='black'),
            Line2D([0], [0], marker='o', color='w', label='Consumer', markerfacecolor=type_color_fallback['consumer'], markersize=10, markeredgecolor='black'),
            Line2D([0], [0], marker='o', color='w', label='Chronic stress', markerfacecolor='none', markeredgecolor='#FFA500', markersize=10, markeredgewidth=2),
            Line2D([0], [0], marker='o', color='w', label='Acute shock', markerfacecolor='none', markeredgecolor='#FF0000', markersize=10, markeredgewidth=3, linestyle='--'),
        ]
        plt.legend(handles=legend_elems, loc='lower left', framealpha=0.9)

        frames_dir = os.path.join(results_dir, "network_frames")
        os.makedirs(frames_dir, exist_ok=True)
        frame_path = os.path.join(frames_dir, f"network_round_{round_num + 1:03d}.png")
        plt.savefig(frame_path, dpi=150, bbox_inches="tight")
        plt.close()

        self._frame_paths.append(frame_path)

    def _create_network_gif(self, results_dir: str):
        """Create an animated GIF from saved network frames."""
        if imageio is None or len(self._frame_paths) < 2:
            # Either imageio not installed or not enough frames – skip GIF creation
            self._dprint("Skipping GIF creation – imageio not installed or insufficient frames")
            return

        gif_path = os.path.join(results_dir, "network_evolution.gif")
        try:
            # imageio expects iterable of file paths ordered as desired
            with imageio.get_writer(gif_path, mode="I", duration=0.7) as writer:
                for frame_fp in self._frame_paths:
                    image = imageio.imread(frame_fp)
                    writer.append_data(image)
            print(f"Saved network evolution GIF to {gif_path}")
        except Exception as exc:
            self._dprint("Failed to create network GIF:", exc)

    def _handle_bankruptcies(self):
        """Remove bankrupt agents and spawn replacements of the same type."""
        bankrupt_agents = [a for a in self.real_agents if getattr(a, "bankrupt", False)]

        if not bankrupt_agents:
            return

        if not hasattr(self, "agent_templates"):
            self.agent_templates = {}

        for agent in bankrupt_agents:
            self._dprint(f"Removing bankrupt agent {agent.name} (money={agent.money:.2f})")

            # Determine template for this type
            template = self.agent_templates.get(agent.group)
            if template is None:
                # Build template from original parameters if not cached
                # Attempt to retrieve from config
                template = self.config['agents'][agent.group].copy()
                template.pop('count', None)
                self.agent_templates[agent.group] = template

            # Delete from scheduler & group
            group_obj = self.agent_groups.get(agent.group)
            if group_obj is not None:
                # Remove node from network and climate bookkeeping
                old_label = f"{agent.group}_{agent.agent_id}"
                if old_label in self.framework.network:
                    self.framework.network.remove_node(old_label)
                # Remove climate data & geo assignments
                self.framework.agent_climate_data.pop((agent.group, agent.agent_id), None)
                self.framework.geographical_assignments.get(agent.group, {}).pop(agent.agent_id, None)

                # Delete from scheduler & group
                group_obj.delete_agents([agent.name])

                # Determine next unique id (avoid collision with existing) – use max id + 1
                current_ids = [name[1] for name in group_obj.names]
                next_id = max(current_ids) + 1 if current_ids else 0
                group_obj.num_agents = next_id  # guides create_agents enumeration

                # Create replacement agent
                new_names = group_obj.create_agents(
                    GeneralizedAgent,
                    agent_parameters=[template.copy()]
                )
                new_name = next(iter(new_names))
                new_agent = self.simulation.scheduler.agents[new_name]

                # Network & geography for new node --------------------------------
                continent = random.choice(self.framework.continents)
                self.framework.geographical_assignments.setdefault(agent.group, {})[next_id] = {'continent': continent}

                node_label = f"{agent.group}_{next_id}"
                self.framework.network.add_node(node_label, agent_type=agent.group, agent_id=next_id)

                # Random edges to existing nodes
                existing_nodes = [n for n in self.framework.network.nodes if n != node_label]
                if existing_nodes:
                    conn_prob = self.framework.network_generator.network_params.get('connection_probability', 0.3)
                    max_conn = self.framework.network_generator.network_params.get('max_connections_per_agent', 5)
                    num_conn = min(np.random.poisson(conn_prob * len(existing_nodes)), max_conn)
                    targets = random.sample(existing_nodes, min(num_conn, len(existing_nodes)))
                    for tgt in targets:
                        self.framework.network.add_edge(node_label, tgt, weight=random.uniform(0.1, 1.0))

                self._dprint(f"Spawned replacement agent {new_name} as network node {node_label}")

        # Recompute real_agents list and update all_agents references
        self.real_agents = list(self.simulation.scheduler.agents.values())
        for ag in self.real_agents:
            ag.all_agents = self.real_agents

        # Rebuild agent connected_agents lists since network changed
        self._setup_network_connections()

        # Force network layout recalc for animation
        self._network_pos = None


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