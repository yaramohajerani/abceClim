#!/usr/bin/env python3
"""
Add Mesa Dynamic Visualization to Climate 3-Layer Model

This script provides a simple way to add real-time, browser-based visualization
to the existing climate 3-layer supply chain model.
"""

import sys
import os
import random

# Add path for climate framework
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def create_simple_visualization():
    """Create a simple Mesa visualization for the climate model."""
    
    print("🌍 Adding Mesa Dynamic Visualization to Climate 3-Layer Model")
    print("="*65)
    
    try:
        # Import Mesa components
        from mesa import Agent, Model
        from mesa.time import RandomActivation
        from mesa.space import MultiGrid
        from mesa.datacollection import DataCollector
        from mesa.visualization.modules import CanvasGrid, ChartModule, TextElement
        from mesa.visualization.ModularVisualization import ModularServer
        
        # Import your existing model components
        from commodity_producer import CommodityProducer
        from intermediary_firm import IntermediaryFirm  
        from final_goods_firm import FinalGoodsFirm
        from household import Household
        from climate_framework import create_climate_framework
        
        print("✅ All components imported successfully")
        
        # Create a Mesa-compatible wrapper for your existing agents
        class ClimateAgentWrapper(Agent):
            """Mesa wrapper for existing abcEconomics agents."""
            
            def __init__(self, unique_id, model, abce_agent, agent_type):
                super().__init__(unique_id, model)
                self.abce_agent = abce_agent
                self.agent_type = agent_type
                self.wealth = getattr(abce_agent, 'money', 10) if hasattr(abce_agent, '__getitem__') else 10
                self.production = getattr(abce_agent, 'current_output_quantity', random.uniform(1, 3))
                self.base_production = self.production
                self.climate_stressed = getattr(abce_agent, 'climate_stressed', False)
                self.supply_chain_impact = 0  # Track indirect impacts from supply chain
                self.directly_hit = False  # Track if directly hit by climate event
                
            def step(self):
                # Update display properties from the underlying abcEconomics agent
                if hasattr(self.abce_agent, '__getitem__'):
                    self.wealth = self.abce_agent.get('money', 0)
                if hasattr(self.abce_agent, 'current_output_quantity'):
                    self.production = self.abce_agent.current_output_quantity
                self.climate_stressed = getattr(self.abce_agent, 'climate_stressed', False)
        
        # Create the Mesa model
        class ClimateVisualizationModel(Model):
            """Mesa model for visualizing the climate supply chain."""
            
            def __init__(self, width=15, height=10):
                super().__init__()
                self.grid = MultiGrid(width, height, True)
                self.schedule = RandomActivation(self)
                self.running = True
                self.step_count = 0
                
                # Track supply chain layers for analysis
                self.commodity_producers = []
                self.intermediary_firms = []
                self.final_goods_firms = []
                self.households = []
                
                # Create agents representing the 3-layer supply chain
                agent_types = [
                    ('commodity_producer', 3),
                    ('intermediary_firm', 2), 
                    ('final_goods_firm', 2),
                    ('household', 8)
                ]
                
                agent_id = 0
                for agent_type, count in agent_types:
                    for i in range(count):
                        # Create a mock abcEconomics-like agent for demonstration
                        mock_agent = type('MockAgent', (), {
                            'id': agent_id,
                            'money': random.randint(20, 100),
                            'current_output_quantity': random.uniform(1.5, 3.0),
                            'climate_stressed': False
                        })()
                        
                        agent = ClimateAgentWrapper(agent_id, self, mock_agent, agent_type)
                        self.schedule.add(agent)
                        
                        # Store agents by type for supply chain analysis
                        if agent_type == 'commodity_producer':
                            self.commodity_producers.append(agent)
                        elif agent_type == 'intermediary_firm':
                            self.intermediary_firms.append(agent)
                        elif agent_type == 'final_goods_firm':
                            self.final_goods_firms.append(agent)
                        else:
                            self.households.append(agent)
                        
                        # Fix Y-axis orientation: (0,0) is top-left, so higher Y values are lower on screen
                        if agent_type == 'commodity_producer':
                            x, y = random.randint(1, 4), random.randint(6, 8)  # Left side, bottom - Layer 1
                        elif agent_type == 'intermediary_firm':
                            x, y = random.randint(6, 9), random.randint(6, 8)  # Middle, bottom - Layer 2
                        elif agent_type == 'final_goods_firm':
                            x, y = random.randint(11, 14), random.randint(6, 8)  # Right side, bottom - Layer 3
                        else:  # households
                            x, y = random.randint(2, 13), random.randint(1, 3)  # Top - consumers
                        
                        self.grid.place_agent(agent, (x, y))
                        agent_id += 1
                
                # Data collection with supply chain analysis - Fix chart names
                self.datacollector = DataCollector(
                    model_reporters={
                        # Network propagation chart data
                        "Layer 1 Stress (Commodity)": lambda m: sum([1 for a in m.commodity_producers if a.climate_stressed]),
                        "Layer 2 Stress (Intermediary)": lambda m: sum([1 for a in m.intermediary_firms if a.climate_stressed]),
                        "Layer 3 Stress (Final Goods)": lambda m: sum([1 for a in m.final_goods_firms if a.climate_stressed]),
                        "Household Stress": lambda m: sum([1 for a in m.households if a.climate_stressed]),
                        
                        # Production levels chart data
                        "Layer 1 Production": lambda m: sum([a.production for a in m.commodity_producers]),
                        "Layer 2 Production": lambda m: sum([a.production for a in m.intermediary_firms]),
                        "Layer 3 Production": lambda m: sum([a.production for a in m.final_goods_firms]),
                        
                        # Impact breakdown chart data
                        "Direct Climate Hits": lambda m: sum([1 for a in m.schedule.agents if a.directly_hit]),
                        "Supply Chain Propagation": lambda m: sum([1 for a in m.schedule.agents if a.supply_chain_impact > 0]),
                        "Total Network Impact": lambda m: sum([1 for a in m.schedule.agents if a.climate_stressed])
                    }
                )
                
                print(f"✅ Model created with {len(self.schedule.agents)} agents")
            
            def step(self):
                """Execute one step of the model."""
                self.step_count += 1
                
                # Reset impact tracking
                for agent in self.schedule.agents:
                    agent.directly_hit = False
                    agent.supply_chain_impact = 0
                
                # Phase 1: Apply direct climate stress (mainly to commodity producers)
                for agent in self.commodity_producers:
                    if random.random() < 0.08:  # 8% chance for commodity producers
                        agent.climate_stressed = True
                        agent.directly_hit = True
                        agent.production = max(0.5, agent.production * 0.7)  # 30% reduction
                
                # Lower chance for other layers to be directly hit
                for agent in self.intermediary_firms + self.final_goods_firms:
                    if random.random() < 0.03:  # 3% chance for other firms
                        agent.climate_stressed = True
                        agent.directly_hit = True
                        agent.production = max(0.5, agent.production * 0.8)  # 20% reduction
                
                # Phase 2: Supply chain propagation effects
                # Commodity stress affects intermediary firms
                commodity_stress_level = sum([1 for a in self.commodity_producers if a.climate_stressed]) / len(self.commodity_producers)
                if commodity_stress_level > 0.3:  # If 30%+ of suppliers stressed
                    for agent in self.intermediary_firms:
                        if not agent.directly_hit and not agent.climate_stressed:
                            agent.supply_chain_impact = commodity_stress_level
                            agent.climate_stressed = True
                            agent.production = max(0.7, agent.production * (1 - commodity_stress_level * 0.3))
                
                # Intermediary stress affects final goods firms
                intermediary_stress_level = sum([1 for a in self.intermediary_firms if a.climate_stressed]) / len(self.intermediary_firms)
                if intermediary_stress_level > 0.4:  # If 40%+ of suppliers stressed
                    for agent in self.final_goods_firms:
                        if not agent.directly_hit and not agent.climate_stressed:
                            agent.supply_chain_impact = intermediary_stress_level
                            agent.climate_stressed = True
                            agent.production = max(0.8, agent.production * (1 - intermediary_stress_level * 0.2))
                
                # Final goods stress affects household consumption
                final_goods_stress_level = sum([1 for a in self.final_goods_firms if a.climate_stressed]) / len(self.final_goods_firms)
                if final_goods_stress_level > 0.5:  # If 50%+ of final goods firms stressed
                    affected_households = random.sample(self.households, min(3, len(self.households)))
                    for agent in affected_households:
                        if not agent.climate_stressed:
                            agent.climate_stressed = True
                            agent.wealth = max(10, agent.wealth * 0.9)  # 10% wealth reduction
                
                # Phase 3: Recovery mechanism
                for agent in self.schedule.agents:
                    if agent.climate_stressed and not agent.directly_hit and random.random() < 0.4:
                        agent.climate_stressed = False
                        agent.production = min(agent.base_production, agent.production * 1.1)
                    elif agent.climate_stressed and agent.directly_hit and random.random() < 0.2:
                        agent.climate_stressed = False
                        agent.directly_hit = False
                        agent.production = min(agent.base_production, agent.production * 1.05)
                
                self.datacollector.collect(self)
                self.schedule.step()
        
        # Agent visualization function
        def agent_portrayal(agent):
            """Define how agents appear on the grid."""
            portrayal = {
                "Shape": "circle",
                "Filled": "true",
                "Layer": 0,
                "r": 0.7
            }
            
            # Color coding by agent type and state
            if agent.agent_type == 'commodity_producer':
                if agent.directly_hit:
                    portrayal["Color"] = "#FF0000"  # Red for direct climate hit
                elif agent.climate_stressed:
                    portrayal["Color"] = "#FF4500"  # Orange-red for stressed
                else:
                    portrayal["Color"] = "#8B4513"  # Brown for normal
                portrayal["r"] = 0.9
                portrayal["Shape"] = "rect"
                portrayal["w"] = 0.8
                portrayal["h"] = 0.8
                
            elif agent.agent_type == 'intermediary_firm':
                if agent.directly_hit:
                    portrayal["Color"] = "#FF0000"  # Red for direct hit
                elif agent.supply_chain_impact > 0:
                    portrayal["Color"] = "#FF6347"  # Tomato for supply chain impact
                elif agent.climate_stressed:
                    portrayal["Color"] = "#FF8C00"  # Orange for other stress
                else:
                    portrayal["Color"] = "#DAA520"  # Goldenrod for normal
                portrayal["r"] = 0.8
                
            elif agent.agent_type == 'final_goods_firm':
                if agent.directly_hit:
                    portrayal["Color"] = "#FF0000"  # Red for direct hit
                elif agent.supply_chain_impact > 0:
                    portrayal["Color"] = "#228B22"  # Forest green for supply chain impact
                elif agent.climate_stressed:
                    portrayal["Color"] = "#32CD32"  # Lime green for other stress
                else:
                    portrayal["Color"] = "#00FF00"  # Bright green for normal
                portrayal["r"] = 0.8
                
            else:  # household
                portrayal["Color"] = "#4169E1"  # Blue
                if agent.climate_stressed:
                    portrayal["Color"] = "#000080"  # Navy blue for stressed households
                elif agent.wealth > 60:
                    portrayal["Color"] = "#0000FF"  # Bright blue for wealthy
                elif agent.wealth < 30:
                    portrayal["Color"] = "#87CEEB"  # Sky blue for poor
                portrayal["r"] = 0.5
            
            return portrayal
        
        # Simplified status display to reduce choppiness
        class StatusDisplay(TextElement):
            def render(self, model):
                climate_events = sum([1 for a in model.schedule.agents if a.climate_stressed])
                total_production = sum([a.production for a in model.schedule.agents])
                direct_hits = sum([1 for a in model.schedule.agents if a.directly_hit])
                indirect_impacts = sum([1 for a in model.schedule.agents if a.supply_chain_impact > 0])
                
                return f"""
                <div style="font-family: Arial; padding: 15px; background: #f0f0f0; border-radius: 8px; margin: 10px;">
                    <h3 style="color: #2E8B57; margin-top: 0;">🌍 Climate 3-Layer Supply Chain Model</h3>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; font-size: 13px;">
                        <div>
                            <p><strong>Round:</strong> {model.step_count}</p>
                            <p><strong>Total Production:</strong> {total_production:.2f}</p>
                            <p><strong>Active Climate Events:</strong> <span style="color: red;">{climate_events}</span></p>
                        </div>
                        <div>
                            <p><strong>🎯 Direct Climate Hits:</strong> <span style="color: red;">{direct_hits}</span></p>
                            <p><strong>🔗 Supply Chain Impacts:</strong> <span style="color: orange;">{indirect_impacts}</span></p>
                        </div>
                    </div>
                    
                    <div style="margin-top: 15px; padding: 10px; background: white; border-radius: 5px;">
                        <h4 style="margin: 0 0 8px 0; color: #333;">📊 Supply Chain Status by Layer:</h4>
                        <div style="font-size: 12px;">
                            <p><span style="color: #8B4513;">■</span> <strong>Layer 1 (Commodity):</strong> {len([a for a in model.commodity_producers if a.climate_stressed])}/{len(model.commodity_producers)} stressed</p>
                            <p><span style="color: #DAA520;">■</span> <strong>Layer 2 (Intermediary):</strong> {len([a for a in model.intermediary_firms if a.climate_stressed])}/{len(model.intermediary_firms)} stressed</p>
                            <p><span style="color: #00FF00;">■</span> <strong>Layer 3 (Final Goods):</strong> {len([a for a in model.final_goods_firms if a.climate_stressed])}/{len(model.final_goods_firms)} stressed</p>
                            <p><span style="color: #4169E1;">■</span> <strong>Households:</strong> {len([a for a in model.households if a.climate_stressed])}/{len(model.households)} stressed</p>
                        </div>
                    </div>
                </div>
                """
        
        # Simplified grid explanation - static content
        class GridExplanation(TextElement):
            def render(self, model):
                return f"""
                <div style="font-family: Arial; padding: 10px; background: #e8f4f8; border-radius: 5px; margin: 5px; font-size: 12px;">
                    <h4 style="margin: 0 0 8px 0; color: #2E8B57;">🗺️ Agent Grid Layout</h4>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; margin: 8px 0;">
                        <div style="background: #f9f9f9; padding: 6px; border-radius: 3px; text-align: center;">
                            <strong>LEFT</strong><br/>
                            <span style="color: #8B4513;">🟤 Layer 1</span><br/>
                            Commodity Producers
                        </div>
                        <div style="background: #f9f9f9; padding: 6px; border-radius: 3px; text-align: center;">
                            <strong>CENTER</strong><br/>
                            <span style="color: #DAA520;">🟡 Layer 2</span><br/>
                            Intermediary Firms
                        </div>
                        <div style="background: #f9f9f9; padding: 6px; border-radius: 3px; text-align: center;">
                            <strong>RIGHT</strong><br/>
                            <span style="color: #00FF00;">🟢 Layer 3</span><br/>
                            Final Goods Firms
                        </div>
                    </div>
                    
                    <div style="background: #f9f9f9; padding: 6px; border-radius: 3px; text-align: center; margin-top: 8px;">
                        <strong>TOP</strong><br/>
                        <span style="color: #4169E1;">🔵 Households</span> - Consumers
                    </div>
                    
                    <div style="margin-top: 8px; padding: 6px; background: #fff3cd; border-radius: 3px;">
                        <strong>Colors:</strong> <span style="color: red;">🔴 Direct hit</span> | 
                        <span style="color: orange;">🟠 Supply chain impact</span> | 
                        <span style="color: navy;">🔵 Stressed households</span>
                    </div>
                </div>
                """
        
        # Create visualization elements
        print("🎨 Setting up visualization...")
        grid = CanvasGrid(agent_portrayal, 15, 10, 750, 500)
        
        # Network propagation chart showing cascade effects over time
        network_propagation_chart = ChartModule([
            {"Label": "Layer 1 Stress (Commodity)", "Color": "#8B4513"},
            {"Label": "Layer 2 Stress (Intermediary)", "Color": "#DAA520"},
            {"Label": "Layer 3 Stress (Final Goods)", "Color": "#00FF00"},
            {"Label": "Household Stress", "Color": "#4169E1"}
        ])
        
        # Production levels by layer
        production_levels_chart = ChartModule([
            {"Label": "Layer 1 Production", "Color": "#8B4513"},
            {"Label": "Layer 2 Production", "Color": "#DAA520"}, 
            {"Label": "Layer 3 Production", "Color": "#00FF00"}
        ])
        
        # Impact type breakdown
        impact_breakdown_chart = ChartModule([
            {"Label": "Direct Climate Hits", "Color": "#FF0000"},
            {"Label": "Supply Chain Propagation", "Color": "#FF8C00"},
            {"Label": "Total Network Impact", "Color": "#8B0000"}
        ])
        
        status = StatusDisplay()
        grid_explanation = GridExplanation()
        
        # Create the server
        print("🌐 Creating visualization server...")
        server = ModularServer(
            ClimateVisualizationModel,
            [status, grid_explanation, grid, network_propagation_chart, production_levels_chart, impact_breakdown_chart],
            "Climate 3-Layer Supply Chain - Network Propagation Visualization",
            {"width": 15, "height": 10}
        )
        
        server.port = 8521
        
        print("="*65)
        print(f"🌐 Server will start on: http://localhost:{server.port}")
        print("🚀 Starting server...")
        print("   Press Ctrl+C to stop the server")
        print("="*65)
        
        # Launch the server
        server.launch()
        
    except KeyboardInterrupt:
        print("\n🛑 Visualization stopped by user")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n🔧 Troubleshooting:")
        print("   • Make sure Mesa is installed: pip install mesa")
        print("   • Check that port 8521 is available")
        print("   • If browser doesn't open, manually go to the URL")

if __name__ == '__main__':
    create_simple_visualization() 