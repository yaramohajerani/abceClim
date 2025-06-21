"""
Generalized Agent Class
A flexible agent class that can be configured for different roles in the economic network.
"""

from abcEconomics import Agent
from typing import Dict, Any
import random
from abcEconomics.group import Chain
from abcEconomics.contracts.contracting import Contracting, Contracts
from collections import defaultdict


class GeneralizedAgent(Agent, Contracting):
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
        prod_outputs_cfg = production_config['outputs']
        # Convert outputs list -> dict mapping each good to base_output_quantity
        if isinstance(prod_outputs_cfg, list):
            self.production_outputs = {good: self.base_output_quantity for good in prod_outputs_cfg}
        elif isinstance(prod_outputs_cfg, dict):
            self.production_outputs = prod_outputs_cfg
        else:
            raise ValueError("production.outputs must be list or dict")
        
        # Consumption configuration
        consumption_config = agent_parameters.get('consumption', {})
        self.consumption_preference = consumption_config.get('preference', 'output')
        self.consumption_fraction = consumption_config.get('consumption_fraction', 0.5)
        self.minimum_survival_consumption = consumption_config.get('minimum_survival_consumption', 0.1)
        self.consumption_budget_scaling = consumption_config.get('budget_scaling', 0.1)
        
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
        
        # Alias required by abcEconomics Contracting / Trader internals
        # Map _haves to underlying inventory dict so deliver/pay functions work
        if not hasattr(self, '_haves'):
            # Basic fallback: mirror our simple inventory dictionary
            self._haves = self.inventory
        # Ensure we at least have money attribute in _haves for payments
        if 'money' not in self._haves:
            self._haves['money'] = self.money
        
        # Initialize contract bookkeeping if Contracting mixin is present
        if hasattr(self, '_add_contracts_list'):
            try:
                self._add_contracts_list()
                # Ensure internal contract offer structures exist
                if not hasattr(self, '_contract_offers'):
                    self._contract_offers = defaultdict(list)
                if not hasattr(self, '_contract_offers_made'):
                    self._contract_offers_made = {}
                # self.contracts is created by _add_contracts_list(); extend with helper dicts if missing
                if hasattr(self, 'contracts') and isinstance(self.contracts, Contracts):
                    if not hasattr(self.contracts, '_contracts_deliver'):
                        self.contracts._contracts_deliver = defaultdict(dict)
                    if not hasattr(self.contracts, '_contracts_pay'):
                        self.contracts._contracts_pay = defaultdict(dict)
                # Provide _send fallback expected by abcEconomics internals (expects 4 args)
                if not hasattr(self, '_send'):
                    self._send = lambda g, i, topic, msg: self.send((g, i), topic, msg)
            except Exception as e:
                print(f"DEBUG: Failed to initialize contracts list for {self.group} {self.agent_id}: {e}")
        
        # Initialise round counter (abcEconomics Contracting expects self.round)
        self.round = 0
    
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
        """Produce goods based on production inputs and outputs"""
        if not self.production_inputs:
            return
        
        # Check if we have enough inputs for production
        can_produce = True
        for good, required in self.production_inputs.items():
            available = self.inventory.get(good, 0)
            if available < required:
                can_produce = False
                print(f"DEBUG: {self.agent_type} {self.agent_id} cannot produce - needs {required} {good}, has {available}")
                break
        
        if not can_produce:
            return
        
        print(f"DEBUG: {self.agent_type} {self.agent_id} starting production")
        # Consume inputs
        for good, required in self.production_inputs.items():
            self.inventory[good] -= required
            print(f"DEBUG: {self.agent_type} {self.agent_id} consumed {required} {good}")
        
        # Produce outputs
        produced_amount = 0.0
        for good, amount in self.production_outputs.items():
            self.inventory[good] = self.inventory.get(good, 0) + amount
            produced_amount += amount
            print(f"DEBUG: {self.agent_type} {self.agent_id} produced {amount} {good}")
        
        # Deduct overhead costs
        if self.money >= self.current_overhead:
            self.money -= self.current_overhead
            self.total_costs += self.current_overhead
        
        # Record production
        self.total_production += produced_amount
    
    def consumption(self):
        """Consume goods based on preferences and available resources"""
        if not self.consumption_preference:
            return  # No consumption preference defined
        
        # Calculate consumption budget (as a fraction of wealth)
        consumption_budget = self.money * self.consumption_fraction
        
        # Try to consume preferred consumption good
        if self.consumption_preference in self.inventory:
            available_amount = self.inventory[self.consumption_preference]
            
            # Calculate desired consumption based on budget and preferences
            # Higher budget = higher desired consumption (up to a reasonable limit)
            desired_consumption = min(available_amount, self.minimum_survival_consumption + (consumption_budget * self.consumption_budget_scaling))
            
            # Consume the desired amount
            consumption_amount = min(available_amount, desired_consumption)
            
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
        
        # Regenerate labor endowment each round (treat labor as a service)
        if labor_supply > 0:
            # Add labor units to inventory for potential contracting
            self.inventory['labor'] = self.inventory.get('labor', 0) + labor_supply
            if isinstance(self._haves, dict):
                self._haves['labor'] = self.inventory['labor']
            # Offer labor (debug / placeholder)
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
        # Check if we have goods to sell
        for good in self.inventory:
            if self.inventory[good] > 0 and good != 'labor':  # Don't trade labor through this method
                # Offer to sell excess inventory
                sell_amount = min(self.inventory[good] * 0.3, self.inventory[good])  # Sell up to 30% of inventory
                if sell_amount > 0:
                    price = self._calculate_price(good)
                    
                    # Check if target agent wants to buy
                    if hasattr(target_agent, 'money') and target_agent.money >= sell_amount * price:
                        # Check if target agent needs this good
                        if self._agent_needs_good(target_agent, good):
                            self.sell(good, sell_amount, price, target_agent)
                            target_agent.buy(good, sell_amount, price, self)
    
    def _agent_needs_good(self, agent, good):
        """Check if an agent needs a particular good"""
        # Check if it's a consumption preference
        if hasattr(agent, 'consumption_preference') and agent.consumption_preference == good:
            return True
        
        # Check if it's a production input
        if hasattr(agent, 'production_inputs') and good in agent.production_inputs:
            current_amount = agent.inventory.get(good, 0)
            required_amount = agent.production_inputs[good]
            return current_amount < required_amount
        
        return False
    
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
    
    def labor_contracting(self):
        """Handle labor contracting between producers/intermediaries and consumers"""
        # Debug: show connected consumer count
        if hasattr(self, 'connected_agents'):
            consumer_count_debug = sum(1 for a in self.connected_agents if getattr(a, 'group', None) == 'consumer')
        else:
            consumer_count_debug = 0
        # Only print for producers/intermediaries on first round maybe
        if self.time == 0 and self.group in ['producer', 'intermediary']:
            print(f"DEBUG-CONTRACT {self.group} {self.agent_id}: Connected consumers = {consumer_count_debug}")
        contract_actions = []
        
        # Producers/intermediaries request labor contracts
        if self.group in ['producer', 'intermediary']:
            if not self.production_inputs or 'labor' not in self.production_inputs:
                return
            
            required_labor = self.production_inputs['labor']
            current_labor = self.inventory.get('labor', 0)
            needed_labor = max(0, required_labor - current_labor)
            
            if needed_labor > 0 and hasattr(self, 'connected_agents') and self.connected_agents:
                # Find consumer agents among connected agents
                consumers = [agent for agent in self.connected_agents if getattr(agent, 'group', None) == 'consumer']
                
                for consumer in consumers:
                    if needed_labor <= 0:
                        break

                    available_labor = consumer.inventory.get('labor', 0)
                    if available_labor <= 0:
                        continue

                    transfer_qty = min(needed_labor, available_labor)

                    # Transfer money from producer to consumer
                    payment = transfer_qty * self.labor_wage
                    if self.money < payment:
                        continue  # not enough funds

                    self.money -= payment
                    consumer.money += payment

                    # Transfer labor from consumer to producer
                    consumer.inventory['labor'] -= transfer_qty
                    self.inventory['labor'] = self.inventory.get('labor', 0) + transfer_qty

                    # Update _haves alias if present
                    if isinstance(consumer._haves, dict):
                        consumer._haves['labor'] = consumer.inventory['labor']
                    if isinstance(self._haves, dict):
                        self._haves['labor'] = self.inventory['labor']

                    # Update needed labor
                    needed_labor -= transfer_qty

                    contract_actions.append(f"Directly hired {transfer_qty} labor from consumer {consumer.id}")
            
            # Pay for active labor contracts each round
            if hasattr(self, 'active_labor_contracts') and self.active_labor_contracts:
                for contract in list(self.active_labor_contracts):
                    try:
                        self.pay_contract(contract)
                        contract_actions.append(f"Paid for labor contract {contract.id}")
                        # Remove contract after payment (single-round contracts)
                        self.active_labor_contracts.remove(contract)
                    except Exception as e:
                        contract_actions.append(f"Failed to pay contract {contract.id}: {e}")
        
        # Consumers accept and deliver labor contracts
        elif self.group == 'consumer':
            # Get labor contract offers
            try:
                offers = self.get_contract_offers('labor')
                for offer in offers:
                    available_labor = self.inventory.get('labor', 0)
                    if available_labor >= offer.quantity:
                        self.accept_contract(offer)
                        if not hasattr(self, 'active_labor_contracts'):
                            self.active_labor_contracts = []
                        self.active_labor_contracts.append(offer)
                        contract_actions.append(f"Accepted labor contract {offer.id} from {offer.sender_id}")
            except Exception as e:
                contract_actions.append(f"Failed to get contract offers: {e}")
            
            # Deliver on active labor contracts each round
            if hasattr(self, 'active_labor_contracts') and self.active_labor_contracts:
                for contract in list(self.active_labor_contracts):
                    try:
                        self.deliver_contract(contract)
                        self.inventory['labor'] -= contract.quantity
                        contract_actions.append(f"Delivered {contract.quantity} labor for contract {contract.id}")
                        # Remove contract after delivery (single-round contracts)
                        self.active_labor_contracts.remove(contract)
                    except Exception as e:
                        contract_actions.append(f"Failed to deliver contract {contract.id}: {e}")
        
        if contract_actions:
            print(f"[CONTRACT] {self.group} {self.agent_id}: " + "; ".join(contract_actions))

    # ------------------------------------------------------------------
    # abcEconomics lifecycle hooks
    # ------------------------------------------------------------------

    def _advance_round(self, time, str_time):
        """Extend base _advance_round to keep `self.round` in sync for Contracting."""
        super()._advance_round(time, str_time)
        # The Contracting mix-in expects the current round in `self.round`
        self.round = time 