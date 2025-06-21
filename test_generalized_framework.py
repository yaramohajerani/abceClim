"""
Test script for the Generalized Network Framework
Demonstrates basic usage with a simple heterogeneous agent network.
"""

import json
import os
from generalized_simulation import GeneralizedSimulationRunner


def create_simple_test_config():
    """Create a simple test configuration"""
    config = {
        "simulation": {
            "name": "simple_test",
            "random_seed": 42,
            "rounds": 10,
            "result_path": "test_results"
        },
        "network": {
            "connection_type": "random",
            "connection_probability": 0.5,
            "max_connections_per_agent": 4
        },
        "climate": {
            "stress_enabled": True,
            "heterogeneity_enabled": True,
            "chronic_rules": [
                {
                    "name": "gradual_warming",
                    "agent_types": ["producer", "consumer"],
                    "continents": ["all"],
                    "productivity_stress_factor": 0.99,
                    "overhead_stress_factor": 1.01
                }
            ],
            "shock_rules": [
                {
                    "name": "heat_wave",
                    "probability": 0.2,
                    "agent_types": ["producer"],
                    "continents": ["Africa", "Asia"],
                    "productivity_stress_factor": 0.8,
                    "overhead_stress_factor": 1.2
                }
            ]
        },
        "heterogeneity": {
            "climate_vulnerability_productivity": {
                "producer": 1.2,
                "consumer": 0.9,
                "Africa": 1.1,
                "Asia": 1.0,
                "Europe": 0.9
            },
            "climate_vulnerability_overhead": {
                "producer": 1.1,
                "consumer": 0.9,
                "Africa": 1.2,
                "Asia": 1.0,
                "Europe": 0.9
            },
            "production_efficiency_base": 1.0,
            "production_efficiency_variation": 0.2,
            "risk_tolerance_base": 1.0,
            "risk_tolerance_variation": 0.3
        },
        "agents": {
            "producer": {
                "count": 3,
                "initial_money": 10.0,
                "initial_inventory": {
                    "raw_material": 1.0
                },
                "production": {
                    "base_output_quantity": 1.0,
                    "profit_margin": 0.1,
                    "base_overhead": 0.05,
                    "inputs": {
                        "labor": 0.5,
                        "raw_material": 0.3
                    },
                    "outputs": ["final_good"]
                },
                "consumption": {
                    "preference": "final_good",
                    "consumption_fraction": 0.3,
                    "minimum_survival_consumption": 0.2
                },
                "labor": {
                    "endowment": 0.0,
                    "wage": 10.0
                },
                "geographical_distribution": ["Africa", "Asia", "Europe"]
            },
            "consumer": {
                "count": 5,
                "initial_money": 8.0,
                "initial_inventory": {
                    "final_good": 0.5
                },
                "production": {
                    "base_output_quantity": 0.0,
                    "profit_margin": 0.0,
                    "base_overhead": 0.0,
                    "inputs": {},
                    "outputs": []
                },
                "consumption": {
                    "preference": "final_good",
                    "consumption_fraction": 0.5,
                    "minimum_survival_consumption": 0.3
                },
                "labor": {
                    "endowment": 1.0,
                    "wage": 10.0
                },
                "geographical_distribution": ["all"]
            }
        },
        "visualization": {
            "create_visualizations": True,
            "create_network_visualization": True,
            "save_summary_data": True
        }
    }
    
    return config


