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
        
        # Calculate minimum production responsibility for intermediary firms' survival needs
        self.minimum_production_responsibility = config.get('commodity_minimum_per_producer', 0.0)
        
        # Climate stress parameters from configuration
        climate_config = config['climate']
        base_vulnerability = climate_config['base_vulnerability']
        vulnerability_variance = climate_config['vulnerability_variance']
        self.climate_vulnerability = base_vulnerability + (self.id * vulnerability_variance)
        self.chronic_stress_accumulated = 1.0  # Multiplicative factor
        self.climate_stressed = False  # Track if currently stressed
        
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
        """Calculate how much of each input is needed to produce desired output,
        accounting for climate-reduced productivity"""
        required_inputs = {}
        
        # For Cobb-Douglas: Q = A * L^α * K^β...
        # With climate: actual_productivity = base_productivity * climate_productivity
        # So we need: L = (Q / (A * climate_productivity))^(1/α) if only labor
        
        # For simplicity with multiple inputs, assume equal productivity loss
        # So if climate_productivity = 0.8, we need 1/0.8 = 1.25x inputs
        productivity_multiplier = 1.0 / self.climate_productivity if self.climate_productivity > 0 else 999
        
        for input_good, exponent in self.inputs.items():
            # Basic requirement for desired output
            base_requirement = self.desired_output_quantity * exponent
            # Adjust for climate productivity
            required_inputs[input_good] = base_requirement * productivity_multiplier
            
        return required_inputs

    def buy_labor(self):
        """ Buy labor needed to maintain fixed production output """
        labor_start = self['labor']
        offers = self.get_offers("labor")
        
        # Calculate required labor
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
            
            # Check if we need debt to buy
            if self['money'] < cost:
                debt_needed = cost - self['money']
                self.create('money', debt_needed)
                self.debt += debt_needed
                self.debt_created_this_round += debt_needed
                print(f"      💳 Created ${debt_needed:.2f} debt to maintain production")
            
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
        print(f"      Total labor purchased: {labor_purchased:.2f} for ${total_cost:.2f}")
        print(f"      Money remaining: ${self['money']:.2f}")

    def production(self):
        """ Produce fixed quantity of commodities """
        # In fixed supply model, we always produce the desired quantity
        # (assuming we got the inputs we needed)
        inventory_before = self[self.output]
        
        # Check if we have sufficient inputs
        can_produce = True
        for input_good, required in self.calculate_required_inputs().items():
            if self[input_good] < required * 0.95:  # Allow 5% tolerance
                can_produce = False
                print(f"    ⚠️ Insufficient {input_good}: have {self[input_good]:.2f}, need {required:.2f}")
        
        if can_produce:
            # Consume inputs
            for input_good, required in self.calculate_required_inputs().items():
                actual_use = min(self[input_good], required)
                self.destroy(input_good, actual_use)
            
            # Produce fixed output
            self.create(self.output, self.desired_output_quantity)
            self.production_this_round = self.desired_output_quantity
            print(f"    Fixed Supply Commodity Producer {self.id}: Produced {self.desired_output_quantity} {self.output}s")
        else:
            # Partial production based on most limiting input
            production_ratio = 1.0
            for input_good, required in self.calculate_required_inputs().items():
                if required > 0:
                    ratio = self[input_good] / required
                    production_ratio = min(production_ratio, ratio)
            
            actual_production = self.desired_output_quantity * production_ratio
            
            # Consume inputs proportionally
            for input_good, required in self.calculate_required_inputs().items():
                actual_use = required * production_ratio
                self.destroy(input_good, min(self[input_good], actual_use))
            
            self.create(self.output, actual_production)
            self.production_this_round = actual_production
            print(f"    ⚠️ Partial production: {actual_production:.2f} instead of {self.desired_output_quantity}")

    def calculate_dynamic_price(self):
        """Calculate price based on input costs and desired profit margin,
        with 50-50 cost sharing for climate impacts"""
        if self.production_this_round > 0:
            # Base cost per unit
            base_cost_per_unit = self.total_input_costs / self.production_this_round
            
            # Calculate what the cost would have been without climate impact
            normal_cost_per_unit = base_cost_per_unit * self.climate_productivity
            
            # Extra cost due to climate
            climate_extra_cost = base_cost_per_unit - normal_cost_per_unit
            
            # Split climate cost 50-50
            customer_burden = climate_extra_cost * 0.5
            producer_burden = climate_extra_cost * 0.5
            
            # Price = normal cost + margin + customer's share of climate cost
            target_price = normal_cost_per_unit * (1 + self.profit_margin) + customer_burden
            
            # Track how much climate cost we absorbed
            self.climate_cost_burden = producer_burden * self.production_this_round
            
            # Update price
            self.price[self.output] = target_price
            
            print(f"    Dynamic pricing for Commodity Producer {self.id}:")
            print(f"      Base cost/unit: ${base_cost_per_unit:.2f}")
            print(f"      Climate impact: ${climate_extra_cost:.2f}/unit")
            print(f"      Customer bears: ${customer_burden:.2f}/unit")
            print(f"      Producer bears: ${producer_burden:.2f}/unit")
            print(f"      New price: ${target_price:.2f} (was ${self.price[self.output]:.2f})")

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