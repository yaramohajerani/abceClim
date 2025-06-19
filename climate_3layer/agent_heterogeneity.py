"""
Agent Heterogeneity System
Handles individual differences between agents including climate vulnerability,
cost structures, and behavioral characteristics.
"""

import random
import numpy as np
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass


@dataclass
class AgentCharacteristics:
    """Individual agent characteristics that create heterogeneity"""
    
    # Climate vulnerability (0.5 = half as vulnerable, 2.0 = twice as vulnerable)
    climate_vulnerability_productivity: float = 1.0
    climate_vulnerability_overhead: float = 1.0
    
    # Cost structure variations
    overhead_efficiency: float = 1.0  # Multiplier for overhead costs
    production_efficiency: float = 1.0  # Multiplier for production capacity
    
    # Behavioral characteristics
    risk_tolerance: float = 1.0  # 0.5 = very risk averse, 2.0 = very risk seeking
    debt_willingness: float = 1.0  # 0.5 = debt averse, 2.0 = debt seeking
    consumption_preference: float = 1.0  # 0.5 = frugal, 2.0 = spendthrift
    
    # Geographic adaptation (varies by continent)
    geographic_adaptation: Dict[str, float] = None
    
    def __post_init__(self):
        if self.geographic_adaptation is None:
            self.geographic_adaptation = {}


class HeterogeneityGenerator:
    """Generates heterogeneous characteristics for agents"""
    
    def __init__(self, seed: int = None):
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
    
    def generate_agent_characteristics(self, agent_type: str, agent_id: int, 
                                     continent: str, config: Dict[str, Any]) -> AgentCharacteristics:
        """
        Generate individual characteristics for an agent based on type and location.
        
        Args:
            agent_type: Type of agent (household, commodity_producer, etc.)
            agent_id: Unique identifier for the agent
            continent: Geographic location
            config: Configuration with heterogeneity parameters
            
        Returns:
            AgentCharacteristics object with individual traits
        """
        
        # Get heterogeneity configuration for this agent type
        heterogeneity_config = config.get('heterogeneity', {})
        
        # Base characteristics
        characteristics = AgentCharacteristics()
        
        # Generate climate vulnerability based on agent type and location
        characteristics.climate_vulnerability_productivity = self._generate_climate_vulnerability(
            agent_type, continent, heterogeneity_config, 'productivity'
        )
        characteristics.climate_vulnerability_overhead = self._generate_climate_vulnerability(
            agent_type, continent, heterogeneity_config, 'overhead'
        )
        
        # Generate cost structure variations
        characteristics.overhead_efficiency = self._generate_efficiency(
            heterogeneity_config, 'overhead_efficiency'
        )
        characteristics.production_efficiency = self._generate_efficiency(
            heterogeneity_config, 'production_efficiency'
        )
        
        # Generate behavioral characteristics
        characteristics.risk_tolerance = self._generate_behavioral_trait(
            heterogeneity_config, 'risk_tolerance'
        )
        characteristics.debt_willingness = self._generate_behavioral_trait(
            heterogeneity_config, 'debt_willingness'
        )
        characteristics.consumption_preference = self._generate_behavioral_trait(
            heterogeneity_config, 'consumption_preference'
        )
        
        # Generate geographic adaptation factors
        characteristics.geographic_adaptation = self._generate_geographic_adaptation(
            continent, heterogeneity_config
        )
        
        return characteristics
    
    def _generate_climate_vulnerability(self, agent_type: str, continent: str, 
                                      config: Dict, stress_type: str) -> float:
        """Generate climate vulnerability based on agent type and location"""
        
        # Base vulnerability by agent type
        base_vulnerability = {
            'commodity_producer': 1.2,  # Most vulnerable (agriculture, mining)
            'intermediary_firm': 1.0,   # Medium vulnerability
            'final_goods_firm': 0.8,    # Least vulnerable (indoor manufacturing)
            'household': 1.1            # Vulnerable to price shocks
        }.get(agent_type, 1.0)
        
        # Geographic vulnerability modifiers
        geographic_vulnerability = {
            'Africa': 1.3,      # High vulnerability (limited infrastructure)
            'Asia': 1.1,        # Medium-high vulnerability
            'South America': 1.2, # Medium-high vulnerability
            'North America': 0.9, # Lower vulnerability (better infrastructure)
            'Europe': 0.8,      # Lower vulnerability (good infrastructure)
            'Oceania': 1.0      # Medium vulnerability
        }.get(continent, 1.0)
        
        # Random variation (±20%)
        random_factor = random.uniform(0.8, 1.2)
        
        # Configuration overrides
        config_vulnerability = config.get(f'climate_vulnerability_{stress_type}', {})
        type_override = config_vulnerability.get(agent_type, base_vulnerability)
        continent_override = config_vulnerability.get(continent, geographic_vulnerability)
        
        # Combine factors
        vulnerability = type_override * continent_override * random_factor
        
        # Ensure reasonable bounds
        return max(0.1, min(3.0, vulnerability))
    
    def _generate_efficiency(self, config: Dict, efficiency_type: str) -> float:
        """Generate efficiency factors for overhead or production"""
        
        # Base efficiency with random variation
        base_efficiency = config.get(f'{efficiency_type}_base', 1.0)
        variation = config.get(f'{efficiency_type}_variation', 0.2)
        
        # Generate with normal distribution
        efficiency = np.random.normal(base_efficiency, variation)
        
        # Ensure reasonable bounds
        return max(0.5, min(2.0, efficiency))
    
    def _generate_behavioral_trait(self, config: Dict, trait_name: str) -> float:
        """Generate behavioral characteristics like risk tolerance"""
        
        # Base trait value
        base_trait = config.get(f'{trait_name}_base', 1.0)
        variation = config.get(f'{trait_name}_variation', 0.3)
        
        # Generate with normal distribution
        trait = np.random.normal(base_trait, variation)
        
        # Ensure reasonable bounds
        return max(0.3, min(2.5, trait))
    
    def _generate_geographic_adaptation(self, continent: str, config: Dict) -> Dict[str, float]:
        """Generate adaptation factors for different climate types"""
        
        # Base adaptation by continent
        base_adaptations = {
            'Africa': {'heat': 1.2, 'drought': 1.1, 'flood': 0.9},
            'Asia': {'heat': 1.1, 'drought': 1.0, 'flood': 1.2},
            'South America': {'heat': 1.0, 'drought': 0.9, 'flood': 1.1},
            'North America': {'heat': 0.9, 'drought': 1.0, 'flood': 1.0},
            'Europe': {'heat': 0.8, 'drought': 0.9, 'flood': 1.1},
            'Oceania': {'heat': 1.0, 'drought': 1.0, 'flood': 1.0}
        }.get(continent, {'heat': 1.0, 'drought': 1.0, 'flood': 1.0})
        
        # Add random variation
        adaptations = {}
        for climate_type, base_adaptation in base_adaptations.items():
            variation = random.uniform(0.8, 1.2)
            adaptations[climate_type] = base_adaptation * variation
        
        return adaptations


