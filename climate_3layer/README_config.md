# Climate 3-Layer Model - Configuration System

## Overview

The Climate 3-Layer Model now supports flexible configuration through JSON files, allowing you to easily modify simulation parameters without changing code. This makes it simple to test different scenarios, adjust agent behaviors, and configure climate shock patterns.

## Quick Start

### Running with Default Configuration

```bash
python start.py
```
This uses the default `model_config.json` file.

### Running with Custom Configuration

```bash
python start.py config_asia_focus.json
python start.py config_stress_test.json
```

## Configuration File Structure

### Main Sections

1. **simulation**: Basic simulation parameters
2. **climate**: Climate stress and shock configuration  
3. **agents**: Agent types, counts, and behaviors
4. **data_collection**: What data to track
5. **visualization**: Visualization settings

### Example Configuration

```json
{
  "simulation": {
    "name": "my_simulation",
    "rounds": 20,
    "random_seed": 42,
    "result_path": "my_results"
  },
  "climate": {
    "stress_enabled": true,
    "shock_rules": [
      {
        "name": "commodity_shock",
        "probability": 0.15,
        "agent_types": ["commodity_producer"],
        "continents": ["Asia"],
        "stress_factor": 0.7,
        "duration": 1
      }
    ]
  },
  "agents": {
    "commodity_producer": {
      "count": 3,
      "initial_money": 50,
      "production": {
        "base_output_quantity": 1.0,
        "price": 1.0
      }
    }
  }
}
```

## Configuration Parameters

### Simulation Section

- `name`: Simulation name for output files
- `rounds`: Number of simulation rounds
- `random_seed`: Random seed for reproducibility
- `result_path`: Output directory path
- `trade_logging`: "on" or "off" for trade logging

### Climate Section

- `stress_enabled`: Enable/disable climate stress
- `acute_stress_probability`: Base probability for legacy climate stress
- `chronic_stress_factor`: Long-term degradation factor
- `geographical_effects`: Enable geographical climate effects
- `shock_rules`: Array of custom shock rules (see below)

### Climate Shock Rules

Each shock rule can specify:

- `name`: Unique identifier for the shock
- `description`: Human-readable description
- `probability`: Probability of occurrence each round (0.0-1.0)
- `agent_types`: Array of agent types to affect
  - `["commodity_producer"]` - Only commodity producers
  - `["commodity_producer", "intermediary_firm"]` - Multiple types
  - `["all"]` - All agent types
- `continents`: Array of continents to affect
  - `["Asia"]` - Only Asia
  - `["Asia", "Europe"]` - Multiple continents
  - `["all"]` - All continents
- `stress_factor`: Production multiplier (0.0-1.0, where 0.7 = 30% reduction)
- `duration`: Number of rounds the shock lasts

### Agent Configuration

Each agent type supports:

#### Basic Parameters
- `count`: Number of agents to create
- `initial_money`: Starting money amount
- `initial_inventory`: Starting goods inventory

#### Production Parameters
- `production.base_output_quantity`: Base production capacity
- `production.inputs`: Required inputs for production
- `production.output`: Name of good produced
- `production.price`: Price to sell goods

#### Climate Parameters
- `climate.base_vulnerability`: Base climate vulnerability
- `climate.vulnerability_variance`: Variation in vulnerability between agents

#### Geographic Distribution
- `geographical_distribution`: Array of continents where agents are located
  - `["Asia", "Europe"]` - Specific continents
  - `["all"]` - Distributed across all continents

#### Agent-Specific Parameters

**Households:**
- `labor.endowment`: Labor units per round
- `labor.wage`: Wage rate for labor
- `consumption.preference`: Preferred good to consume
- `consumption.budget_fraction`: Fraction of money to spend

## Example Scenarios

### 1. Asia-Focused Manufacturing Hub

Concentrates production in Asia with targeted climate risks:

