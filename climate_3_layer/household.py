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
        # Distribute households across all 7 firms (3 commodity + 2 intermediary + 2 final)
        
        # Use modulo to cycle through all firms
        if self.id < 3:
            # First 3 households go to commodity producers
            self.employer = ('commodity_producer', self.id)
        elif self.id < 5:
            # Next 2 households go to intermediary firms
            self.employer = ('intermediary_firm', self.id - 3)
        elif self.id < 7:
            # Next 2 households go to final goods firms
            self.employer = ('final_goods_firm', self.id - 5)
        else:
            # Remaining households cycle through all firms
            remaining_id = (self.id - 7) % 7
            if remaining_id < 3:
                self.employer = ('commodity_producer', remaining_id)
            elif remaining_id < 5:
                self.employer = ('intermediary_firm', remaining_id - 3)
            else:
                self.employer = ('final_goods_firm', remaining_id - 5)
        
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