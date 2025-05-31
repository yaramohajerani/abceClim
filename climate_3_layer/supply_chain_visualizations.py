"""
Custom Supply Chain Visualizations for 3-Layer Climate Model

This module provides specialized visualizations for the 3-layer supply chain model,
leveraging the core climate framework while adding supply chain-specific analysis.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import os
from typing import Dict, List, Any

# Import the core climate framework
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from climate_framework import CONTINENTS


class SupplyChainVisualizer:
    """Specialized visualizer for 3-layer supply chain climate model."""
    
    def __init__(self, climate_framework):
        """Initialize with reference to the climate framework for geographical/climate data."""
        self.climate_framework = climate_framework
        self.layer_mapping = {
            'commodity_producer': 'Layer 1: Commodity Production',
            'intermediary_firm': 'Layer 2: Intermediate Goods',
            'final_goods_firm': 'Layer 3: Final Goods',
            'household': 'Consumers'
        }
        self.production_goods = {
            'commodity_producer': 'commodity',
            'intermediary_firm': 'intermediate_good', 
            'final_goods_firm': 'final_good'
        }
    
    def create_comprehensive_supply_chain_analysis(self, simulation_path: str, model_name: str = "3-Layer Supply Chain"):
        """Create comprehensive supply chain specific visualizations."""
        # Load all data
        economic_data = self._load_supply_chain_data(simulation_path)
        
        if not economic_data:
            print("No economic data available for supply chain analysis")
            return
        
        # Create the comprehensive analysis
        fig = plt.figure(figsize=(20, 14))
        fig.suptitle(f'{model_name} - Supply Chain Climate Impact Analysis', 
                    fontsize=18, fontweight='bold')
        
        # 1. Supply Chain Flow Analysis (top row, spans 2 columns)
        ax1 = plt.subplot(3, 4, (1, 2))
        self._plot_supply_chain_flow(ax1, economic_data)
        
        # 2. Climate Impact by Layer (top row, spans 2 columns) 
        ax2 = plt.subplot(3, 4, (3, 4))
        self._plot_climate_impact_by_layer(ax2, economic_data)
        
        # 3. Production Efficiency Over Time (middle left)
        ax3 = plt.subplot(3, 4, 5)
        self._plot_production_efficiency(ax3, economic_data)
        
        # 4. Supply Chain Bottlenecks (middle center-left)
        ax4 = plt.subplot(3, 4, 6)
        self._plot_supply_chain_bottlenecks(ax4, economic_data)
        
        # 5. Geographic Impact Analysis (middle center-right)
        ax5 = plt.subplot(3, 4, 7)
        self._plot_geographic_supply_chain_impact(ax5, economic_data)
        
        # 6. Consumer Impact (middle right)
        ax6 = plt.subplot(3, 4, 8)
        self._plot_consumer_impact(ax6, economic_data)
        
        # 7. Multi-Layer Stress Events (bottom left)
        ax7 = plt.subplot(3, 4, 9)
        self._plot_multi_layer_stress_events(ax7, economic_data)
        
        # 8. Supply Chain Resilience (bottom center-left)
        ax8 = plt.subplot(3, 4, 10)
        self._plot_supply_chain_resilience(ax8, economic_data)
        
        # 9. Cross-Layer Correlations (bottom center-right)
        ax9 = plt.subplot(3, 4, 11)
        self._plot_cross_layer_correlations(ax9, economic_data)
        
        # 10. Economic Summary Dashboard (bottom right)
        ax10 = plt.subplot(3, 4, 12)
        self._plot_economic_summary_dashboard(ax10, economic_data)
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        
        # Save the comprehensive analysis
        filename = f'{model_name.lower().replace(" ", "_")}_supply_chain_analysis.png'
        save_path = os.path.join(simulation_path, filename)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"Supply chain analysis saved to '{save_path}'")
        
        # Also create the core climate visualizations
        self.climate_framework.create_simplified_visualizations(
            self._convert_to_agent_groups_format(),
            simulation_path=simulation_path,
            model_name=model_name
        )
    
    def _load_supply_chain_data(self, simulation_path: str) -> Dict[str, pd.DataFrame]:
        """Load and organize data specifically for supply chain analysis."""
        economic_data = {}
        
        try:
            if os.path.exists(simulation_path):
                csv_files = [f for f in os.listdir(simulation_path) if f.endswith('.csv')]
                
                for csv_file in csv_files:
                    file_path = os.path.join(simulation_path, csv_file)
                    try:
                        df = pd.read_csv(file_path)
                        # Organize by agent type and activity
                        if 'production' in csv_file:
                            agent_type = csv_file.replace('panel_', '').replace('_production.csv', '')
                            economic_data[f'{agent_type}_production'] = df
                        elif 'sell' in csv_file:
                            agent_type = csv_file.replace('panel_', '').replace('_sell_commodities.csv', '').replace('_sell_intermediate_goods.csv', '').replace('_sell_final_goods.csv', '')
                            economic_data[f'{agent_type}_sales'] = df
                        elif 'buy' in csv_file:
                            agent_type = csv_file.replace('panel_', '').replace('_buy_final_goods.csv', '')
                            economic_data[f'{agent_type}_purchases'] = df
                        elif 'consumption' in csv_file:
                            economic_data['household_consumption'] = df
                        elif 'HH' in csv_file:
                            economic_data['household_money'] = df
                        
                        print(f"Loaded {len(df)} rows from {csv_file}")
                    except Exception as e:
                        print(f"Could not load {csv_file}: {e}")
                        
        except Exception as e:
            print(f"Error loading supply chain data: {e}")
        
        return economic_data
    
    def _plot_supply_chain_flow(self, ax, economic_data: Dict[str, pd.DataFrame]):
        """Plot the flow of goods through the supply chain over time."""
        ax.set_title('Supply Chain Flow Over Time', fontweight='bold', fontsize=14)
        
        # Get production data for each layer
        layers = ['commodity_producer', 'intermediary_firm', 'final_goods_firm']
        colors = ['brown', 'orange', 'green']
        
        for i, layer in enumerate(layers):
            production_key = f'{layer}_production'
            if production_key in economic_data:
                df = economic_data[production_key]
                good_col = self.production_goods[layer]
                
                if 'round' in df.columns and good_col in df.columns:
                    round_summary = df.groupby('round')[good_col].sum().reset_index()
                    
                    ax.plot(round_summary['round'], round_summary[good_col], 
                           color=colors[i], linewidth=3, marker='o', markersize=8,
                           label=self.layer_mapping[layer], alpha=0.8)
        
        # Highlight climate events
        for round_num, events in enumerate(self.climate_framework.climate_events_history):
            if events:
                ax.axvline(x=round_num, color='red', linestyle='--', alpha=0.7, linewidth=2)
                ax.text(round_num, ax.get_ylim()[1] * 0.9, 'Climate\nEvent', 
                       ha='center', va='top', fontsize=10, color='red', fontweight='bold')
        
        ax.set_xlabel('Round')
        ax.set_ylabel('Total Production')
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)
    
    def _plot_climate_impact_by_layer(self, ax, economic_data: Dict[str, pd.DataFrame]):
        """Plot climate impact analysis by supply chain layer."""
        ax.set_title('Climate Impact by Supply Chain Layer', fontweight='bold', fontsize=14)
        
        # Calculate production drops during climate events
        impact_data = []
        
        for layer in ['commodity_producer', 'intermediary_firm', 'final_goods_firm']:
            production_key = f'{layer}_production'
            if production_key in economic_data:
                df = economic_data[production_key]
                good_col = self.production_goods[layer]
                
                if 'round' in df.columns and good_col in df.columns:
                    round_summary = df.groupby('round')[good_col].sum().reset_index()
                    
                    for round_num, events in enumerate(self.climate_framework.climate_events_history):
                        if round_num < len(round_summary):
                            production = round_summary.iloc[round_num][good_col]
                            normal_production = round_summary[good_col].max()  # Use max as baseline
                            impact_pct = ((normal_production - production) / normal_production) * 100 if normal_production > 0 else 0
                            
                            impact_data.append({
                                'Layer': self.layer_mapping[layer],
                                'Round': round_num,
                                'Impact_Percent': impact_pct,
                                'Has_Climate_Event': len(events) > 0,
                                'Num_Events': len(events)
                            })
        
        if impact_data:
            impact_df = pd.DataFrame(impact_data)
            
            # Create grouped bar chart
            climate_rounds = impact_df[impact_df['Has_Climate_Event'] == True]['Round'].unique()
            layers = impact_df['Layer'].unique()
            
            x = np.arange(len(climate_rounds))
            width = 0.25
            
            for i, layer in enumerate(layers):
                layer_data = impact_df[(impact_df['Layer'] == layer) & (impact_df['Has_Climate_Event'] == True)]
                impacts = []
                for round_num in climate_rounds:
                    round_impact = layer_data[layer_data['Round'] == round_num]['Impact_Percent']
                    impacts.append(round_impact.iloc[0] if len(round_impact) > 0 else 0)
                
                ax.bar(x + i*width, impacts, width, label=layer, alpha=0.8)
            
            ax.set_xlabel('Climate Event Rounds')
            ax.set_ylabel('Production Impact (%)')
            ax.set_xticks(x + width)
            ax.set_xticklabels([f'Round {r}' for r in climate_rounds])
            ax.legend()
            ax.grid(True, alpha=0.3)
        else:
            ax.text(0.5, 0.5, 'No climate impact data available', 
                   ha='center', va='center', transform=ax.transAxes)
    
    def _plot_production_efficiency(self, ax, economic_data: Dict[str, pd.DataFrame]):
        """Plot production efficiency metrics over time."""
        ax.set_title('Production Efficiency', fontweight='bold')
        
        # Calculate efficiency as actual production / theoretical maximum
        if 'commodity_producer_production' in economic_data:
            df = economic_data['commodity_producer_production']
            if 'round' in df.columns and 'commodity' in df.columns:
                round_summary = df.groupby('round')['commodity'].agg(['sum', 'mean']).reset_index()
                
                # Theoretical maximum (3 producers * 2.0 base production)
                theoretical_max = 3 * 2.0
                efficiency = (round_summary['sum'] / theoretical_max) * 100
                
                ax.plot(round_summary['round'], efficiency, 'b-o', linewidth=2, markersize=6)
                ax.set_ylabel('Efficiency (%)')
                ax.set_xlabel('Round')
                ax.set_ylim(0, 105)
                
                # Add efficiency zones
                ax.axhline(y=100, color='green', linestyle='-', alpha=0.3, label='Maximum')
                ax.axhline(y=70, color='orange', linestyle='--', alpha=0.5, label='Stress Level')
                ax.legend()
        
        ax.grid(True, alpha=0.3)
    
    def _plot_supply_chain_bottlenecks(self, ax, economic_data: Dict[str, pd.DataFrame]):
        """Identify and plot supply chain bottlenecks."""
        ax.set_title('Supply Chain Bottlenecks', fontweight='bold')
        
        # Compare production across layers to identify bottlenecks
        bottleneck_data = []
        
        for round_num in range(len(self.climate_framework.climate_events_history)):
            round_production = {}
            
            for layer in ['commodity_producer', 'intermediary_firm', 'final_goods_firm']:
                production_key = f'{layer}_production'
                if production_key in economic_data:
                    df = economic_data[production_key]
                    good_col = self.production_goods[layer]
                    
                    if 'round' in df.columns and good_col in df.columns:
                        round_data = df[df['round'] == round_num]
                        if len(round_data) > 0:
                            total_production = round_data[good_col].sum()
                            round_production[layer] = total_production
            
            # Identify bottleneck (layer with lowest relative production)
            if round_production:
                # Normalize by expected production ratios
                normalized = {
                    'commodity_producer': round_production.get('commodity_producer', 0) / 6.0,  # 3 producers * 2.0
                    'intermediary_firm': round_production.get('intermediary_firm', 0) / 3.0,    # 2 firms * 1.5
                    'final_goods_firm': round_production.get('final_goods_firm', 0) / 3.6       # 2 firms * 1.8
                }
                
                bottleneck = min(normalized.keys(), key=lambda k: normalized[k])
                bottleneck_data.append({
                    'round': round_num,
                    'bottleneck': self.layer_mapping[bottleneck],
                    'severity': 1.0 - normalized[bottleneck]
                })
        
        if bottleneck_data:
            bottleneck_df = pd.DataFrame(bottleneck_data)
            
            # Create stacked bar chart of bottleneck types
            bottleneck_counts = bottleneck_df['bottleneck'].value_counts()
            colors = ['red', 'orange', 'yellow']
            
            bars = ax.bar(range(len(bottleneck_counts)), bottleneck_counts.values, 
                         color=colors[:len(bottleneck_counts)], alpha=0.7)
            
            ax.set_xticks(range(len(bottleneck_counts)))
            ax.set_xticklabels(bottleneck_counts.index, rotation=45)
            ax.set_ylabel('Rounds as Bottleneck')
            
            # Add value labels
            for bar, count in zip(bars, bottleneck_counts.values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                       f'{count}', ha='center', va='bottom')
        
        ax.grid(True, alpha=0.3)
    
    def _plot_geographic_supply_chain_impact(self, ax, economic_data: Dict[str, pd.DataFrame]):
        """Plot geographic distribution of supply chain impacts."""
        ax.set_title('Geographic Supply Chain Impact', fontweight='bold')
        
        from climate_framework import CONTINENTS
        continents = list(CONTINENTS.keys())
        layers = ['commodity_producer', 'intermediary_firm', 'final_goods_firm']
        
        impact_matrix = np.zeros((len(continents), len(layers)))
        
        # Count climate events by continent and affected layers
        for events in self.climate_framework.climate_events_history:
            if events:
                # Handle both old format (continent keys) and new format (rule-based events)
                affected_continents = set()
                
                for event_key, event_data in events.items():
                    if isinstance(event_data, dict) and 'continents' in event_data:
                        # New configurable shock format
                        event_continents = event_data['continents']
                        if 'all' in event_continents:
                            affected_continents.update(continents)
                        else:
                            affected_continents.update(event_continents)
                    elif event_key in continents:
                        # Old format where event key is continent name
                        affected_continents.add(event_key)
                
                # Count impacts for affected continents
                for continent in affected_continents:
                    if continent in continents:
                        continent_idx = continents.index(continent)
                        
                        # Check which layers are in this continent
                        for layer_idx, layer in enumerate(layers):
                            if layer in self.climate_framework.geographical_assignments:
                                assignments = self.climate_framework.geographical_assignments[layer]
                                for agent_id, info in assignments.items():
                                    if info['continent'] == continent:
                                        impact_matrix[continent_idx, layer_idx] += 1
                                        break  # Count once per layer per continent per event
        
        # Create heatmap
        im = ax.imshow(impact_matrix, cmap='Reds', aspect='auto')
        
        ax.set_xticks(range(len(layers)))
        ax.set_xticklabels([self.layer_mapping[layer].split(':')[1].strip() for layer in layers], rotation=45)
        ax.set_yticks(range(len(continents)))
        ax.set_yticklabels(continents)
        
        # Add text annotations
        for i in range(len(continents)):
            for j in range(len(layers)):
                if impact_matrix[i, j] > 0:
                    ax.text(j, i, f'{int(impact_matrix[i, j])}', 
                           ha='center', va='center', color='white', fontweight='bold')
        
        plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label='Climate Events')
    
    def _plot_consumer_impact(self, ax, economic_data: Dict[str, pd.DataFrame]):
        """Plot impact on consumers (households)."""
        ax.set_title('Consumer Impact', fontweight='bold')
        
        if 'household_purchases' in economic_data:
            df = economic_data['household_purchases']
            if 'round' in df.columns and 'final_good' in df.columns:
                round_summary = df.groupby('round')['final_good'].agg(['sum', 'mean']).reset_index()
                
                ax.plot(round_summary['round'], round_summary['sum'], 'g-o', 
                       linewidth=2, label='Total Consumption', markersize=6)
                
                # Add climate event markers
                for round_num, events in enumerate(self.climate_framework.climate_events_history):
                    if events:
                        ax.axvline(x=round_num, color='red', linestyle='--', alpha=0.5)
                
                ax.set_xlabel('Round')
                ax.set_ylabel('Total Final Goods Consumed')
                ax.legend()
        
        ax.grid(True, alpha=0.3)
    
    def _plot_multi_layer_stress_events(self, ax, economic_data: Dict[str, pd.DataFrame]):
        """Plot when multiple layers are stressed simultaneously."""
        ax.set_title('Multi-Layer Stress Events', fontweight='bold')
        
        # Analyze simultaneous stress across layers
        stress_data = []
        
        for round_num, events in enumerate(self.climate_framework.climate_events_history):
            if events:
                affected_layers = set()
                affected_continents = set()
                
                for event_key, event_data in events.items():
                    if isinstance(event_data, dict) and 'continents' in event_data:
                        # New configurable shock format
                        event_continents = event_data['continents']
                        event_agent_types = event_data.get('agent_types', [])
                        
                        # Get affected continents
                        if 'all' in event_continents:
                            from climate_framework import CONTINENTS
                            event_continents = list(CONTINENTS.keys())
                        
                        affected_continents.update(event_continents)
                        affected_layers.update(event_agent_types)
                    elif event_key in ['North America', 'Europe', 'Asia', 'South America', 'Africa']:
                        # Old format where event key is continent name
                        affected_continents.add(event_key)
                        
                        # Check which layers are affected by geography
                        for layer in ['commodity_producer', 'intermediary_firm', 'final_goods_firm']:
                            if layer in self.climate_framework.geographical_assignments:
                                assignments = self.climate_framework.geographical_assignments[layer]
                                for agent_id, info in assignments.items():
                                    if info['continent'] == event_key:
                                        affected_layers.add(layer)
                
                stress_data.append({
                    'round': round_num,
                    'num_layers': len(affected_layers),
                    'layers': list(affected_layers),
                    'continents': list(affected_continents)
                })
        
        if stress_data:
            # Create visualization of multi-layer events
            rounds = [d['round'] for d in stress_data]
            layer_counts = [d['num_layers'] for d in stress_data]
            
            colors = ['yellow', 'orange', 'red']
            bars = ax.bar(rounds, layer_counts, color=[colors[min(c-1, 2)] for c in layer_counts], alpha=0.7)
            
            ax.set_xlabel('Round')
            ax.set_ylabel('Number of Affected Layers')
            ax.set_title('Simultaneous Layer Stress')
            
            # Add labels
            for bar, count, round_num in zip(bars, layer_counts, rounds):
                height = bar.get_height()
                events = self.climate_framework.climate_events_history[round_num]
                
                # Count affected continents correctly
                affected_continents = set()
                for event_key, event_data in events.items():
                    if isinstance(event_data, dict) and 'continents' in event_data:
                        event_continents = event_data['continents']
                        if 'all' in event_continents:
                            from climate_framework import CONTINENTS
                            affected_continents.update(CONTINENTS.keys())
                        else:
                            affected_continents.update(event_continents)
                    elif event_key in ['North America', 'Europe', 'Asia', 'South America', 'Africa']:
                        affected_continents.add(event_key)
                
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                       f'{count}L\n{len(affected_continents)}C', ha='center', va='bottom', fontsize=8)
        
        ax.grid(True, alpha=0.3)
    
    def _plot_supply_chain_resilience(self, ax, economic_data: Dict[str, pd.DataFrame]):
        """Plot supply chain resilience metrics."""
        ax.set_title('Supply Chain Resilience', fontweight='bold')
        
        # Calculate recovery time after climate events
        recovery_data = []
        
        if 'final_goods_firm_production' in economic_data:
            df = economic_data['final_goods_firm_production']
            if 'round' in df.columns and 'final_good' in df.columns:
                round_summary = df.groupby('round')['final_good'].sum().reset_index()
                baseline = round_summary['final_good'].max()
                
                recovery_times = []
                in_stress = False
                stress_start = None
                
                for round_num, events in enumerate(self.climate_framework.climate_events_history):
                    if events and not in_stress:
                        in_stress = True
                        stress_start = round_num
                    elif not events and in_stress:
                        # Recovery period
                        if round_num < len(round_summary):
                            current_production = round_summary.iloc[round_num]['final_good']
                            if current_production >= baseline * 0.9:  # 90% recovery threshold
                                recovery_time = round_num - stress_start
                                recovery_times.append(recovery_time)
                        in_stress = False
                
                if recovery_times:
                    avg_recovery = np.mean(recovery_times)
                    ax.bar(['Average Recovery Time'], [avg_recovery], color='blue', alpha=0.7)
                    ax.set_ylabel('Rounds to Recovery')
                    ax.text(0, avg_recovery + 0.1, f'{avg_recovery:.1f}', 
                           ha='center', va='bottom', fontweight='bold')
                else:
                    ax.text(0.5, 0.5, 'No recovery data\navailable', 
                           ha='center', va='center', transform=ax.transAxes)
        
        ax.grid(True, alpha=0.3)
    
    def _plot_cross_layer_correlations(self, ax, economic_data: Dict[str, pd.DataFrame]):
        """Plot correlations between different supply chain layers."""
        ax.set_title('Cross-Layer Correlations', fontweight='bold')
        
        # Calculate correlations between layer productions
        correlations = {}
        production_data = {}
        
        for layer in ['commodity_producer', 'intermediary_firm', 'final_goods_firm']:
            production_key = f'{layer}_production'
            if production_key in economic_data:
                df = economic_data[production_key]
                good_col = self.production_goods[layer]
                
                if 'round' in df.columns and good_col in df.columns:
                    round_summary = df.groupby('round')[good_col].sum()
                    production_data[layer] = round_summary
        
        # Calculate correlation matrix
        if len(production_data) >= 2:
            layers = list(production_data.keys())
            n_layers = len(layers)
            corr_matrix = np.ones((n_layers, n_layers))
            
            for i in range(n_layers):
                for j in range(n_layers):
                    if i != j:
                        layer1_data = production_data[layers[i]]
                        layer2_data = production_data[layers[j]]
                        
                        # Align the data by round
                        common_rounds = layer1_data.index.intersection(layer2_data.index)
                        if len(common_rounds) > 1:
                            corr = np.corrcoef(layer1_data[common_rounds], layer2_data[common_rounds])[0, 1]
                            corr_matrix[i, j] = corr
            
            # Create heatmap
            im = ax.imshow(corr_matrix, cmap='RdBu_r', vmin=-1, vmax=1, aspect='auto')
            
            ax.set_xticks(range(n_layers))
            ax.set_xticklabels([self.layer_mapping[layer].split(':')[1].strip() for layer in layers], rotation=45)
            ax.set_yticks(range(n_layers))
            ax.set_yticklabels([self.layer_mapping[layer].split(':')[1].strip() for layer in layers])
            
            # Add correlation values
            for i in range(n_layers):
                for j in range(n_layers):
                    if not np.isnan(corr_matrix[i, j]):
                        color = 'white' if abs(corr_matrix[i, j]) > 0.5 else 'black'
                        ax.text(j, i, f'{corr_matrix[i, j]:.2f}', 
                               ha='center', va='center', color=color, fontweight='bold')
            
            plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label='Correlation')
        else:
            ax.text(0.5, 0.5, 'Insufficient data\nfor correlation analysis', 
                   ha='center', va='center', transform=ax.transAxes)
    
    def _plot_economic_summary_dashboard(self, ax, economic_data: Dict[str, pd.DataFrame]):
        """Create a summary dashboard of key economic metrics."""
        ax.set_title('Economic Summary Dashboard', fontweight='bold')
        
        # Calculate key metrics
        metrics = {}
        
        # Total production by layer
        for layer in ['commodity_producer', 'intermediary_firm', 'final_goods_firm']:
            production_key = f'{layer}_production'
            if production_key in economic_data:
                df = economic_data[production_key]
                good_col = self.production_goods[layer]
                
                if good_col in df.columns:
                    total_production = df[good_col].sum()
                    metrics[f'{self.layer_mapping[layer]} Total'] = total_production
        
        # Climate impact metrics
        total_events = sum(len(events) for events in self.climate_framework.climate_events_history)
        metrics['Total Climate Events'] = total_events
        metrics['Simulation Rounds'] = len(self.climate_framework.climate_events_history)
        
        # Consumer metrics
        if 'household_purchases' in economic_data:
            df = economic_data['household_purchases']
            if 'final_good' in df.columns:
                total_consumption = df['final_good'].sum()
                metrics['Total Consumption'] = total_consumption
        
        # Display metrics as text
        y_pos = 0.9
        for metric, value in metrics.items():
            if isinstance(value, float):
                text = f'{metric}: {value:.2f}'
            else:
                text = f'{metric}: {value}'
            
            ax.text(0.05, y_pos, text, transform=ax.transAxes, fontsize=11,
                   verticalalignment='top', fontfamily='monospace')
            y_pos -= 0.12
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
    
    def _convert_to_agent_groups_format(self):
        """Convert supply chain data for use with core climate framework."""
        # This is a placeholder - in practice, you'd pass actual agent groups
        # For now, we'll use the geographical assignments from the climate framework
        return {
            'commodity_producer': None,  # Placeholder
            'intermediary_firm': None,
            'final_goods_firm': None,
            'household': None
        } 