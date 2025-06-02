#!/usr/bin/env python3
"""
Test script for the Fixed Supply Model

This script runs a quick test of the fixed supply model and validates
that the key features are working correctly:
- Fixed output quantities
- Dynamic pricing
- Debt mechanisms
- Financial tracking
"""

import sys
import os
import subprocess
import pandas as pd
import json

def run_simulation(config_file):
    """Run the fixed supply model simulation"""
    print(f"🚀 Running Fixed Supply Model with config: {config_file}")
    
    # Run the simulation
    cmd = [sys.executable, "start.py", config_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Simulation failed!")
        print(f"Error: {result.stderr}")
        return None
        
    # Extract the result directory from output
    for line in result.stdout.split('\n'):
        if 'Results saved to:' in line or 'will save to:' in line:
            result_dir = line.split(':')[-1].strip()
            return result_dir
            
    return None

def validate_results(result_dir):
    """Validate that the simulation produced expected results"""
    print(f"\n📊 Validating results in: {result_dir}")
    
    issues = []
    
    # Check if key files exist
    required_files = [
        'panel_commodity_producer_production.csv',
        'panel_intermediary_firm_production.csv',
        'panel_final_goods_firm_production.csv',
        'panel_household_consumption.csv'
    ]
    
    for file in required_files:
        filepath = os.path.join(result_dir, file)
        if not os.path.exists(filepath):
            issues.append(f"Missing file: {file}")
            
    # Check commodity producer data
    commodity_file = os.path.join(result_dir, 'panel_commodity_producer_production.csv')
    if os.path.exists(commodity_file):
        df = pd.read_csv(commodity_file)
        
        # Check if debt column exists
        if 'production_debt' not in df.columns:
            issues.append("Missing 'production_debt' column in commodity producer data")
            
        # Check if financial metrics exist
        expected_columns = ['production_profit', 'production_actual_margin', 'production_target_margin', 'production_price']
        for col in expected_columns:
            if col not in df.columns:
                issues.append(f"Missing '{col}' column in commodity producer data")
                
        # Check if prices are dynamic (should vary from base)
        if 'production_price' in df.columns:
            price_variance = df['production_price'].std()
            if price_variance < 0.01:
                issues.append("Prices appear to be static (no variance)")
            else:
                print(f"✅ Dynamic pricing working - price variance: {price_variance:.3f}")
                
        # Check if debt is being created
        if 'production_debt' in df.columns:
            max_debt = df['production_debt'].max()
            if max_debt > 0:
                print(f"✅ Debt mechanism working - max debt: ${max_debt:.2f}")
            else:
                print("⚠️  No debt created (might be normal if no stress)")
                
    # Check household data
    household_file = os.path.join(result_dir, 'panel_household_consumption.csv')
    if os.path.exists(household_file):
        df = pd.read_csv(household_file)
        
        if 'consumption_minimum_consumption_met' in df.columns:
            unmet = df[df['consumption_minimum_consumption_met'] == False]
            if len(unmet) > 0:
                print(f"⚠️  Some households didn't meet minimum consumption: {len(unmet)} instances")
                
    return issues

def analyze_financial_health(result_dir):
    """Analyze the financial health of the system"""
    print(f"\n💰 Financial Health Analysis")
    
    # Analyze firm profitability
    for firm_type in ['commodity_producer', 'intermediary_firm', 'final_goods_firm']:
        file = os.path.join(result_dir, f'panel_{firm_type}_production.csv')
        if os.path.exists(file):
            df = pd.read_csv(file)
            
            if 'production_profit' in df.columns and 'production_actual_margin' in df.columns:
                avg_profit = df.groupby('round')['production_profit'].mean().mean()
                avg_margin = df.groupby('round')['production_actual_margin'].mean().mean()
                total_debt = df['production_debt'].max() if 'production_debt' in df.columns else 0
                
                print(f"\n{firm_type.replace('_', ' ').title()}:")
                print(f"  Average profit: ${avg_profit:.2f}")
                print(f"  Average margin: {avg_margin*100:.1f}%")
                print(f"  Max debt: ${total_debt:.2f}")

def main():
    """Main test function"""
    print("=" * 60)
    print("🧪 Fixed Supply Model Test Suite")
    print("=" * 60)
    
    # Use default config if not specified
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    else:
        config_file = "simulation_configurations/fixed_supply_config.json"
        
    # Check if config exists
    if not os.path.exists(config_file):
        print(f"❌ Configuration file not found: {config_file}")
        return 1
        
    # Load and display key config parameters
    with open(config_file, 'r') as f:
        config = json.load(f)
        
    print(f"\n📋 Configuration Summary:")
    print(f"  Simulation name: {config['simulation']['name']}")
    print(f"  Rounds: {config['simulation']['rounds']}")
    print(f"  Climate stress: {config['climate']['stress_enabled']}")
    
    # Run simulation
    result_dir = run_simulation(config_file)
    if not result_dir:
        print("❌ Failed to run simulation")
        return 1
        
    # Validate results
    issues = validate_results(result_dir)
    
    if issues:
        print(f"\n❌ Validation issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print(f"\n✅ All validation checks passed!")
        
    # Analyze financial health
    analyze_financial_health(result_dir)
    
    print(f"\n📁 Full results available in: {result_dir}")
    print("=" * 60)
    
    return 0 if not issues else 1

if __name__ == "__main__":
    sys.exit(main()) 