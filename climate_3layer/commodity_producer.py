import abcEconomics as abce


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
        
        # Overhead costs (CapEx, legal, damages, business interruptions, etc.)
        self.base_overhead = production_config.get('base_overhead', 1.0)  # Fixed base overhead per round
        self.current_overhead = self.base_overhead  # Current overhead (increases with climate stress)
        
        # Financial tracking for dynamic pricing
        self.total_input_costs = 0
        self.revenue = 0
        self.profit = 0
        self.profit_margin = production_config['profit_margin']
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
        
        # Debt tracking system
        self.debt = 0.0  # Total debt accumulated
        self.debt_created_this_round = 0.0  # Track debt created for survival purchasing
        
        # Get intermediary firm count from config for proper distribution
        self.intermediary_count = config['intermediary_count']
        
        print(f"Commodity Producer {self.id} initialized:")
        print(f"  Initial money: ${initial_money}")
        print(f"  Production capacity: {self.base_output_quantity}")
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
        self.revenue = 0
        self.profit = 0
        self.climate_cost_burden = 0  # Track how much extra cost from climate we absorbed
    
    def buy_labor(self):
        """ Buy labor from households and track costs for dynamic pricing """
        labor_start = self['labor']
        money_start = self['money']
        offers = self.get_offers("labor")
        
        print(f"    Commodity Producer {self.id}: Has ${money_start:.2f}, received {len(offers)} labor offers")
        
        for offer in offers:
            # abcEcon already takes care of full and partial acceptances based on how much money is available
            self.accept(offer)
        
        # Track labor purchased this round and costs
        labor_end = self['labor']
        self.labor_purchased = labor_end - labor_start
        
        # get total spend
        money_end = self['money'] 
        total_spent = money_start - money_end + self.current_overhead
        self.total_input_costs += total_spent  # Track for dynamic pricing, also include overhead
        
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
        for good in ['money', 'labor', self.output]:
            print(f"      {good}: {self[good]:.3f}")
        
        # Update production function with current output quantity (accounting for climate stress)
        self.pf = self.create_cobb_douglas(self.output, self.current_output_quantity, self.inputs)
        
        # Prepare actual input quantities (what we actually have available)
        actual_inputs = {}
        for input_good in self.inputs.keys():
            actual_inputs[input_good] = self[input_good]
            print(f"      Available {input_good}: {actual_inputs[input_good]:.3f}")
        
        print(f"      Calling production function with actual inputs: {actual_inputs}")
        
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
            
            # Price = input costs + profit margin + customer's share of overhead
            target_price = input_cost_per_unit * (1 + self.profit_margin)
            
            self.price[self.output] = target_price
            
            print(f"    Dynamic pricing for Commodity Producer {self.id}:")
            print(f"      Input cost per unit: ${input_cost_per_unit:.2f}")
            print(f"      New price: ${target_price:.2f}")
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
        self.profit = self.revenue - self.total_input_costs
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
            'money': current_money,
            'debt': self.debt,
            'debt_created_this_round': self.debt_created_this_round,
            'revenue': self.revenue,
            'input_costs': self.total_input_costs,
            'profit': self.profit,
            'target_margin': self.profit_margin,
            'actual_margin': self.actual_margin,
            'base_overhead': self.base_overhead,
            'current_overhead': self.current_overhead,
            'price': self.price[self.output]
        })
        
        print(f"    Commodity Producer {self.id}: Logged - Production: {self.production_this_round:.2f}, Sales: {self.sales_this_round:.2f}, Labor purchased: {self.labor_purchased:.2f}, Inventory: {cumulative_inventory:.2f}, Money: ${current_money:.2f}, Price: ${self.price[self.output]:.2f}, Overhead: ${self.current_overhead:.2f}, Profit: ${self.profit:.2f}, Debt: ${self.debt:.2f}, Debt created this round: ${self.debt_created_this_round:.2f}")


    def _collect_agent_data(self, round_num, agent_type):
        """ Collect agent data for visualization (called by abcEconomics group system) """
        return {
            'id': self.id,
            'type': agent_type,
            'round': round_num,
            'wealth': self['money'],
            'climate_stressed': self.climate_stressed,
            'continent': getattr(self, 'continent', 'Unknown'),
            'production': self.current_output_quantity
        } 