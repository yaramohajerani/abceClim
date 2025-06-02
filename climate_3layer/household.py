import abcEconomics as abce


class Household(abce.Agent):
    def init(self, config):
        """ Households provide labor and consume final goods.
        They are not directly affected by climate stress but may be affected indirectly through employment.
        
        Args:
            config: Configuration dictionary with initial resources, labor, and consumption parameters.
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
        
        # Consumption parameters from configuration
        consumption_config = config['consumption']
        self.preferred_good = consumption_config['preference']
        self.budget_fraction = consumption_config['budget_fraction']  # Fraction of money to spend each round
        self.consumption_fraction = consumption_config['consumption_fraction']  # Fraction of available goods to consume each round
        self.minimum_survival_consumption = consumption_config.get('minimum_survival_consumption', 0.0)  # Minimum consumption required for survival
        
        # Climate stress (not directly applicable to households but kept for compatibility)
        self.climate_stressed = False
        self.climate_stress_factor = 1.0
        
        # Create initial labor endowment
        self.create('labor_endowment', self.labor_endowment)
        
        # Calculate initial utility
        self.utility = 0.0  # Simple utility tracking
        
        # Track consumption data for proper logging
        self.consumption_this_round = 0
        self.purchases_this_round = 0
        self.labor_sold = 0
        self.inventory_at_start = self[self.preferred_good]
        
        # Get firm counts from config for proper labor distribution
        self.commodity_producer_count = config['commodity_producer_count']
        self.intermediary_firm_count = config['intermediary_firm_count']
        self.final_goods_firm_count = config['final_goods_firm_count']
        
        print(f"Household {self.id} initialized:")
        print(f"  Initial money: ${initial_money}")
        print(f"  Labor endowment: {self.labor_endowment}")
        print(f"  Wage: ${self.wage}")
        print(f"  Consumption preference: {self.preferred_good}")
        print(f"  Budget fraction (spend per round): {self.budget_fraction:.1%}")
        print(f"  Consumption fraction (consume per round): {self.consumption_fraction:.1%}")
        print(f"  Will sell labor to {self.commodity_producer_count + self.intermediary_firm_count + self.final_goods_firm_count} firms total")

    def start_round(self):
        """Called at the start of each round to reset tracking variables"""
        self.consumption_this_round = 0
        self.purchases_this_round = 0
        self.labor_sold = 0
        self.inventory_at_start = self[self.preferred_good]

    def sell_labor(self):
        """ Offer labor to firms """
        # Create fresh labor from endowment each round
        self.create('labor', self.labor_endowment)
        
        labor_stock = self['labor']
        labor_start = labor_stock
        
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
        """ Buy final goods from final goods firms """
        offers = self.get_offers(self.preferred_good)
        available_money = self['money']
        current_inventory = self[self.preferred_good]
        
        # Calculate budget for this round (fraction of available money)
        budget_for_round = available_money * self.budget_fraction
        
        # Calculate how much we need to buy to ensure minimum survival consumption
        # We need enough inventory to consume at least minimum_survival_consumption this round
        # Plus some buffer for next round's consumption
        next_round_buffer = self.minimum_survival_consumption * 0.1  # 10% buffer
        minimum_needed_inventory = self.minimum_survival_consumption + next_round_buffer
        minimum_needed_purchase = max(0, minimum_needed_inventory - current_inventory)
        
        total_spent = 0
        purchases_start = self[self.preferred_good]
        
        print(f"    Household {self.id}: Has ${available_money:.2f}, budget for round: ${budget_for_round:.2f}")
        print(f"      Current inventory: {current_inventory:.2f}")
        print(f"      Minimum survival consumption per round: {self.minimum_survival_consumption:.2f}")
        print(f"      Minimum inventory needed (consumption + buffer): {minimum_needed_inventory:.2f}")
        print(f"      Minimum purchase needed for survival: {minimum_needed_purchase:.2f}")
        print(f"      Received {len(offers)} {self.preferred_good} offers")
        
        # Process all offers in a single pass, prioritizing survival first
        for offer in offers:
            if total_spent >= budget_for_round and minimum_needed_purchase <= 0:
                # Budget exhausted and survival needs met, stop purchasing
                break
                
            cost = offer.quantity * offer.price
            
            # Determine what to buy from this offer
            purchase_quantity = 0
            purchase_reason = ""
            
            if minimum_needed_purchase > 0:
                # Priority 1: Survival purchasing (can exceed budget if necessary)
                survival_purchase = min(offer.quantity, minimum_needed_purchase)
                purchase_quantity = survival_purchase
                purchase_reason = "SURVIVAL"
                minimum_needed_purchase -= survival_purchase
                
            elif total_spent + cost <= budget_for_round:
                # Priority 2: Regular budget-based purchasing
                purchase_quantity = offer.quantity
                purchase_reason = "REGULAR"
                
            elif (budget_for_round - total_spent) > 0.01:
                # Priority 3: Partial purchase within remaining budget
                affordable_quantity = (budget_for_round - total_spent) / offer.price
                if affordable_quantity > 0.01:  # Minimum threshold
                    purchase_quantity = affordable_quantity
                    purchase_reason = "PARTIAL"
            
            # Execute the purchase
            if purchase_quantity > 0:
                purchase_cost = purchase_quantity * offer.price
                
                if purchase_quantity == offer.quantity:
                    self.accept(offer)
                    print(f"        {purchase_reason}: Accepted full offer: {offer.quantity:.2f} units for ${cost:.2f}")
                else:
                    self.accept(offer, quantity=purchase_quantity)
                    print(f"        {purchase_reason}: Partially accepted offer: {purchase_quantity:.2f} units for ${purchase_cost:.2f}")
                
                total_spent += purchase_cost
            else:
                print(f"        SKIPPED: Cannot afford offer: {offer.quantity:.2f} units for ${cost:.2f}")
        
        # Check if survival needs were met
        survival_needs_met = minimum_needed_purchase <= 0
        final_inventory = self[self.preferred_good]
        can_survive_this_round = final_inventory >= self.minimum_survival_consumption
        
        if not survival_needs_met:
            print(f"        ⚠️  WARNING: Could not purchase enough for minimum survival! Still need {minimum_needed_purchase:.2f} units")
        if not can_survive_this_round:
            print(f"        🚨 CRITICAL: Cannot meet minimum consumption this round! Have {final_inventory:.2f}, need {self.minimum_survival_consumption:.2f}")
        
        print(f"    Household {self.id}: Total spent ${total_spent:.2f} (budget: ${budget_for_round:.2f})")
        print(f"      Final inventory: {final_inventory:.2f}, can survive this round: {can_survive_this_round}")
        
        # Calculate purchases for this round (increase in inventory)
        purchases_end = self[self.preferred_good]
        self.purchases_this_round = purchases_end - purchases_start
        
        # Update labor sold calculation after market clearing
        # Labor sold = initial endowment - remaining labor
        labor_remaining = self['labor']  # Use dictionary access instead of get method
        self.labor_sold = self.labor_endowment - labor_remaining

    def consumption(self):
        """ Consume final goods to generate utility """
        consumption_start = self[self.preferred_good]
        available_goods = self[self.preferred_good]
        
        print(f"    Household {self.id}: Has {available_goods:.2f} {self.preferred_good}s available for consumption")
        print(f"      Minimum survival consumption required per round: {self.minimum_survival_consumption:.2f}")
        
        # Calculate intended consumption based on consumption fraction
        normal_consumption = available_goods * self.consumption_fraction
        if self.climate_stressed:
            normal_consumption *= self.climate_stress_factor
            print(f"      Climate stressed! Reducing normal consumption to {normal_consumption:.2f}")
        
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
            'climate_stressed': self.climate_stressed,
            'continent': getattr(self, 'continent', 'Unknown'),
            'vulnerability': 0,  # No direct climate vulnerability
            'consumption': self.get(self.preferred_good, 0)
        } 