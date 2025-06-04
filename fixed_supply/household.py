import abcEconomics as abce
import random
import sys
import os
# Add the root directory to Python path to find the climate framework
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from climate_framework import add_climate_capabilities


@add_climate_capabilities
class Household(abce.Agent, abce.Household):
    def init(self, config):
        """ Households in the fixed supply model try to maintain consumption levels.
        They sell labor and use income to buy final goods, going into debt if needed
        to maintain minimum consumption.
        
        Args:
            config: Configuration dictionary with consumption parameters, labor settings, etc.
        """
        # Initialize money
        initial_money = config['initial_money']
        self.create('money', initial_money)
        
        # Initialize inventory from configuration
        initial_inventory = config.get('initial_inventory', {})
        for good, quantity in initial_inventory.items():
            self.create(good, quantity)
        
        # Labor parameters from configuration
        labor_config = config['labor']
        self.labor_endowment = labor_config['endowment']
        self.wage = labor_config['wage']
        
        # Financial tracking
        self.debt = 0
        self.income = 0
        self.spending = 0
        self.debt_created_this_round = 0
        
        # Consumption parameters from configuration
        consumption_config = config['consumption']
        self.consumption_preference = consumption_config['preference']
        self.budget_fraction = consumption_config['budget_fraction']
        self.consumption_fraction = consumption_config['consumption_fraction']
        self.minimum_survival_consumption = consumption_config['minimum_survival_consumption']
        self.desired_consumption = self.minimum_survival_consumption * 2  # Target 2x minimum
        
        # Track consumption data
        self.consumption_this_round = 0
        self.final_goods_purchased = 0
        self.inventory_at_start = self[self.consumption_preference]
        
        # Get firm counts from config for labor distribution
        self.commodity_producer_count = config['commodity_producer_count']
        self.intermediary_firm_count = config['intermediary_firm_count']
        self.final_goods_firm_count = config['final_goods_firm_count']
        total_firms = self.commodity_producer_count + self.intermediary_firm_count + self.final_goods_firm_count
        
        # Calculate labor allocation based on rough input needs of each firm type
        # Commodity producers need more labor (only input), others need less
        self.labor_allocation = {
            'commodity_producer': 0.5,    # 50% to commodity producers (labor-intensive)
            'intermediary_firm': 0.25,    # 25% to intermediary firms
            'final_goods_firm': 0.25      # 25% to final goods firms
        }
        
        print(f"Fixed Supply Household {self.id} initialized:")
        print(f"  Initial money: ${initial_money}")
        print(f"  Labor endowment: {self.labor_endowment}")
        print(f"  Wage: ${self.wage}")
        print(f"  Minimum consumption: {self.minimum_survival_consumption}")
        print(f"  Desired consumption: {self.desired_consumption}")
        print(f"  Will distribute labor to {total_firms} firms")

    def start_round(self):
        """Called at the start of each round to reset tracking variables"""
        self.consumption_this_round = 0
        self.final_goods_purchased = 0
        self.inventory_at_start = self[self.consumption_preference]
        self.debt_created_this_round = 0
        self.income = 0
        self.spending = 0

    def refresh_services(self, service, derived_from='labor_endowment', units=None):
        """ Refresh labor services - called before selling to reset available labor """
        if units is None:
            units = getattr(self, derived_from, 0)
        
        # First destroy any existing labor to reset to zero
        try:
            current_labor = self[service]
            if current_labor > 0:
                self.destroy(service, current_labor)
        except KeyError:
            current_labor = 0  # No existing labor
        
        # Then create exactly the endowment amount
        self.create(service, units)
        print(f"  Household {self.id}: Refreshed {service} to {units} units (was {current_labor:.2f})")

    def sell_labor(self):
        """ Sell labor to firms based on predetermined allocation strategy """
        labor_available = self['labor']
        
        print(f"  Household {self.id}: Selling {labor_available:.2f} units of labor at ${self.wage}/unit")
        
        # Calculate total labor demand and scale offers proportionally to avoid over-offering
        
        # Commodity producers
        commodity_labor = labor_available * self.labor_allocation['commodity_producer']
        if commodity_labor > 0 and self.commodity_producer_count > 0:
            labor_per_producer = commodity_labor / self.commodity_producer_count
            for producer_id in range(self.commodity_producer_count):
                self.sell(('commodity_producer', producer_id), 'labor', 
                         labor_per_producer, self.wage)
            print(f"    Offered {commodity_labor:.2f} labor to commodity producers")
        
        # Intermediary firms
        intermediary_labor = labor_available * self.labor_allocation['intermediary_firm']
        if intermediary_labor > 0 and self.intermediary_firm_count > 0:
            labor_per_firm = intermediary_labor / self.intermediary_firm_count
            for firm_id in range(self.intermediary_firm_count):
                self.sell(('intermediary_firm', firm_id), 'labor', 
                         labor_per_firm, self.wage)
            print(f"    Offered {intermediary_labor:.2f} labor to intermediary firms")
        
        # Final goods firms
        final_labor = labor_available * self.labor_allocation['final_goods_firm']
        if final_labor > 0 and self.final_goods_firm_count > 0:
            labor_per_firm = final_labor / self.final_goods_firm_count
            for firm_id in range(self.final_goods_firm_count):
                self.sell(('final_goods_firm', firm_id), 'labor', 
                         labor_per_firm, self.wage)
            print(f"    Offered {final_labor:.2f} labor to final goods firms")
        
        # Verify total offers don't exceed available labor
        total_offered = commodity_labor + intermediary_labor + final_labor
        print(f"    Total labor offered: {total_offered:.2f} (available: {labor_available:.2f})")
        
        if abs(total_offered - labor_available) > 0.001:
            print(f"    ⚠️ WARNING: Labor allocation mismatch! Offered {total_offered:.2f}, available {labor_available:.2f}")

    def calculate_labor_income(self):
        """Calculate income from labor sales after market clearing"""
        # Labor income = (initial labor - remaining labor) * wage
        labor_sold = self.labor_endowment - self['labor']
        self.income = labor_sold * self.wage
        print(f"  Household {self.id}: Sold {labor_sold:.2f} labor, earned ${self.income:.2f}")
        
        # If we detect negative labor remaining, log for debugging
        if self['labor'] < 0:
            print(f"    🐛 DEBUG: Household {self.id} has negative labor remaining: {self['labor']:.2f}")
            print(f"    This indicates over-selling in the labor market!")
            print(f"    Labor endowment: {self.labor_endowment}, Labor sold: {labor_sold:.2f}")

    def buy_final_goods(self):
        """ Buy final goods based on total available resources - simple and market-responsive """
        self.calculate_labor_income()  # First calculate income
        
        final_goods_start = self[self.consumption_preference]
        offers = self.get_offers(self.consumption_preference)
        
        # Simple rule: spend a fraction of total available resources on consumption
        available_money = self['money']
        total_resources = self.income + available_money  # Income this round + accumulated wealth
        
        # Spend 60% of total resources on consumption (this makes households responsive to wealth changes)
        consumption_spending_budget = total_resources * 0.6
        
        # Don't spend more money than we have (unless survival emergency)
        actual_spending_budget = min(consumption_spending_budget, available_money)
        
        print(f"  Fixed Supply Household {self.id}:")
        print(f"    Income: ${self.income:.2f}, Money: ${available_money:.2f}, Total resources: ${total_resources:.2f}")
        print(f"    Consumption budget (60% of resources): ${consumption_spending_budget:.2f}")
        print(f"    Actual spending budget: ${actual_spending_budget:.2f}")
        print(f"    Current inventory: {final_goods_start:.2f}")
        print(f"    Received {len(offers)} final good offers")
        
        total_purchased = 0
        total_spent = 0
        remaining_budget = actual_spending_budget
        
        # Buy as much as we can afford with our budget
        for offer in offers:
            if remaining_budget <= 0:
                print(f"    BUDGET EXHAUSTED")
                break
                
            # How much can we afford from this offer?
            affordable_quantity = remaining_budget / offer.price
            purchase_quantity = min(offer.quantity, affordable_quantity)
            
            if purchase_quantity > 0.01:  # Worth buying
                cost = purchase_quantity * offer.price
                
                if purchase_quantity == offer.quantity:
                    self.accept(offer)
                else:
                    self.accept(offer, quantity=purchase_quantity)
                
                total_purchased += purchase_quantity
                total_spent += cost
                remaining_budget -= cost
                print(f"    BOUGHT: {purchase_quantity:.3f} units for ${cost:.2f} (price: ${offer.price:.2f}/unit)")
            else:
                print(f"    SKIPPED: Can't afford offer of {offer.quantity:.2f} at ${offer.price:.2f}/unit")
        
        # Emergency debt creation ONLY if we bought nothing and have no inventory
        current_inventory_after_purchase = final_goods_start + total_purchased
        if current_inventory_after_purchase < 0.01:  # Essentially no food
            print(f"    🆘 SURVIVAL EMERGENCY: No inventory, creating emergency debt")
            emergency_debt = self.minimum_survival_consumption * 50  # Emergency money for survival
            self.create('money', emergency_debt)
            self.debt += emergency_debt
            self.debt_created_this_round += emergency_debt
            print(f"    💳 Created ${emergency_debt:.2f} emergency debt")
            
            # Try to buy something with emergency money
            if offers and len(offers) > 0:
                offer = offers[0]  # Take first available offer
                emergency_quantity = min(offer.quantity, emergency_debt / offer.price)
                if emergency_quantity > 0.01:
                    emergency_cost = emergency_quantity * offer.price
                    self.accept(offer, quantity=emergency_quantity)
                    total_purchased += emergency_quantity
                    total_spent += emergency_cost
                    print(f"    🆘 EMERGENCY BUY: {emergency_quantity:.3f} units for ${emergency_cost:.2f}")
        
        # Record results
        self.final_goods_purchased = total_purchased
        self.spending = total_spent
        
        final_goods_end = self[self.consumption_preference]
        
        print(f"  Household {self.id}: Purchasing complete")
        print(f"    Total purchased: {self.final_goods_purchased:.3f} for ${total_spent:.2f}")
        print(f"    Average price paid: ${total_spent/total_purchased if total_purchased > 0 else 0:.2f}/unit")
        print(f"    Inventory: {final_goods_start:.3f} → {final_goods_end:.3f}")
        print(f"    Money: ${available_money:.2f} → ${self['money']:.2f}")
        print(f"    Debt: ${self.debt:.2f}")

    def consumption(self):
        """ Consume final goods using consumption_fraction to limit consumption """
        available = self[self.consumption_preference]
        
        # Apply consumption_fraction to available goods (but ensure survival minimum)
        normal_consumption = available * self.consumption_fraction
        
        # Try to consume the fraction amount, but ensure at least minimum survival
        consumption_target = max(normal_consumption, min(available, self.minimum_survival_consumption))
        # But don't exceed what we actually have or our desired consumption
        consumption_target = min(consumption_target, available, self.desired_consumption)
        
        self.destroy(self.consumption_preference, consumption_target)
        self.consumption_this_round = consumption_target
        
        print(f"  Household {self.id}: Consumed {consumption_target:.2f} {self.consumption_preference}s")
        print(f"    Available: {available:.2f}, Normal consumption (fraction): {normal_consumption:.2f}")
        print(f"    Consumption fraction: {self.consumption_fraction:.1%}")
        
        # Check if minimum needs were met
        if consumption_target < self.minimum_survival_consumption:
            print(f"    ⚠️ WARNING: Below survival consumption! ({consumption_target:.2f} < {self.minimum_survival_consumption:.2f})")

    def log_round_data(self):
        """Log consumption and financial data for this round"""
        # Calculate inventory change
        inventory_change = self.final_goods_purchased - self.consumption_this_round
        cumulative_inventory = self[self.consumption_preference]
        current_money = self['money']
        
        # Check if minimum consumption was met
        minimum_consumption_met = self.consumption_this_round >= self.minimum_survival_consumption
        desired_consumption_met = self.consumption_this_round >= self.desired_consumption
        
        # Log the data - keep original calculation to see negative values for debugging
        labor_sold = self.labor_endowment - self['labor']
        
        self.log('consumption', {
            'consumption': self.consumption_this_round,
            'purchases': self.final_goods_purchased,
            'inventory_change': inventory_change,
            'cumulative_inventory': cumulative_inventory,
            'labor_sold': labor_sold,  # Keep original to detect negatives
            'income': self.income,
            'spending': self.spending,
            'money': current_money,
            'debt': self.debt,
            'debt_created_this_round': self.debt_created_this_round,
            'net_worth': current_money - self.debt,
            'minimum_consumption': self.minimum_survival_consumption,
            'minimum_consumption_met': minimum_consumption_met,
            'desired_consumption': self.desired_consumption,
            'desired_consumption_met': desired_consumption_met
        })
        
        print(f"  Household {self.id}: Logged - Consumption: {self.consumption_this_round:.2f}, Income: ${self.income:.2f}, Spending: ${self.spending:.2f}, Debt: ${self.debt:.2f}, Net worth: ${current_money - self.debt:.2f}")

    def _collect_agent_data(self, round_num, agent_type):
        """ Collect agent data for visualization """
        return {
            'id': self.id,
            'type': agent_type,
            'round': round_num,
            'wealth': self['money'],
            'debt': self.debt,
            'net_worth': self['money'] - self.debt,
            'consumption': self.consumption_this_round,
            'continent': getattr(self, 'continent', 'Unknown'),
            'minimum_consumption_met': self.consumption_this_round >= self.minimum_survival_consumption
        } 