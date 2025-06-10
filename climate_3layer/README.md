# Climate 3-Layer Economic Model

An agent-based economic simulation model that models a three-layer supply chain with optional climate stress effects. Built using the abcEconomics framework.

## Model Structure

### Agents

The model contains four types of agents:

1. **Commodity Producers** - Transform labor into raw commodities
2. **Intermediary Firms** - Transform labor and commodities into intermediate goods  
3. **Final Goods Firms** - Transform labor and intermediate goods into final consumer goods
4. **Households** - Supply labor to firms and consume final goods

### Supply Chain Flow

```
Households → [Labor] → All Firms
Commodity Producers → [Commodities] → Intermediary Firms
Intermediary Firms → [Intermediate Goods] → Final Goods Firms  
Final Goods Firms → [Final Goods] → Households
```

### Production Functions

All firms use Cobb-Douglas production functions with configurable input coefficients:
- **Commodity Producers**: `output = base_output_quantity * labor^1.0`
- **Intermediary Firms**: `output = base_output_quantity * labor^0.4 * commodity^0.6`
- **Final Goods Firms**: `output = base_output_quantity * labor^0.5 * intermediate_good^0.5`

## Economic Mechanisms

### Dynamic Pricing

All prices are calculated dynamically based on actual input costs:
```
price = (total_input_costs / production_quantity) * (1 + profit_margin)
```

Input costs include:
- Labor costs (wage * labor_quantity)
- Material costs (commodity/intermediate goods)
- Overhead costs (fixed per-round operational costs)

### Market Operations

**Labor Market:**
- Households offer labor endowment to all firms
- Firms accept offers in price-ascending order until budget exhausted
- Wage rates set in agent configuration

**Goods Markets:**
- Firms distribute production evenly among downstream buyers
- Buyers accept offers in price-ascending order
- Market clearing determines actual sales quantities

### Financial System

**Debt Creation:**
- Agents can create debt when money insufficient for purchases
- Households create debt for survival consumption needs
- Firms operate with debt to maintain supply chains
- Debt automatically repaid when cash available

**Overhead Costs:**
- Fixed operational costs per production round
- Included in pricing calculations
- Can be modified by climate stress

## Climate Framework

### Geographic Distribution

Agents are assigned to continents based on configuration:
- Africa, Asia, Europe, North America, South America
- Climate events target specific continents

### Climate Stress Types

**Chronic Stress:**
- Permanent, cumulative effects from long-term climate change
- Applied at simulation start
- Affects base production capacity or overhead costs

**Acute Stress:**  
- Temporary shocks from discrete climate events
- Applied probabilistically each round
- Reset to chronic levels at round end

### Stress Application

Climate stress can affect:
1. **Productivity**: Reduces `current_output_quantity` (multiplier on production)
2. **Overhead**: Increases `current_overhead` (added to costs)

Stress factors are multiplied: `current_value = base_value * stress_factor`

## Configuration

### File Structure

The model uses JSON configuration files with these main sections:

```json
{
  "simulation": {
    "name": "simulation_name",
    "rounds": 20,
    "result_path": "output_directory"
  },
  "climate": {
    "stress_enabled": true,
    "chronic_rules": [...],
    "shock_rules": [...]
  },
  "agents": {
    "agent_type": {
      "count": 2,
      "initial_money": 100,
      "production": {...},
      "geographical_distribution": [...]
    }
  }
}
```

### Agent Configuration

Each agent type requires:
- `count`: Number of agents to create
- `initial_money`: Starting money endowment
- `production.base_output_quantity`: Production capacity multiplier
- `production.base_overhead`: Fixed operational costs per round
- `production.inputs`: Input coefficients for production function
- `production.output`: Good type produced

### Climate Configuration

**Chronic Rules:**
```json
{
  "name": "soil_degradation",
  "agent_types": ["commodity_producer"],
  "continents": ["Africa", "Asia"],
  "productivity_stress_factor": 0.95,
  "overhead_stress_factor": 1.05
}
```

**Shock Rules:**
```json
{
  "name": "extreme_weather",
  "probability": 0.15,
  "agent_types": ["commodity_producer"],
  "continents": ["Africa"],
  "productivity_stress_factor": 0.3,
  "overhead_stress_factor": 2.5
}
```

## Data Output

The simulation exports CSV files for each agent type containing:

**Production Data:**
- Production quantities, costs, revenues
- Inventory levels, sales quantities
- Dynamic pricing evolution
- Debt creation and repayment

**Climate Data:**
- Geographic assignments
- Climate event occurrences
- Stress factor applications
- Production/overhead impacts

## Running Simulations

```bash
# Stable economy (no climate stress)
python start.py simulation_configurations/stable_config.json

# Economy with climate shocks
python start.py simulation_configurations/shock_config.json
```

### Command Line Usage

```bash
python start.py <config_file_path>
```

The simulation will:
1. Load configuration from specified JSON file
2. Create agents with specified parameters
3. Run simulation for configured number of rounds
4. Export data to configured result directory
5. Generate visualizations if enabled

## Visualization

The model includes two visualization systems:

**Animation Visualizer:**
- Time evolution plots of economic variables
- Animated supply chain flow diagrams
- Climate event impact visualization

**Supply Chain Visualizer:**
- Static analysis of production relationships
- Cost flow diagrams
- Economic equilibrium analysis

Enable in configuration:
```json
"visualization": {
  "create_visualizations": true,
  "create_dynamic_visualization": true
}
```

## Implementation Details

### Technology Stack
- **abcEconomics**: Agent-based modeling framework
- **Python 3.x**: Core implementation language
- **Pandas**: Data handling and export
- **Matplotlib**: Visualization and animation
- **JSON**: Configuration file format

### Model Flow (Per Round)
1. Apply climate stress (if enabled)
2. Households offer labor
3. Layer 1: Commodity producers buy labor and produce
4. Layer 2: Intermediary firms buy commodities/labor and produce  
5. Layer 3: Final goods firms buy intermediate goods/labor and produce
6. Households buy final goods and consume
7. Agents repay debts and log data
8. Reset acute climate stress

### Key Files
- `start.py`: Main simulation controller
- `*_producer.py`, `*_firm.py`, `household.py`: Agent implementations
- `climate_framework.py`: Climate stress system
- `config_loader.py`: Configuration management
- `animation_visualizer.py`: Dynamic visualization system

## Model Limitations

- Fixed supply chain topology (no agent creation/destruction)
- Homogeneous agents within each type
- No technological change or adaptation
- No financial markets or external trade
- Simplified climate impact modeling
- Perfect information assumptions

## Dependencies

```
abcEconomics>=0.9.0
pandas>=1.0.0
matplotlib>=3.0.0
numpy>=1.18.0
```