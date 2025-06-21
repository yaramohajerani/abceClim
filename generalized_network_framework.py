"""
Generalized Network Framework for Heterogeneous Agents
A flexible framework for creating complex economic networks with climate stress modeling.
"""

import random
import numpy as np
import networkx as nx
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, field
from abcEconomics import Simulation
import json
import os
from copy import copy


@dataclass
class AgentCharacteristics:
    """Individual agent characteristics for heterogeneity"""
    # Climate vulnerability
    climate_vulnerability_productivity: float = 1.0
    climate_vulnerability_overhead: float = 1.0
    
    # Efficiency factors
    production_efficiency: float = 1.0
    overhead_efficiency: float = 1.0
    
    # Behavioral traits
    risk_tolerance: float = 1.0
    debt_willingness: float = 1.0
    consumption_preference: float = 1.0
    
    # Network characteristics
    network_connectivity: float = 1.0
    trade_preference: float = 1.0
    
    # Geographic adaptation
    geographic_adaptation: Dict[str, float] = field(default_factory=dict)


@dataclass
class AgentType:
    """Definition of an agent type in the network"""
    name: str
    count: int
    base_production: float
    base_overhead: float
    profit_margin: float
    inputs: Dict[str, float]
    outputs: List[str]
    initial_money: float
    initial_inventory: Dict[str, float]
    geographical_distribution: List[str]
    heterogeneity_config: Dict[str, Any] = field(default_factory=dict)


