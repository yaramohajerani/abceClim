import abcEconomics as abce


class Household(abce.Agent):
    def init(self, config=None):
        """ Households provide labor and consume final goods.
        They are not directly affected by climate stress but may be affected indirectly through employment.
        
        Args:
            config: Configuration dictionary with initial resources, labor, and consumption parameters.
        """
        # Use configuration or fall back to defaults for backward compatibility
        if config is None:
            config = {
                'initial_money': 10,
                'initial_inventory': {},
                'labor': {
                    'endowment': 1,
                    'wage': 1.0
                },
                'consumption': {
                    'preference': 'final_good',
                    'budget_fraction': 0.8
                }
            }
        
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
        
        # Create initial labor endowment
        self.create('labor_endowment', self.labor_endowment)
        
        print(f"Household {self.id} initialized:")
        print(f"  Initial money: ${initial_money}")
        print(f"  Labor endowment: {self.labor_endowment}")
        print(f"  Wage: ${self.wage}")
        print(f"  Consumption preference: {self.preferred_good}")
        print(f"  Budget fraction: {self.budget_fraction:.1%}")

    def sell_labor(self):
        """ Offer labor to firms """
        # Create fresh labor from endowment each round
        self.create('labor', self.labor_endowment)
        
        labor_stock = self['labor']
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

    def buy_final_goods(self):
        """ Buy final goods for consumption """
        budget = self['money'] * self.budget_fraction
        
        offers = self.get_offers(self.preferred_good)
        print(f"    Household {self.id}: Has ${self['money']:.2f}, budget ${budget:.2f}, received {len(offers)} {self.preferred_good} offers")
        
        total_spent = 0
        for offer in offers:
            cost = offer.quantity * offer.price
            if total_spent + cost <= budget:
                self.accept(offer)
                total_spent += cost
                print(f"      Household {self.id}: Bought {offer.quantity:.2f} {self.preferred_good} for ${cost:.2f}")
            else:
                # Partial acceptance if we can afford part of the offer
                affordable_quantity = (budget - total_spent) / offer.price
                if affordable_quantity > 0.01:  # Minimum purchase threshold
                    self.accept(offer, quantity=affordable_quantity)
                    total_spent += affordable_quantity * offer.price
                    print(f"      Household {self.id}: Partially bought {affordable_quantity:.2f} {self.preferred_good} for ${affordable_quantity * offer.price:.2f}")
                break  # Budget exhausted
        
        if not offers:
            print(f"    Household {self.id}: No {self.preferred_good} offers received")
        
        print(f"    Household {self.id}: Total spent ${total_spent:.2f} of ${budget:.2f} budget")

    def consumption(self):
        """ Consume final goods """
        final_goods_stock = self[self.preferred_good]
        if final_goods_stock > 0:
            # Consume all available final goods
            consumption_amount = final_goods_stock
            self.destroy(self.preferred_good, consumption_amount)
            print(f"    Household {self.id}: Consumed {consumption_amount:.2f} {self.preferred_good}")
        else:
            print(f"    Household {self.id}: No {self.preferred_good} to consume")

    def _collect_agent_data(self, round_num, agent_type):
        """ Collect agent data for visualization (called by abcEconomics group system) """
        return {
            'id': self.id,
            'type': agent_type,
            'round': round_num,
            'wealth': self['money'],
            'climate_stressed': False,  # Households not directly affected by climate
            'continent': getattr(self, 'continent', 'Unknown'),
            'vulnerability': 0,  # No direct climate vulnerability
            'consumption': self.get(self.preferred_good, 0)
        } 