import abcEconomics as abce


class Household(abce.Agent):
    def init(self, config):
        """ Households are consumers and laborers in the economy.
        They sell labor to firms and use the income to buy final goods for consumption.
        They try to meet their minimum survival consumption requirements.
        
        Args:
            config: Configuration dictionary with consumption parameters, labor settings, etc.
        """
        # Initialize money
        initial_money = config['initial_money']
        self.create('money', initial_money)
        
        # Initialize inventory from configuration
        initial_inventory = config.get('initial_inventory', {})
        for good, quantity in initial_inventory.items():
            self.create(good, quantity)
        
        # Labor parameters from configuration
        labor_config = config['labor']
        self.labor_endowment = labor_config['endowment']
        self.wage = labor_config['wage']
        
        # Financial tracking
        self.debt = 0
        self.income = 0
        self.spending = 0
        self.debt_created_this_round = 0
        
        # Consumption parameters from configuration
        consumption_config = config['consumption']
        self.preferred_good = consumption_config['preference']
        self.budget_fraction = consumption_config['budget_fraction']
        self.consumption_fraction = consumption_config['consumption_fraction']
        self.minimum_survival_consumption = consumption_config['minimum_survival_consumption']
        
        # Track consumption data for logging
        self.consumption_this_round = 0
        self.final_goods_purchased = 0
        self.purchases_this_round = 0
        self.labor_sold = 0
        
        # Initialize utility tracking
        self.utility = 0.0
        
        # Get firm counts from config for labor distribution
        self.commodity_producer_count = config['commodity_producer_count']
        self.intermediary_firm_count = config['intermediary_firm_count']
        self.final_goods_firm_count = config['final_goods_firm_count']
        total_firms = self.commodity_producer_count + self.intermediary_firm_count + self.final_goods_firm_count
        
        # Calculate labor allocation based on rough needs
        self.labor_allocation = {
            'commodity_producer': 0.5,    # 50% to commodity producers (labor-intensive)
            'intermediary_firm': 0.25,    # 25% to intermediary firms
            'final_goods_firm': 0.25      # 25% to final goods firms
        }
        
        print(f"Household {self.id} initialized:")
        print(f"  Initial money: ${initial_money}")
        print(f"  Labor endowment: {self.labor_endowment}")
        print(f"  Wage: ${self.wage}")
        print(f"  Minimum consumption: {self.minimum_survival_consumption}")
        print(f"  Will distribute labor to {total_firms} firms")

    def start_round(self):
        """Called at the start of each round to reset tracking variables"""
        self.consumption_this_round = 0
        self.final_goods_purchased = 0
        self.purchases_this_round = 0
        self.labor_sold = 0
        self.debt_created_this_round = 0
        self.income = 0
        self.spending = 0

    def sell_labor(self):
        """ Offer labor to firms """
        # Reset labor to exactly the endowment each round
        try:
            current_labor = self['labor']
            if current_labor > 0:
                self.destroy('labor', current_labor)
        except KeyError:
            current_labor = 0  # No existing labor
        self.create('labor', self.labor_endowment)
        
        labor_stock = self['labor']
        labor_start = labor_stock
        
        print(f"    Household {self.id}: Reset labor to {self.labor_endowment} (was {current_labor:.2f})")
        
        if labor_stock > 0:
            # Distribute labor offers among all types of firms
            firms = []
            # Add commodity producers
            for i in range(self.commodity_producer_count):
                firms.append(('commodity_producer', i))
            # Add intermediary firms  
            for i in range(self.intermediary_firm_count):
                firms.append(('intermediary_firm', i))
            # Add final goods firms
            for i in range(self.final_goods_firm_count):
                firms.append(('final_goods_firm', i))
            
            # Distribute labor among firms
            labor_per_firm = labor_stock / len(firms)
            for firm in firms:
                if labor_per_firm > 0:
                    self.sell(firm, 'labor', labor_per_firm, self.wage)
        
        # Track labor sold (will be calculated after firms accept offers, but we estimate it here)
        # Note: This will be updated after the market clearing in the simulation
        self.labor_sold = labor_start  # Initially assume all labor is offered

    def buy_final_goods(self):
        """ Buy final goods based on total available resources - simple and market-responsive """
        self.calculate_labor_income()  # First calculate income
        
        final_goods_start = self[self.preferred_good]
        offers = self.get_offers(self.preferred_good)
        
        # Simple rule: spend a fraction of total available resources on consumption
        available_money = self['money']
        total_resources = self.income + available_money  # Income this round + accumulated wealth
        
        # Spend 60% of total resources on consumption (this makes households responsive to wealth changes)
        consumption_spending_budget = total_resources * 0.6
        
        # Don't spend more money than we have (unless survival emergency)
        actual_spending_budget = min(consumption_spending_budget, available_money)
        
        print(f"  Household {self.id}:")
        print(f"    Income: ${self.income:.2f}, Money: ${available_money:.2f}, Total resources: ${total_resources:.2f}")
        print(f"    Consumption budget (60% of resources): ${consumption_spending_budget:.2f}")
        print(f"    Actual spending budget: ${actual_spending_budget:.2f}")
        print(f"    Current inventory: {final_goods_start:.2f}")
        print(f"    Received {len(offers)} final good offers")
        
        total_purchased = 0
        total_spent = 0
        remaining_budget = actual_spending_budget
        
        # Buy as much as we can afford with our budget
        for offer in offers:
            if remaining_budget <= 0:
                print(f"    BUDGET EXHAUSTED")
                break
                
            # How much can we afford from this offer?
            affordable_quantity = remaining_budget / offer.price
            purchase_quantity = min(offer.quantity, affordable_quantity)
            
            if purchase_quantity > 0.01:  # Worth buying
                cost = purchase_quantity * offer.price
                
                if purchase_quantity == offer.quantity:
                    self.accept(offer)
                else:
                    self.accept(offer, quantity=purchase_quantity)
                
                total_purchased += purchase_quantity
                total_spent += cost
                remaining_budget -= cost
                print(f"    BOUGHT: {purchase_quantity:.3f} units for ${cost:.2f} (price: ${offer.price:.2f}/unit)")
            else:
                print(f"    SKIPPED: Can't afford offer of {offer.quantity:.2f} at ${offer.price:.2f}/unit")
        
        # Emergency debt creation ONLY if we bought nothing and have no inventory
        current_inventory_after_purchase = final_goods_start + total_purchased
        if current_inventory_after_purchase < 0.01:  # Essentially no food
            print(f"    🆘 SURVIVAL EMERGENCY: No inventory, creating emergency debt")
            emergency_debt = self.minimum_survival_consumption * 50  # Emergency money for survival
            self.create('money', emergency_debt)
            self.debt += emergency_debt
            self.debt_created_this_round += emergency_debt
            print(f"    💳 Created ${emergency_debt:.2f} emergency debt")
            
            # Try to buy something with emergency money
            if offers and len(offers) > 0:
                offer = offers[0]  # Take first available offer
                emergency_quantity = min(offer.quantity, emergency_debt / offer.price)
                if emergency_quantity > 0.01:
                    emergency_cost = emergency_quantity * offer.price
                    self.accept(offer, quantity=emergency_quantity)
                    total_purchased += emergency_quantity
                    total_spent += emergency_cost
                    print(f"    🆘 EMERGENCY BUY: {emergency_quantity:.3f} units for ${emergency_cost:.2f}")
        
        # Record results
        self.final_goods_purchased = total_purchased
        self.spending = total_spent
        
        final_goods_end = self[self.preferred_good]
        
        print(f"  Household {self.id}: Purchasing complete")
        print(f"    Total purchased: {self.final_goods_purchased:.3f} for ${total_spent:.2f}")
        print(f"    Average price paid: ${total_spent/total_purchased if total_purchased > 0 else 0:.2f}/unit")
        print(f"    Inventory: {final_goods_start:.3f} → {final_goods_end:.3f}")
        print(f"    Money: ${available_money:.2f} → ${self['money']:.2f}")
        print(f"    Debt: ${self.debt:.2f}")

    def consumption(self):
        """ Consume final goods to generate utility """
        consumption_start = self[self.preferred_good]
        available_goods = self[self.preferred_good]
        
        print(f"    Household {self.id}: Has {available_goods:.2f} {self.preferred_good}s available for consumption")
        print(f"      Minimum survival consumption required per round: {self.minimum_survival_consumption:.2f}")
        
        # Calculate intended consumption based on consumption fraction
        normal_consumption = available_goods * self.consumption_fraction
        
        # Ensure consumption is at least the minimum survival level, but never more than available
        intended_consumption = max(self.minimum_survival_consumption, normal_consumption)
        consumption_amount = min(intended_consumption, available_goods)  # Critical fix: can't consume more than available!
        
        print(f"      Normal consumption (fraction of inventory): {normal_consumption:.2f}")
        print(f"      Minimum survival consumption required: {self.minimum_survival_consumption:.2f}")
        print(f"      Intended consumption (max of normal/survival): {intended_consumption:.2f}")
        print(f"      Actual consumption (limited by availability): {consumption_amount:.2f}")
        
        # Check if we can meet survival needs
        survival_needs_met = consumption_amount >= self.minimum_survival_consumption
        if not survival_needs_met:
            print(f"      ⚠️  WARNING: Cannot meet minimum survival consumption! Need {self.minimum_survival_consumption:.2f}, can only consume {consumption_amount:.2f}")
            print(f"          This household is in survival crisis - should have purchased more goods!")
        
        if consumption_amount > 0:
            try:
                self.destroy(self.preferred_good, consumption_amount)
                print(f"      ✅ Consumed {consumption_amount:.2f} {self.preferred_good}s (survival needs met: {survival_needs_met})")
                # Update utility based on consumption
                self.utility += consumption_amount
            except Exception as e:
                print(f"      ❌ Consumption failed: {e}")
                consumption_amount = 0
        else:
            print(f"      ❌ No {self.preferred_good}s available to consume - SURVIVAL CRISIS!")
        
        # Verify final state
        final_inventory = self[self.preferred_good]
        
        # Calculate consumption for this round (should match the amount we just consumed)
        self.consumption_this_round = consumption_amount  # Direct assignment to ensure consistency
        
        print(f"    Household {self.id}: Consumed {self.consumption_this_round:.2f}, remaining inventory: {final_inventory:.2f}")
        print(f"      Current utility: {self.utility:.2f}, survival needs met: {survival_needs_met}")
        
        return survival_needs_met

    def log_round_data(self):
        """Log consumption, purchases, and inventory data for this round"""
        # Calculate inventory change and cumulative inventory
        inventory_change = self.purchases_this_round - self.consumption_this_round
        cumulative_inventory = self[self.preferred_good]
        current_money = self['money']
        
        # Check if minimum consumption requirement is met
        minimum_consumption_met = self.consumption_this_round >= self.minimum_survival_consumption
        survival_buffer = cumulative_inventory  # How much is left for next round
        
        # Log the data using abcEconomics logging
        self.log('consumption', {
            'consumption': self.consumption_this_round,
            'purchases': self.purchases_this_round,
            'inventory_change': inventory_change,
            'cumulative_inventory': cumulative_inventory,
            'labor_sold': self.labor_sold,
            'money': current_money,
            'minimum_survival_consumption': self.minimum_survival_consumption,
            'minimum_consumption_met': minimum_consumption_met,
            'survival_buffer': survival_buffer
        })
        
        print(f"    Household {self.id}: Logged - Consumption: {self.consumption_this_round:.2f}, Purchases: {self.purchases_this_round:.2f}, Labor sold: {self.labor_sold:.2f}")
        print(f"      Inventory: {cumulative_inventory:.2f}, Money: ${current_money:.2f}")
        print(f"      Minimum consumption met: {minimum_consumption_met} (consumed {self.consumption_this_round:.2f}, required {self.minimum_survival_consumption:.2f})")

    def _collect_agent_data(self, round_num, agent_type):
        """ Collect agent data for visualization (called by abcEconomics group system) """
        return {
            'id': self.id,
            'type': agent_type,
            'round': round_num,
            'wealth': self['money'],
            'climate_stressed': False,  # Households don't experience direct climate stress
            'continent': getattr(self, 'continent', 'Unknown'),
            'vulnerability': 0,  # No direct climate vulnerability
            'consumption': self.get(self.preferred_good, 0)
        }

    def calculate_labor_income(self):
        """Calculate income from labor sales after market clearing"""
        # Labor income = (initial labor - remaining labor) * wage
        labor_sold = self.labor_endowment - self['labor']
        self.income = labor_sold * self.wage
        print(f"  Household {self.id}: Sold {labor_sold:.2f} labor, earned ${self.income:.2f}")
        
        # If we detect negative labor remaining, log for debugging
        if self['labor'] < 0:
            print(f"    🐛 DEBUG: Household {self.id} has negative labor remaining: {self['labor']:.2f}")
            print(f"    This indicates over-selling in the labor market!")
            print(f"    Labor endowment: {self.labor_endowment}, Labor sold: {labor_sold:.2f}") 