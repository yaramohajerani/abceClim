import abcEconomics as abce
import random
import sys
import os
# Add the root directory to Python path to find the climate framework
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from climate_framework import add_climate_capabilities


@add_climate_capabilities
class IntermediaryFirm(abce.Agent, abce.Firm):
    def init(self, config):
        """ Intermediary firms are the second layer in the supply chain.
        They use labor and commodities to produce intermediate goods that will be used by final goods firms.
        They are also vulnerable to climate stress but typically less than commodity producers.
        
        Args:
            config: Configuration dictionary with production parameters, climate settings, etc.
        """
        # Initialize money
        initial_money = config['initial_money']
        self.create('money', initial_money)
        
        # Initialize inventory from configuration
        initial_inventory = config.get('initial_inventory', {})
        for good, quantity in initial_inventory.items():
            self.create(good, quantity)
        
        # Production parameters from configuration
        production_config = config['production']
        self.inputs = production_config['inputs']
        self.output = production_config['output']
        self.base_output_quantity = production_config['base_output_quantity']
        self.current_output_quantity = self.base_output_quantity
        
        # Climate stress parameters from configuration
        climate_config = config['climate']
        base_vulnerability = climate_config['base_vulnerability']
        vulnerability_variance = climate_config['vulnerability_variance']
        self.climate_vulnerability = base_vulnerability + (self.id * vulnerability_variance)
        self.chronic_stress_accumulated = 1.0  # Multiplicative factor
        self.climate_stressed = False  # Track if currently stressed
        
        # Pricing from configuration
        self.price = {self.output: production_config['price']}
        
        # Create production function
        self.pf = self.create_cobb_douglas(self.output, self.current_output_quantity, self.inputs)
        
        # Track production data for proper logging
        self.production_this_round = 0
        self.sales_this_round = 0
        self.labor_purchased = 0
        self.commodities_purchased = 0
        self.inventory_at_start = self[self.output]
        
        # Get final goods firm count from config for proper distribution
        self.final_goods_count = config['final_goods_count']
        
        print(f"Intermediary Firm {self.id} initialized:")
        print(f"  Initial money: ${initial_money}")
        print(f"  Production capacity: {self.base_output_quantity}")
        print(f"  Climate vulnerability: {self.climate_vulnerability:.3f}")
        print(f"  Price: ${self.price[self.output]}")
        print(f"  Will distribute to {self.final_goods_count} final goods firms")

    def start_round(self):
        """Called at the start of each round to reset tracking variables"""
        self.production_this_round = 0
        self.sales_this_round = 0
        self.labor_purchased = 0
        self.commodities_purchased = 0
        self.inventory_at_start = self[self.output]

    def buy_commodities(self):
        """ Buy commodities from commodity producers """
        commodities_start = self['commodity']
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
        
        # Track commodities purchased this round
        commodities_end = self['commodity']
        self.commodities_purchased = commodities_end - commodities_start
        
        print(f"    Intermediary Firm {self.id}: Spent ${total_spent:.2f} on commodities, purchased {self.commodities_purchased:.2f} units")

    def buy_labor(self):
        """ Buy labor from households """
        labor_start = self['labor']
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
        
        # Track labor purchased this round
        labor_end = self['labor']
        self.labor_purchased = labor_end - labor_start
        
        print(f"    Intermediary Firm {self.id}: Spent ${total_spent:.2f} on labor, purchased {self.labor_purchased:.2f} units")

    def production(self):
        """ Produce intermediate goods using labor and commodities """
        # Log inventory before production
        inventory_before = self[self.output]
        print(f"    Intermediary Firm {self.id}: BEFORE production:")
        print(f"      Current output quantity (multiplier): {self.current_output_quantity}")
        print(f"      Inputs recipe: {self.inputs}")
        for good in ['money', 'labor', 'commodity', self.output]:
            print(f"      {good}: {self[good]:.3f}")
        
        # Update production function with current output quantity (accounting for climate stress)
        self.pf = self.create_cobb_douglas(self.output, self.current_output_quantity, self.inputs)
        print(f"      Production function created with multiplier: {self.current_output_quantity}, exponents: {self.inputs}")
        
        # Prepare actual input quantities (what we actually have available)
        actual_inputs = {}
        for input_good in self.inputs.keys():
            actual_inputs[input_good] = self[input_good]
            print(f"      Available {input_good}: {actual_inputs[input_good]:.3f}")
        
        print(f"      Calling production function with actual inputs: {actual_inputs}")
        
        # Manual calculation of expected Cobb-Douglas output for verification
        expected_output = self.current_output_quantity  # multiplier
        for input_good, exponent in self.inputs.items():
            available_quantity = actual_inputs[input_good]
            expected_output *= (available_quantity ** exponent)
        print(f"      Expected Cobb-Douglas output: {self.current_output_quantity} * {' * '.join([f'{actual_inputs[good]}^{exp}' for good, exp in self.inputs.items()])} = {expected_output:.3f}")
        
        try:
            self.produce(self.pf, actual_inputs)
            print(f"    Intermediary Firm {self.id}: Production successful")
        except Exception as e:
            print(f"    Intermediary Firm {self.id}: Production failed: {e}")
        
        # Calculate actual production this round
        inventory_after = self[self.output]
        self.production_this_round = inventory_after - inventory_before
        
        # Log inventory after production
        print(f"    Intermediary Firm {self.id}: AFTER production:")
        for good in ['money', 'labor', 'commodity', self.output]:
            print(f"      {good}: {self[good]:.3f}")
        print(f"      Production this round: {self.production_this_round:.3f}")

    def sell_intermediate_goods(self):
        """ Sell intermediate goods to final goods firms """
        intermediate_stock = self[self.output]
        self.inventory_before_sales = intermediate_stock  # Track inventory before creating offers
        
        print(f"    Intermediary Firm {self.id}: Has {intermediate_stock:.2f} {self.output}s to sell")
        if intermediate_stock > 0:
            # Distribute sales among final goods firms
            quantity_per_firm = intermediate_stock / self.final_goods_count  # Assuming final_goods_count final goods firms
            for final_firm_id in range(self.final_goods_count):
                if quantity_per_firm > 0:
                    print(f"      Offering {quantity_per_firm:.2f} {self.output}s to final_goods_firm {final_firm_id} at price {self.price[self.output]}")
                    self.sell(('final_goods_firm', final_firm_id), self.output, 
                             quantity_per_firm, self.price[self.output])
        else:
            print(f"    Intermediary Firm {self.id}: No {self.output}s to sell")

    def calculate_sales_after_market_clearing(self):
        """Calculate actual sales after market clearing has occurred"""
        if hasattr(self, 'inventory_before_sales'):
            current_inventory = self[self.output]
            self.sales_this_round = self.inventory_before_sales - current_inventory
            print(f"    Intermediary Firm {self.id}: Sales calculated after market clearing: {self.sales_this_round:.2f} {self.output}s")
        else:
            self.sales_this_round = 0
            print(f"    Intermediary Firm {self.id}: No sales tracking data available")

    def log_round_data(self):
        """Log production, sales, and inventory data for this round"""
        # Calculate inventory change and cumulative inventory
        inventory_change = self.production_this_round - self.sales_this_round
        cumulative_inventory = self[self.output]
        current_money = self['money']
        
        # Log the data using abcEconomics logging
        self.log('production', {
            'production': self.production_this_round,
            'sales': self.sales_this_round,
            'inventory_change': inventory_change,
            'cumulative_inventory': cumulative_inventory,
            'labor_purchased': self.labor_purchased,
            'commodities_purchased': self.commodities_purchased,
            'money': current_money
        })
        
        print(f"    Intermediary Firm {self.id}: Logged - Production: {self.production_this_round:.2f}, Sales: {self.sales_this_round:.2f}, Labor: {self.labor_purchased:.2f}, Commodities: {self.commodities_purchased:.2f}, Inventory: {cumulative_inventory:.2f}, Money: ${current_money:.2f}")

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