class NetworkGenerator:
    """Generates complex randomized networks between agents"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.network_params = config.get('network', {})
        self.seed = config.get('random_seed', 42)
        if self.seed:
            random.seed(self.seed)
            np.random.seed(self.seed)
    
    def generate_network(self, agent_types: Dict[str, AgentType]) -> nx.DiGraph:
        """Generate a directed network connecting agents"""
        G = nx.DiGraph()
        
        # Add all agents as nodes
        agent_id = 0
        for agent_type_name, agent_type in agent_types.items():
            for i in range(agent_type.count):
                node_id = f"{agent_type_name}_{i}"
                G.add_node(node_id, 
                          agent_type=agent_type_name,
                          agent_id=i,
                          characteristics=None)  # Will be filled later
                agent_id += 1
        
        # Generate connections based on network configuration
        connection_type = self.network_params.get('connection_type', 'random')
        
        if connection_type == 'random':
            self._generate_random_connections(G, agent_types)
        elif connection_type == 'supply_chain':
            self._generate_supply_chain_connections(G, agent_types)
        elif connection_type == 'small_world':
            self._generate_small_world_connections(G, agent_types)
        elif connection_type == 'scale_free':
            self._generate_scale_free_connections(G, agent_types)
        
        return G
    
    def _generate_random_connections(self, G: nx.DiGraph, agent_types: Dict[str, AgentType]):
        """Generate random connections between agents"""
        nodes = list(G.nodes())
        connection_probability = self.network_params.get('connection_probability', 0.3)
        max_connections = self.network_params.get('max_connections_per_agent', 5)
        
        for node in nodes:
            # Determine number of connections for this agent
            num_connections = min(
                np.random.poisson(connection_probability * len(nodes)),
                max_connections
            )
            
            # Randomly select target nodes
            potential_targets = [n for n in nodes if n != node]
            if potential_targets:
                targets = random.sample(potential_targets, min(num_connections, len(potential_targets)))
                for target in targets:
                    G.add_edge(node, target, weight=random.uniform(0.1, 1.0))
    
    def _generate_supply_chain_connections(self, G: nx.DiGraph, agent_types: Dict[str, AgentType]):
        """Generate supply chain connections based on input/output relationships"""
        # Create connections based on who produces what others need
        for source_type_name, source_type in agent_types.items():
            for source_id in range(source_type.count):
                source_node = f"{source_type_name}_{source_id}"
                
                for target_type_name, target_type in agent_types.items():
                    if source_type_name == target_type_name:
                        continue
                    
                    # Check if target needs what source produces
                    for output in source_type.outputs:
                        if output in target_type.inputs:
                            # Connect with probability based on network density
                            connection_prob = self.network_params.get('supply_chain_probability', 0.7)
                            if random.random() < connection_prob:
                                for target_id in range(target_type.count):
                                    target_node = f"{target_type_name}_{target_id}"
                                    G.add_edge(source_node, target_node, 
                                             weight=target_type.inputs[output])
    
    def _generate_small_world_connections(self, G: nx.DiGraph, agent_types: Dict[str, AgentType]):
        """Generate small-world network connections"""
        nodes = list(G.nodes())
        k = self.network_params.get('small_world_k', 4)  # Average degree
        p = self.network_params.get('small_world_p', 0.1)  # Rewiring probability
        
        # Start with regular ring lattice
        for i, node in enumerate(nodes):
            for j in range(1, k // 2 + 1):
                target_idx = (i + j) % len(nodes)
                target = nodes[target_idx]
                G.add_edge(node, target, weight=random.uniform(0.1, 1.0))
        
        # Rewire edges with probability p
        edges_to_rewire = list(G.edges())
        for source, target in edges_to_rewire:
            if random.random() < p:
                G.remove_edge(source, target)
                new_target = random.choice([n for n in nodes if n != source])
                G.add_edge(source, new_target, weight=random.uniform(0.1, 1.0))
    
    def _generate_scale_free_connections(self, G: nx.DiGraph, agent_types: Dict[str, AgentType]):
        """Generate scale-free network connections using preferential attachment"""
        nodes = list(G.nodes())
        m = self.network_params.get('scale_free_m', 3)  # Edges to add per new node
        
        # Start with a small clique
        initial_nodes = nodes[:m+1]
        for i, node1 in enumerate(initial_nodes):
            for node2 in initial_nodes[i+1:]:
                G.add_edge(node1, node2, weight=random.uniform(0.1, 1.0))
        
        # Add remaining nodes with preferential attachment
        for node in nodes[m+1:]:
            # Calculate attachment probabilities based on degree
            degrees = dict(G.degree())
            total_degree = sum(degrees.values())
            
            if total_degree > 0:
                probabilities = [degrees.get(n, 0) / total_degree for n in nodes[:len(nodes)-len(nodes[m+1:])]]
                probabilities = [p / sum(probabilities) for p in probabilities]
                
                # Select m targets based on preferential attachment
                targets = np.random.choice(
                    nodes[:len(nodes)-len(nodes[m+1:])], 
                    size=min(m, len(probabilities)), 
                    p=probabilities, 
                    replace=False
                )
                
                for target in targets:
                    G.add_edge(node, target, weight=random.uniform(0.1, 1.0))


class HeterogeneityManager:
    """Manages agent heterogeneity throughout the simulation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.heterogeneity_config = config.get('heterogeneity', {})
        self.seed = config.get('random_seed', 42)
        if self.seed:
            random.seed(self.seed)
            np.random.seed(self.seed)
        
        self.agent_characteristics: Dict[Tuple[str, int], AgentCharacteristics] = {}
    
    def initialize_agent(self, agent_type: str, agent_id: int, continent: str) -> AgentCharacteristics:
        """Initialize characteristics for a new agent"""
        agent_key = (agent_type, agent_id)
        
        if agent_key in self.agent_characteristics:
            return self.agent_characteristics[agent_key]
        
        # Generate characteristics
        characteristics = AgentCharacteristics()
        
        # Climate vulnerability
        characteristics.climate_vulnerability_productivity = self._generate_climate_vulnerability(
            agent_type, continent, 'productivity'
        )
        characteristics.climate_vulnerability_overhead = self._generate_climate_vulnerability(
            agent_type, continent, 'overhead'
        )
        
        # Efficiency factors
        characteristics.production_efficiency = self._generate_efficiency('production_efficiency')
        characteristics.overhead_efficiency = self._generate_efficiency('overhead_efficiency')
        
        # Behavioral traits
        characteristics.risk_tolerance = self._generate_behavioral_trait('risk_tolerance')
        characteristics.debt_willingness = self._generate_behavioral_trait('debt_willingness')
        characteristics.consumption_preference = self._generate_behavioral_trait('consumption_preference')
        
        # Network characteristics
        characteristics.network_connectivity = self._generate_network_trait('network_connectivity')
        characteristics.trade_preference = self._generate_network_trait('trade_preference')
        
        # Geographic adaptation
        characteristics.geographic_adaptation = self._generate_geographic_adaptation(continent)
        
        self.agent_characteristics[agent_key] = characteristics
        return characteristics
    
    def _generate_climate_vulnerability(self, agent_type: str, continent: str, stress_type: str) -> float:
        """Generate climate vulnerability based on agent type and location"""
        config = self.heterogeneity_config.get(f'climate_vulnerability_{stress_type}', {})
        
        # Get base vulnerability
        base_vulnerability = config.get(agent_type, 1.0)
        continent_vulnerability = config.get(continent, 1.0)
        
        # Add random variation
        random_factor = random.uniform(0.8, 1.2)
        
        vulnerability = base_vulnerability * continent_vulnerability * random_factor
        return max(0.1, min(3.0, vulnerability))
    
    def _generate_efficiency(self, efficiency_type: str) -> float:
        """Generate efficiency factors"""
        base = self.heterogeneity_config.get(f'{efficiency_type}_base', 1.0)
        variation = self.heterogeneity_config.get(f'{efficiency_type}_variation', 0.2)
        
        efficiency = np.random.normal(base, variation)
        return max(0.5, min(2.0, efficiency))
    
    def _generate_behavioral_trait(self, trait_name: str) -> float:
        """Generate behavioral characteristics"""
        base = self.heterogeneity_config.get(f'{trait_name}_base', 1.0)
        variation = self.heterogeneity_config.get(f'{trait_name}_variation', 0.3)
        
        trait = np.random.normal(base, variation)
        return max(0.3, min(2.5, trait))
    
    def _generate_network_trait(self, trait_name: str) -> float:
        """Generate network-related characteristics"""
        base = self.heterogeneity_config.get(f'{trait_name}_base', 1.0)
        variation = self.heterogeneity_config.get(f'{trait_name}_variation', 0.2)
        
        trait = np.random.normal(base, variation)
        return max(0.5, min(2.0, trait))
    
    def _generate_geographic_adaptation(self, continent: str) -> Dict[str, float]:
        """Generate geographic adaptation factors"""
        adaptations = {}
        climate_types = ['heat', 'drought', 'flood', 'storm']
        
        for climate_type in climate_types:
            base_adaptation = self.heterogeneity_config.get(f'geographic_adaptation_{climate_type}', {}).get(continent, 1.0)
            variation = random.uniform(0.8, 1.2)
            adaptations[climate_type] = base_adaptation * variation
        
        return adaptations
    
    def apply_climate_stress_with_heterogeneity(self, agent_type: str, agent_id: int, 
                                              base_stress_factor: float, stress_target: str) -> float:
        """Apply climate stress with heterogeneity modifications"""
        agent_key = (agent_type, agent_id)
        if agent_key not in self.agent_characteristics:
            return base_stress_factor
        
        characteristics = self.agent_characteristics[agent_key]
        
        if stress_target == 'productivity':
            vulnerability = characteristics.climate_vulnerability_productivity
        else:  # overhead
            vulnerability = characteristics.climate_vulnerability_overhead
        
        # Modify stress factor based on vulnerability
        modified_stress_factor = base_stress_factor * vulnerability
        
        return modified_stress_factor
    
    def get_agent_characteristics(self, agent_type: str, agent_id: int) -> Optional[AgentCharacteristics]:
        """Get characteristics for an agent"""
        return self.agent_characteristics.get((agent_type, agent_id))


