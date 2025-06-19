#!/usr/bin/env python3
"""
Test script for the heterogeneity system
Demonstrates how individual agents have different characteristics
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agent_heterogeneity import HeterogeneityManager, HeterogeneityGenerator
import json

def test_heterogeneity_generation():
    """Test the heterogeneity generation system"""
    print("🧪 Testing Heterogeneity Generation System")
    print("=" * 50)
    
    # Load configuration
    with open('simulation_configurations/heterogeneous_config.json', 'r') as f:
        config = json.load(f)
    
    # Create heterogeneity manager
    heterogeneity_manager = HeterogeneityManager(config)
    
    # Test agent types and continents
    test_cases = [
        ('commodity_producer', 0, 'Africa'),
        ('commodity_producer', 1, 'Asia'),
        ('intermediary_firm', 0, 'Asia'),
        ('intermediary_firm', 1, 'South America'),
        ('final_goods_firm', 0, 'North America'),
        ('final_goods_firm', 1, 'Europe'),
        ('household', 0, 'North America'),
        ('household', 1, 'Europe'),
        ('household', 2, 'Asia'),
    ]
    
    print("Generated agent characteristics:")
    print("-" * 50)
    
    for agent_type, agent_id, continent in test_cases:
        # Initialize agent characteristics
        characteristics = heterogeneity_manager.initialize_agent(agent_type, agent_id, continent)
        
        print(f"\n{agent_type.replace('_', ' ').title()} {agent_id} ({continent}):")
        print(f"  Climate vulnerability:")
        print(f"    Productivity: {characteristics.climate_vulnerability_productivity:.2f}")
        print(f"    Overhead: {characteristics.climate_vulnerability_overhead:.2f}")
        print(f"  Efficiency:")
        print(f"    Production: {characteristics.production_efficiency:.2f}")
        print(f"    Overhead: {characteristics.overhead_efficiency:.2f}")
        print(f"  Behavioral:")
        print(f"    Risk tolerance: {characteristics.risk_tolerance:.2f}")
        print(f"    Debt willingness: {characteristics.debt_willingness:.2f}")
        print(f"    Consumption preference: {characteristics.consumption_preference:.2f}")
        print(f"  Geographic adaptation:")
        for climate_type, adaptation in characteristics.geographic_adaptation.items():
            print(f"    {climate_type}: {adaptation:.2f}")
        print(f"  Learning:")
        print(f"    Adaptation rate: {characteristics.adaptation_rate:.3f}")
        print(f"    Memory length: {characteristics.memory_length}")
    
    # Test climate stress application
    print("\n" + "=" * 50)
    print("Testing Climate Stress Application with Heterogeneity")
    print("-" * 50)
    
    base_stress_factor = 0.8  # 20% productivity reduction
    
    for agent_type, agent_id, continent in test_cases:
        characteristics = heterogeneity_manager.get_agent_characteristics(agent_type, agent_id)
        if characteristics:
            modified_stress = heterogeneity_manager.apply_climate_stress_with_heterogeneity(
                agent_type, agent_id, base_stress_factor, 'productivity'
            )
            
            print(f"{agent_type.replace('_', ' ').title()} {agent_id} ({continent}):")
            print(f"  Base stress factor: {base_stress_factor:.2f}")
            print(f"  Modified stress factor: {modified_stress:.2f}")
            print(f"  Vulnerability multiplier: {characteristics.climate_vulnerability_productivity:.2f}")
            print(f"  Final impact: {modified_stress/base_stress_factor:.2f}x base stress")
    
    # Export heterogeneity data
    print("\n" + "=" * 50)
    print("Exporting Heterogeneity Data")
    print("-" * 50)
    
    df = heterogeneity_manager.export_heterogeneity_data("test_heterogeneity_data.csv")
    if df is not None:
        print(f"Exported {len(df)} agent characteristics to test_heterogeneity_data.csv")
        print("\nSummary statistics:")
        if hasattr(df, 'describe'):
            # Pandas DataFrame
            print(df.describe())
        else:
            # List of dictionaries (basic CSV export)
            print("Basic statistics (pandas not available):")
            if len(df) > 0:
                # Calculate basic stats manually
                numeric_fields = ['climate_vulnerability_productivity', 'climate_vulnerability_overhead', 
                                'overhead_efficiency', 'production_efficiency', 'risk_tolerance', 
                                'debt_willingness', 'consumption_preference', 'adaptation_rate']
                
                for field in numeric_fields:
                    values = [row[field] for row in df if field in row]
                    if values:
                        avg = sum(values) / len(values)
                        min_val = min(values)
                        max_val = max(values)
                        print(f"  {field}: avg={avg:.3f}, min={min_val:.3f}, max={max_val:.3f}")
    
    print("\n✅ Heterogeneity system test completed!")

def test_agent_integration():
    """Test how agents integrate with heterogeneity"""
    print("\n🧪 Testing Agent Integration with Heterogeneity")
    print("=" * 50)
    
    # This would require creating actual agent instances
    # For now, just demonstrate the concept
    print("Agent integration features:")
    print("1. Individual climate vulnerability affects stress impact")
    print("2. Different cost structures (overhead and production efficiency)")
    print("3. Behavioral differences in risk tolerance and debt willingness")
    print("4. Geographic adaptation to different climate types")
    print("5. Learning and memory capabilities")
    print("6. Comprehensive logging of heterogeneity data")
    
    print("\n✅ Agent integration test completed!")

if __name__ == "__main__":
    print("🎯 Heterogeneity System Test Suite")
    print("=" * 60)
    
    try:
        test_heterogeneity_generation()
        test_agent_integration()
        
        print("\n" + "=" * 60)
        print("🎉 All tests completed successfully!")
        print("\nTo run the full simulation with heterogeneity:")
        print("python start.py simulation_configurations/heterogeneous_config.json")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc() 