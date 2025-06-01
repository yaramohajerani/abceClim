import abcEconomics as abce
import random
import sys
import os
# Add the root directory to Python path to find the climate framework
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from climate_framework import add_climate_capabilities


@add_climate_capabilities
class IntermediaryFirm(abce.Agent, abce.Firm):
    def init(self, config=None):
        """ Intermediary firms are the second layer in the supply chain.
        They use labor and commodities to produce intermediate goods that will be used by final goods firms.
        They are also vulnerable to climate stress but typically less than commodity producers.
        
        Args:
            config: Configuration dictionary with production parameters, climate settings, etc.
        """
        # Use configuration or fall back to defaults for backward compatibility
        if config is None:
            config = {
                'initial_money': 50,
                'initial_inventory': {'commodity': 1},
                'production': {
                    'base_output_quantity': 1.5,
                    'inputs': {'labor': 1, 'commodity': 1},
                    'output': 'intermediate_good',
                    'price': 2.0
                },
                'climate': {
                    'base_vulnerability': 0.1,
                    'vulnerability_variance': 0.05
                }
            }
        
        # Initialize money
        initial_money = config.get('initial_money', 50)
        self.create('money', initial_money)
        
        # Initialize inventory from configuration
        initial_inventory = config.get('initial_inventory', {})
        for good, quantity in initial_inventory.items():
            self.create(good, quantity)
        
        # Production parameters from configuration
        production_config = config.get('production', {})
        self.inputs = production_config.get('inputs', {"labor": 1, "commodity": 1})
        self.output = production_config.get('output', "intermediate_good")
        self.base_output_quantity = production_config.get('base_output_quantity', 1.5)
        self.current_output_quantity = self.base_output_quantity
        
        # Climate stress parameters from configuration
        climate_config = config.get('climate', {})
        base_vulnerability = climate_config.get('base_vulnerability', 0.1)
        vulnerability_variance = climate_config.get('vulnerability_variance', 0.05)
        self.climate_vulnerability = base_vulnerability + (self.id * vulnerability_variance)
        self.chronic_stress_accumulated = 1.0  # Multiplicative factor
        self.climate_stressed = False  # Track if currently stressed
        
        # Pricing from configuration
        self.price = {self.output: production_config.get('price', 2.0)}
        
        # Create production function
        self.pf = self.create_cobb_douglas(self.output, self.current_output_quantity, self.inputs)
        
        print(f"Intermediary Firm {self.id} initialized:")
        print(f"  Initial money: ${initial_money}")
        print(f"  Production capacity: {self.base_output_quantity}")
        print(f"  Climate vulnerability: {self.climate_vulnerability:.3f}")
        print(f"  Price: ${self.price[self.output]}")

    def buy_commodities(self):
        """ Buy commodities from commodity producers """
        offers = self.get_offers("commodity")
        available_money = self['money']
        total_spent = 0
        
        print(f"    Intermediary Firm {self.id}: Received {len(offers)} commodity offers")
        print(f"    Intermediary Firm {self.id}: Has ${available_money:.2f} money")
        
        for i, offer in enumerate(offers):
            cost = offer.quantity * offer.price
            print(f"      Offer {i}: {offer.good} quantity={offer.quantity} price={offer.price} from {offer.sender}")
            
            if total_spent + cost <= available_money:
                self.accept(offer)
                total_spent += cost
                print(f"        Accepted: cost ${cost:.2f}")
            else:
                # Try partial acceptance
                affordable_quantity = (available_money - total_spent) / offer.price
                if affordable_quantity > 0.01:
                    self.accept(offer, quantity=affordable_quantity)
                    total_spent += affordable_quantity * offer.price
                    print(f"        Partially accepted: {affordable_quantity:.2f} units for ${affordable_quantity * offer.price:.2f}")
                else:
                    print(f"        Cannot afford: needs ${cost:.2f}, only have ${available_money - total_spent:.2f} left")
                break
        
        if not offers:
            print(f"    Intermediary Firm {self.id}: No commodity offers received")
        
        print(f"    Intermediary Firm {self.id}: Spent ${total_spent:.2f} on commodities")

    def buy_labor(self):
        """ Buy labor from households """
        offers = self.get_offers("labor")
        available_money = self['money']
        total_spent = 0
        
        print(f"    Intermediary Firm {self.id}: Has ${available_money:.2f}, received {len(offers)} labor offers")
        
        for offer in offers:
            cost = offer.quantity * offer.price
            if total_spent + cost <= available_money:
                self.accept(offer)
                total_spent += cost
                print(f"      Accepted labor offer: {offer.quantity:.2f} units for ${cost:.2f}")
            else:
                # Try partial acceptance
                affordable_quantity = (available_money - total_spent) / offer.price
                if affordable_quantity > 0.01:
                    self.accept(offer, quantity=affordable_quantity)
                    total_spent += affordable_quantity * offer.price
                    print(f"      Partially accepted labor offer: {affordable_quantity:.2f} units for ${affordable_quantity * offer.price:.2f}")
                else:
                    print(f"      Cannot afford labor offer: {offer.quantity:.2f} units for ${cost:.2f}")
                break
        
        print(f"    Intermediary Firm {self.id}: Spent ${total_spent:.2f} on labor")

    def production(self):
        """ Produce intermediate goods using labor and commodities """
        # Check available inputs
        available_inputs = {}
        can_produce = True
        
        for input_good, required_quantity in self.inputs.items():
            available = self[input_good]
            available_inputs[input_good] = available
            if available < required_quantity:
                can_produce = False
        
        if can_produce:
            # Full production possible
            # Update production function with current (potentially climate-affected) output quantity
            self.pf = self.create_cobb_douglas(self.output, self.current_output_quantity, self.inputs)
            self.produce(self.pf, self.inputs)
            print(f"    Intermediary Firm {self.id}: Produced {self.current_output_quantity:.2f} {self.output}s using full inputs")
        else:
            # Partial or zero production based on available inputs
            # Calculate production scaling factor based on most limiting input
            production_scale = 1.0
            for input_good, required_quantity in self.inputs.items():
                available = available_inputs[input_good]
                if required_quantity > 0:
                    input_scale = available / required_quantity
                    production_scale = min(production_scale, input_scale)
            
            if production_scale > 0:
                # Scale down production and inputs
                scaled_output = self.current_output_quantity * production_scale
                scaled_inputs = {good: quantity * production_scale for good, quantity in self.inputs.items()}
                
                # Create scaled production function
                self.pf = self.create_cobb_douglas(self.output, scaled_output, scaled_inputs)
                self.produce(self.pf, scaled_inputs)
                print(f"    Intermediary Firm {self.id}: Partial production {scaled_output:.2f} {self.output}s (scale: {production_scale:.2f})")
            else:
                # No production possible
                print(f"    Intermediary Firm {self.id}: No production - insufficient inputs")
                for input_good, required in self.inputs.items():
                    available = available_inputs[input_good]
                    print(f"      Need {required:.2f} {input_good}, have {available:.2f}")

    def sell_intermediate_goods(self):
        """ Sell intermediate goods to final goods firms """
        intermediate_stock = self[self.output]
        if intermediate_stock > 0:
            # Distribute sales among final goods firms
            quantity_per_firm = intermediate_stock / 2  # Assuming 2 final goods firms
            for final_firm_id in range(2):
                if quantity_per_firm > 0:
                    self.sell(('final_goods_firm', final_firm_id), self.output, 
                             quantity_per_firm, self.price[self.output])

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

    def _collect_agent_data(self, round_num, agent_type):
        """ Collect agent data for visualization (called by abcEconomics group system) """
        return {
            'id': self.id,
            'type': agent_type,
            'round': round_num,
            'wealth': self['money'],
            'climate_stressed': self.climate_stressed,
            'continent': getattr(self, 'continent', 'Unknown'),
            'vulnerability': getattr(self, 'climate_vulnerability', 0),
            'production': self.current_output_quantity
        } 