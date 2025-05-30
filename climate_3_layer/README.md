# Climate 3-Layer Economic Model

This is a closed-world 3-layer supply-chain economic model built with abcEconomics that examines the macroeconomic effects of climate stress on different layers of production.

## Model Structure

### Supply Chain Layers

1. **Commodity Producers** (Layer 1)
   - Use labor to produce raw commodities
   - Most vulnerable to climate stress (vulnerability: 0.3-0.5)
   - Supply intermediary firms

2. **Intermediary Firms** (Layer 2)
   - Use labor and commodities to produce intermediate goods
   - Moderate climate vulnerability (vulnerability: 0.1-0.15)
   - Supply final goods firms

3. **Final Goods Firms** (Layer 3)
   - Use labor and intermediate goods to produce final goods
   - Least vulnerable to climate stress (vulnerability: 0.05-0.09)
   - Supply households

4. **Households**
   - Provide labor to all firm layers
   - Consume final goods
   - Generate utility from consumption
   - Not directly affected by climate stress

## Climate Stress Features

### Acute Climate Stress
- Random events with configurable probability (default: 10% per round)
- Causes temporary productivity shocks to firms
- Impact varies by firm type and individual vulnerability
- Affects current round production only

### Chronic Climate Stress
- Permanent, cumulative productivity degradation
- Applied gradually over time (default: 5% reduction per round)
- Affects long-term productive capacity
- Accumulates multiplicatively

## Configuration Parameters

```python
simulation_parameters = {
    'name': 'climate_3_layer',
    'rounds': 20,                        # Number of simulation rounds
    'climate_stress_enabled': True,      # Enable/disable climate effects
    'acute_stress_probability': 0.1,     # Probability of acute events per round
    'chronic_stress_factor': 0.95        # Chronic degradation factor per round
}
```

## Agent Populations

- **3 Commodity Producers**: Primary sector with high climate vulnerability
- **2 Intermediary Firms**: Secondary processing with moderate vulnerability  
- **2 Final Goods Firms**: Tertiary sector with low vulnerability
- **4 Households**: Diverse employment across all firm layers

## Key Features

### Differentiated Climate Vulnerability
- Each agent type has different base vulnerability levels
- Individual agents within types have varying vulnerability
- Creates realistic heterogeneous climate impacts

### Multi-Layer Labor Market
- Households work across different firm layers
- Creates employment dependencies and wage relationships
- Enables study of labor market effects from climate stress

### Supply Chain Dependencies
- Clear material flow: commodities → intermediate goods → final goods
- Bottlenecks in earlier layers affect downstream production
- Climate impacts propagate through the supply chain

### Economic Tracking
- Production levels across all layers
- Employment and wage dynamics
- Household utility and consumption patterns
- Climate event occurrence and impacts

## Running the Model

```bash
cd climate_3_layer
python start.py
```

## Output and Analysis

The model generates:
- Round-by-round production data for each firm type
- Household utility and consumption tracking
- Climate event logs and impact measurements
- Agent inventory and financial position data

Results are automatically saved to the `result/` directory for post-simulation analysis.

## Model Extensions

The framework supports various extensions:
- Additional supply chain layers
- More sophisticated climate impact models
- Dynamic pricing mechanisms
- Government intervention policies
- Adaptive agent behaviors

## File Structure

```
climate_3_layer/
├── start.py                 # Main simulation runner
├── commodity_producer.py    # Layer 1: Raw commodity production
├── intermediary_firm.py     # Layer 2: Intermediate goods processing  
├── final_goods_firm.py      # Layer 3: Final goods manufacturing
├── household.py             # Consumer and labor supplier agents
├── description.md           # Model description
└── README.md               # This documentation
``` 