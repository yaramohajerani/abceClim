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
        """ Intermediary firms in the fixed supply model maintain constant output.
        They buy commodities and labor, adjusting purchases based on climate-affected 
        productivity, and calculate prices dynamically based on costs and profit margin.
        
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
        self.climate_cost_burden = 0
        
        # Climate productivity factor
        self.climate_productivity = 1.0
        
        # Climate stress parameters from configuration
        climate_config = config['climate']
        base_vulnerability = climate_config['base_vulnerability']
        vulnerability_variance = climate_config['vulnerability_variance']
        self.climate_vulnerability = base_vulnerability + (self.id * vulnerability_variance)
        self.chronic_stress_accumulated = 1.0
        self.climate_stressed = False
        
        # Climate cost sharing parameters
        cost_sharing_config = climate_config.get('cost_sharing', {'customer_share': 0.5})
        self.customer_share = cost_sharing_config['customer_share']
        self.producer_share = 1.0 - self.customer_share
        
        # Calculate initial price from expected costs using actual values from config
        wage = config['wage']
        commodity_price = config['commodity_price']
        expected_labor_cost = self.inputs.get('labor', 0) * wage
        expected_commodity_cost = self.inputs.get('commodity', 0) * commodity_price
        expected_total_cost = expected_labor_cost + expected_commodity_cost
        expected_cost_per_unit = expected_total_cost / self.desired_output_quantity
        initial_price = expected_cost_per_unit * (1 + self.profit_margin)
        self.price = {self.output: initial_price}
        
        # Track production data
        self.production_this_round = 0
        self.sales_this_round = 0
        self.inputs_purchased = {good: 0 for good in self.inputs.keys()}
        self.inventory_at_start = self[self.output]
        self.debt_created_this_round = 0
        
        # Get final goods firm count from config for proper distribution
        self.final_goods_count = config['final_goods_count']
        
        print(f"Fixed Supply Intermediary Firm {self.id} initialized:")
        print(f"  Initial money: ${initial_money}")
        print(f"  Desired output: {self.desired_output_quantity} (constant)")
        print(f"  Profit margin target: {self.profit_margin*100:.1f}%")
        print(f"  Initial price: ${initial_price:.2f} (wage: ${wage}, commodity: ${commodity_price:.2f})")
        print(f"  Climate vulnerability: {self.climate_vulnerability:.3f}")
        print(f"  Will distribute to {self.final_goods_count} final goods firms")

    def start_round(self):
        """Called at the start of each round to reset tracking variables"""
        self.production_this_round = 0
        self.sales_this_round = 0
        self.inputs_purchased = {good: 0 for good in self.inputs.keys()}
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
        
        productivity_factor = 1.0 / self.climate_productivity if self.climate_productivity > 0 else 999
        
        # For multiple inputs case - assume balanced inputs
        # Each input contributes its share: L^α * K^β = productivity_factor
        # Assume L = K for simplicity, then L^(α+β) = productivity_factor, so L = productivity_factor^(1/(α+β))
        total_exponents = sum(self.inputs.values())
        
        for input_good, exponent in self.inputs.items():
            if total_exponents > 0:
                required_inputs[input_good] = productivity_factor ** (1.0 / total_exponents)
            else:
                required_inputs[input_good] = productivity_factor
                
        return required_inputs

    def buy_inputs_optimally(self):
        """ Buy both commodities and labor optimally to maintain fixed production """
        required_inputs = self.calculate_required_inputs()
        
        print(f"    Fixed Supply Intermediary Firm {self.id}:")
        print(f"      Climate productivity: {self.climate_productivity:.2f}")
        print(f"      Required inputs for {self.desired_output_quantity} output:")
        for good, amount in required_inputs.items():
            print(f"        {good}: {amount:.2f}")
        print(f"      Current money: ${self['money']:.2f}, Debt: ${self.debt:.2f}")
        
        # Process offers for each input type
        for input_good in self.inputs.keys():
            offers = self.get_offers(input_good)
            needed = required_inputs.get(input_good, 0)
            purchased = 0
            
            for offer in offers:
                if purchased >= needed:
                    break
                    
                quantity_to_buy = min(offer.quantity, needed - purchased)
                cost = quantity_to_buy * offer.price
                
                # Check if we need debt
                if self['money'] < cost:
                    debt_needed = cost - self['money']
                    self.create('money', debt_needed)
                    self.debt += debt_needed
                    self.debt_created_this_round += debt_needed
                    print(f"      💳 Created ${debt_needed:.2f} debt for {input_good}")
                
                # Make the purchase
                if quantity_to_buy == offer.quantity:
                    self.accept(offer)
                else:
                    self.accept(offer, quantity=quantity_to_buy)
                    
                purchased += quantity_to_buy
                self.total_input_costs += cost
                self.inputs_purchased[input_good] += quantity_to_buy
                
                print(f"      Bought {quantity_to_buy:.2f} {input_good} for ${cost:.2f}")
            
            if purchased < needed * 0.95:
                print(f"      ⚠️ Could only buy {purchased:.2f} {input_good} (needed {needed:.2f})")

    def production(self):
        """ Produce intermediate goods using actual production function """
        inventory_before = self[self.output]
        
        print(f"    Fixed Supply Intermediary Firm {self.id}: PRODUCTION:")
        print(f"      Target output: {self.desired_output_quantity}")
        print(f"      Climate productivity: {self.climate_productivity:.3f}")
        
        # Create production function with climate-adjusted productivity
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
        """Calculate price with configurable climate cost sharing"""
        if self.production_this_round > 0:
            base_cost_per_unit = self.total_input_costs / self.production_this_round
            normal_cost_per_unit = base_cost_per_unit * self.climate_productivity
            climate_extra_cost = base_cost_per_unit - normal_cost_per_unit
            
            # Split climate cost according to configuration
            customer_burden = climate_extra_cost * self.customer_share
            producer_burden = climate_extra_cost * self.producer_share
            
            # Price = normal cost + margin + customer's share
            target_price = normal_cost_per_unit * (1 + self.profit_margin) + customer_burden
            
            self.climate_cost_burden = producer_burden * self.production_this_round
            self.price[self.output] = target_price
            
            print(f"    Dynamic pricing for Intermediary Firm {self.id}:")
            print(f"      Base cost/unit: ${base_cost_per_unit:.2f}")
            print(f"      Climate impact: ${climate_extra_cost:.2f}/unit")
            print(f"      Customer bears: ${customer_burden:.2f}/unit ({self.customer_share:.1%})")
            print(f"      Producer bears: ${producer_burden:.2f}/unit ({self.producer_share:.1%})")
            print(f"      New price: ${target_price:.2f} (was ${self.price[self.output]:.2f})")

    def sell_intermediate_goods(self):
        """ Sell intermediate goods to final goods firms """
        self.calculate_dynamic_price()
        
        inventory = self[self.output]
        self.inventory_before_sales = inventory
        
        print(f"    Fixed Supply Intermediary Firm {self.id}: Has {inventory:.2f} {self.output}s to sell at ${self.price[self.output]:.2f}")
        if inventory > 0:
            quantity_per_firm = inventory / self.final_goods_count
            for final_goods_id in range(self.final_goods_count):
                if quantity_per_firm > 0:
                    self.sell(('final_goods_firm', final_goods_id), self.output,
                             quantity_per_firm, self.price[self.output])

    def calculate_sales_after_market_clearing(self):
        """Calculate actual sales and financial metrics"""
        if hasattr(self, 'inventory_before_sales'):
            current_inventory = self[self.output]
            self.sales_this_round = self.inventory_before_sales - current_inventory
            self.revenue = self.sales_this_round * self.price[self.output]
            
            if self.sales_this_round > 0:
                self.profit = self.revenue - self.total_input_costs
                self.actual_margin = self.profit / self.revenue if self.revenue > 0 else 0
            else:
                self.profit = -self.total_input_costs
                self.actual_margin = 0
            
            print(f"    Financial summary for Intermediary Firm {self.id}:")
            print(f"      Revenue: ${self.revenue:.2f}")
            print(f"      Costs: ${self.total_input_costs:.2f}")
            print(f"      Profit: ${self.profit:.2f}")
            print(f"      Target margin: {self.profit_margin*100:.1f}%")
            print(f"      Actual margin: {self.actual_margin*100:.1f}%")
            
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
                
                print(f"    💰 Intermediary Firm {self.id}: Repaid ${debt_payment:.2f} debt")
                print(f"      Remaining debt: ${self.debt:.2f}, Remaining money: ${self['money']:.2f}")
            
            # Set to zero if very small to avoid floating point issues
            if self.debt < 0.01:
                self.debt = 0

    def log_round_data(self):
        """Log comprehensive data including financial metrics"""
        inventory_change = self.production_this_round - self.sales_this_round
        cumulative_inventory = self[self.output]
        current_money = self['money']
        
        self.log('production', {
            'production': self.production_this_round,
            'sales': self.sales_this_round,
            'inventory_change': inventory_change,
            'cumulative_inventory': cumulative_inventory,
            'inputs_purchased': self.inputs_purchased,
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
        """ Apply climate stress by reducing productivity """
        self.climate_stressed = True
        self.climate_productivity = stress_factor * self.chronic_stress_accumulated
        print(f"  Intermediary Firm {self.id}: CLIMATE STRESS! Productivity: {self.climate_productivity:.2f}")

    def reset_climate_stress(self):
        """ Reset productivity to chronic level """
        if self.climate_stressed:
            self.climate_stressed = False
            self.climate_productivity = self.chronic_stress_accumulated
            print(f"  Intermediary Firm {self.id}: Climate stress cleared, productivity: {self.climate_productivity:.2f}")

    def apply_acute_stress(self):
        """ Apply acute climate stress """
        stress_factor = 1.0 - (self.climate_vulnerability * random.uniform(0.2, 0.8))
        self.climate_productivity = stress_factor * self.chronic_stress_accumulated
        print(f"  Intermediary Firm {self.id}: Acute stress! Productivity: {self.climate_productivity:.2f}")

    def apply_chronic_stress(self, stress_factor):
        """ Apply chronic climate stress """
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