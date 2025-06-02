import abcEconomics as abce


class Household(abce.Agent):
    def init(self, config):
        """ Households provide labor and consume final goods.
        They are not directly affected by climate stress but may be affected indirectly through employment.
        
        Args:
            config: Configuration dictionary with initial resources, labor, and consumption parameters.
        """
        # Initialize money
        initial_money = config.get('initial_money', 10)
        self.create('money', initial_money)
        
        # Initialize inventory from configuration
        initial_inventory = config.get('initial_inventory', {})
        for good, quantity in initial_inventory.items():
            self.create(good, quantity)
        
        # Labor parameters from configuration
        labor_config = config.get('labor', {})
        self.labor_endowment = labor_config.get('endowment', 1)
        self.wage = labor_config.get('wage', 1.0)
        
        # Consumption parameters from configuration
        consumption_config = config.get('consumption', {})
        self.preferred_good = consumption_config.get('preference', 'final_good')
        self.budget_fraction = consumption_config.get('budget_fraction', 0.8)
        self.consumption_fraction = consumption_config.get('consumption_fraction', 0.9)  # Fraction of goods to consume
        
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
        
        print(f"Household {self.id} initialized:")
        print(f"  Initial money: ${initial_money}")
        print(f"  Labor endowment: {self.labor_endowment}")
        print(f"  Wage: ${self.wage}")
        print(f"  Consumption preference: {self.preferred_good}")
        print(f"  Budget fraction: {self.budget_fraction:.1%}")

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
            for i in range(3):  # Assuming 3 commodity producers
                firms.append(('commodity_producer', i))
            # Add intermediary firms  
            for i in range(2):  # Assuming 2 intermediary firms
                firms.append(('intermediary_firm', i))
            # Add final goods firms
            for i in range(2):  # Assuming 2 final goods firms
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
        total_spent = 0
        purchases_start = self[self.preferred_good]
        
        print(f"    Household {self.id}: Has ${available_money:.2f}, received {len(offers)} {self.preferred_good} offers")
        
        for offer in offers:
            cost = offer.quantity * offer.price
            if total_spent + cost <= available_money:
                self.accept(offer)
                total_spent += cost
                print(f"      Accepted offer: {offer.quantity:.2f} units for ${cost:.2f}")
            else:
                # Try partial acceptance if we can afford at least part of it
                affordable_quantity = (available_money - total_spent) / offer.price
                if affordable_quantity > 0.01:  # Minimum threshold
                    self.accept(offer, quantity=affordable_quantity)
                    total_spent += affordable_quantity * offer.price
                    print(f"      Partially accepted offer: {affordable_quantity:.2f} units for ${affordable_quantity * offer.price:.2f}")
                else:
                    print(f"      Cannot afford offer: {offer.quantity:.2f} units for ${cost:.2f}")
                break  # Budget exhausted
        
        print(f"    Household {self.id}: Spent ${total_spent:.2f} on {self.preferred_good}s")
        
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
        
        # Apply climate stress to consumption preferences (if any)
        consumption_fraction = self.consumption_fraction
        if self.climate_stressed:
            consumption_fraction *= self.climate_stress_factor
            print(f"      Climate stressed! Reducing consumption to {consumption_fraction:.2f} of available goods")
        
        # Consume a fraction of available goods
        consumption_amount = available_goods * consumption_fraction
        
        if consumption_amount > 0:
            try:
                self.destroy(self.preferred_good, consumption_amount)
                print(f"      Consumed {consumption_amount:.2f} {self.preferred_good}s")
                # Update utility based on consumption
                self.utility += consumption_amount
            except Exception as e:
                print(f"      Consumption failed: {e}")
                consumption_amount = 0
        else:
            print(f"      No {self.preferred_good}s to consume")
        
        # Calculate consumption for this round
        consumption_end = self[self.preferred_good]
        self.consumption_this_round = consumption_start - consumption_end
        
        print(f"    Household {self.id}: Current utility: {self.utility:.2f}")

    def log_round_data(self):
        """Log consumption, purchases, and inventory data for this round"""
        # Calculate inventory change and cumulative inventory
        inventory_change = self.purchases_this_round - self.consumption_this_round
        cumulative_inventory = self[self.preferred_good]
        current_money = self['money']
        
        # Log the data using abcEconomics logging
        self.log('consumption', {
            'consumption': self.consumption_this_round,
            'purchases': self.purchases_this_round,
            'inventory_change': inventory_change,
            'cumulative_inventory': cumulative_inventory,
            'labor_sold': self.labor_sold,
            'money': current_money
        })
        
        print(f"    Household {self.id}: Logged - Consumption: {self.consumption_this_round:.2f}, Purchases: {self.purchases_this_round:.2f}, Labor sold: {self.labor_sold:.2f}, Inventory: {cumulative_inventory:.2f}, Money: ${current_money:.2f}")

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