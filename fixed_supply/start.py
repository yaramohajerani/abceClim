""" Fixed Supply Model simulation
This is a modified version of the 3-layer supply chain model where:
- Firms maintain fixed output quantities (desired_output_quantity from config)
- Input requirements are calculated dynamically based on climate-affected productivity
- Prices are calculated dynamically based on input costs and profit margins
- Climate cost increases are split 50-50 between producers and consumers
- Agents can go into debt to maintain production/consumption levels
- Enhanced financial tracking for visualization

The model still has the same structure:
- commodity producers (layer 1)
- intermediary firms (layer 2) 
- final goods and services firms (layer 3)
- households

Simulation parameters are provided through JSON configuration files.
"""
import sys
import os
# Add the root directory to Python path to find local abcEconomics
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from abcEconomics import Simulation
from commodity_producer import CommodityProducer
from intermediary_firm import IntermediaryFirm
from final_goods_firm import FinalGoodsFirm
from household import Household

# Import the reusable Climate Framework
from climate_framework import create_climate_framework

# Import the configuration loader
from config_loader import load_model_config

# Import the simulation logger from abcEconomics
from abcEconomics.logger import create_simulation_logger, replace_agent_prints_with_logging



def main(config_file_path):
    """
    Main simulation function for the Fixed Supply Model.
    
    Args:
        config_file_path: Path to the JSON configuration file. If None, uses default "model_config.json"
    """
    # Load configuration - use provided path or default
    if config_file_path is None:
        config_file_path = os.path.join(os.path.dirname(__file__), "model_config.json")
    
    print(f"🔧 Loading configuration from: {config_file_path}")
    config_loader = load_model_config(config_file_path)
    
    # Get simulation parameters from configuration
    simulation_parameters = config_loader.get_simulation_parameters()
    
    # Set up simulation path
    simulation_path = simulation_parameters.get('result_path', 'result_fixed_supply')
    w = Simulation(path=simulation_path)
    
    # Get the actual path that abcEconomics created (handles increments like resultI, resultII, etc.)
    actual_simulation_path = w.path
    print(f"Simulation will save to: {actual_simulation_path}")

    # Set up simulation logger with climate-specific keywords
    climate_agent_keywords = [
        'Household', 'Producer', 'Firm', 'Commodity', 'Intermediary', 'Final',
        'buy', 'sell', 'production', 'consumption', 'labor', 'market',
        'money', 'trade', 'offer', 'accepted', 'spent', 'received',
        'debt', 'profit', 'margin', 'cost', 'revenue', 'price'
    ]
    
    climate_event_keywords = [
        'Climate', 'stress', 'shock', 'CLIMATE', 'Weather', 'Event',
        'Disruption', 'Impact', 'Crisis', 'reset', 'applied', 'cleared',
        'productivity', 'Fixed Supply'
    ]
    
    sim_logger = create_simulation_logger(
        config=config_loader.config,
        simulation_path=actual_simulation_path,
        simulation_name="Fixed Supply Economic Model with Climate Impacts",
        agent_keywords=climate_agent_keywords,
        climate_keywords=climate_event_keywords
    )
    
    if sim_logger:
        # Replace agent print statements with structured logging
        replace_agent_prints_with_logging(sim_logger)
        print(f"📄 Detailed agent activity will be logged to: {sim_logger.log_file_path}")
    else:
        print("📄 Agent activity logging is disabled")

    # Build agents for each layer using configuration
    print(f"\n🏭 Building agents for Fixed Supply Model...")
    
    # Get agent configurations
    commodity_config = config_loader.get_agent_config('commodity_producer')
    intermediary_config = config_loader.get_agent_config('intermediary_firm')
    final_goods_config = config_loader.get_agent_config('final_goods_firm')
    household_config = config_loader.get_agent_config('household')
    
    # Add cross-agent information needed for market distribution
    final_goods_config['household_count'] = household_config['count']
    intermediary_config['final_goods_count'] = final_goods_config['count']
    commodity_config['intermediary_count'] = intermediary_config['count']
    
    # Add firm counts to household config for labor distribution
    household_config['commodity_producer_count'] = commodity_config['count']
    household_config['intermediary_firm_count'] = intermediary_config['count']
    household_config['final_goods_firm_count'] = final_goods_config['count']
    
    # Add wage information to all firm configs for price calculation
    wage = household_config['labor']['wage']
    commodity_config['wage'] = wage
    intermediary_config['wage'] = wage
    final_goods_config['wage'] = wage
    
    # Calculate initial prices for each layer based on config parameters
    # Commodity price calculation
    commodity_labor_cost = commodity_config['production']['inputs'].get('labor', 0) * wage
    commodity_cost_per_unit = commodity_labor_cost / commodity_config['production']['desired_output_quantity']
    commodity_initial_price = commodity_cost_per_unit * (1 + commodity_config['production']['profit_margin'])
    
    # Add commodity price to intermediary config
    intermediary_config['commodity_price'] = commodity_initial_price
    
    # Intermediate good price calculation
    intermediary_labor_cost = intermediary_config['production']['inputs'].get('labor', 0) * wage
    intermediary_commodity_cost = intermediary_config['production']['inputs'].get('commodity', 0) * commodity_initial_price
    intermediary_total_cost = intermediary_labor_cost + intermediary_commodity_cost
    intermediary_cost_per_unit = intermediary_total_cost / intermediary_config['production']['desired_output_quantity']
    intermediary_initial_price = intermediary_cost_per_unit * (1 + intermediary_config['production']['profit_margin'])
    
    # Add intermediate good price to final goods config
    final_goods_config['intermediate_good_price'] = intermediary_initial_price
    
    # Build agents with their configurations
    commodity_producers = w.build_agents(
        CommodityProducer, 
        'commodity_producer', 
        commodity_config['count'],
        config=commodity_config
    )
    
    intermediary_firms = w.build_agents(
        IntermediaryFirm, 
        'intermediary_firm', 
        intermediary_config['count'],
        config=intermediary_config
    )
    
    final_goods_firms = w.build_agents(
        FinalGoodsFirm, 
        'final_goods_firm', 
        final_goods_config['count'],
        config=final_goods_config
    )
    
    households = w.build_agents(
        Household, 
        'household', 
        household_config['count'],
        config=household_config
    )
    
    # Create the climate framework
    climate_framework = create_climate_framework(simulation_parameters)
    
    # Organize agents into groups for the framework
    agent_groups = {
        'commodity_producer': commodity_producers,
        'intermediary_firm': intermediary_firms,
        'final_goods_firm': final_goods_firms,
        'household': households
    }
    
    # Assign geographical locations using the framework with configuration rules
    print("🌍 Assigning geographical locations...")
    distribution_rules = config_loader.get_geographical_distribution_rules()
    climate_framework.assign_geographical_locations(agent_groups, distribution_rules)
    
    print(f"\n📊 Starting Fixed Supply Model simulation with:")
    print(f"  {commodity_producers.num_agents} commodity producers (fixed output)")
    print(f"  {intermediary_firms.num_agents} intermediary firms (fixed output)") 
    print(f"  {final_goods_firms.num_agents} final goods firms (fixed output)")
    print(f"  {households.num_agents} households")
    print(f"  Dynamic pricing based on costs + profit margins")
    print(f"  50-50 climate cost sharing")
    print(f"  Debt mechanism enabled")
    print(f"  Distributed across continents according to configuration")

    # Set up data collection using configuration
    goods_to_track = config_loader.get_goods_to_track()
    print("📈 Goods to track: ", goods_to_track)
    
    # Run simulation
    print(f"\n🚀 Starting simulation for {simulation_parameters['rounds']} rounds...")
    for r in range(simulation_parameters['rounds']):
        print(f"\n{'='*60}")
        print(f"Round {r}...", end=" ")
        
        # Log the round start in the detailed log
        if sim_logger:
            sim_logger.set_round(r)
        
        w.advance_round(r)
        
        # Initialize round tracking for all agents
        commodity_producers.start_round()
        intermediary_firms.start_round()
        final_goods_firms.start_round()
        households.start_round()
        
        # Apply geographical climate stress using the framework
        climate_events = {}
        if simulation_parameters['climate_stress_enabled']:
            if sim_logger:
                sim_logger.set_phase("Climate Events")
            climate_events = climate_framework.apply_geographical_climate_stress(agent_groups)

        # Labor market
        print(f"  💼 Labor market...")
        if sim_logger:
            sim_logger.set_phase("Labor Market")
        labor_endowment = household_config['labor']['endowment']
        households.refresh_services('labor', derived_from='labor_endowment', units=labor_endowment)
        households.sell_labor()
        if sim_logger:
            sim_logger.log_phase_summary(f"Labor offered by households (endowment: {labor_endowment} per household)")
        
        # Layer 1: Commodity producers buy labor and produce
        print(f"  🏭 Layer 1: Commodity producers...")
        if sim_logger:
            sim_logger.set_phase("Layer 1: Commodity Producers")
        commodity_producers.buy_labor()
        commodity_producers.production()
        
        # Layer 2: Intermediary firms buy commodities and labor, then produce
        print(f"  🏭 Layer 2: Intermediary firms...")
        if sim_logger:
            sim_logger.set_phase("Layer 2: Intermediary Firms")
        commodity_producers.sell_commodities()  # Create offers for commodities
        intermediary_firms.buy_inputs_optimally()    # Buy commodities and labor with optimal allocation
        commodity_producers.calculate_sales_after_market_clearing()
        commodity_producers.log_round_data()    # Log with correct sales data
        intermediary_firms.production()
        
        # Layer 3: Final goods firms buy intermediate goods and labor, then produce
        print(f"  🏭 Layer 3: Final goods firms...")
        if sim_logger:
            sim_logger.set_phase("Layer 3: Final Goods Firms")
        intermediary_firms.sell_intermediate_goods()  # Create offers for intermediate goods
        final_goods_firms.buy_inputs_optimally()    # Buy intermediate goods and labor with optimal allocation
        intermediary_firms.calculate_sales_after_market_clearing()  # Now calculate actual sales
        intermediary_firms.log_round_data()           # Log with correct sales data
        final_goods_firms.production()
        
        # Households buy final goods and consume
        print(f"  🛒 Consumer market...")
        if sim_logger:
            sim_logger.set_phase("Consumer Market")
        final_goods_firms.sell_final_goods()   # Create offers for final goods
        households.buy_final_goods()           # Accept final good offers - THIS changes inventory
        final_goods_firms.calculate_sales_after_market_clearing()  # Now calculate actual sales
        final_goods_firms.log_round_data()     # Log with correct sales data
        households.consumption()
        households.log_round_data()
        
        # Collect data using the new framework method (still needed for climate data)
        if sim_logger:
            sim_logger.set_phase("Data Collection")
        
        print("✅ completed")
    
    print("\n📊 Finalizing simulation...")
    w.finalize()
    print("✅ Simulation completed!")
    print(f"📁 Results saved to: {actual_simulation_path}")
    
    # Log simulation end
    if sim_logger:
        summary_stats = {
            "Model type": "Fixed Supply Model",
            "Total rounds": simulation_parameters['rounds'],
            "Climate events": len([e for events in climate_framework.climate_events_history for e in events]),
            "Agent types": len(agent_groups),
            "Total agents": sum(group.num_agents for group in agent_groups.values()),
            "Output directory": actual_simulation_path
        }
        sim_logger.log_simulation_end(summary_stats)
    
    # Always export climate summary for animation visualizer (regardless of visualization settings)
    print("📊 Exporting climate summary for animation visualizer...")
    climate_framework.export_climate_summary(actual_simulation_path, "fixed_supply_climate_summary.csv")
    
    # Create visualizations using the custom supply chain visualizer
    if simulation_parameters['create_visualizations']:
        print("📊 Creating specialized supply chain visualizations...")
        
        # Import the custom supply chain visualizer
        from supply_chain_visualizations import SupplyChainVisualizer
        
        # Create the specialized visualizer
        supply_chain_viz = SupplyChainVisualizer(climate_framework)
        
        # Create comprehensive supply chain analysis
        supply_chain_viz.create_comprehensive_supply_chain_analysis(
            simulation_path=actual_simulation_path,
            model_name="Fixed Supply Model with Dynamic Pricing"
        )
        
        print("✅ Specialized supply chain visualizations completed!")
    
    # Create time-evolving visualizations using the new modular animation visualizer
    if simulation_parameters.get('create_dynamic_visualization', False):
        print("\n🎬 Creating time-evolving visualizations with financial metrics...")
        
        try:
            # Import the new animation visualizer
            from animation_visualizer import run_animation_visualizations
            
            # Run the animation visualizations
            animation_results = run_animation_visualizations(
                simulation_path=actual_simulation_path
            )
            
            if animation_results:
                print(f"\n🎉 Dynamic visualizations completed!")
                print(f"📊 Time evolution plot: {animation_results['time_plot']}")
                print(f"🎞️ Animation: {animation_results['animation']}")
            else:
                print("⚠️ Animation visualizations failed to complete")
                
        except ImportError as e:
            print(f"⚠️ Could not import animation visualizer: {e}")
        except Exception as e:
            print(f"⚠️ Error creating animations: {e}")
    
    # Print summary
    total_climate_events = sum(len(events) for events in climate_framework.climate_events_history)
    print(f"\n📊 Summary: Successfully completed {len(climate_framework.climate_events_history)} rounds")
    print(f"🌪️ Total climate events occurred: {total_climate_events}")
    print(f"🌍 Geographical assignments: {len(climate_framework.geographical_assignments)} agent types")
    print(f"💰 Model features: Fixed output, dynamic pricing, debt mechanism, 50-50 cost sharing")
    
    return climate_framework


if __name__ == '__main__':
    import sys
    
    # Allow specifying config file as command line argument
    config_file = sys.argv[1] if len(sys.argv) > 1 else None
    
    if config_file is None:
        print("❌ No configuration file provided.")
        sys.exit()
        
    print("🏭 Fixed Supply Economic Model with Dynamic Pricing and Climate Impacts")
    print("=" * 70)
    
    results = main(config_file)
    print(f"\n✅ Final result summary: {len(results.climate_events_history)} rounds completed")
    print(f"📊 Fixed Supply Model simulation successful!") 