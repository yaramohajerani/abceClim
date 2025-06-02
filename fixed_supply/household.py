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
        self.inventory_at_start = self.get(self.consumption_preference, 0)
        
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
        self.inventory_at_start = self.get(self.consumption_preference, 0)
        self.debt_created_this_round = 0
        self.income = 0
        self.spending = 0

    def refresh_services(self, service, derived_from='labor_endowment', units=None):
        """ Refresh labor services - called before selling to reset available labor """
        if units is None:
            units = getattr(self, derived_from, 0)
        self.create(service, units)
        print(f"  Household {self.id}: Refreshed {service} to {units} units")

    def sell_labor(self):
        """ Sell labor to firms based on predetermined allocation strategy """
        labor_available = self['labor']
        
        print(f"  Household {self.id}: Selling {labor_available:.2f} units of labor at ${self.wage}/unit")
        
        # Distribute labor offers among different firm types based on allocation
        
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

    def calculate_labor_income(self):
        """Calculate income from labor sales after market clearing"""
        # Labor income = (initial labor - remaining labor) * wage
        labor_sold = self.labor_endowment - self['labor']
        self.income = labor_sold * self.wage
        print(f"  Household {self.id}: Sold {labor_sold:.2f} labor, earned ${self.income:.2f}")

    def buy_final_goods(self):
        """ Buy final goods to meet consumption needs, using debt if necessary """
        self.calculate_labor_income()  # First calculate income
        
        final_goods_start = self[self.consumption_preference]
        offers = self.get_offers(self.consumption_preference)
        
        # Calculate how much we need
        current_inventory = self[self.consumption_preference]
        needed_for_desired = max(0, self.desired_consumption - current_inventory)
        needed_for_survival = max(0, self.minimum_survival_consumption - current_inventory)
        
        print(f"  Fixed Supply Household {self.id}:")
        print(f"    Income: ${self.income:.2f}, Current money: ${self['money']:.2f}, Debt: ${self.debt:.2f}")
        print(f"    Current inventory: {current_inventory:.2f}")
        print(f"    Need for survival: {needed_for_survival:.2f}")
        print(f"    Need for desired consumption: {needed_for_desired:.2f}")
        print(f"    Received {len(offers)} final good offers")
        
        total_purchased = 0
        total_spent = 0
        
        for offer in offers:
            # First priority: ensure survival minimum
            if needed_for_survival > 0:
                purchase_quantity = min(offer.quantity, needed_for_survival)
                cost = purchase_quantity * offer.price
                
                # Create debt if needed for survival
                if self['money'] < cost:
                    debt_needed = cost - self['money']
                    self.create('money', debt_needed)
                    self.debt += debt_needed
                    self.debt_created_this_round += debt_needed
                    print(f"    💳 Created ${debt_needed:.2f} debt for survival consumption")
                
                if purchase_quantity == offer.quantity:
                    self.accept(offer)
                else:
                    self.accept(offer, quantity=purchase_quantity)
                
                total_purchased += purchase_quantity
                total_spent += cost
                needed_for_survival -= purchase_quantity
                needed_for_desired -= purchase_quantity
                print(f"    SURVIVAL: Bought {purchase_quantity:.2f} for ${cost:.2f}")
                
            # Second priority: buy towards desired consumption if we have money
            elif needed_for_desired > 0 and self['money'] > 0:
                affordable_quantity = min(offer.quantity, self['money'] / offer.price, needed_for_desired)
                if affordable_quantity > 0.01:
                    cost = affordable_quantity * offer.price
                    
                    if affordable_quantity == offer.quantity:
                        self.accept(offer)
                    else:
                        self.accept(offer, quantity=affordable_quantity)
                    
                    total_purchased += affordable_quantity
                    total_spent += cost
                    needed_for_desired -= affordable_quantity
                    print(f"    DESIRED: Bought {affordable_quantity:.2f} for ${cost:.2f}")
            else:
                print(f"    SKIPPED: Offer of {offer.quantity:.2f} at ${offer.price:.2f}/unit")
        
        final_goods_end = self[self.consumption_preference]
        self.final_goods_purchased = final_goods_end - final_goods_start
        self.spending = total_spent
        
        print(f"  Household {self.id}: Purchasing complete")
        print(f"    Total purchased: {self.final_goods_purchased:.2f} for ${total_spent:.2f}")
        print(f"    Money remaining: ${self['money']:.2f}")
        print(f"    Total debt: ${self.debt:.2f}")

    def consumption(self):
        """ Consume final goods """
        available = self[self.consumption_preference]
        
        # Try to consume desired amount, but at least minimum
        consumption_target = min(available, self.desired_consumption)
        consumption_target = max(consumption_target, min(available, self.minimum_survival_consumption))
        
        self.destroy(self.consumption_preference, consumption_target)
        self.consumption_this_round = consumption_target
        
        print(f"  Household {self.id}: Consumed {consumption_target:.2f} {self.consumption_preference}s")
        
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
        
        # Log the data
        self.log('consumption', {
            'consumption': self.consumption_this_round,
            'purchases': self.final_goods_purchased,
            'inventory_change': inventory_change,
            'cumulative_inventory': cumulative_inventory,
            'labor_sold': self.labor_endowment - self['labor'],
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