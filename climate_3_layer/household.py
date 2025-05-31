import abcEconomics as abce
import sys
import os
# Add the root directory to Python path to find the climate framework
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from climate_framework import add_climate_capabilities


@add_climate_capabilities
class Household(abce.Agent, abce.Household):
    def init(self):
        """ Households provide labor to firms across all three layers and consume final goods.
        They are the end consumers in the supply chain and are generally not directly affected 
        by climate stress, but may experience indirect effects through employment and prices.
        """
        self.labor_endowment = 1
        self.create('labor', self.labor_endowment)  # Create initial labor endowment
        self.create('money', 10)  # Give households some initial money
        self.utility_function = self.create_cobb_douglas_utility_function({"final_good": 1})
        self.accumulated_utility = 0
        
        # Each household is assigned to work for firms across different layers
        # This creates a more realistic labor market with more workers than firms
        # Safely distribute households across available firms using modulo
        
        # Get simulation parameters to know how many firms exist
        # Default to original assumptions if parameters not available
        try:
            sim_params = getattr(self._simulation, 'simulation_parameters', {})
            num_commodity = sim_params.get('num_commodity_producers', 3)
            num_intermediary = sim_params.get('num_intermediary_firms', 2) 
            num_final = sim_params.get('num_final_goods_firms', 2)
        except:
            # Fallback: use agent counting method
            try:
                # Try to get the actual number of firms from simulation
                sim = getattr(self, '_simulation', None)
                if hasattr(sim, 'commodity_producers'):
                    num_commodity = len(sim.commodity_producers)
                    num_intermediary = len(sim.intermediary_firms)
                    num_final = len(sim.final_goods_firms)
                else:
                    # Safe defaults
                    num_commodity = 3
                    num_intermediary = 2
                    num_final = 2
            except:
                # Ultimate fallback
                num_commodity = 3
                num_intermediary = 2
                num_final = 2
        
        # Ensure we have at least 1 firm of each type
        num_commodity = max(1, num_commodity)
        num_intermediary = max(1, num_intermediary)
        num_final = max(1, num_final)
        
        # Distribute households across all available firms
        total_firms = num_commodity + num_intermediary + num_final
        household_position = self.id % total_firms
        
        if household_position < num_commodity:
            # Assign to commodity producers
            firm_id = household_position % num_commodity
            self.employer = ('commodity_producer', firm_id)
        elif household_position < num_commodity + num_intermediary:
            # Assign to intermediary firms
            firm_id = (household_position - num_commodity) % num_intermediary
            self.employer = ('intermediary_firm', firm_id)
        else:
            # Assign to final goods firms
            firm_id = (household_position - num_commodity - num_intermediary) % num_final
            self.employer = ('final_goods_firm', firm_id)
        
        # Make labor perishable
        self._inventory._perishable.append('labor')
        
        print(f"Household {self.id} works for {self.employer[0]} {self.employer[1]}")

    def sell_labor(self):
        """ Offers labor to their assigned employer for the price of 1 "money" """
        if self['labor'] > 0:
            self.sell(self.employer, "labor", quantity=1, price=1)

    def buy_final_goods(self):
        """ Receives offers for final goods and accepts them """
        offers = self.get_offers("final_good")
        for offer in offers:
            self.accept(offer)

    def consumption(self):
        """ Consumes final goods and logs the aggregate utility """
        try:
            current_utility = self.consume(self.utility_function, ['final_good'])
            self.accumulated_utility += current_utility
            self.log('HH', {'utility': self.accumulated_utility, 'current_utility': current_utility})
        except Exception as e:
            # If no final goods available, log zero utility
            self.log('HH', {'utility': self.accumulated_utility, 'current_utility': 0})
            
        # Also log money and final_good possessions for analysis
        self.log('HH', {
            'money': self['money'],
            'final_good': self['final_good']
        }) 