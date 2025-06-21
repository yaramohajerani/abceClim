"""
Generalized Agent Class
A flexible agent class that can be configured for different roles in the economic network.
"""

from abcEconomics import Agent
from typing import Dict, List, Any, Optional
import random
from abcEconomics.group import Chain


class GeneralizedAgent(Agent):
    """
    A generalized agent that can be configured for different economic roles.
    Supports production, consumption, trading, and climate stress effects.
    """
    
    def __init__(self, id, agent_parameters, simulation_parameters):
        super().__init__(id, agent_parameters, simulation_parameters)
        
        # Basic agent properties
        self.agent_type = agent_parameters.get('agent_type', 'generalized')
        self.agent_id = id
        
        # Financial properties - required
        if 'initial_money' not in agent_parameters:
            raise ValueError(f"Agent {self.agent_type} {id} missing required 'initial_money' parameter")
        self.initial_money = agent_parameters['initial_money']
        self.money = self.initial_money
        
        # Inventory
        self.initial_inventory = agent_parameters.get('initial_inventory', {})
        self.inventory = self.initial_inventory.copy()
        
        # Production configuration - required
        if 'production' not in agent_parameters:
            raise ValueError(f"Agent {self.agent_type} {id} missing required 'production' configuration")
        production_config = agent_parameters['production']
        
        if 'base_output_quantity' not in production_config:
            raise ValueError(f"Agent {self.agent_type} {id} missing required 'base_output_quantity' in production config")
        self.base_output_quantity = production_config['base_output_quantity']
        self.current_output_quantity = self.base_output_quantity
        
        if 'base_overhead' not in production_config:
            raise ValueError(f"Agent {self.agent_type} {id} missing required 'base_overhead' in production config")
        self.base_overhead = production_config['base_overhead']
        self.current_overhead = self.base_overhead
        
        if 'profit_margin' not in production_config:
            raise ValueError(f"Agent {self.agent_type} {id} missing required 'profit_margin' in production config")
        self.profit_margin = production_config['profit_margin']
        
        if 'inputs' not in production_config:
            raise ValueError(f"Agent {self.agent_type} {id} missing required 'inputs' in production config")
        self.production_inputs = production_config['inputs']
        
        if 'outputs' not in production_config:
            raise ValueError(f"Agent {self.agent_type} {id} missing required 'outputs' in production config")
        self.production_outputs = production_config['outputs']
        
        # Consumption configuration
        consumption_config = agent_parameters.get('consumption', {})
        self.consumption_preference = consumption_config.get('preference', 'output')
        self.consumption_fraction = consumption_config.get('consumption_fraction', 0.5)
        self.minimum_survival_consumption = consumption_config.get('minimum_survival_consumption', 0.1)
        
        # Labor configuration
        labor_config = agent_parameters.get('labor', {})
        self.labor_endowment = labor_config.get('endowment', 1.0)
        self.labor_wage = labor_config.get('wage', 1.0)
        self.labor_supplied = 0.0
        
        # Trading behavior
        self.trade_preference = agent_parameters.get('trade_preference', 1.0)
        self.risk_tolerance = agent_parameters.get('risk_tolerance', 1.0)
        self.debt_willingness = agent_parameters.get('debt_willingness', 1.0)
        
        # Network properties
        self.network_connectivity = agent_parameters.get('network_connectivity', 1.0)
        self.connected_agents = agent_parameters.get('connected_agents', [])
        
        # Climate stress tracking
        self.climate_stressed = False
        self.climate_vulnerability_productivity = agent_parameters.get('climate_vulnerability_productivity', 1.0)
        self.climate_vulnerability_overhead = agent_parameters.get('climate_vulnerability_overhead', 1.0)
        
        # Performance tracking
        self.total_production = 0.0
        self.total_consumption = 0.0
        self.total_trades = 0
        self.total_revenue = 0.0
        self.total_costs = 0.0
        self.wealth_history = []
        
        # Initialize inventory with initial values
        for good, quantity in self.initial_inventory.items():
            self.inventory[good] = quantity
    
    def init(self, **kwargs):
        # Avoid overwriting methods with config dicts
        forbidden = {"production", "consumption", "trading", "labor_supply"}
        for k, v in kwargs.items():
            if k in forbidden:
                print(f"Warning: Skipping attribute '{k}' to avoid shadowing a method.")
                continue
            setattr(self, k, v)
        # Optionally, add any post-initialization logic here
    
    def production(self):
        """Produce goods based on available inputs and production function"""
        if not self.production_inputs:
            return  # No production inputs defined
        
        # Check if we have enough inputs for production
        can_produce = True
        for input_good, required_amount in self.production_inputs.items():
            if self.inventory.get(input_good, 0) < required_amount:
                can_produce = False
                break
        
        if not can_produce:
            return
        
        # Consume inputs
        for input_good, required_amount in self.production_inputs.items():
            self.inventory[input_good] -= required_amount
        
        # Calculate production with overhead costs
        production_amount = self.current_output_quantity * (1 - self.current_overhead)
        
        # Add output to inventory
        for output_good in self.production_outputs:
            self.inventory[output_good] = self.inventory.get(output_good, 0) + production_amount
        
        self.total_production += production_amount
        self.total_costs += self.current_overhead * self.current_output_quantity
        
        print(f"{self.agent_type} {self.agent_id}: Produced {production_amount:.2f} units")
    
    def consumption(self):
        """Consume goods based on preferences and available resources"""
        if not self.consumption_preference:
            return  # No consumption preference defined
        
        # Calculate consumption budget
        consumption_budget = self.money * self.consumption_fraction
        
        # Try to buy preferred consumption good
        if self.consumption_preference in self.inventory:
            available_amount = self.inventory[self.consumption_preference]
            consumption_amount = min(available_amount, self.minimum_survival_consumption)
            
            if consumption_amount > 0:
                self.inventory[self.consumption_preference] -= consumption_amount
                self.total_consumption += consumption_amount
                print(f"{self.agent_type} {self.agent_id}: Consumed {consumption_amount:.2f} {self.consumption_preference}")
    
    def labor_supply(self):
        """Supply labor to the market"""
        if self.labor_endowment <= 0:
            return
        
        # Calculate labor supply based on preferences and market conditions
        labor_supply = self.labor_endowment * self.trade_preference
        
        # Offer labor for sale
        if labor_supply > 0:
            self.offer_labor(labor_supply, self.labor_wage)
    
    def trading(self):
        """Engage in trading with other agents"""
        if not self.connected_agents:
            return
        
        # Trade with connected agents based on network connectivity
        trade_probability = min(1.0, self.network_connectivity / len(self.connected_agents))
        
        for connected_agent in self.connected_agents:
            if random.random() < trade_probability:
                self._trade_with_agent(connected_agent)
    
    def _trade_with_agent(self, target_agent):
        """Trade with a specific agent"""
        # Simple trading logic - can be extended
        for good in self.inventory:
            if self.inventory[good] > 0:
                # Offer to sell excess inventory
                sell_amount = self.inventory[good] * 0.1  # Sell 10% of inventory
                if sell_amount > 0:
                    price = self._calculate_price(good)
                    self.sell(good, sell_amount, price, target_agent)
    
    def _calculate_price(self, good: str) -> float:
        """Calculate price for a good based on costs and profit margin"""
        base_cost = self.base_overhead
        return base_cost * (1 + self.profit_margin)
    
    def buy(self, good, quantity, price, seller):
        """Buy goods from another agent"""
        total_cost = quantity * price
        
        if self.money >= total_cost:
            self.money -= total_cost
            self.inventory[good] = self.inventory.get(good, 0) + quantity
            self.total_trades += 1
            print(f"{self.agent_type} {self.agent_id}: Bought {quantity:.2f} {good} for {total_cost:.2f}")
    
    def sell(self, good, quantity, price, buyer):
        """Sell goods to another agent"""
        if self.inventory.get(good, 0) >= quantity:
            total_revenue = quantity * price
            self.money += total_revenue
            self.inventory[good] -= quantity
            self.total_revenue += total_revenue
            self.total_trades += 1
            print(f"{self.agent_type} {self.agent_id}: Sold {quantity:.2f} {good} for {total_revenue:.2f}")
    
    def offer_labor(self, quantity, wage):
        """Offer labor for sale"""
        # This would typically interact with a labor market
        # For now, just track the offer
        self.labor_supplied = quantity
        print(f"{self.agent_type} {self.agent_id}: Offered {quantity:.2f} labor at wage {wage:.2f}")
    
    def apply_climate_stress(self, stress_factor: float, stress_target: str):
        """Apply climate stress to the agent"""
        self.climate_stressed = True
        
        if stress_target == 'productivity':
            # Apply vulnerability modifier
            modified_factor = stress_factor * self.climate_vulnerability_productivity
            self.current_output_quantity = self.base_output_quantity * modified_factor
            print(f"{self.agent_type} {self.agent_id}: Climate stress applied to productivity (factor: {modified_factor:.2f})")
        
        elif stress_target == 'overhead':
            # Apply vulnerability modifier
            modified_factor = stress_factor * self.climate_vulnerability_overhead
            self.current_overhead = self.base_overhead * modified_factor
            print(f"{self.agent_type} {self.agent_id}: Climate stress applied to overhead (factor: {modified_factor:.2f})")
    
    def reset_climate_stress(self):
        """Reset climate stress effects"""
        if self.climate_stressed:
            self.current_output_quantity = self.base_output_quantity
            self.current_overhead = self.base_overhead
            self.climate_stressed = False
            print(f"{self.agent_type} {self.agent_id}: Climate stress reset")
    
    def calculate_wealth(self) -> float:
        wealth = getattr(self, 'money', 0.0)
        if isinstance(wealth, Chain):
            print(f"Warning: calculate_wealth called on a group, returning 0.0")
            return 0.0
        try:
            return float(wealth)
        except Exception:
            return 0.0
    
    def record_performance(self):
        """Record current performance metrics"""
        self.round = getattr(self, 'time', None)  # Ensure round is set from simulation round
        wealth = self.calculate_wealth()
        self.wealth_history.append({
            'round': self.round,
            'wealth': wealth,
            'money': self.money,
            'total_production': self.total_production,
            'total_consumption': self.total_consumption,
            'total_trades': self.total_trades,
            'total_revenue': self.total_revenue,
            'total_costs': self.total_costs,
            'climate_stressed': self.climate_stressed
        })
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of agent performance"""
        return {
            'agent_type': self.agent_type,
            'agent_id': self.agent_id,
            'current_wealth': self.calculate_wealth(),
            'total_production': self.total_production,
            'total_consumption': self.total_consumption,
            'total_trades': self.total_trades,
            'total_revenue': self.total_revenue,
            'total_costs': self.total_costs,
            'climate_stressed': self.climate_stressed,
            'inventory': self.inventory.copy()
        } 