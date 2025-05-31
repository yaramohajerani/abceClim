import abcEconomics as abce
import random
import sys
import os
# Add the root directory to Python path to find the climate framework
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from climate_framework import add_climate_capabilities


@add_climate_capabilities
class IntermediaryFirm(abce.Agent, abce.Firm):
    def init(self):
        """ Intermediary firms are the second layer in the supply chain.
        They use labor and commodities to produce intermediate goods that will be used by final goods firms.
        They are also vulnerable to climate stress but typically less than commodity producers.
        """
        self.create('money', 75)  # Increased initial capital for longer simulation
        self.create('commodity', 2)  # Initial stock to avoid bootstrapping issues
        
        # Production parameters
        self.inputs = {"labor": 1, "commodity": 1}
        self.output = "intermediate_good"
        self.base_output_quantity = 1.5  # Base production capacity
        self.current_output_quantity = self.base_output_quantity
        
        # Climate stress parameters (generally less vulnerable than commodity producers)
        self.climate_vulnerability = 0.1 + (self.id * 0.05)  # Lower base vulnerability
        self.chronic_stress_accumulated = 1.0  # Multiplicative factor
        self.climate_stressed = False  # Track if currently stressed
        
        # Pricing
        self.price = {'intermediate_good': 2}
        
        # Create production function
        self.pf = self.create_cobb_douglas(self.output, self.current_output_quantity, self.inputs)
        
        print(f"Intermediary Firm {self.id} initialized with vulnerability {self.climate_vulnerability:.2f}")

    def buy_commodities(self):
        """ Buy commodities from commodity producers """
        offers = self.get_offers("commodity")
        print(f"    Intermediary Firm {self.id}: Received {len(offers)} commodity offers")
        print(f"    Intermediary Firm {self.id}: Has {self['money']:.2f} money")
        for i, offer in enumerate(offers):
            print(f"      Offer {i}: {offer.good} quantity={offer.quantity} price={offer.price} from {offer.sender}")
            self.accept(offer)
        if not offers:
            print(f"    Intermediary Firm {self.id}: No commodity offers received")

    def buy_labor(self):
        """ Buy labor from households """
        offers = self.get_offers("labor")
        for offer in offers:
            self.accept(offer)

    def production(self):
        """ Produce intermediate goods using labor and commodities """
        # Update production function with current (potentially climate-affected) output quantity
        self.pf = self.create_cobb_douglas(self.output, self.current_output_quantity, self.inputs)
        self.produce(self.pf, self.inputs)

    def sell_intermediate_goods(self):
        """ Sell intermediate goods to final goods firms """
        intermediate_stock = self['intermediate_good']
        if intermediate_stock > 0:
            # Distribute sales among final goods firms
            quantity_per_firm = intermediate_stock / 2  # Assuming 2 final goods firms
            for final_firm_id in range(2):
                if quantity_per_firm > 0:
                    self.sell(('final_goods_firm', final_firm_id), 'intermediate_good', 
                             quantity_per_firm, self.price['intermediate_good'])

    def apply_climate_stress(self, stress_factor):
        """ Apply climate stress by reducing production capacity """
        self.climate_stressed = True
        original_quantity = self.current_output_quantity
        self.current_output_quantity = self.base_output_quantity * stress_factor * self.chronic_stress_accumulated
        print(f"  Intermediary Firm {self.id}: CLIMATE STRESS applied! Production: {original_quantity:.2f} -> {self.current_output_quantity:.2f}")

    def reset_climate_stress(self):
        """ Reset production to normal levels """
        if self.climate_stressed:
            self.climate_stressed = False
            self.current_output_quantity = self.base_output_quantity * self.chronic_stress_accumulated
            print(f"  Intermediary Firm {self.id}: Climate stress cleared, production restored to {self.current_output_quantity:.2f}")

    def apply_acute_stress(self):
        """ Apply acute climate stress (temporary productivity shock) """
        stress_factor = 1.0 - (self.climate_vulnerability * random.uniform(0.2, 0.6))
        original_quantity = self.current_output_quantity
        self.current_output_quantity = self.base_output_quantity * stress_factor * self.chronic_stress_accumulated
        
        print(f"  Intermediary Firm {self.id}: Acute stress! Production: {original_quantity:.2f} -> {self.current_output_quantity:.2f}")

    def apply_chronic_stress(self, stress_factor):
        """ Apply chronic climate stress (permanent productivity degradation) """
        self.chronic_stress_accumulated *= stress_factor
        self.current_output_quantity = self.base_output_quantity * self.chronic_stress_accumulated 