import abcEconomics as abce
import random
import sys
import os
# Add the root directory to Python path to find the climate framework
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from climate_framework import add_climate_capabilities


@add_climate_capabilities
class FinalGoodsFirm(abce.Agent, abce.Firm):
    def init(self, config):
        """ Final goods firms are the third layer in the supply chain.
        They use labor and intermediate goods to produce final goods that will be consumed by households.
        They are typically least vulnerable to direct climate stress.
        
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
        
        # Calculate minimum production responsibility based on household survival needs
        # This ensures coordination between household needs and firm production
        household_minimum_survival = config.get('household_minimum_survival_consumption', 0.0)
        num_final_goods_firms = config['final_goods_firm_count']
        num_households = config['household_count']
        
        # Calculate total minimum needed for ALL households
        total_minimum_needed_all_households = household_minimum_survival * num_households
        
        # Each firm is responsible for their share of the total
        # Add a small safety buffer (10%) to account for market inefficiencies
        safety_buffer = 1.1
        self.minimum_production_per_household = household_minimum_survival  # Each household needs this amount
        self.total_minimum_production_responsibility = (total_minimum_needed_all_households / num_final_goods_firms) * safety_buffer
        
        print(f"  Minimum production calculation:")
        print(f"    Household survival consumption: {household_minimum_survival:.3f} per household")
        print(f"    Number of households: {num_households}")
        print(f"    Total minimum needed (all households): {total_minimum_needed_all_households:.3f}")
        print(f"    Number of final goods firms: {num_final_goods_firms}")
        print(f"    This firm's responsibility: {self.total_minimum_production_responsibility:.3f}")
        print(f"    Safety buffer: {safety_buffer:.1f}")
        
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
        self.intermediate_goods_purchased = 0
        self.inventory_at_start = self[self.output]
        
        # Store household count for distribution
        self.num_households = num_households
        
        print(f"Final Goods Firm {self.id} initialized:")
        print(f"  Initial money: ${initial_money}")
        print(f"  Production capacity: {self.base_output_quantity}")
        print(f"  Minimum production per household: {self.minimum_production_per_household:.3f}")
        print(f"  Total minimum production responsibility: {self.total_minimum_production_responsibility:.3f}")
        print(f"  Climate vulnerability: {self.climate_vulnerability:.3f}")
        print(f"  Price: ${self.price[self.output]}")
        print(f"  Will distribute to {self.num_households} households")

    def start_round(self):
        """Called at the start of each round to reset tracking variables"""
        self.production_this_round = 0
        self.sales_this_round = 0
        self.labor_purchased = 0
        self.intermediate_goods_purchased = 0
        self.inventory_at_start = self[self.output]

    def buy_inputs_optimally(self):
        """ Buy all inputs with optimal money allocation based on Cobb-Douglas exponents to maximize production """
        print(f"    Final Goods Firm {self.id}: Starting optimal input purchasing with ${self['money']:.2f}")
        
        # Get all input offers (only call this once!)
        intermediate_goods_offers = self.get_offers("intermediate_good")
        labor_offers = self.get_offers("labor")
        
        available_money = self['money']
        current_inventory = self[self.output]
        
        # Calculate minimum inputs needed to ensure minimum production for households
        total_minimum_needed = self.total_minimum_production_responsibility
        minimum_production_needed = max(0, total_minimum_needed - current_inventory)
        
        print(f"      Current inventory: {current_inventory:.2f}")
        print(f"      Total minimum needed for this firm's responsibility: {total_minimum_needed:.2f}")
        print(f"      Additional production needed: {minimum_production_needed:.2f}")
        
        # Calculate inputs needed for minimum production
        minimum_inputs_needed = {}
        if minimum_production_needed > 0:
            # For Cobb-Douglas Q = A * L^α * K^β where α + β = 1
            # If we want Q = minimum_production_needed and symmetric inputs L = K
            # Then: Q = A * L^α * L^β = A * L^(α+β) = A * L^1 = A * L
            # So: L = Q/A = minimum_production_needed / current_output_quantity
            required_input_level = minimum_production_needed / self.current_output_quantity
            
            for input_good in self.inputs.keys():
                minimum_inputs_needed[input_good] = required_input_level
        
        print(f"      Minimum inputs needed: {minimum_inputs_needed}")
        
        # Calculate optimal budget allocation for total available money
        optimal_allocation = self.calculate_optimal_input_allocation(available_money, self.inputs)
        
        print(f"      Optimal allocation (total budget): Labor: ${optimal_allocation['labor']:.2f}, Intermediate goods: ${optimal_allocation['intermediate_good']:.2f}")
        
        # Track starting inventories
        labor_start = self['labor']
        intermediate_goods_start = self['intermediate_good']
        total_spent = 0
        survival_spending = 0
        
        # Process intermediate goods offers (survival + regular in one pass)
        minimum_intermediate_needed = minimum_inputs_needed.get('intermediate_good', 0)
        intermediate_budget = optimal_allocation['intermediate_good']
        intermediate_spent = 0
        intermediate_survival_bought = 0
        
        print(f"      INTERMEDIATE GOODS PURCHASING:")
        print(f"        Minimum needed for survival: {minimum_intermediate_needed:.2f}")
        print(f"        Total budget available: ${intermediate_budget:.2f}")
        
        for offer in intermediate_goods_offers:
            if intermediate_spent >= intermediate_budget:
                break
                
            # Determine purchase type and quantity
            purchase_quantity = 0
            purchase_reason = ""
            
            if minimum_intermediate_needed > 0:
                # Priority 1: Survival purchasing (even if it exceeds budget)
                survival_purchase = min(offer.quantity, minimum_intermediate_needed)
                purchase_quantity = survival_purchase
                purchase_reason = "SURVIVAL"
                minimum_intermediate_needed -= survival_purchase
                intermediate_survival_bought += survival_purchase
                
            elif intermediate_spent + (offer.quantity * offer.price) <= intermediate_budget:
                # Priority 2: Regular budget-based purchasing
                purchase_quantity = offer.quantity
                purchase_reason = "REGULAR"
                
            elif (intermediate_budget - intermediate_spent) > 0.01:
                # Priority 3: Partial purchase within remaining budget
                affordable_quantity = (intermediate_budget - intermediate_spent) / offer.price
                if affordable_quantity > 0.01:
                    purchase_quantity = affordable_quantity
                    purchase_reason = "PARTIAL"
            
            # Execute the purchase
            if purchase_quantity > 0:
                purchase_cost = purchase_quantity * offer.price
                
                if purchase_quantity == offer.quantity:
                    self.accept(offer)
                    print(f"        {purchase_reason}: Accepted full intermediate offer: {offer.quantity:.2f} units for ${purchase_cost:.2f}")
                else:
                    self.accept(offer, quantity=purchase_quantity)
                    print(f"        {purchase_reason}: Partially accepted intermediate offer: {purchase_quantity:.2f} units for ${purchase_cost:.2f}")
                
                intermediate_spent += purchase_cost
                if purchase_reason == "SURVIVAL":
                    survival_spending += purchase_cost
            else:
                print(f"        SKIPPED: Intermediate offer: {offer.quantity:.2f} units for ${offer.quantity * offer.price:.2f}")
        
        # Process labor offers (survival + regular in one pass)
        minimum_labor_needed = minimum_inputs_needed.get('labor', 0)
        labor_budget = optimal_allocation['labor']
        labor_spent = 0
        labor_survival_bought = 0
        
        print(f"      LABOR PURCHASING:")
        print(f"        Minimum needed for survival: {minimum_labor_needed:.2f}")
        print(f"        Total budget available: ${labor_budget:.2f}")
        
        for offer in labor_offers:
            if labor_spent >= labor_budget:
                break
                
            # Determine purchase type and quantity
            purchase_quantity = 0
            purchase_reason = ""
            
            if minimum_labor_needed > 0:
                # Priority 1: Survival purchasing (even if it exceeds budget)
                survival_purchase = min(offer.quantity, minimum_labor_needed)
                purchase_quantity = survival_purchase
                purchase_reason = "SURVIVAL"
                minimum_labor_needed -= survival_purchase
                labor_survival_bought += survival_purchase
                
            elif labor_spent + (offer.quantity * offer.price) <= labor_budget:
                # Priority 2: Regular budget-based purchasing
                purchase_quantity = offer.quantity
                purchase_reason = "REGULAR"
                
            elif (labor_budget - labor_spent) > 0.01:
                # Priority 3: Partial purchase within remaining budget
                affordable_quantity = (labor_budget - labor_spent) / offer.price
                if affordable_quantity > 0.01:
                    purchase_quantity = affordable_quantity
                    purchase_reason = "PARTIAL"
            
            # Execute the purchase
            if purchase_quantity > 0:
                purchase_cost = purchase_quantity * offer.price
                
                if purchase_quantity == offer.quantity:
                    self.accept(offer)
                    print(f"        {purchase_reason}: Accepted full labor offer: {offer.quantity:.2f} units for ${purchase_cost:.2f}")
                else:
                    self.accept(offer, quantity=purchase_quantity)
                    print(f"        {purchase_reason}: Partially accepted labor offer: {purchase_quantity:.2f} units for ${purchase_cost:.2f}")
                
                labor_spent += purchase_cost
                if purchase_reason == "SURVIVAL":
                    survival_spending += purchase_cost
            else:
                print(f"        SKIPPED: Labor offer: {offer.quantity:.2f} units for ${offer.quantity * offer.price:.2f}")
        
        total_spent = intermediate_spent + labor_spent
        regular_spending = total_spent - survival_spending
        
        # Track purchases
        labor_end = self['labor']
        intermediate_goods_end = self['intermediate_good']
        self.labor_purchased = labor_end - labor_start
        self.intermediate_goods_purchased = intermediate_goods_end - intermediate_goods_start
        
        print(f"    Final Goods Firm {self.id}: Input purchasing complete:")
        print(f"      Total spent: ${total_spent:.2f} (survival: ${survival_spending:.2f}, regular: ${regular_spending:.2f})")
        print(f"      Intermediate goods: purchased {self.intermediate_goods_purchased:.2f} (survival: {intermediate_survival_bought:.2f})")
        print(f"      Labor: purchased {self.labor_purchased:.2f} (survival: {labor_survival_bought:.2f})")
        print(f"      Money remaining: ${self['money']:.2f}")
        
        if self['money'] < 0:
            print(f"      WARNING: Firm went into debt (${self['money']:.2f}) to ensure minimum production for households!")

    def production(self):
        """ Produce final goods using intermediate goods and labor """
        # Log inventory before production
        inventory_before = self[self.output]
        print(f"    Final Goods Firm {self.id}: BEFORE production:")
        print(f"      Current output quantity (multiplier): {self.current_output_quantity}")
        print(f"      Inputs recipe: {self.inputs}")
        for good in ['money', 'labor', 'intermediate_good', self.output]:
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
            print(f"    Final Goods Firm {self.id}: Production successful")
        except Exception as e:
            print(f"    Final Goods Firm {self.id}: Production failed: {e}")
        
        # Calculate actual production this round
        inventory_after = self[self.output]
        self.production_this_round = inventory_after - inventory_before
        
        # Log inventory after production
        print(f"    Final Goods Firm {self.id}: AFTER production:")
        for good in ['money', 'labor', 'intermediate_good', self.output]:
            print(f"      {good}: {self[good]:.3f}")
        print(f"      Production this round: {self.production_this_round:.3f}")

    def sell_final_goods(self):
        """ Sell final goods to households """
        final_goods_stock = self[self.output]
        self.inventory_before_sales = final_goods_stock  # Track inventory before creating offers
        
        print(f"    Final Goods Firm {self.id}: Has {final_goods_stock:.2f} {self.output}s to sell")
        if final_goods_stock > 0:
            # Distribute sales among households - get actual household count dynamically
            # Use the household count from configuration (no fallback since config is required)
            num_households = self.num_households
            quantity_per_household = final_goods_stock / num_households
            for household_id in range(num_households):
                if quantity_per_household > 0:
                    print(f"      Offering {quantity_per_household:.2f} {self.output}s to household {household_id} at price {self.price[self.output]}")
                    self.sell(('household', household_id), self.output, 
                             quantity_per_household, self.price[self.output])
        else:
            print(f"    Final Goods Firm {self.id}: No {self.output}s to sell")

    def calculate_sales_after_market_clearing(self):
        """Calculate actual sales after market clearing has occurred"""
        if hasattr(self, 'inventory_before_sales'):
            current_inventory = self[self.output]
            self.sales_this_round = self.inventory_before_sales - current_inventory
            print(f"    Final Goods Firm {self.id}: Sales calculated after market clearing: {self.sales_this_round:.2f} {self.output}s")
        else:
            self.sales_this_round = 0
            print(f"    Final Goods Firm {self.id}: No sales tracking data available")

    def log_round_data(self):
        """Log production, sales, and inventory data for this round"""
        # Calculate inventory change and cumulative inventory
        inventory_change = self.production_this_round - self.sales_this_round
        cumulative_inventory = self[self.output]
        current_money = self['money']
        
        # Check if firm is in debt and if minimum production for households is met
        is_in_debt = current_money < 0
        total_minimum_needed = self.total_minimum_production_responsibility
        minimum_production_met = cumulative_inventory >= total_minimum_needed
        
        # Log the data using abcEconomics logging
        self.log('production', {
            'production': self.production_this_round,
            'sales': self.sales_this_round,
            'inventory_change': inventory_change,
            'cumulative_inventory': cumulative_inventory,
            'labor_purchased': self.labor_purchased,
            'intermediate_goods_purchased': self.intermediate_goods_purchased,
            'money': current_money,
            'is_in_debt': is_in_debt,
            'minimum_production_responsibility': self.total_minimum_production_responsibility,
            'total_minimum_needed': total_minimum_needed,
            'minimum_production_met': minimum_production_met
        })
        
        print(f"    Final Goods Firm {self.id}: Logged - Production: {self.production_this_round:.2f}, Sales: {self.sales_this_round:.2f}, Labor: {self.labor_purchased:.2f}, Intermediate goods: {self.intermediate_goods_purchased:.2f}, Inventory: {cumulative_inventory:.2f}, Money: ${current_money:.2f}, In debt: {is_in_debt}, Min. production met: {minimum_production_met}")

    def apply_climate_stress(self, stress_factor):
        """ Apply climate stress by reducing production capacity """
        self.climate_stressed = True
        original_quantity = self.current_output_quantity
        self.current_output_quantity = self.base_output_quantity * stress_factor * self.chronic_stress_accumulated
        print(f"  Final Goods Firm {self.id}: CLIMATE STRESS applied! Production: {original_quantity:.2f} -> {self.current_output_quantity:.2f}")

    def reset_climate_stress(self):
        """ Reset production to normal levels """
        if self.climate_stressed:
            self.climate_stressed = False
            self.current_output_quantity = self.base_output_quantity * self.chronic_stress_accumulated
            print(f"  Final Goods Firm {self.id}: Climate stress cleared, production restored to {self.current_output_quantity:.2f}")

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