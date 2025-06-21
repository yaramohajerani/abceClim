# Generalized Network Framework for Heterogeneous Agents

A flexible framework for creating complex economic networks with arbitrary heterogeneous agents, spatial distribution, and climate stress modeling.

## Overview

This framework generalizes the climate_3layer model to support:
- **Arbitrary agent types** with configurable production, consumption, and trading behaviors
- **Complex randomized networks** with multiple connection types (random, supply chain, small world, scale-free)
- **Spatial distribution** across continents with geographical climate effects
- **Heterogeneous agents** with individual characteristics affecting climate vulnerability and behavior
- **Chronic and acute climate shocks** with configurable probabilities and effects
- **Comprehensive data collection** and visualization

## Key Components

### 1. GeneralizedAgent (`generalized_agent.py`)
A flexible agent class that can be configured for different economic roles:
- **Production**: Configurable inputs, outputs, efficiency, and overhead costs
- **Consumption**: Preferences, consumption fractions, and survival requirements
- **Trading**: Network-based trading with connected agents
- **Labor**: Supply and demand for labor services
- **Climate stress**: Vulnerability to productivity and overhead shocks
- **Performance tracking**: Wealth, production, consumption, and trade metrics

### 2. GeneralizedNetworkFramework (`generalized_network_framework.py`)
Core framework managing:
- **Network generation**: Multiple network topologies (random, supply chain, small world, scale-free)
- **Geographical distribution**: Agent assignment to continents
- **Heterogeneity management**: Individual agent characteristics and climate vulnerability
- **Climate stress application**: Chronic and acute climate events
- **Data export**: Network structure, climate events, and heterogeneity data

### 3. GeneralizedSimulationRunner (`generalized_simulation.py`)
Complete simulation runner with:
- **Configuration loading**: JSON-based parameter specification
- **Agent creation**: Dynamic agent generation from configuration
- **Network setup**: Connection establishment between agents
- **Simulation execution**: Multi-phase simulation with climate stress
- **Result export**: CSV files and visualizations

## Quick Start

### 1. Install Dependencies
```bash
pip install networkx pandas matplotlib numpy
```

### 2. Create Configuration File
Create a JSON configuration file (see `sample_generalized_config.json` for example):

```json
{
  "simulation": {
    "name": "my_network_simulation",
    "random_seed": 42,
    "rounds": 30,
    "result_path": "my_results"
  },
  "network": {
    "connection_type": "random",
    "connection_probability": 0.4
  },
  "climate": {
    "stress_enabled": true,
    "heterogeneity_enabled": true,
    "shock_rules": [
      {
        "name": "extreme_weather",
        "probability": 0.1,
        "agent_types": ["producer"],
        "continents": ["Africa", "Asia"],
        "productivity_stress_factor": 0.7
      }
    ]
  },
  "agents": {
    "producer": {
      "count": 5,
      "initial_money": 10.0,
      "production": {
        "base_output_quantity": 1.0,
        "inputs": {"labor": 0.5},
        "outputs": ["good"]
      }
    }
  }
}
```

### 3. Run Simulation
```python
from generalized_simulation import GeneralizedSimulationRunner

# Create and run simulation
runner = GeneralizedSimulationRunner("my_config.json")
results = runner.run_complete_simulation(rounds=30)
```

Or from command line:
```bash
python generalized_simulation.py my_config.json --rounds 30
```

## Configuration Options

### Simulation Parameters
- `name`: Simulation name
- `random_seed`: Random seed for reproducibility
- `rounds`: Number of simulation rounds
- `result_path`: Output directory

### Network Configuration
- `connection_type`: Network topology
  - `"random"`: Random connections with probability
  - `"supply_chain"`: Connections based on input/output relationships
  - `"small_world"`: Small-world network with rewiring
  - `"scale_free"`: Scale-free network with preferential attachment
- `connection_probability`: Probability of connections (for random networks)
- `max_connections_per_agent`: Maximum connections per agent

### Climate Configuration
- `stress_enabled`: Enable climate stress effects
- `heterogeneity_enabled`: Enable agent heterogeneity
- `chronic_rules`: List of chronic climate stress rules
- `shock_rules`: List of acute climate shock rules

Each climate rule specifies:
- `name`: Rule identifier
- `probability`: Probability of occurrence (for shocks)
- `agent_types`: Target agent types
- `continents`: Target geographical regions
- `productivity_stress_factor`: Multiplier for production capacity
- `overhead_stress_factor`: Multiplier for overhead costs

### Agent Configuration
Each agent type specifies:
- `count`: Number of agents of this type
- `initial_money`: Starting money
- `initial_inventory`: Starting inventory
- `production`: Production function parameters
- `consumption`: Consumption preferences
- `labor`: Labor supply/demand parameters
- `geographical_distribution`: Target continents
- `heterogeneity`: Agent-specific heterogeneity parameters

