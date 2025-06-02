# Climate 3-Layer Economic Model

A 3-layer supply-chain economic model built with abcEconomics that examines the macroeconomic effects of climate stress on different layers of production. The model features optimal input allocation for firms based on Cobb-Douglas production functions with purchase optimization to maximize production. Note there are no energy limitations in this simple model.

## Model Overview

### Supply Chain Layers

1. **Commodity Producers** (Layer 1)
   - Use labor to produce raw commodities
   - Supply intermediary firms

2. **Intermediary Firms** (Layer 2)
   - Use labor and commodities to produce intermediate goods
   - Supply final goods firms
   - **Features optimal input allocation** based on market prices

3. **Final Goods Firms** (Layer 3)
   - Use labor and intermediate goods to produce final goods
   - Supply households
   - **Features optimal input allocation** based on market prices

4. **Households**
   - Provide labor to all firm layers
   - Consume final goods and generate utility
   - Not directly affected by climate stress

### Key Economic Features

- **Cobb-Douglas Production Functions**: Configurable production functions with customizable exponents
- **Price-Aware Optimization**: Budget allocation considers both production exponents and market prices
- **Multi-Layer Labor Market**: Households work across different firm layers
- **Supply Chain Dependencies**: Material flow creates bottlenecks and propagation effects
- **Configurable Climate Vulnerability**: Each agent type has customizable vulnerability levels

## Configuration System

### Quick Start

**Configuration file is required:**

```bash
# Using config files in subdirectories
python start.py simulation_configurations/model_config.json
python start.py simulation_configurations/config_asia_focus.json
python start.py simulation_configurations/config_stress_test.json
```

### Configuration File Structure

#### Main Sections

1. **simulation**: Basic simulation parameters
2. **climate**: Climate stress and shock configuration  
3. **agents**: Agent types, counts, and behaviors
4. **data_collection**: What data to track
5. **visualization**: Visualization settings

## Configuration Parameters

### Agent Configuration

Each agent type supports:

#### Basic Parameters
- `count`: Number of agents to create
- `initial_money`: Starting money amount
- `production.inputs`: Production function exponents (e.g., `{"labor": 0.5, "commodity": 0.5}`)
- `production.base_output_quantity`: Production capacity multiplier
- `production.price`: Selling price for goods

#### Climate Parameters
- `climate.base_vulnerability`: Base climate vulnerability
- `climate.vulnerability_variance`: Variation in vulnerability between agents

#### Geographic Distribution
- `geographical_distribution`: Array of continents where agents are located

### Climate Shock Rules

- `probability`: Probability of occurrence each round (0.0-1.0)
- `agent_types`: Array of agent types to affect (`["commodity_producer"]`, `["all"]`, etc.)
- `continents`: Array of continents to affect (`["Asia"]`, `["all"]`, etc.)
- `stress_factor`: Production multiplier (0.0-1.0, where 0.7 = 30% reduction)

### Minimum Consumption for Household Survival

The model now includes a **minimum mandatory consumption system** to ensure household survival:

#### Household Survival Mechanism
- **Configurable minimum consumption**: Set `minimum_survival_consumption` in household configuration
- **Survival-first purchasing**: Households purchase goods for survival before regular budget-based purchasing
- **Debt tolerance**: Households can exceed their budget to secure minimum consumption
- **Consumption protection**: Households never consume below their minimum survival level
- **Status tracking**: Logging includes whether minimum consumption requirements are met

#### Firm Minimum Production Requirement
- **Production guarantees**: Firms must produce enough goods to meet household survival needs
- **Debt-based production**: Firms can go into debt to purchase inputs for minimum production
- **Supply chain coordination**: All firms (commodity, intermediary, final goods) support minimum production
- **Crisis response**: System ensures goods availability even during economic or climate crises

#### Configuration Parameters

**Household Configuration:**
```json
"consumption": {
  "preference": "final_good",
  "budget_fraction": 0.8,
  "consumption_fraction": 0.9,
  "minimum_survival_consumption": 0.2  
}
```

## File Organization

```
climate_3layer/
├── start.py                      # Main simulation runner
├── simulation_configurations/
│   ├── model_config.json         # Default configuration
│   ├── config_asia_focus.json    # Asia-focused scenario
│   └── config_stress_test.json   # High-stress testing
└── result_*/                     # Generated output directories
```

## Climate Stress Features

### Types of Climate Stress

1. **Acute Climate Stress**: Random events with configurable probability per shock rule
2. **Chronic Climate Stress**: Permanent, cumulative productivity degradation
3. **Geographical Climate Effects**: Agents distributed across continents with region-specific shocks

## Visualization and Animation

### Animation Features
The model includes a built-in animation system that creates:
- **Time Evolution Plots**: Static 4-panel analysis with production, wealth, climate events, and statistics
- **Animated GIFs**: Multi-panel visualization showing supply chain networks, production evolution, geographical distribution, and climate impacts

### Enable Animations
Set in your configuration file:
```json
{
  "simulation": {
    "create_dynamic_visualization": true
  }
}
```

### Standalone Animation Creation
Create animations from existing simulation data:
```bash
python animation_visualizer.py result_supply_chain_test/
```

## Configuration Testing

### Validate Configurations
Test configurations without running full simulations:
```bash
# Validate all configurations
python test_configurations.py --validate-only

# Test specific configuration
python test_configurations.py --config simulation_configurations/model_config.json
```

## Output and Analysis

### Generated Files

- **CSV files**: Economic data for each agent type with production and optimization details
- **Visualizations**: Climate analysis charts and supply chain diagrams
- **Climate summary**: `climate_3_layer_summary.csv` with shock details
- **Animations**: Time-evolving GIF animations (if enabled)
- **Optimization logs**: Detailed logs showing input allocation decisions

## Troubleshooting

### Common Issues

**"No configuration file provided"**
- Always specify a config file path: `python start.py config.json`

**"Configuration file not found"**
- Ensure the file path is correct relative to current directory
- Use forward slashes in paths even on Windows

**"Invalid JSON"**
- Validate JSON syntax using an online validator
- Check for missing commas, brackets, or quotes

**"Missing required parameter"**
- Review the error message for the specific missing parameter
- Compare with the example configurations