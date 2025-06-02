# Simulation Logger for abcEconomics

A generic, configurable logging system for abcEconomics simulations that captures and formats agent activity in structured log files.

## Overview

The `SimulationLogger` provides a clean, structured way to log agent activities, market interactions, and special events (like climate shocks) during abcEconomics simulations. Instead of verbose console output, it creates well-formatted log files with customizable keyword-based categorization.

## Basic Usage

### Quick Start with Factory Function

```python
from abcEconomics.logger import create_simulation_logger, replace_agent_prints_with_logging

# Create logger from configuration
sim_logger = create_simulation_logger(
    config=your_config_dict,
    simulation_path=your_simulation_path,
    simulation_name="Your Simulation Name"
)

if sim_logger:
    # Replace print statements with structured logging
    replace_agent_prints_with_logging(sim_logger)
```

### Manual Creation with Custom Keywords

```python
from abcEconomics.logger import SimulationLogger, replace_agent_prints_with_logging

# Define keywords specific to your simulation
agent_keywords = [
    'Bank', 'Customer', 'Trader', 'Market', 'Portfolio',
    'buy', 'sell', 'loan', 'deposit', 'transaction'
]

event_keywords = [
    'Crisis', 'Bubble', 'Crash', 'Regulation', 'Policy',
    'shock', 'intervention', 'bailout'
]

# Create logger
sim_logger = SimulationLogger(
    log_file_path="financial_simulation_log.txt",
    console_level="WARNING",  # Only show warnings/errors on console
    agent_keywords=agent_keywords,
    climate_keywords=event_keywords,  # Can be any type of event
    simulation_name="Financial Market Simulation"
)

# Replace print statements
replace_agent_prints_with_logging(sim_logger)
```

## Configuration

Add logging configuration to your JSON config file:

```json
{
  "logging": {
    "agent_activity_logging": true,
    "console_level": "WARNING",
    "log_filename": "my_simulation_log.txt",
    "agent_keywords": [
      "Agent", "Market", "Firm", "buy", "sell", "trade"
    ],
    "climate_keywords": [
      "Shock", "Crisis", "Event", "Disruption"
    ]
  }
}
```

### Configuration Options

- `agent_activity_logging`: Enable/disable logging (boolean)
- `console_level`: Console output level ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "OFF")
- `log_filename`: Name of the log file
- `agent_keywords`: List of keywords that identify agent activities
- `climate_keywords`: List of keywords that identify special events

## Keyword-Based Categorization

The logger automatically categorizes messages based on keywords:

### Agent Activities
Messages containing agent keywords are logged as regular agent actions:
```
00:15:30 | INFO     |     Bank 1: Processed loan application for $50,000
00:15:31 | INFO     |     Customer 5: Withdrew $200 from account
```

### Special Events  
Messages containing event keywords are logged as special events:
```
00:16:45 | WARNING  | 🔔 EVENT: Market crash detected! All trading halted
00:16:46 | WARNING  | 🔔 EVENT: Central bank intervention initiated
```

## Integration in Simulation Loop

```python
def main():
    # Set up logger
    sim_logger = create_simulation_logger(config, simulation_path, "My Simulation")
    
    if sim_logger:
        replace_agent_prints_with_logging(sim_logger)
    
    # Run simulation
    for round_num in range(num_rounds):
        if sim_logger:
            sim_logger.set_round(round_num)
        
        # Your simulation phases
        if sim_logger:
            sim_logger.set_phase("Market Opening")
        
        # Agent activities...
        
        if sim_logger:
            sim_logger.set_phase("Settlement")
        
        # More agent activities...
    
    # End simulation
    if sim_logger:
        sim_logger.log_simulation_end({
            "Total rounds": num_rounds,
            "Total transactions": transaction_count
        })
```

## Manual Logging Methods

### Basic Methods
```python
# Log simulation phases
sim_logger.set_round(5)
sim_logger.set_phase("Market Making")

# Log agent actions
sim_logger.log_agent_action("Agent 1: Placed buy order for 100 shares")

# Log special events
sim_logger.log_event("System maintenance started", "🔧")
sim_logger.log_climate_event("Hurricane affecting East Coast agents")  # Shortcut

# Log phase summaries
sim_logger.log_phase_summary("Market clearing completed: 1,250 trades")
```

### End Simulation
```python
summary_stats = {
    "Total rounds": 100,
    "Agents active": 50,
    "Average trades per round": 125.5,
    "System uptime": "99.8%"
}
sim_logger.log_simulation_end(summary_stats)
```

## Log File Format

The logger creates structured log files with:

```
================================================================================
🚀 YOUR SIMULATION NAME LOG
================================================================================
📅 Started: 2025-06-01 10:30:15
📄 Log file: your_simulation_log.txt
🔍 Agent keywords: Agent, Market, Firm, buy, sell...
🌪️ Event keywords: Shock, Crisis, Event...
================================================================================

🔄 ROUND 0
----------------------------------------

📍 Market Opening
    Agent 1: Checking portfolio balance: $10,000
    Agent 2: Submitting buy order: 50 shares at $25.00
    ✅ Market opening completed: 15 agents active

📍 Trading Session
🔔 EVENT: High volatility detected in tech sector
    Agent 3: Order filled: bought 30 shares at $24.95
    Agent 1: Stop-loss triggered: sold 100 shares
    ✅ Trading session completed: 245 transactions

🔄 ROUND 1
----------------------------------------
...

================================================================================
🏁 SIMULATION COMPLETED
📊 Total rounds: 100
📊 Agents active: 50
📊 Average trades per round: 125.5
================================================================================
```

## Benefits

1. **Clean Console**: Reduces verbose console output during simulation runs
2. **Structured Logs**: Well-formatted, searchable log files with timestamps
3. **Flexible Keywords**: Easily customizable for different simulation types
4. **Phase Organization**: Clear separation of simulation phases and rounds
5. **Event Categorization**: Automatic categorization of agent vs. event messages
6. **Reusable**: Generic design works with any abcEconomics simulation

## Examples by Domain

### Financial Markets
```python
agent_keywords = ['Bank', 'Trader', 'Portfolio', 'buy', 'sell', 'loan', 'deposit']
event_keywords = ['Crisis', 'Bubble', 'Regulation', 'Bailout', 'intervention']
```

### Supply Chain
```python
agent_keywords = ['Supplier', 'Manufacturer', 'Retailer', 'order', 'delivery', 'inventory']
event_keywords = ['Disruption', 'Shortage', 'Strike', 'Transport', 'delay']
```

### Healthcare System
```python
agent_keywords = ['Patient', 'Doctor', 'Hospital', 'treatment', 'diagnosis', 'appointment']
event_keywords = ['Epidemic', 'Emergency', 'Shortage', 'Outbreak', 'quarantine']
```

### Energy Markets
```python
agent_keywords = ['Generator', 'Consumer', 'Grid', 'power', 'demand', 'supply']
event_keywords = ['Blackout', 'Peak', 'Renewable', 'Outage', 'maintenance']
```

The logger automatically adapts to your simulation's vocabulary while providing consistent, professional log formatting. 