### Heterogeneity Configuration
- `climate_vulnerability_productivity`: Climate vulnerability by agent type and continent
- `climate_vulnerability_overhead`: Overhead vulnerability by agent type and continent
- `production_efficiency_base/variation`: Production efficiency parameters
- `overhead_efficiency_base/variation`: Overhead efficiency parameters
- `risk_tolerance_base/variation`: Risk tolerance parameters
- `debt_willingness_base/variation`: Debt willingness parameters
- `consumption_preference_base/variation`: Consumption preference parameters
- `network_connectivity_base/variation`: Network connectivity parameters
- `trade_preference_base/variation`: Trading preference parameters
- `geographic_adaptation_*`: Adaptation factors for different climate types

## Network Types

### Random Network
- Agents connect randomly with specified probability
- Good for exploring general network effects
- Configurable connection probability and maximum connections

### Supply Chain Network
- Connections based on input/output relationships
- Agents connect if they produce what others need
- Realistic for economic supply chains

### Small World Network
- Starts with regular ring lattice
- Edges rewired with specified probability
- Combines local clustering with short path lengths

### Scale-Free Network
- Uses preferential attachment
- Few highly connected hubs, many peripheral nodes
- Realistic for many real-world networks

## Climate Stress Modeling

### Chronic Stress
- Long-term climate effects applied every round
- Gradual changes in productivity and overhead
- Accumulates over time

### Acute Shocks
- Random climate events with specified probabilities
- Immediate effects on productivity and overhead
- Reset each round

### Heterogeneity Effects
- Individual agents have different climate vulnerabilities
- Based on agent type, geographical location, and random factors
- Affects both productivity and overhead stress

## Output Files

The framework generates several output files:

### Data Files
- `simulation_results.csv`: Round-by-round aggregate statistics
- `agent_performance.csv`: Individual agent performance summaries
- `network_summary.csv`: Network structure and connections
- `network_summary_heterogeneity.csv`: Agent heterogeneity characteristics
- `climate_events.csv`: Climate events and their effects

### Visualizations
- `simulation_results.png`: Time series plots of key metrics
- `network_structure.png`: Network visualization with agent types

## Example Use Cases

### 1. Supply Chain Analysis
```json
{
  "network": {"connection_type": "supply_chain"},
  "agents": {
    "raw_material_producer": {...},
    "manufacturer": {...},
    "distributor": {...},
    "retailer": {...}
  }
}
```

### 2. Regional Climate Impact Study
```json
{
  "climate": {
    "shock_rules": [
      {
        "name": "hurricane",
        "probability": 0.05,
        "agent_types": ["all"],
        "continents": ["North America"],
        "productivity_stress_factor": 0.5
      }
    ]
  }
}
```

### 3. Heterogeneous Agent Behavior
```json
{
  "heterogeneity": {
    "risk_tolerance_variation": 0.5,
    "debt_willingness_variation": 0.6,
    "climate_vulnerability_productivity": {
      "small_firm": 1.5,
      "large_firm": 0.8
    }
  }
}
```

## Extending the Framework

### Adding New Agent Types
1. Define agent configuration in JSON
2. The `GeneralizedAgent` class handles all agent behaviors
3. No code changes needed for new agent types

### Adding New Network Types
1. Extend `NetworkGenerator` class
2. Add new connection generation method
3. Update configuration schema

### Adding New Climate Effects
1. Extend climate rule configuration
2. Modify `GeneralizedNetworkFramework.apply_climate_stress()`
3. Add new stress application methods

### Custom Agent Behaviors
1. Inherit from `GeneralizedAgent`
2. Override specific methods (production, consumption, trading)
3. Use custom agent class in simulation

## Performance Considerations

- **Large networks**: Use sparse network representations for efficiency
- **Many agents**: Consider parallel processing for agent updates
- **Long simulations**: Use incremental data collection to reduce memory usage
- **Complex networks**: Pre-compute network structure for better performance

## Troubleshooting

### Common Issues
1. **Import errors**: Ensure all dependencies are installed
2. **Configuration errors**: Validate JSON syntax and required fields
3. **Network generation**: Check connection parameters for reasonable values
4. **Climate effects**: Verify agent types and continents match configuration

### Debugging
- Enable detailed logging in configuration
- Check agent performance summaries for unexpected behavior
- Validate network structure with visualization
- Monitor climate event application

## Contributing

The framework is designed to be extensible. Key areas for contribution:
- Additional network topologies
- New climate stress models
- Enhanced agent behaviors
- Improved visualization options
- Performance optimizations