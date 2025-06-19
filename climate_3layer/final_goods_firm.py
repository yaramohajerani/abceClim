import abcEconomics as abce

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
        
        # Overhead costs (CapEx, legal, damages, business interruptions, etc.)
        self.base_overhead = production_config['base_overhead']  # Fixed base overhead per round
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
        self.intermediate_goods_purchased = 0
        self.inventory_at_start = self[self.output]
        
        # Debt tracking system
        self.debt = 0.0  # Total debt accumulated
        self.debt_created_this_round = 0.0  # Debt created in this round for tracking
        
        # Store household count for distribution
        self.num_households = config['household_count']
        
        # Initialize heterogeneity characteristics (will be set by climate framework)
        self.heterogeneity_characteristics = None
        
        print(f"Final Goods Firm {self.id} initialized:")
        print(f"  Initial money: ${initial_money}")
        print(f"  Production capacity: {self.base_output_quantity}")
        print(f"  Will distribute to {self.num_households} households")

    def set_heterogeneity_characteristics(self, characteristics):
        """Set individual characteristics for this firm"""
        self.heterogeneity_characteristics = characteristics
        if characteristics:
            # Apply efficiency modifications to base values
            modified_overhead = self.base_overhead * characteristics.overhead_efficiency
            modified_production = self.base_output_quantity * characteristics.production_efficiency
            
            self.base_overhead = modified_overhead
            self.current_overhead = modified_overhead
            self.base_output_quantity = modified_production
            self.current_output_quantity = modified_production
            
            # Update production function with new capacity
            self.pf = self.create_cobb_douglas(self.output, self.current_output_quantity, self.inputs)
            
            print(f"  Final Goods Firm {self.id} heterogeneity set:")
            print(f"    Climate vulnerability: productivity={characteristics.climate_vulnerability_productivity:.2f}, overhead={characteristics.climate_vulnerability_overhead:.2f}")
            print(f"    Efficiency: production={characteristics.production_efficiency:.2f}, overhead={characteristics.overhead_efficiency:.2f}")
            print(f"    Behavior: risk_tolerance={characteristics.risk_tolerance:.2f}, debt_willingness={characteristics.debt_willingness:.2f}")
            print(f"    Modified base overhead: {modified_overhead:.2f}, base production: {modified_production:.2f}")

    def start_round(self):
        """Called at the start of each round to reset tracking variables"""
        self.production_this_round = 0
        self.sales_this_round = 0
        self.labor_purchased = 0
        self.intermediate_goods_purchased = 0
        self.inventory_at_start = self[self.output]
        self.debt_created_this_round = 0  # Track debt created for survival purchasing

    def buy_inputs_optimally(self):
        """ Buy all inputs with optimal money allocation based on Cobb-Douglas exponents to maximize production - with heterogeneity in risk tolerance """
        print(f"    Final Goods Firm {self.id}: Starting optimal input purchasing with ${self['money']:.2f}")
        
        # Get behavioral modifiers from heterogeneity
        risk_tolerance = 1.0
        debt_willingness = 1.0
        if self.heterogeneity_characteristics:
            risk_tolerance = self.heterogeneity_characteristics.risk_tolerance
            debt_willingness = self.heterogeneity_characteristics.debt_willingness
        
        print(f"      Risk tolerance: {risk_tolerance:.2f}, Debt willingness: {debt_willingness:.2f}")
        
        # Get all input offers (only call this once!)
        intermediate_goods_offers = self.get_offers("intermediate_good")
        labor_offers = self.get_offers("labor")
        
        # Sort offers by price (ascending - cheapest first)
        intermediate_goods_offers.sort(key=lambda offer: offer.price)
        labor_offers.sort(key=lambda offer: offer.price)
        
        available_money = self['money']
        current_inventory = self[self.output]
        
        # Apply risk tolerance to available budget
        risk_adjusted_money = available_money * risk_tolerance
        
        print(f"      Current inventory: {current_inventory:.2f}")
        print(f"      Risk-adjusted budget: ${risk_adjusted_money:.2f} (original: ${available_money:.2f})")
        
        # Calculate optimal budget allocation for total available money
        optimal_allocation = self.calculate_optimal_input_allocation(risk_adjusted_money, self.inputs)
        
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
        self.total_input_costs = total_spent + self.current_overhead  # Track total costs for dynamic pricing
        
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
            
            target_price = input_cost_per_unit * (1 + self.profit_margin)
            
            self.price[self.output] = target_price
            
            print(f"    Dynamic pricing for Final Goods Firm {self.id}:")
            print(f"      Input cost per unit: ${input_cost_per_unit:.2f}")
            print(f"      New price: ${target_price:.2f}")
        else:
            print(f"    Final Goods Firm {self.id}: No production, keeping previous price")

    def sell_final_goods(self):
        """ Sell final goods to households """
        # First calculate the price based on this round's costs
        self.calculate_dynamic_price()
        
        final_goods_stock = self[self.output]
        self.inventory_before_sales = final_goods_stock  # Track inventory before creating offers
        
        print(f"    Final Goods Firm {self.id}: Has {final_goods_stock:.2f} {self.output}s to sell at ${self.price[self.output]:.2f}")
        if final_goods_stock > 0:
            # Distribute sales among households
            quantity_per_household = final_goods_stock / self.num_households  # Assuming evenly distributed
            for household_id in range(self.num_households):
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
        
        # Get heterogeneity data for logging
        heterogeneity_data = {}
        if self.heterogeneity_characteristics:
            heterogeneity_data = {
                'climate_vulnerability_productivity': self.heterogeneity_characteristics.climate_vulnerability_productivity,
                'climate_vulnerability_overhead': self.heterogeneity_characteristics.climate_vulnerability_overhead,
                'overhead_efficiency': self.heterogeneity_characteristics.overhead_efficiency,
                'production_efficiency': self.heterogeneity_characteristics.production_efficiency,
                'risk_tolerance': self.heterogeneity_characteristics.risk_tolerance,
                'debt_willingness': self.heterogeneity_characteristics.debt_willingness
            }
        
        # Log the data using abcEconomics logging
        log_data = {
            'production': self.production_this_round,
            'sales': self.sales_this_round,
            'inventory_change': inventory_change,
            'cumulative_inventory': cumulative_inventory,
            'labor_purchased': self.labor_purchased,
            'intermediate_goods_purchased': self.intermediate_goods_purchased,
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
        }
        
        # Add heterogeneity data if available
        log_data.update(heterogeneity_data)
        
        self.log('production', log_data)
        
        print(f"    Final Goods Firm {self.id}: Logged - Production: {self.production_this_round:.2f}, Sales: {self.sales_this_round:.2f}, Labor purchased: {self.labor_purchased:.2f}, Intermediate goods purchased: {self.intermediate_goods_purchased:.2f}, Inventory: {cumulative_inventory:.2f}, Money: ${current_money:.2f}, Price: ${self.price[self.output]:.2f}, Overhead: ${self.current_overhead:.2f}, Profit: ${self.profit:.2f}, Debt: ${self.debt:.2f}, Debt created this round: ${self.debt_created_this_round:.2f}")
        if self.heterogeneity_characteristics:
            print(f"      Heterogeneity: risk_tolerance={self.heterogeneity_characteristics.risk_tolerance:.2f}, debt_willingness={self.heterogeneity_characteristics.debt_willingness:.2f}, production_efficiency={self.heterogeneity_characteristics.production_efficiency:.2f}")

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