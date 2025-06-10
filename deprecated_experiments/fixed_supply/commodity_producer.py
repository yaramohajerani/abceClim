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
        """ Commodity producers in the fixed supply model maintain constant output.
        They adjust input purchases based on climate-affected productivity and
        calculate prices dynamically based on costs and desired profit margin.
        
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
        self.desired_output_quantity = production_config['desired_output_quantity']
        self.profit_margin = production_config['profit_margin']
        
        # Financial tracking
        self.debt = 0  # Track total debt
        self.total_input_costs = 0
        self.revenue = 0
        self.profit = 0
        self.actual_margin = 0
        self.climate_cost_burden = 0  # Track how much extra cost from climate we absorbed
        
        # Climate productivity factor (affects how much input needed for output)
        self.climate_productivity = 1.0  # 1.0 means normal, <1.0 means need more inputs
        
        # Climate stress parameters from configuration
        climate_config = config['climate']
        base_vulnerability = climate_config['base_vulnerability']
        vulnerability_variance = climate_config['vulnerability_variance']
        self.climate_vulnerability = base_vulnerability + (self.id * vulnerability_variance)
        self.chronic_stress_accumulated = 1.0  # Multiplicative factor
        self.climate_stressed = False  # Track if currently stressed
        
        # Climate cost sharing parameters
        cost_sharing_config = climate_config.get('cost_sharing', {'customer_share': 0.5})
        self.customer_share = cost_sharing_config['customer_share']
        self.producer_share = 1.0 - self.customer_share
        
        # Calculate initial price from expected costs using actual wage from config
        wage = config['wage']
        expected_labor_cost = self.inputs.get('labor', 0) * wage
        expected_cost_per_unit = expected_labor_cost / self.desired_output_quantity
        initial_price = expected_cost_per_unit * (1 + self.profit_margin)
        self.price = {self.output: initial_price}
        
        # Track production data for proper logging
        self.production_this_round = 0
        self.sales_this_round = 0
        self.labor_purchased = 0
        self.inventory_at_start = self[self.output]
        self.debt_created_this_round = 0
        
        # Get intermediary firm count from config for proper distribution
        self.intermediary_count = config['intermediary_count']
        
        print(f"Fixed Supply Commodity Producer {self.id} initialized:")
        print(f"  Initial money: ${initial_money}")
        print(f"  Desired output: {self.desired_output_quantity} (constant)")
        print(f"  Profit margin target: {self.profit_margin*100:.1f}%")
        print(f"  Initial price: ${initial_price:.2f} (wage: ${wage}, labor: {self.inputs.get('labor', 0)})")
        print(f"  Climate vulnerability: {self.climate_vulnerability:.3f}")
        print(f"  Will distribute to {self.intermediary_count} intermediary firms")

    def start_round(self):
        """Called at the start of each round to reset tracking variables"""
        self.production_this_round = 0
        self.sales_this_round = 0
        self.labor_purchased = 0
        self.inventory_at_start = self[self.output]
        self.debt_created_this_round = 0
        self.total_input_costs = 0
        self.revenue = 0
        self.climate_cost_burden = 0

    def calculate_required_inputs(self):
        """Calculate inputs needed to produce desired output with current climate productivity"""
        required_inputs = {}
        
        # For Cobb-Douglas Q = A * L^α * K^β..., to get desired output:
        # If we want Q = desired_output_quantity and A = desired_output_quantity * climate_productivity
        # Then: desired_output_quantity = (desired_output_quantity * climate_productivity) * L^α * K^β...
        # Simplifying: 1 = climate_productivity * L^α * K^β...
        # So: L^α * K^β... = 1/climate_productivity
        
        # For simple case with single input (labor with exponent α):
        # L^α = 1/climate_productivity, so L = (1/climate_productivity)^(1/α)
        
        productivity_factor = 1.0 / self.climate_productivity if self.climate_productivity > 0 else 999
        
        # For each input, calculate required quantity
        # This assumes inputs work multiplicatively: each input^exponent multiplied together should equal productivity_factor
        # Simple approach: distribute the productivity requirement equally among inputs
        num_inputs = len(self.inputs)
        if num_inputs == 1:
            # Single input case
            for input_good, exponent in self.inputs.items():
                required_inputs[input_good] = productivity_factor ** (1.0 / exponent)
        else:
            # Multiple inputs case - assume balanced inputs
            for input_good, exponent in self.inputs.items():
                # Each input contributes its share: L^α * K^β = productivity_factor
                # Assume L = K for simplicity, then L^(α+β) = productivity_factor, so L = productivity_factor^(1/(α+β))
                total_exponents = sum(self.inputs.values())
                required_inputs[input_good] = productivity_factor ** (exponent / total_exponents / exponent)
                
        return required_inputs

    def buy_labor(self):
        """ Buy labor needed to maintain fixed production output """
        labor_start = self['labor']
        offers = self.get_offers("labor")
        
        # Calculate required labor for desired output using production function
        required_inputs = self.calculate_required_inputs()
        labor_needed = required_inputs.get('labor', 0)
        
        print(f"    Fixed Supply Commodity Producer {self.id}:")
        print(f"      Climate productivity: {self.climate_productivity:.2f}")
        print(f"      Labor needed for {self.desired_output_quantity} output: {labor_needed:.2f}")
        print(f"      Current money: ${self['money']:.2f}, Debt: ${self.debt:.2f}")
        
        labor_purchased = 0
        total_cost = 0
        
        for offer in offers:
            if labor_purchased >= labor_needed:
                break
                
            # Determine how much to buy from this offer
            quantity_to_buy = min(offer.quantity, labor_needed - labor_purchased)
            cost = quantity_to_buy * offer.price
            
            # Check if we need debt to buy (ALWAYS ensure we get the inputs needed)
            if self['money'] < cost:
                debt_needed = cost - self['money']
                self.create('money', debt_needed)
                self.debt += debt_needed
                self.debt_created_this_round += debt_needed
                print(f"      💳 Created ${debt_needed:.2f} debt to maintain fixed production")
            
            # Make the purchase
            if quantity_to_buy == offer.quantity:
                self.accept(offer)
            else:
                self.accept(offer, quantity=quantity_to_buy)
                
            labor_purchased += quantity_to_buy
            total_cost += cost
            self.total_input_costs += cost
            
            print(f"      Bought {quantity_to_buy:.2f} labor for ${cost:.2f}")
        
        self.labor_purchased = labor_purchased
        
        # If we couldn't buy enough, still track what we bought
        if labor_purchased < labor_needed * 0.99:
            print(f"      ⚠️ Could only buy {labor_purchased:.2f} labor (needed {labor_needed:.2f})")
        
        print(f"      Total labor purchased: {labor_purchased:.2f} for ${total_cost:.2f}")
        print(f"      Money remaining: ${self['money']:.2f}")

    def production(self):
        """ Produce commodities using labor with actual production function """
        inventory_before = self[self.output]
        
        print(f"    Fixed Supply Commodity Producer {self.id}: PRODUCTION:")
        print(f"      Target output: {self.desired_output_quantity}")
        print(f"      Climate productivity: {self.climate_productivity:.3f}")
        
        # Create production function with climate-adjusted productivity
        # In fixed supply model, we use desired_output_quantity as the base productivity (A in Cobb-Douglas)
        adjusted_productivity = self.desired_output_quantity * self.climate_productivity
        production_function = self.create_cobb_douglas(self.output, adjusted_productivity, self.inputs)
        
        # Prepare actual input quantities available
        actual_inputs = {}
        for input_good in self.inputs.keys():
            actual_inputs[input_good] = self[input_good]
            print(f"      Available {input_good}: {actual_inputs[input_good]:.3f}")
        
        # Calculate expected output using Cobb-Douglas: Q = A * L^α * K^β...
        expected_output = adjusted_productivity
        for input_good, exponent in self.inputs.items():
            available_quantity = actual_inputs[input_good]
            expected_output *= (available_quantity ** exponent)
        
        print(f"      Expected output: {adjusted_productivity:.3f} * {' * '.join([f'{actual_inputs[good]:.3f}^{exp}' for good, exp in self.inputs.items()])} = {expected_output:.3f}")
        
        # Use the actual production function
        try:
            self.produce(production_function, actual_inputs)
            print(f"      Production function executed successfully")
        except Exception as e:
            print(f"      Production function failed: {e}")
        
        # Calculate actual production this round
        inventory_after = self[self.output]
        self.production_this_round = inventory_after - inventory_before
        
        print(f"      Actual production: {self.production_this_round:.3f}")
        print(f"      Total inventory: {inventory_after:.3f}")
        
        # In fixed supply model, we should produce close to desired amount
        if abs(self.production_this_round - self.desired_output_quantity) > 0.1:
            print(f"      ⚠️ Production deviation: wanted {self.desired_output_quantity}, got {self.production_this_round:.3f}")

    def calculate_dynamic_price(self):
        """Calculate price based on input costs and desired profit margin,
        with configurable cost sharing for climate impacts"""
        if self.production_this_round > 0:
            # Simple cost-plus pricing
            cost_per_unit = self.total_input_costs / self.production_this_round
            
            # For own climate effects: calculate what cost would be without climate impact
            if self.climate_productivity < 1.0:
                # If we have reduced productivity, we needed more inputs to produce the same amount
                # Normal cost would be: cost_per_unit * climate_productivity 
                normal_cost_per_unit = cost_per_unit * self.climate_productivity
                
                # Extra cost due to our own climate productivity loss
                own_climate_extra_cost = cost_per_unit - normal_cost_per_unit
                
                # Split climate cost burden according to configuration
                customer_climate_burden = own_climate_extra_cost * self.customer_share
                producer_climate_burden = own_climate_extra_cost * self.producer_share
                
                # Price = normal cost + margin + customer's share of climate cost
                target_price = normal_cost_per_unit * (1 + self.profit_margin) + customer_climate_burden
                
                # Firm absorbs its share of climate costs
                self.climate_cost_burden = producer_climate_burden * self.production_this_round
                
                print(f"    Dynamic pricing for Commodity Producer {self.id}:")
                print(f"      Cost per unit: ${cost_per_unit:.2f}")
                print(f"      Normal cost (no climate): ${normal_cost_per_unit:.2f}")
                print(f"      Climate impact: ${own_climate_extra_cost:.2f}/unit")
                print(f"      Climate productivity: {self.climate_productivity:.3f}")
                print(f"      Customer bears: ${customer_climate_burden:.2f}/unit ({self.customer_share:.1%})")
                print(f"      Producer bears: ${producer_climate_burden:.2f}/unit ({self.producer_share:.1%})")
                print(f"      Climate cost absorbed this round: ${self.climate_cost_burden:.2f}")
            else:
                # No climate impact - simple cost plus margin
                target_price = cost_per_unit * (1 + self.profit_margin)
                self.climate_cost_burden = 0
                
                print(f"    Dynamic pricing for Commodity Producer {self.id}:")
                print(f"      Cost per unit: ${cost_per_unit:.2f}")
                print(f"      No climate impact")
            
            self.price[self.output] = target_price
            print(f"      New price: ${target_price:.2f}")
        else:
            print(f"    Commodity Producer {self.id}: No production, keeping previous price")

    def sell_commodities(self):
        """ Sell commodities to intermediary firms at dynamically calculated price """
        # First calculate the price based on this round's costs
        self.calculate_dynamic_price()
        
        commodity_stock = self[self.output]
        self.inventory_before_sales = commodity_stock
        
        print(f"    Fixed Supply Commodity Producer {self.id}: Has {commodity_stock:.2f} {self.output}s to sell at ${self.price[self.output]:.2f}")
        if commodity_stock > 0:
            # Distribute sales among intermediary firms
            quantity_per_firm = commodity_stock / self.intermediary_count
            for intermediary_id in range(self.intermediary_count):
                if quantity_per_firm > 0:
                    self.sell(('intermediary_firm', intermediary_id), self.output, 
                             quantity_per_firm, self.price[self.output])

    def calculate_sales_after_market_clearing(self):
        """Calculate actual sales and financial metrics after market clearing"""
        if hasattr(self, 'inventory_before_sales'):
            current_inventory = self[self.output]
            self.sales_this_round = self.inventory_before_sales - current_inventory
            self.revenue = self.sales_this_round * self.price[self.output]
            
            # Calculate profit and actual margin
            if self.sales_this_round > 0:
                self.profit = self.revenue - self.total_input_costs
                self.actual_margin = self.profit / self.revenue if self.revenue > 0 else 0
            else:
                self.profit = -self.total_input_costs
                self.actual_margin = 0
            
            print(f"    Financial summary for Commodity Producer {self.id}:")
            print(f"      Revenue: ${self.revenue:.2f}")
            print(f"      Costs: ${self.total_input_costs:.2f}")
            print(f"      Profit: ${self.profit:.2f}")
            print(f"      Target margin: {self.profit_margin*100:.1f}%")
            print(f"      Actual margin: {self.actual_margin*100:.1f}%")
            print(f"      Climate cost absorbed: ${self.climate_cost_burden:.2f}")
            
            # Automatically repay debt if we have cash
            self.repay_debt()

    def repay_debt(self):
        """Automatically repay debt using available cash after sales"""
        if self.debt > 0 and self['money'] > 0:
            # Determine how much debt we can repay (don't spend all money - keep some for operations)
            available_for_debt = self['money']
            debt_payment = min(available_for_debt, self.debt)
            
            if debt_payment > 0:
                # Reduce money and debt by the payment amount
                self.destroy('money', debt_payment)
                self.debt -= debt_payment
                
                print(f"    💰 Commodity Producer {self.id}: Repaid ${debt_payment:.2f} debt")
                print(f"      Remaining debt: ${self.debt:.2f}, Remaining money: ${self['money']:.2f}")
            
            # Set to zero if very small to avoid floating point issues
            if self.debt < 0.01:
                self.debt = 0

    def log_round_data(self):
        """Log comprehensive data including financial metrics"""
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
            'money': current_money,
            'debt': self.debt,
            'debt_created_this_round': self.debt_created_this_round,
            'revenue': self.revenue,
            'costs': self.total_input_costs,
            'profit': self.profit,
            'target_margin': self.profit_margin,
            'actual_margin': self.actual_margin,
            'climate_cost_absorbed': self.climate_cost_burden,
            'climate_productivity': self.climate_productivity,
            'price': self.price[self.output]
        })

    def apply_climate_stress(self, stress_factor):
        """ Apply climate stress by reducing productivity (requiring more inputs) """
        self.climate_stressed = True
        self.climate_productivity = stress_factor * self.chronic_stress_accumulated
        print(f"  Commodity Producer {self.id}: CLIMATE STRESS! Productivity: {self.climate_productivity:.2f}")

    def reset_climate_stress(self):
        """ Reset productivity to chronic level """
        if self.climate_stressed:
            self.climate_stressed = False
            self.climate_productivity = self.chronic_stress_accumulated
            print(f"  Commodity Producer {self.id}: Climate stress cleared, productivity: {self.climate_productivity:.2f}")

    def apply_acute_stress(self):
        """ Apply acute climate stress (temporary productivity shock) """
        stress_factor = 1.0 - (self.climate_vulnerability * random.uniform(0.2, 0.8))
        self.climate_productivity = stress_factor * self.chronic_stress_accumulated
        print(f"  Commodity Producer {self.id}: Acute stress! Productivity: {self.climate_productivity:.2f}")

    def apply_chronic_stress(self, stress_factor):
        """ Apply chronic climate stress (permanent productivity degradation) """
        self.chronic_stress_accumulated *= stress_factor
        self.climate_productivity = self.chronic_stress_accumulated

    def _collect_agent_data(self, round_num, agent_type):
        """ Collect agent data for visualization """
        return {
            'id': self.id,
            'type': agent_type,
            'round': round_num,
            'wealth': self['money'],
            'debt': self.debt,
            'net_worth': self['money'] - self.debt,
            'profit': self.profit,
            'margin': self.actual_margin,
            'climate_stressed': self.climate_stressed,
            'continent': getattr(self, 'continent', 'Unknown'),
            'vulnerability': getattr(self, 'climate_vulnerability', 0),
            'production': self.production_this_round,
            'climate_productivity': self.climate_productivity
        } 