import abcEconomics as abce
import random
import sys
import os
# Add the root directory to Python path to find the climate framework
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from climate_framework import add_climate_capabilities


@add_climate_capabilities
class CommodityProducer(abce.Agent, abce.Firm):
    def init(self):
        """ Commodity producers are the first layer in the supply chain.
        They use labor to produce raw commodities that will be used by intermediary firms.
        They are vulnerable to climate stress which affects their productivity.
        """
        self.create('money', 50)  # Increased initial capital for longer simulation
        
        # Production parameters
        self.inputs = {"labor": 1}
        self.output = "commodity"
        self.base_output_quantity = 2  # Base production capacity
        self.current_output_quantity = self.base_output_quantity
        
        # Climate stress parameters
        self.climate_vulnerability = 0.3 + (self.id * 0.1)  # Different vulnerabilities
        self.chronic_stress_accumulated = 1.0  # Multiplicative factor
        self.climate_stressed = False  # Track if currently stressed
        
        # Pricing
        self.price = {'commodity': 1}
        
        # Create production function
        self.pf = self.create_cobb_douglas(self.output, self.current_output_quantity, self.inputs)
        
        print(f"Commodity Producer {self.id} initialized with vulnerability {self.climate_vulnerability:.2f}")

    def buy_labor(self):
        """ Buy labor from households """
        offers = self.get_offers("labor")
        for offer in offers:
            self.accept(offer)

    def production(self):
        """ Produce commodities using labor """
        # Update production function with current (potentially climate-affected) output quantity
        self.pf = self.create_cobb_douglas(self.output, self.current_output_quantity, self.inputs)
        self.produce(self.pf, self.inputs)

    def sell_commodities(self):
        """ Sell commodities to intermediary firms """
        commodity_stock = self.possession('commodity')
        if commodity_stock > 0:
            # Distribute sales among intermediary firms
            quantity_per_firm = commodity_stock / 2  # Assuming 2 intermediary firms
            for intermediary_id in range(2):
                if quantity_per_firm > 0:
                    self.sell(('intermediary_firm', intermediary_id), 'commodity', 
                             quantity_per_firm, self.price['commodity'])

    def apply_climate_stress(self, stress_factor):
        """ Apply climate stress by reducing production capacity """
        self.climate_stressed = True
        original_quantity = self.current_output_quantity
        self.current_output_quantity = self.base_output_quantity * stress_factor * self.chronic_stress_accumulated
        print(f"  Commodity Producer {self.id}: CLIMATE STRESS applied! Production: {original_quantity:.2f} -> {self.current_output_quantity:.2f}")

    def reset_climate_stress(self):
        """ Reset production to normal levels """
        if self.climate_stressed:
            self.climate_stressed = False
            self.current_output_quantity = self.base_output_quantity * self.chronic_stress_accumulated
            print(f"  Commodity Producer {self.id}: Climate stress cleared, production restored to {self.current_output_quantity:.2f}")

    def apply_acute_stress(self):
        """ Apply acute climate stress (temporary productivity shock) """
        stress_factor = 1.0 - (self.climate_vulnerability * random.uniform(0.2, 0.8))
        original_quantity = self.current_output_quantity
        self.current_output_quantity = self.base_output_quantity * stress_factor * self.chronic_stress_accumulated
        
        print(f"  Commodity Producer {self.id}: Acute stress! Production: {original_quantity:.2f} -> {self.current_output_quantity:.2f}")

    def apply_chronic_stress(self, stress_factor):
        """ Apply chronic climate stress (permanent productivity degradation) """
        self.chronic_stress_accumulated *= stress_factor
        self.current_output_quantity = self.base_output_quantity * self.chronic_stress_accumulated 