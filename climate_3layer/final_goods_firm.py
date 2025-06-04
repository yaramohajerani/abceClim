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
        
        # Climate stress parameters from configuration
        climate_config = config['climate']
        base_vulnerability = climate_config['base_vulnerability']
        vulnerability_variance = climate_config['vulnerability_variance']
        self.climate_vulnerability = base_vulnerability + (self.id * vulnerability_variance)
        self.chronic_stress_accumulated = 1.0  # Multiplicative factor
        self.climate_stressed = False  # Track if currently stressed
        
        # Overhead costs (CapEx, legal, damages, business interruptions, etc.)
        self.base_overhead = production_config.get('base_overhead', 1.0)  # Fixed base overhead per round
        self.current_overhead = self.base_overhead  # Current overhead (increases with climate stress)
        
        # Climate cost sharing parameters
        cost_sharing_config = climate_config.get('cost_sharing', {'customer_share': 0.5})
        self.customer_share = cost_sharing_config['customer_share']
        self.producer_share = 1.0 - self.customer_share
        
        # Financial tracking for dynamic pricing
        self.total_input_costs = 0
        self.total_overhead_costs = 0  # Track overhead separately
        self.overhead_absorbed = 0     # How much overhead firm absorbed this round
        self.overhead_passed_to_customers = 0  # How much overhead passed to price
        self.revenue = 0
        self.profit = 0
        self.profit_margin = production_config.get('profit_margin', 0.0)
        self.actual_margin = 0
        
        # No initial price calculation - price will be calculated dynamically after purchasing inputs
        self.price = {self.output: 0.0}  # Placeholder, will be set by calculate_dynamic_price()
        
        # Create production function
        self.pf = self.create_cobb_douglas(self.output, self.current_output_quantity, self.inputs)
        
        # Track production data for proper logging
        self.production_this_round = 0
        self.sales_this_round = 0
        self.labor_purchased = 0
        self.intermediate_goods_purchased = 0
        self.inventory_at_start = self[self.output]
        
        # Store household count for distribution
        self.num_households = config['household_count']
        
        print(f"Final Goods Firm {self.id} initialized:")
        print(f"  Initial money: ${initial_money}")
        print(f"  Production capacity: {self.base_output_quantity}")
        print(f"  Climate vulnerability: {self.climate_vulnerability:.3f}")
        print(f"  Will distribute to {self.num_households} households")

    def start_round(self):
        """Called at the start of each round to reset tracking variables"""
        self.production_this_round = 0
        self.sales_this_round = 0
        self.labor_purchased = 0
        self.intermediate_goods_purchased = 0
        self.inventory_at_start = self[self.output]
        self.debt_created_this_round = 0  # Track debt created for survival purchasing

    def buy_inputs_optimally(self):
        """ Buy all inputs with optimal money allocation based on Cobb-Douglas exponents to maximize production """
        print(f"    Final Goods Firm {self.id}: Starting optimal input purchasing with ${self['money']:.2f}")
        
        # Get all input offers (only call this once!)
        intermediate_goods_offers = self.get_offers("intermediate_good")
        labor_offers = self.get_offers("labor")
        
        available_money = self['money']
        current_inventory = self[self.output]
        
        print(f"      Current inventory: {current_inventory:.2f}")
        
        # Calculate optimal budget allocation for total available money
        optimal_allocation = self.calculate_optimal_input_allocation(available_money, self.inputs)
        
        print(f"      Optimal allocation (total budget): Labor: ${optimal_allocation['labor']:.2f}, Intermediate goods: ${optimal_allocation['intermediate_good']:.2f}")
        
        # Track starting inventories
        labor_start = self['labor']
        intermediate_goods_start = self['intermediate_good']
        total_spent = 0
        
        # Process intermediate goods offers (pure market-based purchasing)
        intermediate_budget = optimal_allocation['intermediate_good']
        intermediate_spent = 0
        
        print(f"      INTERMEDIATE GOODS PURCHASING:")
        print(f"        Budget available: ${intermediate_budget:.2f}")
        
        for offer in intermediate_goods_offers:
            if intermediate_spent >= intermediate_budget:
                break
                
            # Pure market-based purchasing within budget
            if intermediate_spent + (offer.quantity * offer.price) <= intermediate_budget:
                # Full purchase within budget
                purchase_quantity = offer.quantity
                purchase_reason = "REGULAR"
            elif (intermediate_budget - intermediate_spent) > 0.01:
                # Partial purchase within remaining budget
                affordable_quantity = (intermediate_budget - intermediate_spent) / offer.price
                if affordable_quantity > 0.01:
                    purchase_quantity = affordable_quantity
                    purchase_reason = "PARTIAL"
                else:
                    break
            else:
                break
            
            # Execute the purchase
            purchase_cost = purchase_quantity * offer.price
            
            if purchase_quantity == offer.quantity:
                self.accept(offer)
                print(f"        {purchase_reason}: Accepted full intermediate offer: {offer.quantity:.2f} units for ${purchase_cost:.2f}")
            else:
                self.accept(offer, quantity=purchase_quantity)
                print(f"        {purchase_reason}: Partially accepted intermediate offer: {purchase_quantity:.2f} units for ${purchase_cost:.2f}")
            
            intermediate_spent += purchase_cost
        
        # Process labor offers (pure market-based purchasing)
        labor_budget = optimal_allocation['labor']
        labor_spent = 0
        
        print(f"      LABOR PURCHASING:")
        print(f"        Budget available: ${labor_budget:.2f}")
        
        for offer in labor_offers:
            if labor_spent >= labor_budget:
                break
                
            # Pure market-based purchasing within budget
            if labor_spent + (offer.quantity * offer.price) <= labor_budget:
                # Full purchase within budget
                purchase_quantity = offer.quantity
                purchase_reason = "REGULAR"
            elif (labor_budget - labor_spent) > 0.01:
                # Partial purchase within remaining budget
                affordable_quantity = (labor_budget - labor_spent) / offer.price
                if affordable_quantity > 0.01:
                    purchase_quantity = affordable_quantity
                    purchase_reason = "PARTIAL"
                else:
                    break
            else:
                break
            
            # Execute the purchase
            purchase_cost = purchase_quantity * offer.price
            
            if purchase_quantity == offer.quantity:
                self.accept(offer)
                print(f"        {purchase_reason}: Accepted full labor offer: {offer.quantity:.2f} units for ${purchase_cost:.2f}")
            else:
                self.accept(offer, quantity=purchase_quantity)
                print(f"        {purchase_reason}: Partially accepted labor offer: {purchase_quantity:.2f} units for ${purchase_cost:.2f}")
            
            labor_spent += purchase_cost
        
        total_spent = intermediate_spent + labor_spent
        
        # Track purchases and input costs for dynamic pricing
        labor_end = self['labor']
        intermediate_goods_end = self['intermediate_good']
        self.labor_purchased = labor_end - labor_start
        self.intermediate_goods_purchased = intermediate_goods_end - intermediate_goods_start
        self.total_input_costs = total_spent  # Track total costs for dynamic pricing
        
        print(f"    Final Goods Firm {self.id}: Input purchasing complete:")
        print(f"      Total spent: ${total_spent:.2f}")
        print(f"      Intermediate goods: purchased {self.intermediate_goods_purchased:.2f}")
        print(f"      Labor: purchased {self.labor_purchased:.2f}")
        print(f"      Money remaining: ${self['money']:.2f}")

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

    def calculate_dynamic_price(self):
        """Calculate price dynamically based on input costs, overhead, and cost sharing"""
        if self.production_this_round > 0:
            # Calculate input cost per unit
            input_cost_per_unit = self.total_input_costs / self.production_this_round
            
            # Calculate overhead cost per unit 
            overhead_cost_per_unit = self.current_overhead / self.production_this_round
            
            # Split overhead according to customer_share parameter
            overhead_to_customers = overhead_cost_per_unit * self.customer_share
            overhead_absorbed_by_firm = overhead_cost_per_unit * self.producer_share
            
            # Track overhead costs for financial reporting
            self.overhead_absorbed = overhead_absorbed_by_firm * self.production_this_round
            self.overhead_passed_to_customers = overhead_to_customers * self.production_this_round
            self.total_overhead_costs = self.current_overhead
            
            # Price = input costs + profit margin + customer's share of overhead
            base_cost_per_unit = input_cost_per_unit + overhead_to_customers
            target_price = base_cost_per_unit * (1 + self.profit_margin)
            
            self.price[self.output] = target_price
            
            # Deduct absorbed overhead costs from firm's money
            money_before = self['money']
            self.destroy('money', self.overhead_absorbed)
            money_after = self['money']
            
            print(f"    Dynamic pricing for Final Goods Firm {self.id}:")
            print(f"      Input cost per unit: ${input_cost_per_unit:.2f}")
            print(f"      Overhead per unit: ${overhead_cost_per_unit:.2f} (total overhead: ${self.current_overhead:.2f})")
            print(f"      Customer bears: ${overhead_to_customers:.2f}/unit ({self.customer_share:.1%})")
            print(f"      Firm absorbs: ${overhead_absorbed_by_firm:.2f}/unit ({self.producer_share:.1%})")
            print(f"      New price: ${target_price:.2f}")
            print(f"      💰 Overhead cost deducted: ${self.overhead_absorbed:.2f} (Money: ${money_before:.2f} → ${money_after:.2f})")
        else:
            print(f"    Final Goods Firm {self.id}: No production, keeping previous price")

    def sell_final_goods(self):
        """ Sell final goods to households """
        # First calculate the price based on this round's costs
        self.calculate_dynamic_price()
        
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
        
        # Calculate revenue and profit (including overhead absorption)
        self.revenue = self.sales_this_round * self.price[self.output]
        self.profit = self.revenue - self.total_input_costs - self.overhead_absorbed
        if self.total_input_costs > 0:
            self.actual_margin = self.profit / self.total_input_costs
        else:
            self.actual_margin = 0
        
        # Log the data using abcEconomics logging
        self.log('production', {
            'production': self.production_this_round,
            'sales': self.sales_this_round,
            'inventory_change': inventory_change,
            'cumulative_inventory': cumulative_inventory,
            'labor_purchased': self.labor_purchased,
            'intermediate_goods_purchased': self.intermediate_goods_purchased,
            'money': current_money,
            'debt_created_this_round': self.debt_created_this_round,
            'revenue': self.revenue,
            'input_costs': self.total_input_costs,
            'overhead_total': self.total_overhead_costs,
            'overhead_absorbed': self.overhead_absorbed,
            'overhead_passed_to_customers': self.overhead_passed_to_customers,
            'profit': self.profit,
            'target_margin': self.profit_margin,
            'actual_margin': self.actual_margin,
            'base_overhead': self.base_overhead,
            'current_overhead': self.current_overhead,
            'price': self.price[self.output]
        })
        
        print(f"    Final Goods Firm {self.id}: Logged - Production: {self.production_this_round:.2f}, Sales: {self.sales_this_round:.2f}, Labor: {self.labor_purchased:.2f}, Intermediate goods: {self.intermediate_goods_purchased:.2f}, Inventory: {cumulative_inventory:.2f}, Money: ${current_money:.2f}, Price: ${self.price[self.output]:.2f}, Overhead: ${self.current_overhead:.2f}, Profit: ${self.profit:.2f}, Debt created this round: ${self.debt_created_this_round:.2f}")

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
        stress_factor = 1.0 - (self.climate_vulnerability * random.uniform(0.2, 0.8))
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