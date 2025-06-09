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
        
        # Climate framework requirements (households don't produce but framework expects these)
        self.current_output_quantity = 1.0  # For labor capacity
        self.current_overhead = 0.0  # Households have no overhead
        
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
        print(f"  Minimum survival consumption: {self.minimum_survival_consumption}")
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
        
        # Don't spend more money than we have
        spending_budget = min(consumption_spending_budget, available_money)
        
        print(f"  💰 Available money: ${available_money:.2f}, Spending budget: ${spending_budget:.2f}")
        
        # Try to buy final goods - prioritize survival first, then budget considerations
        total_spent = 0
        total_purchased = 0
        
        # Calculate current and projected inventory levels
        current_inventory = final_goods_start
        
        for offer in offers:
            # Calculate how much we need for survival
            total_inventory_after_purchase = current_inventory + total_purchased
            survival_shortfall = max(0, self.minimum_survival_consumption - total_inventory_after_purchase)
            
            # Calculate budget-based quantity we can afford
            remaining_budget = spending_budget - total_spent
            affordable_quantity = remaining_budget / offer.price if remaining_budget > 0 else 0
            
            # Determine purchase strategy
            if survival_shortfall > 0:
                # SURVIVAL MODE: Buy as much as needed for survival, using debt if necessary
                survival_purchase_quantity = min(survival_shortfall, offer.quantity)
                
                if survival_purchase_quantity <= affordable_quantity:
                    # Can afford survival purchase within budget
                    quantity_to_buy = survival_purchase_quantity
                    use_debt_for_survival = False
                else:
                    # Need debt for survival purchase
                    quantity_to_buy = survival_purchase_quantity
                    use_debt_for_survival = True
                    
                print(f"    🆘 SURVIVAL MODE: Need {survival_shortfall:.2f} units, buying {quantity_to_buy:.2f} (debt: {use_debt_for_survival})")
            else:
                # NORMAL MODE: Buy within budget for additional consumption
                quantity_to_buy = min(affordable_quantity, offer.quantity)
                use_debt_for_survival = False
                
                if quantity_to_buy > 0.01:
                    print(f"    💰 NORMAL MODE: Buying {quantity_to_buy:.2f} units within budget")
            
            if quantity_to_buy > 0.01:  # Only accept meaningful amounts
                cost = quantity_to_buy * offer.price
                
                if use_debt_for_survival:
                    # Use debt for survival purchases
                    print(f"    🆘 SURVIVAL PURCHASE WITH DEBT: {quantity_to_buy:.2f} units at ${offer.price:.2f}/unit = ${cost:.2f}")
                    self.spend_money_with_debt(cost, f"survival purchase from {offer.sender}")
                else:
                    # Regular budget purchase - but still use debt-aware mechanism in case of rounding errors
                    print(f"    💰 REGULAR PURCHASE: {quantity_to_buy:.2f} units at ${offer.price:.2f}/unit = ${cost:.2f}")
                    self.spend_money_with_debt(cost, f"regular purchase from {offer.sender}")
                    total_spent += cost
                
                try:
                    result = self.accept(offer, quantity=quantity_to_buy)
                    total_purchased += quantity_to_buy
                    
                    if use_debt_for_survival:
                        print(f"    ✅ Survival purchase successful: {quantity_to_buy:.2f} units (debt: ${self.debt_created_this_round:.2f})")
                    else:
                        print(f"    ✅ Regular purchase: {quantity_to_buy:.2f} units for ${cost:.2f}")
                        
                except Exception as e:
                    print(f"    ❌ Could not accept offer: {e}")
                    # Reverse any debt/money creation for failed purchase
                    if cost <= self.debt_created_this_round:
                        # If we created debt for this purchase, reverse it
                        money_to_destroy = min(cost, self['money'])
                        if money_to_destroy > 0:
                            self.destroy('money', money_to_destroy)
                        self.debt -= cost
                        self.debt_created_this_round -= cost
                        print(f"    🔄 Reversed ${cost:.2f} debt creation and destroyed ${money_to_destroy:.2f} money due to failed purchase")
        
        # Final survival check after all purchases
        final_inventory_after_purchase = final_goods_start + total_purchased
        if final_inventory_after_purchase < self.minimum_survival_consumption:
            remaining_shortfall = self.minimum_survival_consumption - final_inventory_after_purchase
            print(f"    ⚠️ WARNING: Still short {remaining_shortfall:.2f} units for survival after all purchase attempts")
            print(f"    Either no offers available or all purchase attempts failed")
        
        print(f"  🛒 Total purchased: {total_purchased:.2f} units, Total spent: ${total_spent:.2f}")
        if self.debt_created_this_round > 0:
            print(f"  💳 Created debt this round: ${self.debt_created_this_round:.2f}, Total debt: ${self.debt:.2f}")
        
        return total_purchased

    def spend_money_with_debt(self, amount, description="expense"):
        """
        Spend money, creating debt if insufficient funds available.
        For abcEconomics compatibility, creates actual money when in debt to enable offer acceptance.
        
        Args:
            amount: Amount to spend
            description: Description of the expense for logging
            
        Returns:
            float: Actual cost paid (amount of money spent/debt created)
        """
        current_money = self['money']
        
        if current_money >= amount:
            # Sufficient funds - no action needed, money will be destroyed when offer is accepted
            # print(f"    Household {self.id}: Has sufficient funds (${current_money:.2f}) for {description} (${amount:.2f})")
            return amount
        else:
            # Insufficient funds - create money for the shortfall via debt
            debt_created = amount - current_money
            
            # Create money to cover the shortfall - this enables offer acceptance
            self.create('money', debt_created)
            
            # Track the debt
            self.debt += debt_created
            self.debt_created_this_round += debt_created
            
            print(f"    💳 Household {self.id}: Created ${debt_created:.2f} in money via debt for {description}")
            print(f"    Total debt now: ${self.debt:.2f}, Money available: ${self['money']:.2f}")
            return amount

    def receive_money_and_pay_debt(self, amount, source="income"):
        """
        Receive money and automatically use it to pay down debt first.
        
        Args:
            amount: Amount of money received
            source: Source of the money for logging
        """
        self.create('money', amount)
        print(f"    Household {self.id}: Received ${amount:.2f} from {source}")
        
        if self.debt > 0:
            debt_payment = min(amount, self.debt)
            self.debt -= debt_payment
            self.destroy('money', debt_payment)
            print(f"    Household {self.id}: Paid ${debt_payment:.2f} toward debt (Remaining debt: ${self.debt:.2f})")

    def consumption(self):
        """ Consume final goods to generate utility """
        consumption_start = self[self.preferred_good]
        available_goods = self[self.preferred_good]
        
        print(f"    Household {self.id}: Has {available_goods:.2f} {self.preferred_good}s available for consumption")
        print(f"      Minimum survival consumption required per round: {self.minimum_survival_consumption:.2f}")
        
        # Calculate intended consumption based on consumption fraction
        normal_consumption = available_goods * self.consumption_fraction
        
        # Calculate intended consumption based on consumption fraction
        normal_consumption = available_goods * self.consumption_fraction
        
        # Consume what we can from available inventory - can't consume more than we have!
        intended_consumption = max(self.minimum_survival_consumption, normal_consumption)
        consumption_amount = min(intended_consumption, available_goods)  # Cannot exceed actual inventory
        
        print(f"      Normal consumption (fraction of inventory): {normal_consumption:.2f}")
        print(f"      Minimum survival consumption required: {self.minimum_survival_consumption:.2f}")
        print(f"      Intended consumption: {intended_consumption:.2f}")
        print(f"      Actual consumption (limited by inventory): {consumption_amount:.2f}")
        
        # Check if we can meet survival needs
        survival_needs_met = consumption_amount >= self.minimum_survival_consumption
        if not survival_needs_met:
            shortfall = self.minimum_survival_consumption - consumption_amount
            print(f"      ⚠️ SURVIVAL CRISIS: Need {self.minimum_survival_consumption:.2f}, can only consume {consumption_amount:.2f}")
            print(f"          Shortfall: {shortfall:.2f} units - household should have bought more goods!")
        
        # Actually consume the goods from inventory
        if consumption_amount > 0:
            try:
                self.destroy(self.preferred_good, consumption_amount)
                self.utility += consumption_amount
                print(f"      ✅ Consumed {consumption_amount:.2f} {self.preferred_good}s from inventory")
            except Exception as e:
                print(f"      ❌ Consumption failed: {e}")
                consumption_amount = 0
        else:
            print(f"      ❌ No {self.preferred_good}s available to consume - SURVIVAL CRISIS!")
        
        # Final status
        print(f"      Survival needs met: {survival_needs_met}")
        
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
        
        # Log the data using abcEconomics logging - NOW INCLUDING DEBT DATA
        self.log('consumption', {
            'consumption': self.consumption_this_round,
            'purchases': self.purchases_this_round,
            'inventory_change': inventory_change,
            'cumulative_inventory': cumulative_inventory,
            'labor_sold': self.labor_sold,
            'money': current_money,
            'debt': self.debt,  # Add debt tracking
            'debt_created_this_round': self.debt_created_this_round,  # Add debt creation tracking
            'minimum_survival_consumption': self.minimum_survival_consumption,
            'minimum_consumption_met': minimum_consumption_met,
            'survival_buffer': survival_buffer
        })
        
        print(f"    Household {self.id}: Logged - Consumption: {self.consumption_this_round:.2f}, Purchases: {self.purchases_this_round:.2f}, Labor sold: {self.labor_sold:.2f}")
        print(f"      Inventory: {cumulative_inventory:.2f}, Money: ${current_money:.2f}, Debt: ${self.debt:.2f}")
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