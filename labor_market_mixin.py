class LaborMarketMixin:
    """Mixin that provides labour supply and simplified direct-hire labour contracting."""

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------
    def _dprint(self, *args, **kwargs):
        if getattr(self, 'debug', False):
            print(*args, **kwargs)

    # ------------------------------------------------------------------
    # Labour supply
    # ------------------------------------------------------------------
    def labor_supply(self):
        """Regenerate and offer labour each round."""
        labor_endowment = getattr(self, 'labor_endowment', 0.0)
        if labor_endowment <= 0:
            return

        trade_pref = getattr(self, 'trade_preference', 1.0)
        labor_supply = labor_endowment * trade_pref
        if labor_supply <= 0:
            return

        self.inventory['labor'] = self.inventory.get('labor', 0) + labor_supply
        # keep _haves mirror in sync
        if isinstance(getattr(self, '_haves', None), dict):
            self._haves['labor'] = self.inventory['labor']

        self._dprint(f"{self.agent_type} {self.agent_id}: Offered {labor_supply:.2f} labour at wage {self.labor_wage:.2f}")

    # ------------------------------------------------------------------
    # Labour contracting – direct hire fallback
    # ------------------------------------------------------------------
    def labor_contracting(self):
        """Direct-hire labour transaction along network connections."""
        if not hasattr(self, 'connected_agents'):
            return

        contract_actions = []

        if self.group in ['producer', 'intermediary']:
            # Producers / intermediaries hire labour
            if not self.production_inputs or 'labor' not in self.production_inputs:
                return
            needed = max(0.0, self.production_inputs['labor'] - self.inventory.get('labor', 0))
            if needed == 0:
                return

            consumers = [a for a in self.connected_agents if getattr(a, 'group', None) == 'consumer']
            for consumer in consumers:
                if needed <= 0:
                    break
                avail = consumer.inventory.get('labor', 0)
                if avail <= 0:
                    continue
                qty = min(needed, avail)
                cost = qty * self.labor_wage
                if self.money < cost:
                    continue
                # transfer
                self.money -= cost
                consumer.money += cost
                consumer.inventory['labor'] -= qty
                self.inventory['labor'] = self.inventory.get('labor', 0) + qty
                if isinstance(self._haves, dict):
                    self._haves['labor'] = self.inventory['labor']
                if isinstance(consumer._haves, dict):
                    consumer._haves['labor'] = consumer.inventory['labor']
                needed -= qty
                contract_actions.append(f"hired {qty:.2f} from consumer {consumer.id}")

        elif self.group == 'consumer':
            # Nothing extra: labour is regenerated in labour_supply
            pass

        if contract_actions and getattr(self, 'debug', False):
            print(f"[LABOUR] {self.group} {self.agent_id}: " + "; ".join(contract_actions)) 