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
        """ Buy final goods to meet consumption needs, using budget_fraction to limit spending """
        self.calculate_labor_income()  # First calculate income
        
        final_goods_start = self[self.consumption_preference]
        offers = self.get_offers(self.consumption_preference)
        
        # Calculate budget for this round using budget_fraction
        available_money = self['money']
        budget_for_round = available_money * self.budget_fraction
        
        # Calculate how much we need
        current_inventory = self[self.consumption_preference]
        needed_for_desired = max(0, self.desired_consumption - current_inventory)
        needed_for_survival = max(0, self.minimum_survival_consumption - current_inventory)
        
        print(f"  Fixed Supply Household {self.id}:")
        print(f"    Income: ${self.income:.2f}, Current money: ${available_money:.2f}, Budget for round: ${budget_for_round:.2f}")
        print(f"    Budget fraction: {self.budget_fraction:.1%}, Debt: ${self.debt:.2f}")
        print(f"    Current inventory: {current_inventory:.2f}")
        print(f"    Need for survival: {needed_for_survival:.2f}")
        print(f"    Need for desired consumption: {needed_for_desired:.2f}")
        print(f"    Received {len(offers)} final good offers")
        
        total_purchased = 0
        total_spent = 0
        remaining_budget = budget_for_round
        
        for offer in offers:
            # First priority: ensure survival minimum (can create debt if needed)
            if needed_for_survival > 0:
                purchase_quantity = min(offer.quantity, needed_for_survival)
                cost = purchase_quantity * offer.price
                
                # For survival, we can create debt if budget is insufficient
                if remaining_budget < cost:
                    debt_needed = cost - remaining_budget
                    self.create('money', debt_needed)
                    self.debt += debt_needed
                    self.debt_created_this_round += debt_needed
                    remaining_budget += debt_needed  # Add to budget
                    print(f"    💳 Created ${debt_needed:.2f} debt for survival consumption")
                
                if purchase_quantity == offer.quantity:
                    self.accept(offer)
                else:
                    self.accept(offer, quantity=purchase_quantity)
                
                total_purchased += purchase_quantity
                total_spent += cost
                remaining_budget -= cost
                needed_for_survival -= purchase_quantity
                needed_for_desired -= purchase_quantity
                print(f"    SURVIVAL: Bought {purchase_quantity:.2f} for ${cost:.2f}")
                
            # Second priority: buy towards desired consumption within remaining budget
            elif needed_for_desired > 0 and remaining_budget > 0:
                affordable_quantity = min(offer.quantity, remaining_budget / offer.price, needed_for_desired)
                if affordable_quantity > 0.01:
                    cost = affordable_quantity * offer.price
                    
                    if affordable_quantity == offer.quantity:
                        self.accept(offer)
                    else:
                        self.accept(offer, quantity=affordable_quantity)
                    
                    total_purchased += affordable_quantity
                    total_spent += cost
                    remaining_budget -= cost
                    needed_for_desired -= affordable_quantity
                    print(f"    DESIRED: Bought {affordable_quantity:.2f} for ${cost:.2f}")
            else:
                print(f"    SKIPPED: Offer of {offer.quantity:.2f} at ${offer.price:.2f}/unit (budget: ${remaining_budget:.2f})")
        
        # Use the actual total purchased rather than inventory change
        self.final_goods_purchased = total_purchased
        self.spending = total_spent
        
        final_goods_end = self[self.consumption_preference]
        actual_inventory_change = final_goods_end - final_goods_start
        
        print(f"  Household {self.id}: Purchasing complete")
        print(f"    Total purchased: {self.final_goods_purchased:.2f} for ${total_spent:.2f}")
        print(f"    Budget used: ${total_spent:.2f} of ${budget_for_round:.2f} ({total_spent/budget_for_round*100 if budget_for_round > 0 else 0:.1f}%)")
        print(f"    Inventory: {final_goods_start:.2f} → {final_goods_end:.2f} (change: {actual_inventory_change:.2f})")
        print(f"    Money remaining: ${self['money']:.2f}")
        print(f"    Total debt: ${self.debt:.2f}")
        
        # Verify our calculation matches actual inventory change
        if abs(actual_inventory_change - total_purchased) > 0.001:
            print(f"    ⚠️ WARNING: Purchase calculation mismatch! Calculated {total_purchased:.3f}, actual change {actual_inventory_change:.3f}")

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