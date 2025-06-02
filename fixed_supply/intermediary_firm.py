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
        self.base_price = production_config['base_price']
        
        # Financial tracking
        self.debt = 0  # Track total debt
        self.total_input_costs = 0
        self.revenue = 0
        self.profit = 0
        self.actual_margin = 0
        self.climate_cost_burden = 0
        
        # Climate productivity factor
        self.climate_productivity = 1.0
        
        # Calculate minimum production responsibility for final goods firms' survival needs
        self.minimum_production_responsibility = config.get('intermediary_minimum_per_firm', 0.0)
        
        # Climate stress parameters from configuration
        climate_config = config['climate']
        base_vulnerability = climate_config['base_vulnerability']
        vulnerability_variance = climate_config['vulnerability_variance']
        self.climate_vulnerability = base_vulnerability + (self.id * vulnerability_variance)
        self.chronic_stress_accumulated = 1.0
        self.climate_stressed = False
        
        # Dynamic pricing
        self.price = {self.output: self.base_price}
        
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
        print(f"  Base price: ${self.base_price}")
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
        """Calculate required inputs for desired output, accounting for climate"""
        required_inputs = {}
        productivity_multiplier = 1.0 / self.climate_productivity if self.climate_productivity > 0 else 999
        
        for input_good, exponent in self.inputs.items():
            base_requirement = self.desired_output_quantity * exponent
            required_inputs[input_good] = base_requirement * productivity_multiplier
            
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
        """ Produce fixed quantity of intermediate goods """
        inventory_before = self[self.output]
        
        # Check if we have sufficient inputs
        can_produce = True
        for input_good, required in self.calculate_required_inputs().items():
            if self[input_good] < required * 0.95:
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
            print(f"    Fixed Supply Intermediary Firm {self.id}: Produced {self.desired_output_quantity} {self.output}s")
        else:
            # Partial production
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
        """Calculate price with 50-50 climate cost sharing"""
        if self.production_this_round > 0:
            base_cost_per_unit = self.total_input_costs / self.production_this_round
            normal_cost_per_unit = base_cost_per_unit * self.climate_productivity
            climate_extra_cost = base_cost_per_unit - normal_cost_per_unit
            
            # Split climate cost 50-50
            customer_burden = climate_extra_cost * 0.5
            producer_burden = climate_extra_cost * 0.5
            
            # Price = normal cost + margin + customer's share
            target_price = normal_cost_per_unit * (1 + self.profit_margin) + customer_burden
            
            self.climate_cost_burden = producer_burden * self.production_this_round
            self.price[self.output] = target_price
            
            print(f"    Dynamic pricing for Intermediary Firm {self.id}:")
            print(f"      Base cost/unit: ${base_cost_per_unit:.2f}")
            print(f"      Climate impact: ${climate_extra_cost:.2f}/unit")
            print(f"      New price: ${target_price:.2f} (was ${self.base_price:.2f})")

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