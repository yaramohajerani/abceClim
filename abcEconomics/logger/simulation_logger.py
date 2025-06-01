"""
Generic Simulation Logger for abcEconomics
Captures and formats agent activity logs with configurable keywords
"""
import logging
import sys
import os
from datetime import datetime
from contextlib import contextmanager


class SimulationLogger:
    """Generic logger for abcEconomics simulations with configurable keywords"""
    
    def __init__(self, log_file_path=None, console_level='INFO', 
                 agent_keywords=None, climate_keywords=None, simulation_name="abcEconomics Simulation"):
        """
        Initialize the simulation logger
        
        Args:
            log_file_path: Path to the log file. If None, uses default naming
            console_level: Level for console output ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'OFF')
            agent_keywords: List of keywords that identify agent actions (e.g., ['Household', 'Firm', 'Producer'])
            climate_keywords: List of keywords that identify climate/stress events (e.g., ['Climate', 'stress', 'shock'])
            simulation_name: Name of the simulation for the log header
        """
        if log_file_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file_path = f"simulation_log_{timestamp}.txt"
        
        self.log_file_path = log_file_path
        self.console_level = console_level
        self.simulation_name = simulation_name
        
        # Set default keywords if none provided
        self.agent_keywords = agent_keywords or [
            'Household', 'Producer', 'Firm', 'Agent', 'Buy', 'Sell', 'Trade', 
            'Commodity', 'Intermediary', 'Final', 'Consumer', 'Market'
        ]
        self.climate_keywords = climate_keywords or [
            'Climate', 'stress', 'shock', 'CLIMATE', 'Weather', 'Event', 
            'Disruption', 'Impact', 'Crisis'
        ]
        
        # Create logger
        self.logger = logging.getLogger('simulation')
        self.logger.setLevel(logging.DEBUG)
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # File handler with detailed formatting
        file_handler = logging.FileHandler(log_file_path, mode='w', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler with simplified formatting (if enabled)
        if console_level.upper() != 'OFF':
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, console_level.upper()))
            console_formatter = logging.Formatter('%(message)s')
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
        
        self.current_round = None
        self.current_phase = None
        
        # Write header to log file
        self.log_simulation_start()
    
    def log_simulation_start(self):
        """Log simulation start header"""
        self.logger.info("=" * 80)
        self.logger.info(f"🚀 {self.simulation_name.upper()} LOG")
        self.logger.info("=" * 80)
        self.logger.info(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"📄 Log file: {self.log_file_path}")
        self.logger.info(f"🔍 Agent keywords: {', '.join(self.agent_keywords[:5])}{'...' if len(self.agent_keywords) > 5 else ''}")
        self.logger.info(f"🌪️ Event keywords: {', '.join(self.climate_keywords[:3])}{'...' if len(self.climate_keywords) > 3 else ''}")
        self.logger.info("=" * 80)
    
    def set_round(self, round_num):
        """Set the current simulation round"""
        self.current_round = round_num
        self.logger.info("")
        self.logger.info(f"🔄 ROUND {round_num}")
        self.logger.info("-" * 40)
    
    def set_phase(self, phase_name):
        """Set the current simulation phase"""
        self.current_phase = phase_name
        self.logger.info(f"\n📍 {phase_name}")
    
    def log_agent_action(self, message, level='INFO'):
        """Log an agent action"""
        if self.current_phase:
            formatted_msg = f"    {message}"
        else:
            formatted_msg = f"  {message}"
        
        getattr(self.logger, level.lower())(formatted_msg)
    
    def log_event(self, event_description, event_icon="🔔"):
        """Log a special event (climate, economic, etc.)"""
        self.logger.warning(f"{event_icon} EVENT: {event_description}")
    
    def log_climate_event(self, event_description):
        """Log a climate event (backward compatibility)"""
        self.log_event(event_description, "🌪️")
    
    def log_phase_summary(self, summary):
        """Log a phase summary"""
        self.logger.info(f"    ✅ {summary}")
    
    def log_simulation_end(self, summary_stats=None):
        """Log simulation end"""
        self.logger.info("")
        self.logger.info("=" * 80)
        self.logger.info("🏁 SIMULATION COMPLETED")
        if summary_stats:
            for key, value in summary_stats.items():
                self.logger.info(f"📊 {key}: {value}")
        self.logger.info("=" * 80)
    
    def categorize_message(self, message):
        """Categorize a message based on keywords"""
        message_lower = message.lower()
        
        # Check for climate/event keywords first
        if any(keyword.lower() in message_lower for keyword in self.climate_keywords):
            return 'event'
        
        # Check for agent keywords
        elif any(keyword.lower() in message_lower for keyword in self.agent_keywords):
            return 'agent'
        
        # Default to agent activity
        else:
            return 'agent'


class AgentPrintCapture:
    """Context manager to capture agent print statements and redirect to logger"""
    
    def __init__(self, sim_logger):
        self.sim_logger = sim_logger
        self.original_stdout = sys.stdout
        self.captured_output = []
    
    def write(self, text):
        """Capture print output"""
        if text.strip():  # Ignore empty lines
            clean_text = text.strip()
            
            # Use the logger's categorization method
            category = self.sim_logger.categorize_message(clean_text)
            
            if category == 'event':
                self.sim_logger.log_event(clean_text)
            else:  # 'agent' or default
                self.sim_logger.log_agent_action(clean_text)
    
    def flush(self):
        """Required for stdout compatibility"""
        pass


@contextmanager
def capture_agent_output(sim_logger):
    """Context manager to capture agent print statements"""
    capture = AgentPrintCapture(sim_logger)
    original_stdout = sys.stdout
    try:
        sys.stdout = capture
        yield
    finally:
        sys.stdout = original_stdout


def replace_agent_prints_with_logging(sim_logger):
    """Replace print statements with logging calls using configurable keywords"""
    
    def smart_print(*args, **kwargs):
        """Replacement for print that uses our logger with configurable categorization"""
        message = ' '.join(str(arg) for arg in args)
        
        # Use the logger's categorization method
        category = sim_logger.categorize_message(message)
        
        if category == 'event':
            sim_logger.log_event(message)
        else:  # 'agent' or default
            sim_logger.log_agent_action(message)
    
    # Replace the built-in print function
    import builtins
    builtins.print = smart_print


def create_simulation_logger(config, simulation_path, simulation_name="abcEconomics Simulation", 
                           agent_keywords=None, climate_keywords=None):
    """
    Factory function to create a simulation logger from configuration
    
    Args:
        config: Configuration dictionary with logging settings
        simulation_path: Path where simulation results are saved
        simulation_name: Name of the simulation
        agent_keywords: Custom keywords for agent activities
        climate_keywords: Custom keywords for events/disruptions
        
    Returns:
        SimulationLogger instance or None if logging is disabled
    """
    logging_config = config.get('logging', {})
    
    if logging_config.get('agent_activity_logging', True):
        log_filename = logging_config.get('log_filename', 'simulation_detailed_log.txt')
        log_file_path = os.path.join(simulation_path, log_filename)
        console_level = logging_config.get('console_level', 'WARNING')
        
        # Get custom keywords from config if provided
        config_agent_keywords = logging_config.get('agent_keywords', agent_keywords)
        config_climate_keywords = logging_config.get('climate_keywords', climate_keywords)
        
        sim_logger = SimulationLogger(
            log_file_path=log_file_path,
            console_level=console_level,
            agent_keywords=config_agent_keywords,
            climate_keywords=config_climate_keywords,
            simulation_name=simulation_name
        )
        
        return sim_logger
    else:
        return None 