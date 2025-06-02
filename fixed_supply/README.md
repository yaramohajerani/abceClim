# Fixed Supply Economic Model

A modified version of the 3-layer supply chain model where firms maintain fixed output quantities and dynamically adjust prices based on input costs and climate impacts.

## Key Features

### 1. Fixed Output Quantity
- Each firm type has a `desired_output_quantity` specified in the configuration
- Firms always try to produce this exact amount (no supply variation)
- Production only falls short if inputs are insufficient

### 2. Dynamic Pricing
- Prices are calculated each round based on:
  - Actual input costs incurred
  - Desired profit margin (from config)
  - Climate impact costs
- Formula: `Price = (Input Costs / Output) * (1 + Profit Margin) + Climate Cost Share`

### 3. Climate Cost Sharing (50-50 Split)
- When climate reduces productivity, firms need more inputs → higher costs
- Extra costs are split:
  - 50% passed to customers as higher prices
  - 50% absorbed by the producer (reduces profit margin)

### 4. Debt Mechanism
- Agents can go into debt to maintain production/consumption levels
- Firms create debt to buy inputs needed for fixed output
- Households create debt to maintain minimum consumption
- Net worth = Wealth - Debt

### 5. Enhanced Financial Tracking
The model tracks comprehensive financial metrics:
- **Debt levels** by agent and sector
- **Profit/Loss** for each firm
- **Profit margins** (target vs actual)
- **Climate cost burden** absorbed by producers
- **Net worth** (wealth minus debt)

## Model Structure

The model maintains the same 3-layer supply chain:

1. **Commodity Producers** (Layer 1)
   - Use labor to produce commodities
   - Most vulnerable to climate impacts
   
2. **Intermediary Firms** (Layer 2)
   - Use labor + commodities to produce intermediate goods
   - Moderate climate vulnerability
   
3. **Final Goods Firms** (Layer 3)
   - Use labor + intermediate goods to produce final goods
   - Least climate vulnerable
   
4. **Households**
   - Supply labor to all firms
   - Consume final goods
   - Can go into debt for survival consumption

## Configuration

Edit `simulation_configurations/fixed_supply_config.json`:

```json
{
  "agents": {
    "commodity_producer": {
      "production": {
        "desired_output_quantity": 4,    // Fixed output target
        "profit_margin": 0.2,            // 20% target margin
        "base_price": 1.0,               // Starting price
        "inputs": {"labor": 1}           // Cobb-Douglas exponents
      }
    }
  }
}
```

Key parameters:
- `desired_output_quantity`: The fixed production target
- `profit_margin`: Target profit margin (e.g., 0.2 = 20%)
- `base_price`: Initial price (before dynamic adjustments)

## Running the Model

1. **Basic simulation**:
   ```bash
   python start.py simulation_configurations/fixed_supply_config.json
   ```

2. **With climate shocks**:
   ```bash
   python start.py simulation_configurations/fixed_supply_shock_config.json
   ```

## Output Files

Results are saved in `result_fixed_supply/` (or similar):

### Data Files
- `panel_[agent_type]_production.csv`: Production, financial metrics
- `panel_household_consumption.csv`: Household consumption and debt
- `fixed_supply_climate_summary.csv`: Climate event timeline

### Key Metrics in CSV Files
- `money`: Current cash on hand
- `debt`: Total debt accumulated
- `profit`: Profit this round
- `target_margin`: Configured profit margin target
- `actual_margin`: Realized profit margin
- `climate_cost_absorbed`: Cost burden from climate impacts
- `price`: Dynamic price this round

### Visualizations
- `fixed_supply_time_evolution_[timestamp].png`: 6-panel analysis including:
  - Production levels
  - Wealth by sector
  - Inventory accumulation
  - Total system debt
  - Net worth evolution
  - Profit and climate costs
  
- `fixed_supply_animation_[timestamp].gif`: Animated visualization showing:
  - Supply chain network with debt indicators
  - Production and inventory dynamics
  - Geographical climate impacts
  - Financial metrics dashboard

## Understanding the Results

### Price Dynamics
- Watch how prices increase when climate shocks hit
- Compare actual vs target profit margins
- See which sectors absorb the most climate costs

### Debt Accumulation
- Track which agents go into debt first
- Monitor total system debt over time
- Compare debt levels across sectors

### System Stability
- Check if production targets are maintained
- Monitor inventory buildups or shortages
- Assess if the 50-50 cost sharing is sustainable

## Example Analysis Questions

1. **How do prices evolve during climate shocks?**
   - Look at the `price` column in production CSV files
   - Compare to `base_price` in config

2. **Which agents struggle most financially?**
   - Check `debt` and `net_worth` columns
   - Look for negative net worth

3. **Are profit margins maintained?**
   - Compare `actual_margin` vs `target_margin`
   - See how climate costs affect margins

4. **Is the system sustainable long-term?**
   - Monitor total debt growth
   - Check if agents can service their debt
   - Look for cascading failures

## Extending the Model

To modify the model behavior:

1. **Change cost sharing ratio** (currently 50-50):
   - Edit `calculate_dynamic_price()` in agent files
   - Adjust `customer_burden` and `producer_burden`

2. **Add interest on debt**:
   - Track debt age
   - Apply interest charges each round

3. **Implement credit limits**:
   - Set maximum debt levels
   - Handle production failures when credit exhausted

4. **Vary profit margins by market conditions**:
   - Make margins responsive to supply/demand
   - Implement market power dynamics