```json
{
  "agents": {
    "commodity_producer": {
      "count": 5,
      "geographical_distribution": ["Asia", "Asia", "Asia", "Europe", "Africa"]
    }
  },
  "climate": {
    "shock_rules": [
      {
        "name": "asian_manufacturing_crisis",
        "probability": 0.20,
        "agent_types": ["commodity_producer", "intermediary_firm"],
        "continents": ["Asia"],
        "stress_factor": 0.5
      }
    ]
  }
}
```

### 2. High-Stress Resilience Test

Tests system resilience with frequent, severe shocks:

```json
{
  "climate": {
    "shock_rules": [
      {
        "name": "frequent_global_disruption",
        "probability": 0.30,
        "agent_types": ["all"],
        "continents": ["all"],
        "stress_factor": 0.6
      }
    ]
  }
}
```

### 3. Commodity-Only Shocks

Only affects commodity producers:

```json
{
  "climate": {
    "shock_rules": [
      {
        "name": "commodity_crisis",
        "probability": 0.15,
        "agent_types": ["commodity_producer"],
        "continents": ["all"],
        "stress_factor": 0.5
      }
    ]
  }
}
```

### 4. Regional Focus

Affects only specific regions:

```json
{
  "climate": {
    "shock_rules": [
      {
        "name": "americas_drought",
        "probability": 0.12,
        "agent_types": ["commodity_producer"],
        "continents": ["North America", "South America"],
        "stress_factor": 0.6
      }
    ]
  }
}
```

## Advanced Features

### Multiple Shock Rules

You can define multiple shock rules that operate independently:

```json
{
  "climate": {
    "shock_rules": [
      {
        "name": "global_commodity_shock",
        "probability": 0.10,
        "agent_types": ["commodity_producer"],
        "continents": ["all"],
        "stress_factor": 0.7
      },
      {
        "name": "asian_manufacturing_shock", 
        "probability": 0.08,
        "agent_types": ["intermediary_firm"],
        "continents": ["Asia"],
        "stress_factor": 0.6
      }
    ]
  }
}
```

### Variable Agent Distributions

Control exactly how many agents are in each location:

```json
{
  "agents": {
    "commodity_producer": {
      "count": 6,
      "geographical_distribution": [
        "Asia", "Asia", "Asia",
        "Europe", "Europe", 
        "Africa"
      ]
    }
  }
}
```

### Custom Production Networks

Modify the supply chain structure:

```json
{
  "agents": {
    "commodity_producer": {
      "production": {
        "base_output_quantity": 2.0,
        "price": 1.5
      }
    },
    "intermediary_firm": {
      "production": {
        "base_output_quantity": 1.8,
        "price": 3.0
      }
    }
  }
}
```

## Output and Analysis

### Generated Files

- **CSV files**: Economic data for each agent type
- **Visualizations**: Climate analysis charts and supply chain diagrams
- **Climate summary**: `climate_3_layer_summary.csv` with shock details
- **Animations**: Time-evolving GIF animations (if enabled)

### Configuration Validation

The system automatically validates:
- Required parameters are present
- Agent counts are positive
- Probabilities are between 0 and 1
- Referenced agent types exist
- Continent names are valid

### Error Handling

If configuration errors occur:
- Clear error messages indicate the problem
- Suggestions for fixing common issues
- Fallback to default values when possible

## Best Practices

1. **Start with default configuration** and modify incrementally
2. **Use descriptive names** for shock rules and simulations
3. **Test with short simulations** before running long scenarios
4. **Keep backups** of working configurations
5. **Document your modifications** in the `_description` field

## Troubleshooting

### Common Issues

**"Configuration file not found"**
- Ensure the file path is correct
- Check that the file exists in the expected location

**"Invalid JSON"**
- Validate JSON syntax using an online validator
- Check for missing commas, brackets, or quotes

**"Missing required parameter"**
- Review the error message for the specific missing parameter
- Compare with the example configurations

**"Agent type not found"**
- Ensure agent type names match exactly: `commodity_producer`, `intermediary_firm`, `final_goods_firm`, `household`

### Getting Help

1. Check the example configurations (`config_*.json`)
2. Review error messages carefully
3. Validate JSON syntax
4. Start with minimal modifications to working configurations 