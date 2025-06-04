import abcEconomics as abce
import random
import sys
import os
# Add the root directory to Python path to find the climate framework
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from climate_framework import add_climate_capabilities


@add_climate_capabilities
class CommodityProducer(abce.Agent, abce.Firm):
    def init(self, config):
        """ Commodity producers are the first layer in the supply chain.
        They use labor to produce raw commodities that will be used by intermediary firms.
        They are vulnerable to climate stress which affects their productivity.
        
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
        
        # Calculate minimum production responsibility for intermediary firms' survival needs
        self.minimum_production_responsibility = config.get('commodity_minimum_per_producer', 0.0)
        
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
        self.inventory_at_start = self[self.output]
        self.debt_created_this_round = 0  # Track debt created for survival purchasing
        
        # Get intermediary firm count from config for proper distribution
        self.intermediary_count = config['intermediary_count']
        
        print(f"Commodity Producer {self.id} initialized:")
        print(f"  Initial money: ${initial_money}")
        print(f"  Production capacity: {self.base_output_quantity}")
        print(f"  Minimum production responsibility: {self.minimum_production_responsibility:.3f}")
        print(f"  Climate vulnerability: {self.climate_vulnerability:.3f}")
        print(f"  Profit margin target: {self.profit_margin*100:.1f}%")
        print(f"  Will distribute to {self.intermediary_count} intermediary firms")

    def start_round(self):
        """Called at the start of each round to reset tracking variables"""
        self.production_this_round = 0
        self.sales_this_round = 0
        self.labor_purchased = 0
        self.inventory_at_start = self[self.output]
        self.debt_created_this_round = 0  # Track debt created for survival purchasing
        self.total_input_costs = 0
        self.total_overhead_costs = 0  # Track overhead separately
        self.overhead_absorbed = 0     # How much overhead firm absorbed this round
        self.overhead_passed_to_customers = 0  # How much overhead passed to price
        self.revenue = 0
        self.profit = 0
        self.climate_cost_burden = 0  # Track how much extra cost from climate we absorbed

    def buy_labor(self):
        """ Buy labor from households and track costs for dynamic pricing """
        labor_start = self['labor']
        offers = self.get_offers("labor")
        available_money = self['money']
        
        print(f"    Commodity Producer {self.id}: Has ${available_money:.2f}, received {len(offers)} labor offers")
        
        total_spent = 0
        
        for offer in offers:
            # Simple market purchasing: buy what we can afford
            if total_spent + (offer.quantity * offer.price) <= available_money:
                purchase_cost = offer.quantity * offer.price
                self.accept(offer)
                total_spent += purchase_cost
                print(f"      Accepted full labor offer: {offer.quantity:.2f} units for ${purchase_cost:.2f}")
            else:
                # Partial purchase within remaining budget
                remaining_budget = available_money - total_spent
                if remaining_budget > 0.01:
                    affordable_quantity = remaining_budget / offer.price
                    if affordable_quantity > 0.01:
                        purchase_cost = affordable_quantity * offer.price
                        self.accept(offer, quantity=affordable_quantity)
                        total_spent += purchase_cost
                        print(f"      Partially accepted labor offer: {affordable_quantity:.2f} units for ${purchase_cost:.2f}")
                    break
                else:
                    print(f"      Budget exhausted, skipping remaining offers")
                    break
        
        # Track labor purchased this round and costs
        labor_end = self['labor']
        self.labor_purchased = labor_end - labor_start
        self.total_input_costs += total_spent  # Track for dynamic pricing
        
        print(f"    Commodity Producer {self.id}: Labor purchasing complete:")
        print(f"      Total spent: ${total_spent:.2f}")
        print(f"      Labor purchased: {self.labor_purchased:.2f}")
        print(f"      Money remaining: ${self['money']:.2f}")

    def production(self):
        """ Produce commodities using labor """
        # Log inventory before production
        inventory_before = self[self.output]
        print(f"    Commodity Producer {self.id}: BEFORE production:")
        print(f"      Current output quantity (multiplier): {self.current_output_quantity}")
        print(f"      Inputs recipe: {self.inputs}")
        for good in ['money', 'labor', self.output]:
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
            print(f"    Commodity Producer {self.id}: Production successful")
        except Exception as e:
            print(f"    Commodity Producer {self.id}: Production failed: {e}")
        
        # Calculate actual production this round
        inventory_after = self[self.output]
        self.production_this_round = inventory_after - inventory_before
        
        # Log inventory after production
        print(f"    Commodity Producer {self.id}: AFTER production:")
        for good in ['money', 'labor', self.output]:
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
            
            print(f"    Dynamic pricing for Commodity Producer {self.id}:")
            print(f"      Input cost per unit: ${input_cost_per_unit:.2f}")
            print(f"      Overhead per unit: ${overhead_cost_per_unit:.2f} (total overhead: ${self.current_overhead:.2f})")
            print(f"      Customer bears: ${overhead_to_customers:.2f}/unit ({self.customer_share:.1%})")
            print(f"      Firm absorbs: ${overhead_absorbed_by_firm:.2f}/unit ({self.producer_share:.1%})")
            print(f"      New price: ${target_price:.2f}")
            print(f"      💰 Overhead cost deducted: ${self.overhead_absorbed:.2f} (Money: ${money_before:.2f} → ${money_after:.2f})")
        else:
            print(f"    Commodity Producer {self.id}: No production, keeping previous price")

    def sell_commodities(self):
        """ Sell commodities to intermediary firms at dynamically calculated price """
        # First calculate the price based on this round's costs
        self.calculate_dynamic_price()
        
        commodity_stock = self[self.output]
        self.inventory_before_sales = commodity_stock  # Track inventory before creating offers
        
        print(f"    Commodity Producer {self.id}: Has {commodity_stock:.2f} {self.output}s to sell at ${self.price[self.output]:.2f}")
        if commodity_stock > 0:
            # Distribute sales among intermediary firms
            quantity_per_firm = commodity_stock / self.intermediary_count  # Assuming evenly distributed
            for intermediary_id in range(self.intermediary_count):
                if quantity_per_firm > 0:
                    print(f"      Offering {quantity_per_firm:.2f} {self.output}s to intermediary_firm {intermediary_id} at price {self.price[self.output]}")
                    self.sell(('intermediary_firm', intermediary_id), self.output, 
                             quantity_per_firm, self.price[self.output])
        else:
            print(f"    Commodity Producer {self.id}: No {self.output}s to sell")

    def calculate_sales_after_market_clearing(self):
        """Calculate actual sales after market clearing has occurred"""
        if hasattr(self, 'inventory_before_sales'):
            current_inventory = self[self.output]
            self.sales_this_round = self.inventory_before_sales - current_inventory
            print(f"    Commodity Producer {self.id}: Sales calculated after market clearing: {self.sales_this_round:.2f} {self.output}s")
        else:
            self.sales_this_round = 0
            print(f"    Commodity Producer {self.id}: No sales tracking data available")

    def log_round_data(self):
        """Log comprehensive production, sales, and financial data"""
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
        
        # Check if minimum production for intermediary firms is met
        minimum_production_met = cumulative_inventory >= self.minimum_production_responsibility
        
        # Log the data using abcEconomics logging
        self.log('production', {
            'production': self.production_this_round,
            'sales': self.sales_this_round,
            'inventory_change': inventory_change,
            'cumulative_inventory': cumulative_inventory,
            'labor_purchased': self.labor_purchased,
            'money': current_money,
            'minimum_production_responsibility': self.minimum_production_responsibility,
            'minimum_production_met': minimum_production_met,
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
        
        print(f"    Commodity Producer {self.id}: Logged - Production: {self.production_this_round:.2f}, Sales: {self.sales_this_round:.2f}, Labor purchased: {self.labor_purchased:.2f}, Inventory: {cumulative_inventory:.2f}, Money: ${current_money:.2f}, Price: ${self.price[self.output]:.2f}, Overhead: ${self.current_overhead:.2f}, Profit: ${self.profit:.2f}, Min. production met: {minimum_production_met}, Debt created this round: ${self.debt_created_this_round:.2f}")



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