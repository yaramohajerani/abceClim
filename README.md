*Note:* This is a fork of [abcEconomics](https://github.com/AB-CE/abce) ([docs](https://abce.readthedocs.io/)) that updates some of the deprecated functionality for new Python libraries, since abcEcon was archived in early 2024. In particular, the logging functionality of the original repository is no longer functional with updated libraries, which is replaced with a new logging system in this fork. More importantly, this repo builds on the original framework to focus on climate risk propagation in an economic network. **This is work in progress and is by no means finished, so you may often see temporary placeholder values for various parameters and experimental methodologies. Therefore, do not use this code for any real study or application (yet).** If you have any thoughts or would like to contribute, please [reach out](mailto:yara@pluripotent.tech). 

# Climate Economics Agent-Based Modeling based on abcEconomics

A reusable framework for adding geographical distribution, climate stress modeling, and comprehensive visualization capabilities to agent-based economic models built with abcEconomics.

## Overview

The Climate Framework provides a standardized way to:
- **Distribute agents geographically** across continents with different climate risks
- **Apply climate stress** (both acute events and chronic degradation) based on geography
- **Collect comprehensive data** about agent interactions and climate impacts
- **Generate rich visualizations** showing geographical networks, climate events, and economic impacts
- **Export data** for further analysis

## Key Features

### 🌍 Geographical Distribution
- Automatically assigns agents to continents based on configurable rules
- Different agent types can have different geographical preferences
- Climate vulnerability is adjusted based on continental climate risk

### 🌡️ Climate Stress Modeling
- **Acute stress**: Random climate events with continent-specific probabilities
- **Chronic stress**: Gradual productivity degradation over time
- Flexible application to any agent type with production capabilities

### 📊 Comprehensive Visualizations
- Geographical network showing agent locations and connections
- Production timelines by continent
- Climate event heatmaps
- Agent financial status analysis
- Supply chain flow visualization
- Economic impact analysis

### 📈 Data Collection & Export
- Automatic data collection during simulation
- Export to CSV for further analysis
- Flexible metrics collection

## Quick Start

### 1. Basic Integration

```python
from climate_framework import create_climate_framework

# Create your simulation and agents as usual
simulation_parameters = {
    'climate_stress_enabled': True,
    'acute_stress_probability': 0.15,
    'chronic_stress_factor': 0.96,
    'create_visualizations': True
}

# Create the framework
climate_framework = create_climate_framework(simulation_parameters)

# Organize your agents
agent_groups = {
    'firm': your_firms,
    'household': your_households
}

# Assign geographical locations
climate_framework.assign_geographical_locations(agent_groups)
```

### 2. Adding Climate Capabilities to Agents

Use the decorator to automatically add climate stress methods:

```python
from climate_framework import add_climate_capabilities

@add_climate_capabilities
class MyFirm(Agent, Firm):
    def init(self):
        self.current_output_quantity = 10.0  # This will be affected by climate
        # ... rest of your initialization
```

### 3. Running with Climate Stress

```python
for round_num in range(total_rounds):
    # Apply climate stress
    climate_events = climate_framework.apply_geographical_climate_stress(agent_groups)
    
    # Your economic simulation steps here
    firms.produce()
    firms.trade()
    
    # Collect data
    climate_framework.collect_round_data(round_num, agent_groups, climate_events)
```

### 4. Generate Visualizations

```python
# Create comprehensive visualizations
climate_framework.create_visualizations(
    agent_groups,
    model_name="My Climate Economic Model"
)

# Export data for analysis
climate_framework.export_data("my_model_data.csv")
```

## Configuration

### Simulation Parameters

```python
simulation_parameters = {
    'climate_stress_enabled': True,        # Enable/disable climate effects
    'acute_stress_probability': 0.15,      # Base probability of acute events
    'chronic_stress_factor': 0.96,         # Productivity reduction per round
    'geographical_effects': True,          # Enable continent-specific effects
    'create_visualizations': True,         # Generate visualizations
    'random_seed': 42                      # For reproducible results
}
```

### Geographical Distribution Rules

Customize how agents are distributed across continents:

```python
distribution_rules = {
    'commodity_producer': ['Asia', 'South America', 'Africa'],  # Resource-rich
    'tech_firm': ['North America', 'Europe', 'Asia'],          # Developed markets
    'manufacturer': ['Asia', 'Europe'],                        # Industrial
    'household': ['North America', 'Europe', 'Asia', 'South America', 'Africa']  # Global
}

climate_framework.assign_geographical_locations(agent_groups, distribution_rules)
```

## Continents and Climate Characteristics

The framework includes 5 continents with different climate risk profiles:

| Continent | Climate Risk | Description |
|-----------|--------------|-------------|
| Europe | 0.6 | Lower climate risk, stable conditions |
| North America | 0.8 | Moderate climate risk |
| South America | 1.0 | Baseline climate risk |
| Africa | 1.1 | Higher climate risk |
| Asia | 1.2 | Highest climate risk |

## Agent Requirements

### For Climate Stress Capabilities

Agents that should be affected by climate stress need:

```python
class MyAgent(Agent):
    def init(self):
        self.climate_vulnerability = 0.3        # How vulnerable to climate (0-1)
        self.current_output_quantity = 10.0     # Current production capacity
        self.base_output_quantity = 10.0        # Base production capacity
        self.chronic_stress_accumulated = 1.0   # Accumulated chronic stress
    
    def apply_acute_stress(self):
        # Method for handling acute climate events
        pass
    
    def apply_chronic_stress(self, stress_factor):
        # Method for handling gradual climate degradation
        pass
```

Or simply use the `@add_climate_capabilities` decorator!

## Examples

### 1. Climate 3-Layer Supply Chain Model

See `climate_3_layer/start.py` for a comprehensive example of a 3-layer supply chain model with:
- Commodity producers (high climate vulnerability)
- Intermediary firms (moderate vulnerability)
- Final goods firms (low vulnerability)
- Households (distributed globally)

### 2. Simple Climate Model

See `example_simple_climate_model.py` for a minimal example showing how to integrate the framework with any model.

## Visualization Outputs

The framework generates a comprehensive visualization dashboard with 6 panels:

1. **Geographical Network**: Shows agent locations and supply chain connections
2. **Production Timeline**: Production levels by continent over time
3. **Climate Events Map**: Heatmap of climate events across continents and time
4. **Agent Status**: Financial health of agents by continent
5. **Economic Flow**: Flow of goods through the economic system
6. **Impact Analysis**: Economic impact of climate events

## Data Export

The framework automatically exports simulation data including:
- Agent financial status by round
- Production levels by continent and agent type
- Climate event occurrence
- Agent vulnerability and stress factors

## Extension Points

### Custom Metrics

Add custom metrics to data collection:

```python
custom_metrics = {
    'total_unemployment': calculate_unemployment(households),
    'market_concentration': calculate_concentration(firms)
}

climate_framework.collect_round_data(round_num, agent_groups, climate_events, custom_metrics)
```

### Custom Visualizations

Extend the visualization framework by subclassing `ClimateFramework` and overriding visualization methods.

## Requirements

- abcEconomics
- matplotlib
- networkx
- numpy
- pandas
- seaborn

## Future Models

This framework is designed to be model-agnostic. You can easily create new climate economic models:

- **Financial sector models** with climate-sensitive banks
- **Agricultural models** with weather-dependent yields
- **Energy transition models** with renewable/fossil fuel firms
- **Urban planning models** with climate adaptation
- **Trade models** with climate-affected supply chains

Each model just needs to organize its agents into groups and call the framework methods!

## License

This framework is designed to work with the abcEconomics library and follows the same licensing structure. 
