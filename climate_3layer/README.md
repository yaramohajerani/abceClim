# Climate 3-Layer Economic Model

A climate-economics simulation model that captures the effects of climate stress on supply chain production through overhead cost increases rather than direct productivity impacts.

## Model Architecture

### Core Design Philosophy

This model uses an **overhead-based climate impact system** where climate stress manifests as increased business costs (CapEx, legal fees, damages, disruptions) rather than direct productivity reductions. This approach is more realistic as firms rarely lose productive capacity directly, but instead face higher operational costs when dealing with climate-related challenges.

### Agent Types

**Supply Chain Layers (Production)**
- **Commodity Producers**: Transform labor into raw commodities (e.g., agriculture, mining)
- **Intermediary Firms**: Transform labor + commodities into intermediate goods (e.g., processing, manufacturing)
- **Final Goods Firms**: Transform labor + intermediate goods into final consumer goods

**Economic Actors**
- **Households**: Supply labor, consume final goods, accumulate wealth

### Climate Impact Mechanism

Climate stress affects firms through **overhead cost increases**:

- **Base Overhead**: Fixed operational costs per round (configured per agent type)
- **Current Overhead**: Base overhead multiplied by stress factors from climate events
- **Cost Sharing**: Configurable split between firm absorption vs. customer price pass-through

**Stress Types:**
- **Acute Stress**: Temporary overhead spikes from discrete climate events
- **Chronic Stress**: Permanent overhead increases from long-term climate degradation

### Dynamic Pricing System

All prices are calculated dynamically based on actual costs:

**Pricing Formula**: `(input_costs + overhead_shared_with_customers) × (1 + profit_margin)`

- **Input Costs**: Actual labor and material costs from current round
- **Overhead Sharing**: `customer_share` parameter determines how much overhead is passed to customers vs. absorbed by firm
- **No Hardcoded Prices**: Initial prices use simple wage-based estimates; market forces drive all subsequent pricing

### Supply Chain Coordination

The model ensures household survival through cascading minimum production responsibilities:

1. **Household Survival Needs**: Each household requires minimum consumption per round
2. **Final Goods Responsibility**: Each firm calculates their share of total household needs
3. **Intermediary Responsibility**: Based on final goods firms' input requirements
4. **Commodity Responsibility**: Based on intermediary firms' input requirements

This creates automatic supply chain coordination without central planning.

## Configuration Structure

### Required Parameters

```json
{
  "simulation": {
    "name": "simulation_name",
    "rounds": 20,
    "result_path": "result_directory"
  },
  "wage": 4.0,
  "climate": {
    "stress_enabled": true/false,
    "acute_stress_ranges": {
      "commodity_producer": [0.2, 0.8],
      "intermediary_firm": [0.2, 0.6], 
      "final_goods_firm": [0.1, 0.4]
    }
  },
  "agents": {
    "agent_type": {
      "count": 4,
      "initial_money": 100,
      "production": {
        "base_output_quantity": 4.0,
        "base_overhead": 2.0,
        "inputs": {"labor": 1.0},
        "output": "commodity"
      },
      "climate": {
        "base_vulnerability": 0.3,
        "cost_sharing": {"customer_share": 0.5}
      }
    }
  }
}
```

### Optional Parameters

- **supply_chain.safety_buffer**: Production buffer above strict minimum (defaults to 1.0 = no buffer)
- **profit_margin**: Target profit margin for pricing (defaults to 0.0)
- **geographical_distribution**: Agent distribution across continents

### Removed Dependencies

- No hardcoded expected prices
- No mandatory safety buffers
- No fixed price configurations
- Acute stress ranges only required when climate stress is enabled

## Key Features

### 1. Realistic Climate Economics
- Climate stress as overhead costs rather than productivity loss
- Configurable cost sharing between firms and customers
- Separate acute (temporary) and chronic (permanent) stress impacts

### 2. Pure Dynamic Pricing
- All prices emerge from actual input costs and overhead
- No hardcoded price expectations
- Market-driven price discovery and adjustment

### 3. Supply Chain Resilience
- Firms prioritize survival purchasing to maintain minimum production
- Debt creation allowed for essential inputs
- Automatic coordination across supply chain layers

### 4. Comprehensive Data Tracking
- Overhead cost breakdown (absorbed vs. passed to customers)
- Debt tracking for all agent types
- Dynamic pricing evolution
- Climate event impacts on costs

## Output Data

The model generates detailed CSV files tracking:

**Production Data:**
- `production_base_overhead`: Original overhead costs
- `production_current_overhead`: Stress-adjusted overhead costs  
- `production_overhead_absorbed`: Overhead absorbed by firm
- `production_overhead_passed_to_customers`: Overhead included in prices
- `production_price`: Current market price
- `debt_created_this_round`: Emergency debt for survival purchases

**Visualization:**
- Time evolution plots showing overhead, pricing, and debt trends
- Animated supply chain visualizations
- Climate event impact tracking

## Running Simulations

```bash
# Stable economy (no climate stress)
python start.py simulation_configurations/stable_config.json

# Climate shock scenario  
python start.py simulation_configurations/stable_shock_config.json
```

## Model Validation

The model demonstrates:
- **Economic Stability**: Households maintain consumption above survival minimums
- **Price Convergence**: Dynamic pricing reaches stable equilibrium
- **Supply Chain Functionality**: Production meets demand without shortages
- **Climate Responsiveness**: Overhead costs increase appropriately with climate stress
- **Market Efficiency**: No artificial constraints or hardcoded values

## Future Extensions

- Industry-specific overhead responses to different climate stress types
- Regional climate variation impacts
- Technological adaptation reducing overhead over time
- Financial market integration for climate risk pricing