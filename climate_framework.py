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
        # Track ongoing shock effects for severity-based recovery
        self.ongoing_shocks = {}  # {agent_type: {agent_continent: {'severity': float, 'rounds_remaining': int}}}
        self.shock_recovery_rate = simulation_parameters.get('shock_recovery_rate', 0.2)  # 20% recovery per round by default
    
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
        Apply climate stress events by continent using group-level method calls.
        Uses configurable rules for both acute and chronic events.
        """
        climate_events = {}
        
        # Apply selective chronic stress using chronic_rules (happens every round)
        chronic_rules = self.params.get('chronic_rules', [])
        if chronic_rules:
            print(f"\n🏭 Applying selective chronic stress...")
            self._apply_chronic_stress_selective(agent_groups, chronic_rules)
        else:
            print(f"\n🏭 No chronic stress rules configured")
        
        # Apply acute events using shock_rules system
        shock_rules = self.params.get('shock_rules', [])
        
        if shock_rules:
            # Use configurable shock system with severity-based recovery
            climate_events = self._apply_configurable_shocks(agent_groups, shock_rules)
        else:
            # Even if no shock rules, still process ongoing shock recovery
            print(f"\n  No shock rules configured, but checking for ongoing shock recovery...")
            
            # Process any ongoing shock recovery
            self._process_shock_recovery(agent_groups)
            
            # Apply any ongoing shock effects that haven't fully recovered
            self._apply_ongoing_shocks(agent_groups)
            
            # Reset all agents to normal production if no ongoing shocks
            if not self.ongoing_shocks:
                print(f"\n  No ongoing shocks - resetting all agents to normal production...")
                for agent_type, agent_group in agent_groups.items():
                    try:
                        agent_group.reset_climate_stress()
                        print(f"    Reset climate stress for {agent_type} group")
                    except Exception as e:
                        print(f"    Could not reset {agent_type}: {e}")
            else:
                print(f"\n  Ongoing shocks still active - agents remain affected")
        
        # Store climate events
        self.climate_events_history.append(climate_events)
        
        print(f"Climate events recorded: {climate_events}")
        return climate_events
    
    def _apply_chronic_stress_selective(self, agent_groups: Dict[str, List], chronic_rules: List[Dict]):
        """
        Apply chronic climate stress selectively based on configurable rules.
        
        Args:
            agent_groups: Dictionary mapping agent type names to abcEconomics agent groups
            chronic_rules: List of chronic stress rule configurations
        
        Each chronic rule should have:
        - agent_types: List of agent types to affect
        - continents: List of continents to affect (optional, defaults to 'all')
        - stress_factor: Multiplier for permanent productivity reduction (e.g., 0.99 = 1% permanent loss per round)
        - description: Optional description of the chronic stress
        """
        for rule in chronic_rules:
            rule_name = rule.get('name', 'chronic_stress')
            agent_types = rule.get('agent_types', [])
            continents = rule.get('continents', ['all'])
            stress_factor = rule.get('stress_factor', 0.99)
            description = rule.get('description', '')
            
            print(f"  Applying chronic stress rule: {rule_name}")
            if description:
                print(f"    Description: {description}")
            print(f"    Affects: {agent_types} in {continents}")
            print(f"    Stress factor: {stress_factor} (permanent)")
            
            # Apply chronic stress to specified agent types and continents
            self._apply_targeted_chronic_stress(
                agent_groups, agent_types, continents, stress_factor, rule_name
            )

    def _apply_targeted_chronic_stress(self, agent_groups: Dict[str, List], 
                                     target_agent_types: List[str], 
                                     target_continents: List[str], 
                                     stress_factor: float,
                                     rule_name: str):
        """
        Apply chronic stress to specific agent types in specific continents.
        
        Args:
            agent_groups: Dictionary mapping agent type names to abcEconomics agent groups
            target_agent_types: List of agent types to affect
            target_continents: List of continents to affect (or ['all'] for all continents)
            stress_factor: Multiplier for permanent productivity reduction (e.g., 0.99 = 1% permanent loss)
            rule_name: Name of the chronic stress rule for logging
        """
        # Expand 'all' continents to actual continent list
        if 'all' in target_continents:
            target_continents = list(CONTINENTS.keys())
        
        for agent_type in target_agent_types:
            if agent_type not in agent_groups:
                print(f"    Warning: Agent type '{agent_type}' not found in simulation")
                continue
                
            agent_group = agent_groups[agent_type]
            
            # Check if this agent type has geographical assignments
            if agent_type not in self.geographical_assignments:
                print(f"    Warning: No geographical assignments for '{agent_type}'")
                continue
            
            assignments = self.geographical_assignments[agent_type]
            
            # Find agents in target continents
            affected_agent_ids = []
            for agent_id, agent_info in assignments.items():
                agent_continent = agent_info['continent']
                if agent_continent in target_continents:
                    affected_agent_ids.append(agent_id)
            
            if affected_agent_ids and hasattr(agent_group, 'apply_chronic_stress'):
                try:
                    # Apply chronic stress to the entire group - abcEconomics will handle distribution
                    agent_group.apply_chronic_stress(stress_factor)
                    print(f"    Applied {rule_name} to {len(affected_agent_ids)} {agent_type}s in {target_continents}")
                except Exception as e:
                    print(f"    Could not apply {rule_name} to {agent_type} group: {e}")
            else:
                print(f"    No applicable {agent_type}s found in target continents: {target_continents}")

    def _apply_configurable_shocks(self, agent_groups: Dict[str, List], shock_rules: List[Dict]) -> Dict[str, str]:
        """
        Apply climate shocks based on configurable rules with severity-based recovery.
        Recovery time is proportional to shock severity - more severe shocks take longer to recover from.
        
        Args:
            agent_groups: Dictionary mapping agent type names to abcEconomics agent groups
            shock_rules: List of shock rule configurations (duration parameter is ignored)
            
        Returns:
            Dictionary of climate events that occurred this round
        """
        climate_events = {}
        
        # First, process ongoing shock recovery
        print(f"\n  Processing shock recovery...")
        self._process_shock_recovery(agent_groups)
        
        # Apply any ongoing shock effects that haven't fully recovered
        print(f"\n  Applying ongoing shock effects...")
        self._apply_ongoing_shocks(agent_groups)
        
        # Process each shock rule for new shocks
        for rule in shock_rules:
            rule_name = rule.get('name', 'unnamed_shock')
            probability = rule.get('probability', 0.1)
            agent_types = rule.get('agent_types', [])
            continents = rule.get('continents', ['all'])
            stress_factor = rule.get('stress_factor', 0.7)
            description = rule.get('description', '')
            
            # Check if this shock occurs this round
            if random.random() < probability:
                print(f"\n🌪️ CLIMATE SHOCK: {rule_name}")
                if description:
                    print(f"    Description: {description}")
                print(f"    Affects: {agent_types} in {continents}")
                print(f"    Stress factor: {stress_factor}")
                
                # Calculate recovery time based on severity
                # More severe shocks (lower stress_factor) take longer to recover
                shock_severity = 1.0 - stress_factor  # 0.3 severity for 0.7 stress_factor
                recovery_rounds = max(1, int(shock_severity / self.shock_recovery_rate))
                print(f"    Estimated recovery time: {recovery_rounds} rounds")
                
                # Apply shock and track it for ongoing effects
                affected_agents = self._apply_and_track_shock(
                    agent_groups, agent_types, continents, stress_factor, rule_name, recovery_rounds
                )
                
                # Record this event (without duration parameter)
                event_key = f"{rule_name}_{len(climate_events)}"
                climate_events[event_key] = {
                    'type': 'configurable_shock',
                    'rule_name': rule_name,
                    'agent_types': agent_types,
                    'continents': continents,
                    'stress_factor': stress_factor,
                    'estimated_recovery_rounds': recovery_rounds,
                    'affected_agents': affected_agents
                }
        
        return climate_events
    
    def _process_shock_recovery(self, agent_groups: Dict[str, List]):
        """
        Process recovery from ongoing shocks. Recovery rate is proportional to shock recovery rate.
        """
        agents_recovering = 0
        
        for agent_type in list(self.ongoing_shocks.keys()):
            if agent_type not in self.ongoing_shocks:
                continue
                
            for continent in list(self.ongoing_shocks[agent_type].keys()):
                shock_info = self.ongoing_shocks[agent_type][continent]
                
                # Reduce shock severity over time
                current_severity = shock_info['severity']
                recovery_amount = current_severity * self.shock_recovery_rate
                new_severity = max(0.0, current_severity - recovery_amount)
                
                shock_info['severity'] = new_severity
                shock_info['rounds_remaining'] -= 1
                
                agents_recovering += 1
                
                print(f"    {agent_type} in {continent}: severity {current_severity:.3f} -> {new_severity:.3f}")
                
                # Remove shock if fully recovered or rounds expired
                if new_severity <= 0.01 or shock_info['rounds_remaining'] <= 0:
                    print(f"    {agent_type} in {continent}: FULLY RECOVERED")
                    del self.ongoing_shocks[agent_type][continent]
                    
            # Clean up empty agent types
            if not self.ongoing_shocks[agent_type]:
                del self.ongoing_shocks[agent_type]
        
        if agents_recovering > 0:
            print(f"    {agents_recovering} agent groups are recovering from shocks")
        else:
            print(f"    No ongoing shocks to recover from")
    
    def _apply_ongoing_shocks(self, agent_groups: Dict[str, List]):
        """
        Apply the current severity level of ongoing shocks to affected agents.
        """
        for agent_type, continents_dict in self.ongoing_shocks.items():
            if agent_type not in agent_groups:
                continue
                
            for continent, shock_info in continents_dict.items():
                severity = shock_info['severity']
                if severity > 0.01:  # Only apply meaningful shocks
                    # Calculate current stress factor from severity
                    current_stress_factor = 1.0 - severity
                    
                    print(f"    Applying ongoing shock to {agent_type} in {continent}: stress_factor = {current_stress_factor:.3f}")
                    
                    # Apply shock to this specific agent type and continent
                    self._apply_targeted_shock(
                        agent_groups, [agent_type], [continent], current_stress_factor, f"ongoing_shock_{continent}"
                    )
    
    def _apply_and_track_shock(self, agent_groups: Dict[str, List], 
                             target_agent_types: List[str], 
                             target_continents: List[str], 
                             stress_factor: float,
                             shock_name: str,
                             recovery_rounds: int) -> Dict[str, int]:
        """
        Apply a shock and track it for ongoing severity-based recovery.
        """
        # Expand 'all' continents to actual continent list
        if 'all' in target_continents:
            target_continents = list(CONTINENTS.keys())
        
        affected_agents = {}
        shock_severity = 1.0 - stress_factor
        
        for agent_type in target_agent_types:
            if agent_type not in agent_groups:
                print(f"    Warning: Agent type '{agent_type}' not found in simulation")
                continue
            
            # Initialize tracking for this agent type if needed
            if agent_type not in self.ongoing_shocks:
                self.ongoing_shocks[agent_type] = {}
            
            # Track shock for each continent
            for continent in target_continents:
                # Add or update ongoing shock tracking
                if continent in self.ongoing_shocks[agent_type]:
                    # If there's already a shock, take the more severe one
                    existing_severity = self.ongoing_shocks[agent_type][continent]['severity']
                    if shock_severity > existing_severity:
                        self.ongoing_shocks[agent_type][continent] = {
                            'severity': shock_severity,
                            'rounds_remaining': recovery_rounds
                        }
                        print(f"    Updated more severe shock for {agent_type} in {continent}")
                else:
                    # New shock
                    self.ongoing_shocks[agent_type][continent] = {
                        'severity': shock_severity,
                        'rounds_remaining': recovery_rounds
                    }
                    print(f"    Tracking new shock for {agent_type} in {continent}")
            
            # Apply the immediate shock effect
            self._apply_targeted_shock(
                agent_groups, [agent_type], target_continents, stress_factor, shock_name
            )
            
            # Count affected agents for reporting
            if agent_type in self.geographical_assignments:
                assignments = self.geographical_assignments[agent_type]
                affected_count = sum(1 for agent_id, agent_info in assignments.items() 
                                   if agent_info['continent'] in target_continents)
                affected_agents[agent_type] = affected_count
        
        return affected_agents
    
    def _apply_targeted_shock(self, agent_groups: Dict[str, List], 
                            target_agent_types: List[str], 
                            target_continents: List[str], 
                            stress_factor: float,
                            shock_name: str) -> Dict[str, int]:
        """
        Apply a targeted climate shock to specific agent types in specific continents.
        
        Args:
            agent_groups: Dictionary mapping agent type names to abcEconomics agent groups
            target_agent_types: List of agent types to affect
            target_continents: List of continents to affect (or ['all'] for all continents)
            stress_factor: Multiplier for production capacity (e.g., 0.7 = 30% reduction)
            shock_name: Name of the shock for logging
            
        Returns:
            Dictionary with count of affected agents per type
        """
        affected_agents = {}
        
        # Expand 'all' continents to actual continent list
        if 'all' in target_continents:
            target_continents = list(CONTINENTS.keys())
        
        for agent_type in target_agent_types:
            if agent_type not in agent_groups:
                print(f"    Warning: Agent type '{agent_type}' not found in simulation")
                continue
                
            agent_group = agent_groups[agent_type]
            
            # Check if this agent type has geographical assignments
            if agent_type not in self.geographical_assignments:
                print(f"    Warning: No geographical assignments for '{agent_type}'")
                continue
            
            assignments = self.geographical_assignments[agent_type]
            
            # Find agents in target continents
            affected_agent_ids = []
            for agent_id, agent_info in assignments.items():
                agent_continent = agent_info['continent']
                if agent_continent in target_continents:
                    affected_agent_ids.append(agent_id)
            
            if affected_agent_ids and hasattr(agent_group, 'apply_climate_stress'):
                try:
                    # Apply stress to the entire group - abcEconomics will handle distribution
                    agent_group.apply_climate_stress(stress_factor)
                    affected_agents[agent_type] = len(affected_agent_ids)
                    print(f"    Applied {shock_name} to {len(affected_agent_ids)} {agent_type}s in {target_continents}")
                except Exception as e:
                    print(f"    Could not apply {shock_name} to {agent_type} group: {e}")
            else:
                print(f"    No applicable {agent_type}s found in target continents: {target_continents}")
        
        return affected_agents
    
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
        
        Args:
            agent_groups: Dictionary mapping agent type names to abcEconomics agent groups
            simulation_path: ACTUAL simulation path (should be w.path from Simulation object, not the original path)
            model_name: Name of the model for titles
        """
        # Set up the visualization style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        # Ensure simulation path exists
        if simulation_path and not os.path.exists(simulation_path):
            os.makedirs(simulation_path, exist_ok=True)
        
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
        
        # Save visualization to simulation directory
        filename = f'{model_name.lower().replace(" ", "_")}_climate_analysis.png'
        if simulation_path:
            save_path = os.path.join(simulation_path, filename)
        else:
            save_path = filename
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        #plt.show()
        plt.close()
        print(f"Climate visualizations saved to '{save_path}'")
        
        # Create second figure showing simulation results
        if simulation_path:
            self._create_simulation_results_visualization(simulation_path, model_name)
        
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
    
    def _create_simulation_results_visualization(self, simulation_path: str, model_name: str):
        """Create a comprehensive visualization of simulation results and economic impacts."""
        try:
            # Load abcEconomics data
            economic_data = self._load_economic_data(simulation_path)
            
            if not economic_data:
                print("No economic data available for results visualization")
                return
            
            # Create second figure for simulation results
            fig, axes = plt.subplots(2, 3, figsize=(18, 12))
            fig.suptitle(f'{model_name} - Simulation Results & Economic Impact Analysis', 
                        fontsize=16, fontweight='bold')
            
            # 1. Economic Performance Over Time
            self._plot_economic_performance(axes[0, 0], economic_data)
            
            # 2. Climate Events vs Economic Activity
            self._plot_climate_impact_analysis(axes[0, 1], economic_data)
            
            # 3. Agent Performance Comparison
            self._plot_agent_performance(axes[0, 2], economic_data)
            
            # 4. Geographic Economic Analysis
            self._plot_geographic_economic_analysis(axes[1, 0], economic_data)
            
            # 5. Production vs Consumption Trends
            self._plot_production_consumption_trends(axes[1, 1], economic_data)
            
            # 6. Summary Statistics
            self._plot_summary_statistics(axes[1, 2], economic_data)
            
            plt.tight_layout()
            
            # Save results visualization to simulation directory
            filename = f'{model_name.lower().replace(" ", "_")}_simulation_results.png'
            results_save_path = os.path.join(simulation_path, filename)
            plt.savefig(results_save_path, dpi=300, bbox_inches='tight')
            #plt.show()
            plt.close()
            print(f"Simulation results visualization saved to '{results_save_path}'")
            
        except Exception as e:
            print(f"Error creating simulation results visualization: {e}")
            import traceback
            traceback.print_exc()
    
    def _load_economic_data(self, simulation_path: str) -> Dict[str, pd.DataFrame]:
        """Load economic data from abcEconomics output files."""
        economic_data = {}
        
        try:
            if os.path.exists(simulation_path):
                csv_files = [f for f in os.listdir(simulation_path) if f.endswith('.csv')]
                
                for csv_file in csv_files:
                    file_path = os.path.join(simulation_path, csv_file)
                    try:
                        df = pd.read_csv(file_path)
                        # Use the base filename as the key
                        key = csv_file.replace('.csv', '')
                        economic_data[key] = df
                        print(f"Loaded {len(df)} rows from {csv_file}")
                    except Exception as e:
                        print(f"Could not load {csv_file}: {e}")
                        
        except Exception as e:
            print(f"Error loading economic data: {e}")
        
        return economic_data
    
    def _plot_economic_performance(self, ax, economic_data: Dict[str, pd.DataFrame]):
        """Plot overall economic performance over time."""
        ax.set_title('Economic Performance Over Time', fontweight='bold')
        
        # Look for any firm/producer data that has production metrics
        production_data = None
        production_column = None
        
        # Try to find production data in order of preference
        for key, df in economic_data.items():
            if len(df) > 0 and 'round' in df.columns:
                # Look for different types of production columns
                if 'goods' in df.columns:
                    production_data = df
                    production_column = 'goods'
                    break
                elif 'commodity' in df.columns:
                    production_data = df
                    production_column = 'commodity'
                    break
                elif 'final_good' in df.columns:
                    production_data = df
                    production_column = 'final_good'
                    break
                elif 'intermediate_good' in df.columns:
                    production_data = df
                    production_column = 'intermediate_good'
                    break
        
        if production_data is not None and len(production_data) > 0:
            # Aggregate by round
            if 'round' in production_data.columns:
                agg_dict = {production_column: ['sum', 'mean']}
                if 'money' in production_data.columns:
                    agg_dict['money'] = ['sum', 'mean']
                
                round_summary = production_data.groupby('round').agg(agg_dict).reset_index()
                
                # Flatten column names
                new_columns = ['round']
                for col in round_summary.columns[1:]:
                    if isinstance(col, tuple):
                        new_columns.append(f"{col[1]}_{col[0]}")
                    else:
                        new_columns.append(col)
                round_summary.columns = new_columns
                
                # Plot production trends
                production_col = f"sum_{production_column}"
                if production_col in round_summary.columns:
                    ax.plot(round_summary['round'], round_summary[production_col], 
                           'g-o', linewidth=2, label=f'Total {production_column.replace("_", " ").title()}', markersize=6)
                
                # If we have money data, add it on a second axis
                money_col = "sum_money"
                if money_col in round_summary.columns:
                    ax2 = ax.twinx()
                    ax2.plot(round_summary['round'], round_summary[money_col], 
                            'b-s', linewidth=2, label='Total Money', markersize=6)
                    ax2.set_ylabel('Total Money', color='blue')
                    
                    # Combine legends
                    lines1, labels1 = ax.get_legend_handles_labels()
                    lines2, labels2 = ax2.get_legend_handles_labels()
                    ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
                else:
                    ax.legend()
                
                ax.set_xlabel('Round')
                ax.set_ylabel(f'Total {production_column.replace("_", " ").title()}', color='green')
                
                # Highlight climate event rounds
                for round_num, events in enumerate(self.climate_events_history):
                    if events:
                        ax.axvline(x=round_num, color='red', linestyle='--', alpha=0.7, linewidth=1)
                        ax.text(round_num, ax.get_ylim()[1] * 0.9, 'Climate\nEvent', 
                               ha='center', va='top', fontsize=8, color='red')
            else:
                ax.text(0.5, 0.5, 'No round data available', ha='center', va='center', transform=ax.transAxes)
        else:
            ax.text(0.5, 0.5, 'No production data available', ha='center', va='center', transform=ax.transAxes)
        
        ax.grid(True, alpha=0.3)
    
    def _plot_climate_impact_analysis(self, ax, economic_data: Dict[str, pd.DataFrame]):
        """Plot the correlation between climate events and economic activity."""
        ax.set_title('Climate Events vs Economic Activity', fontweight='bold')
        
        if not self.climate_events_history:
            ax.text(0.5, 0.5, 'No climate events recorded', ha='center', va='center', transform=ax.transAxes)
            return
        
        # Create impact analysis
        rounds = list(range(len(self.climate_events_history)))
        climate_intensity = []
        economic_activity = []
        
        # Calculate climate intensity per round
        for events in self.climate_events_history:
            intensity = len(events) if events else 0
            climate_intensity.append(intensity)
        
        # Calculate economic activity (if available)
        firm_data = None
        for key, df in economic_data.items():
            if 'firm' in key.lower() and 'goods' in df.columns:
                firm_data = df
                break
        
        if firm_data is not None and 'round' in firm_data.columns:
            for r in rounds:
                round_data = firm_data[firm_data['round'] == r]
                activity = round_data['goods'].sum() if len(round_data) > 0 else 0
                economic_activity.append(activity)
        else:
            economic_activity = [0] * len(rounds)
        
        # Create dual axis plot
        ax2 = ax.twinx()
        
        bars = ax.bar([r - 0.2 for r in rounds], climate_intensity, width=0.4, 
                     color='red', alpha=0.7, label='Climate Events')
        line = ax2.plot(rounds, economic_activity, 'b-o', linewidth=2, label='Economic Activity')
        
        ax.set_xlabel('Round')
        ax.set_ylabel('Number of Climate Events', color='red')
        ax2.set_ylabel('Total Goods Production', color='blue')
        ax.set_xticks(rounds)
        
        # Add correlation info
        if len(climate_intensity) > 1 and len(economic_activity) > 1:
            correlation = np.corrcoef(climate_intensity, economic_activity)[0, 1]
            ax.text(0.02, 0.98, f'Correlation: {correlation:.3f}', transform=ax.transAxes, 
                   fontsize=10, verticalalignment='top', 
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        # Legend
        lines = [bars] + line
        labels = ['Climate Events', 'Economic Activity']
        ax.legend(lines, labels, loc='upper right')
        
        ax.grid(True, alpha=0.3)
    
    def _plot_agent_performance(self, ax, economic_data: Dict[str, pd.DataFrame]):
        """Plot individual agent performance comparison."""
        ax.set_title('Agent Performance Comparison', fontweight='bold')
        
        # Look for the most recent round data from any producer/firm type
        agent_data = None
        x_column = None
        y_column = None
        
        for key, df in economic_data.items():
            if len(df) > 0 and 'name' in df.columns:
                # Look for production data
                if 'commodity_producer' in key.lower() and 'commodity' in df.columns:
                    agent_data = df
                    x_column = 'commodity'
                    y_column = 'commodity'  # Same for both axes in this case
                    break
                elif 'final_goods_firm' in key.lower() and 'final_good' in df.columns:
                    agent_data = df
                    x_column = 'final_good'
                    y_column = 'final_good'
                    break
                elif 'firm' in key.lower() and 'money' in df.columns and 'goods' in df.columns:
                    agent_data = df
                    x_column = 'money'
                    y_column = 'goods'
                    break
        
        if agent_data is not None and len(agent_data) > 0:
            # Get latest round data
            if 'round' in agent_data.columns:
                latest_round = agent_data['round'].max()
                latest_data = agent_data[agent_data['round'] == latest_round]
            else:
                latest_data = agent_data
            
            if len(latest_data) > 0:
                # Create performance metrics
                agents = latest_data['name'].tolist()
                x_values = latest_data[x_column].tolist()
                
                # For y-axis, use the same column or a different one if available
                if y_column in latest_data.columns:
                    y_values = latest_data[y_column].tolist()
                else:
                    y_values = x_values  # Fallback to same values
                
                # Map agents to continents based on geographical assignments
                agent_continents = []
                continent_colors = []
                
                for agent_name in agents:
                    # Extract agent type and id from name (e.g., 'commodity_producer0' -> 'commodity_producer', 0)
                    # Handle different naming patterns
                    continent = 'Unknown'
                    color = 'gray'
                    
                    for agent_type in self.geographical_assignments:
                        if agent_type in agent_name:
                            try:
                                agent_id = int(''.join([c for c in agent_name if c.isdigit()]))
                                if agent_id in self.geographical_assignments[agent_type]:
                                    continent = self.geographical_assignments[agent_type][agent_id]['continent']
                                    color = CONTINENTS[continent]['color']
                                    break
                            except:
                                continue
                    
                    agent_continents.append(continent)
                    continent_colors.append(color)
                
                # Create scatter plot
                scatter = ax.scatter(x_values, y_values, c=continent_colors, s=100, alpha=0.7)
                
                # Add agent labels
                for i, agent in enumerate(agents):
                    ax.annotate(agent.replace('_', ' '), (x_values[i], y_values[i]), xytext=(5, 5), 
                               textcoords='offset points', fontsize=8)
                
                ax.set_xlabel(x_column.replace('_', ' ').title())
                ax.set_ylabel(y_column.replace('_', ' ').title())
                
                # Create legend for continents
                unique_continents = list(set(agent_continents))
                legend_elements = []
                for continent in unique_continents:
                    if continent in CONTINENTS:
                        legend_elements.append(plt.Line2D([0], [0], marker='o', color='w', 
                                                        markerfacecolor=CONTINENTS[continent]['color'], 
                                                        markersize=10, label=continent))
                
                if legend_elements:
                    ax.legend(handles=legend_elements, loc='upper right', fontsize=8)
            else:
                ax.text(0.5, 0.5, 'No agent data available', ha='center', va='center', transform=ax.transAxes)
        else:
            ax.text(0.5, 0.5, 'No agent performance data available', ha='center', va='center', transform=ax.transAxes)
        
        ax.grid(True, alpha=0.3)
    
    def _plot_geographic_economic_analysis(self, ax, economic_data: Dict[str, pd.DataFrame]):
        """Plot economic performance by geographical region."""
        ax.set_title('Economic Performance by Continent', fontweight='bold')
        
        # Initialize continent data
        continent_data = {continent: {'money': 0, 'goods': 0, 'agents': 0} 
                         for continent in CONTINENTS.keys()}
        
        # Look for latest economic data
        firm_data = None
        for key, df in economic_data.items():
            if 'firm' in key.lower() and 'money' in df.columns:
                firm_data = df
                break
        
        if firm_data is not None and len(firm_data) > 0:
            # Get latest round
            if 'round' in firm_data.columns:
                latest_round = firm_data['round'].max()
                latest_data = firm_data[firm_data['round'] == latest_round]
            else:
                latest_data = firm_data
            
            # Aggregate by continent
            for _, row in latest_data.iterrows():
                agent_name = row['name']
                # Extract agent type and id
                agent_type = ''.join([c for c in agent_name if not c.isdigit()])
                try:
                    agent_id = int(''.join([c for c in agent_name if c.isdigit()]))
                    
                    if agent_type in self.geographical_assignments and agent_id in self.geographical_assignments[agent_type]:
                        continent = self.geographical_assignments[agent_type][agent_id]['continent']
                        continent_data[continent]['money'] += row['money']
                        continent_data[continent]['goods'] += row.get('goods', 0)
                        continent_data[continent]['agents'] += 1
                except:
                    continue
            
            # Create bar chart
            continents = list(continent_data.keys())
            money_values = [continent_data[c]['money'] for c in continents]
            goods_values = [continent_data[c]['goods'] for c in continents]
            colors = [CONTINENTS[c]['color'] for c in continents]
            
            x = np.arange(len(continents))
            width = 0.35
            
            ax2 = ax.twinx()
            bars1 = ax.bar(x - width/2, money_values, width, label='Money', color=colors, alpha=0.7)
            bars2 = ax2.bar(x + width/2, goods_values, width, label='Goods', color=colors, alpha=0.5)
            
            ax.set_xlabel('Continent')
            ax.set_ylabel('Total Money', color='navy')
            ax2.set_ylabel('Total Goods', color='darkred')
            ax.set_xticks(x)
            ax.set_xticklabels(continents, rotation=45)
            
            # Add value labels
            for i, (money, goods) in enumerate(zip(money_values, goods_values)):
                ax.text(i - width/2, money + max(money_values) * 0.01, f'{money}', 
                       ha='center', va='bottom', fontsize=8)
                ax2.text(i + width/2, goods + max(goods_values) * 0.01, f'{goods:.1f}', 
                        ha='center', va='bottom', fontsize=8)
            
            # Legend
            lines1, labels1 = ax.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        else:
            ax.text(0.5, 0.5, 'No economic data by continent available', 
                   ha='center', va='center', transform=ax.transAxes)
        
        ax.grid(True, alpha=0.3)
    
    def _plot_production_consumption_trends(self, ax, economic_data: Dict[str, pd.DataFrame]):
        """Plot production and consumption trends over time."""
        ax.set_title('Production & Consumption Trends', fontweight='bold')
        
        # Look for production data from any type of producer/firm
        production_data = None
        production_column = None
        
        # Look for household consumption data
        household_data = None
        
        # Find the best production and consumption data
        for key, df in economic_data.items():
            if len(df) > 0 and 'round' in df.columns:
                # Look for production data
                if 'commodity_producer' in key.lower() and 'commodity' in df.columns:
                    production_data = df
                    production_column = 'commodity'
                elif 'final_goods_firm' in key.lower() and 'final_good' in df.columns:
                    production_data = df
                    production_column = 'final_good'
                elif 'firm' in key.lower() and 'goods' in df.columns:
                    production_data = df
                    production_column = 'goods'
                
                # Look for household consumption data
                if 'household' in key.lower():
                    if 'final_good' in df.columns:
                        household_data = df
                    elif 'money' in df.columns and household_data is None:
                        household_data = df  # Fallback to money if no consumption data
        
        if production_data is not None and 'round' in production_data.columns:
            # Production trends
            production_summary = production_data.groupby('round').agg({
                production_column: 'sum'
            }).reset_index()
            
            ax.plot(production_summary['round'], production_summary[production_column], 
                   'g-o', linewidth=2, label=f'{production_column.replace("_", " ").title()} Production', markersize=6)
            
            # If we have household data, show it on a second axis
            if household_data is not None and 'round' in household_data.columns:
                household_column = 'final_good' if 'final_good' in household_data.columns else 'money'
                household_summary = household_data.groupby('round').agg({
                    household_column: 'sum'
                }).reset_index()
                
                ax2 = ax.twinx()
                color = 'blue' if household_column == 'money' else 'purple'
                ax2.plot(household_summary['round'], household_summary[household_column], 
                        color=color, linestyle='-', marker='s', linewidth=2, label=f'Household {household_column.replace("_", " ").title()}', markersize=6)
                ax2.set_ylabel(f'Household {household_column.replace("_", " ").title()}', color=color)
                
                # Combine legends
                lines1, labels1 = ax.get_legend_handles_labels()
                lines2, labels2 = ax2.get_legend_handles_labels()
                ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
            else:
                ax.legend()
            
            ax.set_xlabel('Round')
            ax.set_ylabel(f'{production_column.replace("_", " ").title()} Production', color='green')
            
            # Highlight climate events
            for round_num, events in enumerate(self.climate_events_history):
                if events:
                    ax.axvline(x=round_num, color='red', linestyle='--', alpha=0.5)
        else:
            ax.text(0.5, 0.5, 'No production/consumption data available', 
                   ha='center', va='center', transform=ax.transAxes)
        
        ax.grid(True, alpha=0.3)
    
    def _plot_summary_statistics(self, ax, economic_data: Dict[str, pd.DataFrame]):
        """Plot key summary statistics from the simulation."""
        ax.set_title('Simulation Summary Statistics', fontweight='bold')
        
        stats_text = []
        
        # Basic simulation info
        stats_text.append(f"Simulation Rounds: {len(self.climate_events_history)}")
        stats_text.append(f"Total Climate Events: {sum(len(events) for events in self.climate_events_history)}")
        
        # Agent distribution
        total_agents = sum(len(assignments) for assignments in self.geographical_assignments.values())
        stats_text.append(f"Total Agents: {total_agents}")
        
        for agent_type, assignments in self.geographical_assignments.items():
            stats_text.append(f"  {agent_type.replace('_', ' ').title()}s: {len(assignments)}")
        
        # Economic summary (if available)
        firm_data = None
        for key, df in economic_data.items():
            if 'firm' in key.lower() and 'money' in df.columns:
                firm_data = df
                break
        
        if firm_data is not None and len(firm_data) > 0:
            if 'round' in firm_data.columns:
                latest_round = firm_data['round'].max()
                latest_data = firm_data[firm_data['round'] == latest_round]
            else:
                latest_data = firm_data
            
            total_money = latest_data['money'].sum()
            total_goods = latest_data['goods'].sum() if 'goods' in latest_data.columns else 0
            avg_money = latest_data['money'].mean()
            avg_goods = latest_data['goods'].mean() if 'goods' in latest_data.columns else 0
            
            stats_text.append(f"\nEconomic Summary (Final Round):")
            stats_text.append(f"  Total Money: {total_money}")
            stats_text.append(f"  Total Goods: {total_goods:.1f}")
            stats_text.append(f"  Avg Money per Agent: {avg_money:.1f}")
            stats_text.append(f"  Avg Goods per Agent: {avg_goods:.1f}")
        
        # Climate impact summary
        affected_continents = set()
        for events in self.climate_events_history:
            affected_continents.update(events.keys())
        
        if affected_continents:
            stats_text.append(f"\nClimate Impact Summary:")
            stats_text.append(f"  Affected Continents: {', '.join(affected_continents)}")
            
            for continent in affected_continents:
                event_count = sum(1 for events in self.climate_events_history if continent in events)
                stats_text.append(f"    {continent}: {event_count} events")
        
        # Display statistics
        stats_text_str = '\n'.join(stats_text)
        ax.text(0.05, 0.95, stats_text_str, transform=ax.transAxes, fontsize=10,
               verticalalignment='top', fontfamily='monospace',
               bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
    
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
    
    def export_climate_summary(self, simulation_path: str = None, filename: str = "climate_summary.csv"):
        """
        Export a summary of climate events and geographical assignments.
        
        Args:
            simulation_path: ACTUAL simulation path (should be w.path from Simulation object, not the original path)
            filename: Name of the CSV file to create
        """
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
            if events:
                for event_key, event_data in events.items():
                    if isinstance(event_data, dict) and 'continents' in event_data:
                        # New configurable shock format
                        event_continents = event_data['continents']
                        if 'all' in event_continents:
                            event_continents = list(CONTINENTS.keys())
                        
                        for continent in event_continents:
                            if continent in CONTINENTS:
                                summary_data.append({
                                    'agent_type': 'climate_event',
                                    'agent_id': event_key,
                                    'round': round_num,
                                    'continent': continent,
                                    'vulnerability': CONTINENTS[continent]['climate_risk'],
                                    'data_type': event_data.get('rule_name', 'configurable_shock'),
                                    'event_name': event_key,
                                    'stress_factor': event_data.get('stress_factor', 1.0),
                                    'estimated_recovery_rounds': event_data.get('estimated_recovery_rounds', 1),
                                    'affected_agent_types': ','.join(event_data.get('agent_types', []))
                                })
                    elif event_key in CONTINENTS:
                        # Old format where event key is continent name
                        summary_data.append({
                            'agent_type': 'climate_event',
                            'agent_id': event_key,
                            'round': round_num,
                            'continent': event_key,
                            'vulnerability': CONTINENTS[event_key]['climate_risk'],
                            'data_type': event_data if isinstance(event_data, str) else 'climate_stress',
                            'event_name': event_key,
                            'stress_factor': 1.0,
                            'estimated_recovery_rounds': 1,
                            'affected_agent_types': 'all'
                        })
        
        if summary_data:
            df = pd.DataFrame(summary_data)
            
            # Save to simulation directory if provided
            if simulation_path:
                # Ensure simulation path exists
                if not os.path.exists(simulation_path):
                    os.makedirs(simulation_path, exist_ok=True)
                save_path = os.path.join(simulation_path, filename)
            else:
                save_path = filename
                
            df.to_csv(save_path, index=False)
            print(f"Climate summary exported to '{save_path}'")
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