class GeneralizedNetworkFramework:
    """
    Generalized framework for creating complex economic networks with climate stress modeling.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.simulation_params = config.get('simulation', {})
        self.climate_params = config.get('climate', {})
        
        # Initialize components
        self.network_generator = NetworkGenerator(config)
        self.heterogeneity_manager = None
        if config.get('heterogeneity_enabled', True):
            self.heterogeneity_manager = HeterogeneityManager(config)
        
        # Network and agent storage
        self.network: Optional[nx.DiGraph] = None
        self.agent_types: Dict[str, AgentType] = {}
        self.agent_groups: Dict[str, Any] = {}
        self.geographical_assignments: Dict[str, Dict[int, Dict]] = {}
        self.agent_climate_data: Dict[Tuple[str, int], Dict] = {}
        self.climate_events_history: List[Dict] = []
        
        # Geographical distribution
        self.continents = ['North America', 'Europe', 'Asia', 'South America', 'Africa', 'Oceania']
        
        print(f"Generalized Network Framework initialized")
    
    def load_agent_types_from_config(self, config: Dict[str, Any]):
        """Load agent type definitions from configuration"""
        agents_config = config.get('agents', {})
        
        for agent_type_name, agent_config in agents_config.items():
            production_config = agent_config.get('production', {})
            agent_type = AgentType(
                name=agent_type_name,
                count=agent_config['count'],
                base_production=production_config.get('base_output_quantity', 1.0),
                base_overhead=production_config.get('base_overhead', 0.1),
                profit_margin=production_config.get('profit_margin', 0.1),
                inputs=production_config.get('inputs', {}),
                outputs=production_config.get('outputs', []),
                initial_money=agent_config.get('initial_money', 10.0),
                initial_inventory=agent_config.get('initial_inventory', {}),
                geographical_distribution=agent_config.get('geographical_distribution', ['all']),
                heterogeneity_config=agent_config.get('heterogeneity', {})
            )
            self.agent_types[agent_type_name] = agent_type
        
        print(f"Loaded {len(self.agent_types)} agent types from configuration")
    
    def assign_geographical_locations(self):
        """Assign agents to geographical locations"""
        for agent_type_name, agent_type in self.agent_types.items():
            self.geographical_assignments[agent_type_name] = {}
            
            configured_continents = agent_type.geographical_distribution
            if "all" in configured_continents:
                target_continents = copy(self.continents)
            else:
                target_continents = configured_continents
            
            for i in range(agent_type.count):
                continent = target_continents[i % len(target_continents)]
                self.geographical_assignments[agent_type_name][i] = {'continent': continent}
                
                # Initialize heterogeneity if enabled
                if self.heterogeneity_manager:
                    characteristics = self.heterogeneity_manager.initialize_agent(
                        agent_type_name, i, continent
                    )
                    print(f"    {agent_type_name} {i} assigned to {continent}")
                    print(f"      Climate vulnerability: productivity={characteristics.climate_vulnerability_productivity:.2f}, overhead={characteristics.climate_vulnerability_overhead:.2f}")
                else:
                    print(f"    {agent_type_name} {i} assigned to {continent}")
    
    def generate_network(self):
        """Generate the network structure"""
        self.network = self.network_generator.generate_network(self.agent_types)
        print(f"Generated network with {self.network.number_of_nodes()} nodes and {self.network.number_of_edges()} edges")
    
    def apply_climate_stress(self) -> Dict[str, str]:
        """Apply climate stress events to the network"""
        climate_events = {}
        
        # Apply chronic stress
        chronic_rules = self.climate_params.get('chronic_rules', [])
        if chronic_rules:
            print(f"\nApplying chronic stress...")
            self._apply_chronic_stress(chronic_rules)
        
        # Apply acute shocks
        shock_rules = self.climate_params.get('shock_rules', [])
        if shock_rules:
            print(f"\nChecking for acute climate shocks...")
            climate_events = self._apply_shock_rules(shock_rules)
        
        self.climate_events_history.append(climate_events)
        return climate_events
    
    def _apply_chronic_stress(self, chronic_rules: List[Dict]):
        """Apply chronic climate stress"""
        for rule in chronic_rules:
            overhead_factor = rule.get('overhead_stress_factor')
            productivity_factor = rule.get('productivity_stress_factor')
            
            if overhead_factor is not None:
                print(f"  Applying overhead chronic stress: {rule.get('name', 'unnamed')}")
                self._apply_stress_to_agents(rule['agent_types'], rule['continents'], 
                                           overhead_factor, 'chronic', 'overhead')
            
            if productivity_factor is not None:
                print(f"  Applying productivity chronic stress: {rule.get('name', 'unnamed')}")
                self._apply_stress_to_agents(rule['agent_types'], rule['continents'], 
                                           productivity_factor, 'chronic', 'productivity')
    
    def _apply_shock_rules(self, shock_rules: List[Dict]) -> Dict[str, str]:
        """Apply acute climate shocks"""
        climate_events = {}
        
        for rule in shock_rules:
            probability = rule['probability']
            
            if random.random() < probability:
                rule_name = rule.get('name', 'unnamed_shock')
                print(f"  CLIMATE SHOCK: {rule_name}")
                
                overhead_factor = rule.get('overhead_stress_factor')
                productivity_factor = rule.get('productivity_stress_factor')
                
                if overhead_factor:
                    self._apply_stress_to_agents(rule['agent_types'], rule['continents'], 
                                               overhead_factor, 'acute', 'overhead')
                
                if productivity_factor:
                    self._apply_stress_to_agents(rule['agent_types'], rule['continents'], 
                                               productivity_factor, 'acute', 'productivity')
                
                climate_events[rule_name] = {
                    'type': 'shock',
                    'agent_types': rule['agent_types'],
                    'continents': rule['continents'],
                    'overhead_stress_factor': overhead_factor,
                    'productivity_stress_factor': productivity_factor
                }
        
        return climate_events
    
    def _apply_stress_to_agents(self, target_agent_types: List[str], 
                              target_continents: List[str], 
                              stress_factor: float,
                              stress_type: str,
                              stress_target: str):
        """Apply stress to agents of specified types in specified continents"""
        for agent_type in target_agent_types:
            if agent_type not in self.agent_groups:
                continue
            
            agent_group = self.agent_groups[agent_type]
            agent_count = agent_group.num_agents
            
            # Access real agents through the scheduler's agent storage
            scheduler = agent_group._scheduler
            
            for i in range(agent_count):
                # Check if agent is in target continent
                agent_continent = self.geographical_assignments.get(agent_type, {}).get(i, {}).get('continent')
                if agent_continent not in target_continents:
                    continue
                
                # Get the real agent object from the scheduler
                agent_name = (agent_group.agent_name_prefix, i)
                
                if hasattr(scheduler, 'agents') and agent_name in scheduler.agents:
                    real_agent = scheduler.agents[agent_name]
                else:
                    # Fallback: try to get agent through group indexing
                    real_agent = agent_group[i]
                
                # Initialize climate data if needed
                self._initialize_agent_climate_data(agent_type, i, real_agent)
                
                # Apply stress
                if stress_type == 'chronic':
                    self._apply_chronic_stress_to_agent(agent_type, i, real_agent, stress_factor, stress_target)
                else:
                    self._apply_acute_stress_to_agent(agent_type, i, real_agent, stress_factor, stress_target)
    
    def _initialize_agent_climate_data(self, agent_type: str, agent_id: int, agent):
        """Initialize climate data for an agent if not already present"""
        agent_key = (agent_type, agent_id)
        
        if agent_key not in self.agent_climate_data:
            # Get base values from agent attributes
            # These should be regular values, not Action objects
            base_output = getattr(agent, 'base_output_quantity', 0.0)
            base_overhead = getattr(agent, 'base_overhead', 0.0)
            
            # Convert to float if they're not already
            try:
                base_output = float(base_output)
                base_overhead = float(base_overhead)
            except (ValueError, TypeError) as e:
                raise TypeError(f"Agent {agent_type} {agent_id} attribute conversion failed: {e}")
            
            # Apply heterogeneity modifications if enabled
            if self.heterogeneity_manager:
                characteristics = self.heterogeneity_manager.get_agent_characteristics(agent_type, agent_id)
                if characteristics:
                    base_output *= characteristics.production_efficiency
                    base_overhead *= characteristics.overhead_efficiency
            
            self.agent_climate_data[agent_key] = {
                'base_output_quantity': float(base_output),
                'base_overhead': float(base_overhead),
                'chronic_productivity_stress_accumulated': 1.0,
                'chronic_overhead_stress_accumulated': 1.0,
                'climate_stressed': False
            }
    
    def _apply_acute_stress_to_agent(self, agent_type: str, agent_id: int, agent, stress_factor: float, stress_target: str):
        """Apply acute climate stress to an agent"""
        agent_key = (agent_type, agent_id)
        if agent_key not in self.agent_climate_data:
            return
        
        # Apply heterogeneity modifications
        if self.heterogeneity_manager:
            modified_stress_factor = self.heterogeneity_manager.apply_climate_stress_with_heterogeneity(
                agent_type, agent_id, stress_factor, stress_target
            )
        else:
            modified_stress_factor = stress_factor
        
        climate_data = self.agent_climate_data[agent_key]
        climate_data['climate_stressed'] = True
        
        if stress_target == 'productivity':
            base_output = climate_data['base_output_quantity']
            chronic_accumulated = climate_data['chronic_productivity_stress_accumulated']
            new_output = base_output * modified_stress_factor * chronic_accumulated
            
            # Set the value directly on the agent attribute
            setattr(agent, 'current_output_quantity', new_output)
            print(f"      {agent_type} {agent_id}: CLIMATE STRESS! Production: {base_output:.2f} -> {new_output:.2f}")
        
        elif stress_target == 'overhead':
            base_overhead = climate_data['base_overhead']
            chronic_accumulated = climate_data['chronic_overhead_stress_accumulated']
            new_overhead = base_overhead * modified_stress_factor * chronic_accumulated
            
            # Set the value directly on the agent attribute
            setattr(agent, 'current_overhead', new_overhead)
            print(f"      {agent_type} {agent_id}: CLIMATE STRESS! Overhead: {base_overhead:.2f} -> {new_overhead:.2f}")
    
    def _apply_chronic_stress_to_agent(self, agent_type: str, agent_id: int, agent, stress_factor: float, stress_target: str):
        """Apply chronic climate stress to an agent"""
        agent_key = (agent_type, agent_id)
        if agent_key not in self.agent_climate_data:
            return
        
        # Apply heterogeneity modifications
        if self.heterogeneity_manager:
            modified_stress_factor = self.heterogeneity_manager.apply_climate_stress_with_heterogeneity(
                agent_type, agent_id, stress_factor, stress_target
            )
        else:
            modified_stress_factor = stress_factor
        
        climate_data = self.agent_climate_data[agent_key]
        
        if stress_target == 'productivity':
            climate_data['chronic_productivity_stress_accumulated'] *= modified_stress_factor
            
            base_output = climate_data['base_output_quantity']
            chronic_stress = climate_data['chronic_productivity_stress_accumulated']
            # Set the value directly on the agent attribute
            setattr(agent, 'current_output_quantity', base_output * chronic_stress)
            print(f"      {agent_type} {agent_id}: Chronic productivity stress applied (factor: {modified_stress_factor:.2f})")
        
        elif stress_target == 'overhead':
            climate_data['chronic_overhead_stress_accumulated'] *= modified_stress_factor
            
            base_overhead = climate_data['base_overhead']
            chronic_stress = climate_data['chronic_overhead_stress_accumulated']
            # Set the value directly on the agent attribute
            setattr(agent, 'current_overhead', base_overhead * chronic_stress)
            print(f"      {agent_type} {agent_id}: Chronic overhead stress applied (factor: {modified_stress_factor:.2f})")
    
    def reset_climate_stress(self):
        """Reset all acute climate stress effects"""
        print("  Resetting acute climate stress...")
        
        for agent_type, agent_group in self.agent_groups.items():
            agent_count = agent_group.num_agents
            scheduler = agent_group._scheduler
            
            for i in range(agent_count):
                agent_key = (agent_type, i)
                
                if agent_key in self.agent_climate_data:
                    climate_data = self.agent_climate_data[agent_key]
                    
                    if climate_data.get('climate_stressed', False):
                        climate_data['climate_stressed'] = False
                        
                        # Get the real agent object from the scheduler
                        agent_name = (agent_group.agent_name_prefix, i)
                        
                        if hasattr(scheduler, 'agents') and agent_name in scheduler.agents:
                            real_agent = scheduler.agents[agent_name]
                        else:
                            # Fallback: try to get agent through group indexing
                            real_agent = agent_group[i]
                        
                        base_output = climate_data['base_output_quantity']
                        chronic_accumulated = climate_data['chronic_productivity_stress_accumulated']
                        # Set the value directly on the agent attribute
                        setattr(real_agent, 'current_output_quantity', base_output * chronic_accumulated)
                        
                        base_overhead = climate_data['base_overhead']
                        chronic_accumulated = climate_data['chronic_overhead_stress_accumulated']
                        # Set the value directly on the agent attribute
                        setattr(real_agent, 'current_overhead', base_overhead * chronic_accumulated)
                        
                        print(f"      {agent_type} {i}: Climate stress cleared")
    
    def export_network_summary(self, simulation_path: str = None, filename: str = "network_summary.csv"):
        """Export network and climate summary data"""
        import pandas as pd
        
        summary_data = []
        
        # Add geographical assignments
        for agent_type, assignments in self.geographical_assignments.items():
            for agent_id, info in assignments.items():
                summary_data.append({
                    'agent_type': agent_type,
                    'agent_id': agent_id,
                    'continent': info['continent'],
                    'data_type': 'geographical_assignment'
                })
        
        # Add network connections
        if self.network:
            for source, target, data in self.network.edges(data=True):
                summary_data.append({
                    'agent_type': 'network_connection',
                    'source': source,
                    'target': target,
                    'weight': data.get('weight', 1.0),
                    'data_type': 'network_edge'
                })
        
        # Add climate events
        for round_num, events in enumerate(self.climate_events_history):
            for event_key, event_data in events.items():
                summary_data.append({
                    'agent_type': 'climate_event',
                    'agent_id': event_key,
                    'round': round_num,
                    'data_type': 'climate_shock',
                    'event_name': event_key,
                    'agent_types': ','.join(event_data['agent_types']) if 'agent_types' in event_data else '',
                    'productivity_stress_factor': event_data.get('productivity_stress_factor'),
                    'overhead_stress_factor': event_data.get('overhead_stress_factor')
                })
        
        if summary_data:
            df = pd.DataFrame(summary_data)
            
            if simulation_path:
                if not os.path.exists(simulation_path):
                    os.makedirs(simulation_path, exist_ok=True)
                save_path = os.path.join(simulation_path, filename)
            else:
                save_path = filename
            
            df.to_csv(save_path, index=False)
            print(f"Network summary exported to '{save_path}'")
            
            # Export heterogeneity data if available
            if self.heterogeneity_manager:
                heterogeneity_filename = filename.replace('.csv', '_heterogeneity.csv')
                if simulation_path:
                    heterogeneity_path = os.path.join(simulation_path, heterogeneity_filename)
                else:
                    heterogeneity_path = heterogeneity_filename
                self._export_heterogeneity_data(heterogeneity_path)
            
            return df
        else:
            print("No network data to export")
            return None
    
    def _export_heterogeneity_data(self, filename: str):
        """Export heterogeneity data"""
        import pandas as pd
        
        heterogeneity_data = []
        
        for (agent_type, agent_id), characteristics in self.heterogeneity_manager.agent_characteristics.items():
            heterogeneity_data.append({
                'agent_type': agent_type,
                'agent_id': agent_id,
                'climate_vulnerability_productivity': characteristics.climate_vulnerability_productivity,
                'climate_vulnerability_overhead': characteristics.climate_vulnerability_overhead,
                'production_efficiency': characteristics.production_efficiency,
                'overhead_efficiency': characteristics.overhead_efficiency,
                'risk_tolerance': characteristics.risk_tolerance,
                'debt_willingness': characteristics.debt_willingness,
                'consumption_preference': characteristics.consumption_preference,
                'network_connectivity': characteristics.network_connectivity,
                'trade_preference': characteristics.trade_preference
            })
        
        if heterogeneity_data:
            df = pd.DataFrame(heterogeneity_data)
            df.to_csv(filename, index=False)
            print(f"Heterogeneity data exported to '{filename}'")


def create_generalized_network_framework(config: Dict[str, Any]) -> GeneralizedNetworkFramework:
    """Create a new generalized network framework instance"""
    return GeneralizedNetworkFramework(config) 