import abcEconomics as abce
import random


class FinalGoodsFirm(abce.Agent, abce.Firm):
    def init(self):
        """ Final goods firms are the third layer in the supply chain.
        They use labor and intermediate goods to produce final goods that will be consumed by households.
        They have the lowest climate vulnerability as they're typically more protected.
        """
        self.create('money', 20)  # Initial capital
        self.create('intermediate_good', 1)  # Initial stock to avoid bootstrapping issues
        
        # Production parameters
        self.inputs = {"labor": 1, "intermediate_good": 1}
        self.output = "final_good"
        self.base_output_quantity = 1.8  # Base production capacity
        self.current_output_quantity = self.base_output_quantity
        
        # Climate stress parameters (lowest vulnerability)
        self.climate_vulnerability = 0.05 + (self.id * 0.02)  # Very low base vulnerability
        self.chronic_stress_accumulated = 1.0  # Multiplicative factor
        
        # Pricing
        self.price = {'final_good': 3}
        
        # Create production function
        self.pf = self.create_cobb_douglas(self.output, self.current_output_quantity, self.inputs)
        
        print(f"Final Goods Firm {self.id} initialized with vulnerability {self.climate_vulnerability:.2f}")

    def buy_intermediate_goods(self):
        """ Buy intermediate goods from intermediary firms """
        offers = self.get_offers("intermediate_good")
        for offer in offers:
            self.accept(offer)

    def buy_labor(self):
        """ Buy labor from households """
        offers = self.get_offers("labor")
        for offer in offers:
            self.accept(offer)

    def production(self):
        """ Produce final goods using labor and intermediate goods """
        # Update production function with current (potentially climate-affected) output quantity
        self.pf = self.create_cobb_douglas(self.output, self.current_output_quantity, self.inputs)
        self.produce(self.pf, self.inputs)

    def sell_final_goods(self):
        """ Sell final goods to households """
        final_goods_stock = self.possession('final_good')
        if final_goods_stock > 0:
            # Distribute sales among households
            quantity_per_household = final_goods_stock / 20  # 20 households
            for household_id in range(20):
                if quantity_per_household > 0:
                    self.sell(('household', household_id), 'final_good', 
                             quantity_per_household, self.price['final_good'])

    def apply_acute_stress(self):
        """ Apply acute climate stress (temporary productivity shock) """
        stress_factor = 1.0 - (self.climate_vulnerability * random.uniform(0.1, 0.4))
        original_quantity = self.current_output_quantity
        self.current_output_quantity = self.base_output_quantity * stress_factor * self.chronic_stress_accumulated
        
        print(f"  Final Goods Firm {self.id}: Acute stress! Production: {original_quantity:.2f} -> {self.current_output_quantity:.2f}")

    def apply_chronic_stress(self, stress_factor):
        """ Apply chronic climate stress (permanent productivity degradation) """
        self.chronic_stress_accumulated *= stress_factor
        self.current_output_quantity = self.base_output_quantity * self.chronic_stress_accumulated 