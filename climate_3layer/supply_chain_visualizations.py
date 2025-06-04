"""
Custom Supply Chain Visualizations for 3-Layer Climate Model

This module provides specialized visualizations for the 3-layer supply chain model,
leveraging the core climate framework while adding supply chain-specific analysis.
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
from typing import Dict

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
        
        # Create the comprehensive analysis with updated layout
        fig = plt.figure(figsize=(24, 18))
        fig.suptitle(f'{model_name} - Supply Chain Climate Impact Analysis', 
                    fontsize=20, fontweight='bold')
        
        # Create a 4x4 grid for more detailed analysis
        # Row 1: Supply chain flow and pricing
        ax1 = plt.subplot(4, 4, (1, 2))
        self._plot_supply_chain_flow(ax1, economic_data)
        
        ax2 = plt.subplot(4, 4, (3, 4))
        self._plot_pricing_analysis(ax2, economic_data)
        
        # Row 2: Climate impact and overhead costs
        ax3 = plt.subplot(4, 4, (5, 6))
        self._plot_climate_impact_by_layer(ax3, economic_data)
        
        ax4 = plt.subplot(4, 4, (7, 8))
        self._plot_overhead_costs_analysis(ax4, economic_data)
        
        # Row 3: Operational metrics
        ax5 = plt.subplot(4, 4, 9)
        self._plot_production_efficiency(ax5, economic_data)
        
        ax6 = plt.subplot(4, 4, 10)
        self._plot_supply_chain_bottlenecks(ax6, economic_data)
        
        ax7 = plt.subplot(4, 4, 11)
        self._plot_wealth_and_debt_analysis(ax7, economic_data)
        
        ax8 = plt.subplot(4, 4, 12)
        self._plot_consumer_impact(ax8, economic_data)
        
        # Row 4: Geographic and resilience analysis
        ax9 = plt.subplot(4, 4, 13)
        self._plot_geographic_supply_chain_impact(ax9, economic_data)
        
        ax10 = plt.subplot(4, 4, 14)
        self._plot_multi_layer_stress_events(ax10, economic_data)
        
        ax11 = plt.subplot(4, 4, 15)
        self._plot_supply_chain_resilience(ax11, economic_data)
        
        ax12 = plt.subplot(4, 4, 16)
        self._plot_economic_summary_dashboard(ax12, economic_data)
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.97])
        
        # Save the comprehensive analysis
        filename = f'{model_name.lower().replace(" ", "_")}_supply_chain_analysis.png'
        save_path = os.path.join(simulation_path, filename)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        #plt.show()
        plt.close()
        print(f"Supply chain analysis saved to '{save_path}'")
        
        # Create additional inventory-focused analysis
        self._create_inventory_analysis(economic_data, simulation_path, model_name)
        
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
                            # Also store for overhead and pricing analysis
                            economic_data[f'{agent_type}_financial'] = df
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
                    
                    # Plot actual production
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
        ax.legend(loc='upper right', fontsize=9)
        ax.grid(True, alpha=0.3)
    
    def _plot_pricing_analysis(self, ax, economic_data: Dict[str, pd.DataFrame]):
        """Plot pricing evolution across supply chain layers over time."""
        ax.set_title('Price Evolution by Layer', fontweight='bold', fontsize=14)
        
        # Track prices from financial data
        layers = ['commodity_producer', 'intermediary_firm', 'final_goods_firm']
        colors = ['brown', 'orange', 'green']
        price_columns = ['commodity_price', 'intermediate_good_price', 'final_good_price']
        
        for i, layer in enumerate(layers):
            financial_key = f'{layer}_financial'
            if financial_key in economic_data:
                df = economic_data[financial_key]
                
                # Look for price column - could be named differently
                possible_price_cols = [price_columns[i], 'price', f'{self.production_goods[layer]}_price']
                price_col = None
                
                for col in possible_price_cols:
                    if col in df.columns:
                        price_col = col
                        break
                
                if price_col and 'round' in df.columns:
                    round_summary = df.groupby('round')[price_col].mean().reset_index()
                    
                    ax.plot(round_summary['round'], round_summary[price_col], 
                           color=colors[i], linewidth=3, marker='o', markersize=8,
                           label=f'{self.layer_mapping[layer]} Price', alpha=0.8)
        
        # Highlight climate events and their pricing impact
        for round_num, events in enumerate(self.climate_framework.climate_events_history):
            if events:
                ax.axvline(x=round_num, color='red', linestyle='--', alpha=0.7, linewidth=2)
                ax.text(round_num, ax.get_ylim()[1] * 0.9, 'Climate\nEvent', 
                       ha='center', va='top', fontsize=9, color='red', fontweight='bold')
        
        ax.set_xlabel('Round')
        ax.set_ylabel('Price ($)')
        ax.legend(loc='upper left', fontsize=9)
        ax.grid(True, alpha=0.3)
    
    def _plot_overhead_costs_analysis(self, ax, economic_data: Dict[str, pd.DataFrame]):
        """Plot overhead costs evolution and climate impact."""
        ax.set_title('Overhead Costs by Layer', fontweight='bold', fontsize=14)
        
        # Track overhead costs from financial data
        layers = ['commodity_producer', 'intermediary_firm', 'final_goods_firm']
        colors = ['brown', 'orange', 'green']
        
        for i, layer in enumerate(layers):
            financial_key = f'{layer}_financial'
            if financial_key in economic_data:
                df = economic_data[financial_key]
                
                # Look for overhead columns
                overhead_cols = ['current_overhead', 'overhead', 'overhead_cost']
                base_overhead_cols = ['base_overhead', 'base_overhead_cost']
                
                overhead_col = None
                base_overhead_col = None
                
                for col in overhead_cols:
                    if col in df.columns:
                        overhead_col = col
                        break
                
                for col in base_overhead_cols:
                    if col in df.columns:
                        base_overhead_col = col
                        break
                
                if overhead_col and 'round' in df.columns:
                    round_summary = df.groupby('round')[overhead_col].mean().reset_index()
                    
                    # Plot current overhead
                    ax.plot(round_summary['round'], round_summary[overhead_col], 
                           color=colors[i], linewidth=3, marker='o', markersize=6,
                           label=f'{self.layer_mapping[layer]} Overhead', alpha=0.8)
                    
                    # Plot base overhead as dashed line if available
                    if base_overhead_col:
                        base_summary = df.groupby('round')[base_overhead_col].mean().reset_index()
                        ax.plot(base_summary['round'], base_summary[base_overhead_col], 
                               color=colors[i], linewidth=2, linestyle='--', alpha=0.6,
                               label=f'{self.layer_mapping[layer]} Base')
        
        # Highlight climate events
        for round_num, events in enumerate(self.climate_framework.climate_events_history):
            if events:
                ax.axvline(x=round_num, color='red', linestyle='--', alpha=0.7, linewidth=2)
                ax.text(round_num, ax.get_ylim()[1] * 0.95, '🌪️', 
                       ha='center', va='top', fontsize=12, color='red')
        
        ax.set_xlabel('Round')
        ax.set_ylabel('Overhead Cost ($)')
        ax.legend(loc='upper left', fontsize=8)
        ax.grid(True, alpha=0.3)
    
    def _plot_wealth_and_debt_analysis(self, ax, economic_data: Dict[str, pd.DataFrame]):
        """Plot wealth and debt analysis across agents."""
        ax.set_title('Wealth & Debt Analysis', fontweight='bold')
        
        # Household wealth and debt
        if 'household_consumption' in economic_data:
            df = economic_data['household_consumption']
            
            if 'round' in df.columns and 'money' in df.columns:
                wealth_summary = df.groupby('round')['money'].agg(['mean', 'std']).reset_index()
                
                # Plot wealth
                ax.plot(wealth_summary['round'], wealth_summary['mean'], 
                       'g-o', linewidth=2, markersize=6, label='Household Wealth', alpha=0.8)
                
                # Add error bars for wealth distribution
                ax.fill_between(wealth_summary['round'], 
                               wealth_summary['mean'] - wealth_summary['std'],
                               wealth_summary['mean'] + wealth_summary['std'],
                               alpha=0.2, color='green')
                
                # Plot debt if available
                if 'debt' in df.columns:
                    debt_summary = df.groupby('round')['debt'].mean().reset_index()
                    ax.plot(debt_summary['round'], debt_summary['debt'], 
                           'r-s', linewidth=2, markersize=6, label='Household Debt', alpha=0.8)
        
        # Firm financial health
        for layer in ['commodity_producer', 'intermediary_firm', 'final_goods_firm']:
            financial_key = f'{layer}_financial'
            if financial_key in economic_data:
                df = economic_data[financial_key]
                
                if 'round' in df.columns and 'money' in df.columns:
                    money_summary = df.groupby('round')['money'].mean().reset_index()
                    
                    # Simple line for firm money (avoid overcrowding)
                    if layer == 'final_goods_firm':  # Only show final goods firms to avoid clutter
                        ax.plot(money_summary['round'], money_summary['money'], 
                               'b--', linewidth=1, alpha=0.6, label='Final Firms Wealth')
        
        # Highlight climate events
        for round_num, events in enumerate(self.climate_framework.climate_events_history):
            if events:
                ax.axvline(x=round_num, color='red', linestyle='--', alpha=0.5)
        
        ax.set_xlabel('Round')
        ax.set_ylabel('Amount ($)')
        ax.legend(loc='upper left', fontsize=9)
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
        ax.set_title('Production Trends', fontweight='bold')
        
        # Plot production trends instead of efficiency metrics
        if 'commodity_producer_production' in economic_data:
            df = economic_data['commodity_producer_production']
            if 'round' in df.columns and 'commodity' in df.columns:
                round_summary = df.groupby('round')['commodity'].agg(['sum', 'mean']).reset_index()
                
                ax.plot(round_summary['round'], round_summary['sum'], 'b-o', linewidth=2, markersize=6, label='Total Production')
                ax.plot(round_summary['round'], round_summary['mean'], 'r-s', linewidth=2, markersize=6, label='Avg per Producer')
                ax.set_ylabel('Production')
                ax.set_xlabel('Round')
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
        
        # Overhead cost metrics
        total_overhead = 0
        for layer in ['commodity_producer', 'intermediary_firm', 'final_goods_firm']:
            financial_key = f'{layer}_financial'
            if financial_key in economic_data:
                df = economic_data[financial_key]
                
                # Look for overhead columns
                overhead_cols = ['current_overhead', 'overhead', 'overhead_cost']
                for col in overhead_cols:
                    if col in df.columns:
                        layer_overhead = df[col].sum()
                        total_overhead += layer_overhead
                        metrics[f'{self.layer_mapping[layer]} Overhead'] = layer_overhead
                        break
        
        if total_overhead > 0:
            metrics['Total Overhead Costs'] = total_overhead
        
        # Average pricing by layer
        for layer in ['commodity_producer', 'intermediary_firm', 'final_goods_firm']:
            financial_key = f'{layer}_financial'
            if financial_key in economic_data:
                df = economic_data[financial_key]
                
                # Look for price columns
                price_cols = ['price', f'{self.production_goods[layer]}_price']
                for col in price_cols:
                    if col in df.columns:
                        avg_price = df[col].mean()
                        metrics[f'{self.layer_mapping[layer]} Avg Price'] = avg_price
                        break
        
        # Financial health metrics
        if 'household_consumption' in economic_data:
            df = economic_data['household_consumption']
            if 'money' in df.columns:
                avg_household_wealth = df['money'].mean()
                metrics['Avg Household Wealth'] = avg_household_wealth
                
            if 'debt' in df.columns:
                total_household_debt = df['debt'].sum()
                if total_household_debt > 0:
                    metrics['Total Household Debt'] = total_household_debt
        
        # Climate impact metrics
        total_events = sum(len(events) for events in self.climate_framework.climate_events_history)
        metrics['Total Climate Events'] = total_events
        metrics['Simulation Rounds'] = len(self.climate_framework.climate_events_history)
        
        # Consumer metrics
        if 'household_consumption' in economic_data:
            df = economic_data['household_consumption']
            if 'consumption' in df.columns:
                total_consumption = df['consumption'].sum()
                metrics['Total Consumption'] = total_consumption
        
        # Display metrics as text with better formatting
        y_pos = 0.95
        column_break = len(metrics) // 2  # Split into two columns
        
        for i, (metric, value) in enumerate(metrics.items()):
            x_pos = 0.05 if i < column_break else 0.55
            current_y = y_pos - (i % column_break) * 0.08
            
            if isinstance(value, float):
                if 'Price' in metric or 'Wealth' in metric or 'Debt' in metric or 'Overhead' in metric:
                    text = f'{metric}: ${value:.2f}'
                else:
                    text = f'{metric}: {value:.2f}'
            else:
                text = f'{metric}: {value}'
            
            ax.text(x_pos, current_y, text, transform=ax.transAxes, fontsize=10,
                   verticalalignment='top', fontfamily='monospace')
        
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

    def _create_inventory_analysis(self, economic_data: Dict[str, pd.DataFrame], simulation_path: str, model_name: str):
        """Create additional inventory-focused analysis."""
        print("🏭 Creating inventory analysis...")
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 10))
        fig.suptitle(f'{model_name} - Inventory Analysis', fontsize=16, fontweight='bold')
        
        # Plot 1: Inventory levels over time
        ax1.set_title('Inventory Levels Over Time', fontweight='bold')
        layers = ['commodity_producer', 'intermediary_firm', 'final_goods_firm']
        colors = ['brown', 'orange', 'green']
        
        for i, layer in enumerate(layers):
            production_key = f'{layer}_production'
            if production_key in economic_data:
                df = economic_data[production_key]
                good_col = self.production_goods[layer]
                
                if 'round' in df.columns and good_col in df.columns:
                    # Inventory is the cumulative stock at end of each round
                    round_summary = df.groupby('round')[good_col].sum().reset_index()
                    ax1.plot(round_summary['round'], round_summary[good_col], 
                           color=colors[i], linewidth=2, marker='o', markersize=6,
                           label=f'{self.layer_mapping[layer]} Inventory', alpha=0.8)
        
        ax1.set_xlabel('Round')
        ax1.set_ylabel('Inventory Level')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Inventory turnover analysis (if we have sales data)
        ax2.set_title('Inventory Turnover Analysis', fontweight='bold')
        
        for i, layer in enumerate(layers):
            production_key = f'{layer}_production'
            sales_key = f'{layer}_sales'
            
            if production_key in economic_data and sales_key in economic_data:
                inventory_df = economic_data[production_key]
                sales_df = economic_data[sales_key]
                good_col = self.production_goods[layer]
                
                if ('round' in inventory_df.columns and good_col in inventory_df.columns and
                    'round' in sales_df.columns and good_col in sales_df.columns):
                    
                    inventory_summary = inventory_df.groupby('round')[good_col].sum().reset_index()
                    sales_summary = sales_df.groupby('round')[good_col].sum().reset_index()
                    
                    # Calculate turnover ratio (sales/inventory)
                    merged = inventory_summary.merge(sales_summary, on='round', suffixes=('_inv', '_sales'))
                    merged['turnover'] = merged[f'{good_col}_sales'] / (merged[f'{good_col}_inv'] + 0.01)  # Avoid division by zero
                    
                    ax2.plot(merged['round'], merged['turnover'], 
                           color=colors[i], linewidth=2, marker='s', markersize=6,
                           label=f'{self.layer_mapping[layer]} Turnover', alpha=0.8)
        
        ax2.set_xlabel('Round')
        ax2.set_ylabel('Turnover Ratio (Sales/Inventory)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Inventory buildup during climate events
        ax3.set_title('Inventory During Climate Events', fontweight='bold')
        
        # Identify climate event rounds
        climate_rounds = []
        for round_num, events in enumerate(self.climate_framework.climate_events_history):
            if events:
                climate_rounds.append(round_num)
        
        if climate_rounds and 'final_goods_firm_production' in economic_data:
            df = economic_data['final_goods_firm_production']
            if 'round' in df.columns and 'final_good' in df.columns:
                round_summary = df.groupby('round')['final_good'].sum().reset_index()
                
                # Plot inventory levels with climate events highlighted
                ax3.plot(round_summary['round'], round_summary['final_good'], 
                        'g-o', linewidth=2, markersize=4, label='Final Goods Inventory')
                
                # Highlight climate event rounds
                for climate_round in climate_rounds:
                    if climate_round < len(round_summary):
                        ax3.axvline(x=climate_round, color='red', linestyle='--', alpha=0.7)
                        inventory_at_event = round_summary.iloc[climate_round]['final_good']
                        ax3.scatter(climate_round, inventory_at_event, color='red', s=100, zorder=5)
                
                ax3.set_xlabel('Round')
                ax3.set_ylabel('Final Goods Inventory')
                ax3.legend()
        
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Inventory efficiency metrics
        ax4.set_title('Inventory Efficiency Metrics', fontweight='bold')
        
        # Calculate inventory-to-production ratios
        efficiency_data = []
        
        for layer in layers:
            production_key = f'{layer}_production'
            if production_key in economic_data:
                df = economic_data[production_key]
                good_col = self.production_goods[layer]
                
                if 'round' in df.columns and good_col in df.columns:
                    round_summary = df.groupby('round')[good_col].sum()
                    
                    # Calculate efficiency as inverse of inventory accumulation rate
                    if len(round_summary) > 1:
                        inventory_growth_rate = round_summary.pct_change().mean()
                        efficiency_data.append({
                            'Layer': self.layer_mapping[layer].split(':')[1].strip(),
                            'Growth_Rate': inventory_growth_rate
                        })
        
        if efficiency_data:
            layers_names = [d['Layer'] for d in efficiency_data]
            growth_rates = [d['Growth_Rate'] for d in efficiency_data]
            colors_subset = colors[:len(layers_names)]
            
            bars = ax4.bar(layers_names, growth_rates, color=colors_subset, alpha=0.7)
            ax4.set_ylabel('Inventory Growth Rate')
            ax4.set_title('Inventory Accumulation by Layer')
            
            # Add value labels on bars
            for bar, rate in zip(bars, growth_rates):
                height = bar.get_height()
                ax4.text(bar.get_x() + bar.get_width()/2., height + (max(growth_rates) * 0.01),
                        f'{rate:.3f}', ha='center', va='bottom')
        
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save the inventory analysis
        inventory_filename = f'{model_name.lower().replace(" ", "_")}_inventory_analysis.png'
        inventory_save_path = os.path.join(simulation_path, inventory_filename)
        plt.savefig(inventory_save_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Inventory analysis saved to '{inventory_save_path}'") 