class HeterogeneityManager:
    """Manages agent heterogeneity throughout the simulation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.generator = HeterogeneityGenerator(config.get('random_seed', 42))
        self.agent_characteristics: Dict[Tuple[str, int], AgentCharacteristics] = {}
        self.agent_histories: Dict[Tuple[str, int], List[Dict]] = {}
    
    def initialize_agent(self, agent_type: str, agent_id: int, continent: str) -> AgentCharacteristics:
        """Initialize characteristics for a new agent"""
        
        agent_key = (agent_type, agent_id)
        
        # Generate characteristics
        characteristics = self.generator.generate_agent_characteristics(
            agent_type, agent_id, continent, self.config
        )
        
        # Store characteristics and initialize history
        self.agent_characteristics[agent_key] = characteristics
        self.agent_histories[agent_key] = []
        
        return characteristics
    
    def get_agent_characteristics(self, agent_type: str, agent_id: int) -> AgentCharacteristics:
        """Get characteristics for an existing agent"""
        return self.agent_characteristics.get((agent_type, agent_id))
    
    def apply_climate_stress_with_heterogeneity(self, agent_type: str, agent_id: int, 
                                              base_stress_factor: float, stress_target: str) -> float:
        """
        Apply climate stress considering agent's individual vulnerability
        
        Returns:
            Modified stress factor accounting for agent's characteristics
        """
        characteristics = self.get_agent_characteristics(agent_type, agent_id)
        if not characteristics:
            return base_stress_factor
        
        # Apply vulnerability multiplier
        if stress_target == 'productivity':
            vulnerability = characteristics.climate_vulnerability_productivity
        else:  # overhead
            vulnerability = characteristics.climate_vulnerability_overhead
        
        # Apply geographic adaptation if available
        geographic_modifier = 1.0
        if hasattr(characteristics, 'geographic_adaptation'):
            # This would need to be enhanced based on specific climate event types
            geographic_modifier = characteristics.geographic_adaptation.get('heat', 1.0)
        
        modified_stress = base_stress_factor * vulnerability * geographic_modifier
        
        # Record in history
        self._record_climate_event(agent_type, agent_id, {
            'event_type': 'climate_stress',
            'stress_target': stress_target,
            'base_stress_factor': base_stress_factor,
            'vulnerability': vulnerability,
            'geographic_modifier': geographic_modifier,
            'final_stress_factor': modified_stress
        })
        
        return modified_stress
    
    def apply_cost_modifications(self, agent_type: str, agent_id: int, 
                               base_overhead: float, base_production: float) -> Tuple[float, float]:
        """Apply cost structure modifications based on agent characteristics"""
        characteristics = self.get_agent_characteristics(agent_type, agent_id)
        if not characteristics:
            return base_overhead, base_production
        
        modified_overhead = base_overhead * characteristics.overhead_efficiency
        modified_production = base_production * characteristics.production_efficiency
        
        return modified_overhead, modified_production
    
    def get_behavioral_modifiers(self, agent_type: str, agent_id: int) -> Dict[str, float]:
        """Get behavioral modifiers for decision making"""
        characteristics = self.get_agent_characteristics(agent_type, agent_id)
        if not characteristics:
            return {'risk_tolerance': 1.0, 'debt_willingness': 1.0, 'consumption_preference': 1.0}
        
        return {
            'risk_tolerance': characteristics.risk_tolerance,
            'debt_willingness': characteristics.debt_willingness,
            'consumption_preference': characteristics.consumption_preference
        }
    
    def _record_climate_event(self, agent_type: str, agent_id: int, event_data: Dict):
        """Record climate events in agent history"""
        agent_key = (agent_type, agent_id)
        if agent_key in self.agent_histories:
            self.agent_histories[agent_key].append(event_data)
            
            # Trim history to memory length
            characteristics = self.get_agent_characteristics(agent_type, agent_id)
            if characteristics and len(self.agent_histories[agent_key]) > 5:
                self.agent_histories[agent_key] = self.agent_histories[agent_key][-5:]
    
    def export_heterogeneity_data(self, filename: str = "agent_heterogeneity.csv"):
        """Export agent characteristics for analysis"""
        try:
            import pandas as pd
            
            data = []
            for (agent_type, agent_id), characteristics in self.agent_characteristics.items():
                row = {
                    'agent_type': agent_type,
                    'agent_id': agent_id,
                    'climate_vulnerability_productivity': characteristics.climate_vulnerability_productivity,
                    'climate_vulnerability_overhead': characteristics.climate_vulnerability_overhead,
                    'overhead_efficiency': characteristics.overhead_efficiency,
                    'production_efficiency': characteristics.production_efficiency,
                    'risk_tolerance': characteristics.risk_tolerance,
                    'debt_willingness': characteristics.debt_willingness,
                    'consumption_preference': characteristics.consumption_preference
                }
                # Add geographic adaptations
                for climate_type, adaptation in characteristics.geographic_adaptation.items():
                    row[f'adaptation_{climate_type}'] = adaptation
                data.append(row)
            if data:
                df = pd.DataFrame(data)
                df.to_csv(filename, index=False)
                print(f"Agent heterogeneity data exported to '{filename}'")
                return df
            else:
                print("No heterogeneity data to export")
                return None
        except ImportError:
            # Fallback to CSV export without pandas
            print("Pandas not available, using basic CSV export...")
            return self._export_heterogeneity_data_basic(filename)
    
    def _export_heterogeneity_data_basic(self, filename: str):
        """Basic CSV export without pandas dependency"""
        import csv
        data = []
        for (agent_type, agent_id), characteristics in self.agent_characteristics.items():
            row = {
                'agent_type': agent_type,
                'agent_id': agent_id,
                'climate_vulnerability_productivity': characteristics.climate_vulnerability_productivity,
                'climate_vulnerability_overhead': characteristics.climate_vulnerability_overhead,
                'overhead_efficiency': characteristics.overhead_efficiency,
                'production_efficiency': characteristics.production_efficiency,
                'risk_tolerance': characteristics.risk_tolerance,
                'debt_willingness': characteristics.debt_willingness,
                'consumption_preference': characteristics.consumption_preference
            }
            # Add geographic adaptations
            for climate_type, adaptation in characteristics.geographic_adaptation.items():
                row[f'adaptation_{climate_type}'] = adaptation
            data.append(row)
        if data:
            with open(filename, 'w', newline='') as csvfile:
                fieldnames = data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            print(f"Agent heterogeneity data exported to '{filename}' (basic CSV)")
            return data
        else:
            print("No heterogeneity data to export")
            return None 