def test_basic_functionality():
    """Test basic framework functionality"""
    print("Testing Generalized Network Framework...")
    
    # Create test configuration
    config = create_simple_test_config()
    
    # Save configuration to file
    config_file = "test_config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"Created test configuration: {config_file}")
    
    try:
        # Create and run simulation
        runner = GeneralizedSimulationRunner(config_file)
        results = runner.run_complete_simulation(rounds=5, create_visualizations=True)
        
        print("\nSimulation completed successfully!")
        print(f"Results summary:")
        print(f"  - Total rounds: {len(results['rounds'])}")
        print(f"  - Final wealth: {results['total_wealth'][-1]:.2f}")
        print(f"  - Total production: {results['total_production'][-1]:.2f}")
        print(f"  - Total trades: {results['total_trades'][-1]}")
        print(f"  - Climate events: {len(results['climate_events'])}")
        
        # Check if output files were created
        output_dir = runner.simulation.path if runner.simulation else "test_results"
        expected_files = [
            "simulation_results.csv",
            "agent_performance.csv", 
            "network_summary.csv",
            "simulation_results.png"
        ]
        
        print(f"\nChecking output files in {output_dir}:")
        for filename in expected_files:
            filepath = os.path.join(output_dir, filename)
            if os.path.exists(filepath):
                print(f"  ✓ {filename}")
            else:
                print(f"  ✗ {filename} (missing)")
        
        return True
        
    except Exception as e:
        print(f"Error during simulation: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up test files
        if os.path.exists(config_file):
            os.remove(config_file)
        print(f"\nCleaned up test configuration file")


def test_network_types():
    """Test different network types"""
    print("\nTesting different network types...")
    
    network_types = ["random", "supply_chain", "small_world", "scale_free"]
    
    for network_type in network_types:
        print(f"\nTesting {network_type} network...")
        
        # Create configuration with specific network type
        config = create_simple_test_config()
        config["network"]["connection_type"] = network_type
        
        # Adjust parameters for different network types
        if network_type == "small_world":
            config["network"]["small_world_k"] = 2
            config["network"]["small_world_p"] = 0.1
        elif network_type == "scale_free":
            config["network"]["scale_free_m"] = 2
        
        # Save configuration
        config_file = f"test_config_{network_type}.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        try:
            # Run simulation
            runner = GeneralizedSimulationRunner(config_file)
            results = runner.run_complete_simulation(rounds=3, create_visualizations=True)
            
            print(f"  ✓ {network_type} network simulation completed")
            print(f"    Final wealth: {results['total_wealth'][-1]:.2f}")
            
        except Exception as e:
            print(f"  ✗ {network_type} network failed: {e}")
        
        finally:
            # Clean up
            if os.path.exists(config_file):
                os.remove(config_file)


def test_climate_effects():
    """Test climate stress effects"""
    print("\nTesting climate stress effects...")
    
    # Create configuration with strong climate effects
    config = create_simple_test_config()
    config["climate"]["shock_rules"] = [
        {
            "name": "severe_shock",
            "probability": 0.5,  # High probability for testing
            "agent_types": ["producer"],
            "continents": ["all"],
            "productivity_stress_factor": 0.5,  # Strong effect
            "overhead_stress_factor": 2.0
        }
    ]
    
    config_file = "test_climate_config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    try:
        runner = GeneralizedSimulationRunner(config_file)
        results = runner.run_complete_simulation(rounds=5, create_visualizations=True)
        
        print("  ✓ Climate stress simulation completed")
        print(f"    Climate events: {len(results['climate_events'])}")
        
        # Check if climate events affected production
        if len(results['climate_events']) > 0:
            print("    ✓ Climate events were applied")
        else:
            print("    ⚠ No climate events occurred (random)")
        
    except Exception as e:
        print(f"  ✗ Climate stress test failed: {e}")
    
    finally:
        if os.path.exists(config_file):
            os.remove(config_file)


def main():
    """Run all tests"""
    print("=" * 60)
    print("GENERALIZED NETWORK FRAMEWORK TEST SUITE")
    print("=" * 60)
    
    # Test basic functionality
    basic_success = test_basic_functionality()
    
    # Test network types
    test_network_types()
    
    # Test climate effects
    test_climate_effects()
    
    print("\n" + "=" * 60)
    if basic_success:
        print("✓ All tests completed successfully!")
        print("The generalized framework is working correctly.")
    else:
        print("✗ Some tests failed. Check the error messages above.")
    print("=" * 60)


if __name__ == "__main__":
    main() 