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
        self.consumption_fraction = consumption_config['consumption_fraction']
        self.minimum_survival_consumption = consumption_config['minimum_survival_consumption']
        
        # Track consumption data for logging
        self.consumption_this_round = 0
        self.final_goods_purchased = 0
        self.purchases_this_round = 0
        
        # Climate framework requirements (households don't produce but framework expects these)
        self.current_output_quantity = 1.0  # For labor capacity
        self.current_overhead = 0.0  # Households have no overhead
        
        # Get firm counts from config for labor distribution
        self.commodity_producer_count = config['commodity_producer_count']
        self.intermediary_firm_count = config['intermediary_firm_count']
        self.final_goods_firm_count = config['final_goods_firm_count']
        total_firms = self.commodity_producer_count + self.intermediary_firm_count + self.final_goods_firm_count
        
        # get labor allocation per firm (equal labor contribution to each firm)
        self.labor_allocation = self.labor_endowment / total_firms
        
        # Initialize heterogeneity characteristics (will be set by climate framework)
        self.heterogeneity_characteristics = None
        
        print(f"Household {self.id} initialized:")
        print(f"  Initial money: ${initial_money}")
        print(f"  Labor endowment: {self.labor_endowment}")
        print(f"  Wage: ${self.wage}")
        print(f"  Minimum survival consumption: {self.minimum_survival_consumption}")
        print(f"  Will distribute labor to {total_firms} firms")

    def set_heterogeneity_characteristics(self, characteristics):
        """Set individual characteristics for this household"""
        self.heterogeneity_characteristics = characteristics
        if characteristics:
            print(f"  Household {self.id} heterogeneity set:")
            print(f"    Climate vulnerability: productivity={characteristics.climate_vulnerability_productivity:.2f}, overhead={characteristics.climate_vulnerability_overhead:.2f}")
            print(f"    Behavior: risk_tolerance={characteristics.risk_tolerance:.2f}, debt_willingness={characteristics.debt_willingness:.2f}, consumption_preference={characteristics.consumption_preference:.2f}")

    def start_round(self):
        """Called at the start of each round to reset tracking variables"""
        self.consumption_this_round = 0
        self.final_goods_purchased = 0
        self.purchases_this_round = 0
        self.debt_created_this_round = 0
        self.income = 0
        self.spending = 0

    def sell_labor(self):
        for firm_id in range(self.commodity_producer_count):
            self.sell(('commodity_producer', firm_id), 'labor', self.labor_allocation, self.wage)

        for firm_id in range(self.intermediary_firm_count):
            self.sell(('intermediary_firm', firm_id), 'labor', self.labor_allocation, self.wage)

        for firm_id in range(self.final_goods_firm_count):
            self.sell(('final_goods_firm', firm_id), 'labor', self.labor_allocation, self.wage)

    def buy_final_goods(self):
        """ Buy final goods based on total available resources - with heterogeneity in debt willingness """
        final_goods_start = self[self.preferred_good]
        money_start = self['money']
        offers = self.get_offers(self.preferred_good)
        
        # Sort offers by price (ascending - cheapest first)
        offers.sort(key=lambda offer: offer.price)
        
        # Get behavioral modifiers from heterogeneity
        debt_willingness = 1.0
        consumption_preference = 1.0
        if self.heterogeneity_characteristics:
            debt_willingness = self.heterogeneity_characteristics.debt_willingness
            consumption_preference = self.heterogeneity_characteristics.consumption_preference
        
        # first check if there's enough money to get minimum consumption
        additional_inventory_needed = self.minimum_survival_consumption - final_goods_start
        print(f"    DEBUG: Household {self.id} has {final_goods_start}. inventory shortage: {additional_inventory_needed}")
        if additional_inventory_needed > 0:
            acquired_dry_run = 0
            price_dry_run = 0
            for offer in offers:
                acquired_dry_run += offer.quantity
                price_dry_run += offer.quantity * offer.price
            
                if acquired_dry_run >= additional_inventory_needed:
                    break
        
            # check if we need to create enough debt to get minimum
            debt_neeeded = price_dry_run - money_start
            print(f"    DEBUG: Household {self.id} needs {debt_neeeded} more money")

            if debt_neeeded > 0:
                # Apply debt willingness modifier
                modified_debt_needed = debt_neeeded * debt_willingness
                print(f"    DEBUG: Household {self.id} debt willingness: {debt_willingness:.2f}")
                print(f"    DEBUG: Household {self.id} modified debt needed: {modified_debt_needed:.2f}")
                
                if modified_debt_needed > 0:
                    print(f"    DEBUG: Household {self.id} created {modified_debt_needed} more debt")
                    # Insufficient funds - create money for the shortfall via debt
                    self.create('money', modified_debt_needed)
                    
                    # Track the debt
                    self.debt += modified_debt_needed
                    self.debt_created_this_round += modified_debt_needed
        
        # now buy goods with consumption preference modifier
        for offer in offers:
            # Apply consumption preference to buying behavior
            if consumption_preference > 1.0:
                # More spendthrift households might buy more aggressively
                # This could be implemented by adjusting the acceptance logic
                pass
            # abcEcon already takes care of full and partial acceptances based on how much money is available
            self.accept(offer)

        final_goods_end = self[self.preferred_good]
        total_purchased = final_goods_end - final_goods_start
        
        self.purchases_this_round += total_purchased
         
        print(f"    Household {self.id}: Purchased {total_purchased} {self.preferred_good}.")

    def pay_debts(self):
        """
        Use available money to pay debts - with heterogeneity in debt management
        """
        if self.debt > 0:
            # Get behavioral modifiers
            debt_willingness = 1.0
            if self.heterogeneity_characteristics:
                debt_willingness = self.heterogeneity_characteristics.debt_willingness
            
            # More debt-averse households pay more aggressively
            payment_multiplier = 1.0 / debt_willingness  # Inverse relationship
            payment_multiplier = max(0.5, min(2.0, payment_multiplier))  # Reasonable bounds
            
            # get the minimum of money and debt to pay debts 
            available_money = self['money']
            max_payment = available_money * payment_multiplier
            payable_debt = min(self.debt, max_payment)
            
            # Ensure payable_debt is non-negative
            payable_debt = max(0.0, payable_debt)
            
            if payable_debt > 0:
                self.debt -= payable_debt
                self.destroy('money', payable_debt)
                print(f"    Household {self.id}: Paid ${payable_debt:.2f} toward debt (Remaining debt: ${self.debt:.2f}, payment multiplier: {payment_multiplier:.2f})")
            else:
                print(f"    Household {self.id}: No money available to pay debt (debt: ${self.debt:.2f}, money: ${available_money:.2f})")

    def consumption(self):
        """ Consume final goods - with heterogeneity in consumption preferences """
        available_goods = self[self.preferred_good]
        
        print(f"    Household {self.id}: Has {available_goods:.2f} {self.preferred_good}s available for consumption")

        # Get consumption preference modifier
        consumption_preference = 1.0
        if self.heterogeneity_characteristics:
            consumption_preference = self.heterogeneity_characteristics.consumption_preference

        # choose consumption amount as max of consumption fraction or min consumption
        # Apply consumption preference modifier
        modified_consumption_fraction = self.consumption_fraction * consumption_preference
        normal_consumption = available_goods * modified_consumption_fraction
        
        intended_consumption = max(self.minimum_survival_consumption, normal_consumption)

        # Consume what we can from available inventory - can't consume more than we have!
        consumption_amount = min(intended_consumption, available_goods)  # Cannot exceed actual inventory
        
        print(f"      Normal consumption (fraction of inventory): {normal_consumption:.2f}")
        print(f"      Consumption preference modifier: {consumption_preference:.2f}")
        print(f"      Modified consumption fraction: {modified_consumption_fraction:.2f}")
        print(f"      Minimum survival consumption required: {self.minimum_survival_consumption:.2f}")
        print(f"      Intended consumption: {intended_consumption:.2f}")
        print(f"      Actual consumption (limited by inventory): {consumption_amount:.2f}")
        
        # consume amount 
        self.consumption_this_round += consumption_amount
        self.destroy(self.preferred_good, consumption_amount)

        # Check if we can meet survival needs
        survival_needs_met = consumption_amount >= self.minimum_survival_consumption
        return survival_needs_met

    def log_round_data(self):
        """Log consumption, purchases, and inventory data for this round"""
        # Calculate inventory change and cumulative inventory
        inventory_change = self.purchases_this_round - self.consumption_this_round
        cumulative_inventory = self[self.preferred_good]
        current_money = self['money']
        
        # Check if minimum consumption requirement is met
        minimum_consumption_met = self.consumption_this_round >= self.minimum_survival_consumption
        
        # Get heterogeneity data for logging
        heterogeneity_data = {}
        if self.heterogeneity_characteristics:
            heterogeneity_data = {
                'climate_vulnerability_productivity': self.heterogeneity_characteristics.climate_vulnerability_productivity,
                'climate_vulnerability_overhead': self.heterogeneity_characteristics.climate_vulnerability_overhead,
                'risk_tolerance': self.heterogeneity_characteristics.risk_tolerance,
                'debt_willingness': self.heterogeneity_characteristics.debt_willingness,
                'consumption_preference': self.heterogeneity_characteristics.consumption_preference
            }
        
        # Log the data using abcEconomics logging - NOW INCLUDING DEBT DATA
        log_data = {
            'consumption': self.consumption_this_round,
            'purchases': self.purchases_this_round,
            'inventory_change': inventory_change,
            'cumulative_inventory': cumulative_inventory,
            'money': current_money,
            'debt': self.debt,  # Add debt tracking
            'debt_created_this_round': self.debt_created_this_round,  # Add debt creation tracking
            'minimum_survival_consumption': self.minimum_survival_consumption,
            'minimum_consumption_met': minimum_consumption_met
        }
        
        # Add heterogeneity data if available
        log_data.update(heterogeneity_data)
        
        self.log('consumption', log_data)
        
        print(f"    Household {self.id}: Logged - Consumption: {self.consumption_this_round:.2f}, Purchases: {self.purchases_this_round:.2f}")
        print(f"      Inventory: {cumulative_inventory:.2f}, Money: ${current_money:.2f}, Debt: ${self.debt:.2f}")
        print(f"      Minimum consumption met: {minimum_consumption_met} (consumed {self.consumption_this_round:.2f}, required {self.minimum_survival_consumption:.2f})")
        if self.heterogeneity_characteristics:
            print(f"      Heterogeneity: debt_willingness={self.heterogeneity_characteristics.debt_willingness:.2f}, consumption_preference={self.heterogeneity_characteristics.consumption_preference:.2f}")
