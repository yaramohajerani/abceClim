#!/usr/bin/env python3
"""
Test script for demonstrating the flexible configuration system.

This script runs different scenarios and compares results to show how
configuration changes affect simulation outcomes.
"""

import os
import sys
import json
from config_loader import load_model_config
from start import main


def run_configuration_test(config_file, description):
    """Run a single configuration and collect summary statistics."""
    print(f"\n{'='*60}")
    print(f"Testing Configuration: {description}")
    print(f"Config file: {config_file}")
    print(f"{'='*60}")
    
    try:
        # Run the simulation
        climate_framework = main(config_file)
        
        # Collect summary statistics
        total_events = sum(len(events) for events in climate_framework.climate_events_history)
        rounds = len(climate_framework.climate_events_history)
        
        # Get agent counts from geographical assignments
        agent_counts = {}
        for agent_type, assignments in climate_framework.geographical_assignments.items():
            agent_counts[agent_type] = len(assignments)
        
        results = {
            'config_file': config_file,
            'description': description,
            'rounds': rounds,
            'total_climate_events': total_events,
            'events_per_round': total_events / rounds if rounds > 0 else 0,
            'agent_counts': agent_counts,
            'unique_event_types': len(set(
                event.get('rule_name', 'legacy_event') 
                for events in climate_framework.climate_events_history 
                for event in (events.values() if isinstance(events, dict) else [])
                if isinstance(event, dict)
            ))
        }
        
        print(f"\n📊 Results Summary:")
        print(f"  Rounds completed: {results['rounds']}")
        print(f"  Total climate events: {results['total_climate_events']}")
        print(f"  Events per round: {results['events_per_round']:.2f}")
        print(f"  Agent distribution: {results['agent_counts']}")
        print(f"  Event types observed: {results['unique_event_types']}")
        
        return results
        
    except Exception as e:
        print(f"❌ Error running configuration {config_file}: {e}")
        import traceback
        traceback.print_exc()
        return None


def compare_configurations():
    """Compare results from different configurations."""
    
    configurations = [
        ("model_config.json", "Default Configuration"),
        ("config_asia_focus.json", "Asia-Focused Manufacturing"),
        ("config_stress_test.json", "High-Stress Resilience Test")
    ]
    
    results = []
    
    print("🌍 Climate 3-Layer Model Configuration Comparison")
    print("=" * 60)
    print("Testing multiple configurations to demonstrate flexibility...")
    
    # Run each configuration
    for config_file, description in configurations:
        if os.path.exists(config_file):
            result = run_configuration_test(config_file, description)
            if result:
                results.append(result)
        else:
            print(f"⚠️ Warning: Configuration file {config_file} not found, skipping...")
    
    # Create comparison table
    if results:
        print(f"\n{'='*80}")
        print("CONFIGURATION COMPARISON SUMMARY")
        print(f"{'='*80}")
        
        # Header
        print(f"{'Configuration':<25} {'Rounds':<8} {'Events':<8} {'Evt/Rnd':<8} {'Agents':<15}")
        print("-" * 80)
        
        # Results
        for result in results:
            config_name = result['config_file'].replace('.json', '').replace('config_', '')
            total_agents = sum(result['agent_counts'].values())
            print(f"{config_name:<25} {result['rounds']:<8} {result['total_climate_events']:<8} "
                  f"{result['events_per_round']:<8.2f} {total_agents:<15}")
        
        print("\n📈 Analysis:")
        
        # Find configuration with most events
        most_events = max(results, key=lambda x: x['total_climate_events'])
        print(f"  Most climate events: {most_events['description']} ({most_events['total_climate_events']} events)")
        
        # Find configuration with most agents
        most_agents = max(results, key=lambda x: sum(x['agent_counts'].values()))
        total_agents = sum(most_agents['agent_counts'].values())
        print(f"  Most agents: {most_agents['description']} ({total_agents} agents)")
        
        # Event frequency comparison
        highest_frequency = max(results, key=lambda x: x['events_per_round'])
        print(f"  Highest event frequency: {highest_frequency['description']} ({highest_frequency['events_per_round']:.2f} events/round)")
        
        print(f"\n✅ Configuration system successfully tested with {len(results)} scenarios!")
    
    else:
        print("❌ No configurations could be tested successfully.")


def validate_all_configurations():
    """Validate all configuration files without running simulations."""
    print("\n🔍 Validating Configuration Files...")
    
    config_files = [f for f in os.listdir('.') if f.endswith('.json') and 'config' in f.lower()]
    
    valid_configs = 0
    
    for config_file in config_files:
        try:
            print(f"\nValidating {config_file}...")
            config_loader = load_model_config(config_file)
            
            # Basic validation checks
            sim_params = config_loader.get_simulation_parameters()
            agent_configs = config_loader.agent_configs
            
            print(f"  ✅ {config_file}: Valid")
            print(f"     Rounds: {sim_params['rounds']}")
            print(f"     Climate rules: {len(sim_params.get('shock_rules', []))}")
            print(f"     Agent types: {len(agent_configs)}")
            
            valid_configs += 1
            
        except Exception as e:
            print(f"  ❌ {config_file}: Error - {e}")
    
    print(f"\n📊 Validation Summary: {valid_configs}/{len(config_files)} configuration files are valid")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Climate 3-Layer Model configurations")
    parser.add_argument("--validate-only", action="store_true", 
                       help="Only validate configurations without running simulations")
    parser.add_argument("--config", type=str, 
                       help="Test a specific configuration file")
    
    args = parser.parse_args()
    
    if args.validate_only:
        validate_all_configurations()
    elif args.config:
        if os.path.exists(args.config):
            run_configuration_test(args.config, f"Single test: {args.config}")
        else:
            print(f"❌ Configuration file not found: {args.config}")
    else:
        # Run full comparison
        compare_configurations() 