"""
Simulation Logger for Climate 3-Layer Model
Captures and formats agent activity logs instead of printing to console
"""
import logging
import sys
import os
from datetime import datetime
from contextlib import contextmanager


class SimulationLogger:
    """Custom logger for simulation activities with structured formatting"""
    
    def __init__(self, log_file_path=None, console_level='INFO'):
        """
        Initialize the simulation logger
        
        Args:
            log_file_path: Path to the log file. If None, uses default naming
            console_level: Level for console output ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'OFF')
        """
        if log_file_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file_path = f"simulation_log_{timestamp}.txt"
        
        self.log_file_path = log_file_path
        self.console_level = console_level
        
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
        self.logger.info("🚀 CLIMATE 3-LAYER ECONOMIC SIMULATION LOG")
        self.logger.info("=" * 80)
        self.logger.info(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"📄 Log file: {self.log_file_path}")
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
    
    def log_climate_event(self, event_description):
        """Log a climate event"""
        self.logger.warning(f"🌪️  CLIMATE EVENT: {event_description}")
    
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


class AgentPrintCapture:
    """Context manager to capture agent print statements and redirect to logger"""
    
    def __init__(self, sim_logger):
        self.sim_logger = sim_logger
        self.original_stdout = sys.stdout
        self.captured_output = []
    
    def write(self, text):
        """Capture print output"""
        if text.strip():  # Ignore empty lines
            # Clean up the text and log it
            clean_text = text.strip()
            # Try to categorize the message
            if "Climate stress" in clean_text or "CLIMATE" in clean_text:
                self.sim_logger.log_climate_event(clean_text)
            elif any(keyword in clean_text for keyword in ["Household", "Producer", "Firm"]):
                self.sim_logger.log_agent_action(clean_text)
            else:
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
    """Replace print statements in agent files with logging calls"""
    
    def smart_print(*args, **kwargs):
        """Replacement for print that uses our logger"""
        message = ' '.join(str(arg) for arg in args)
        
        # Categorize the message based on content
        if "Climate stress" in message or "CLIMATE" in message:
            sim_logger.log_climate_event(message)
        elif any(keyword in message for keyword in ["Household", "Producer", "Firm", "Commodity", "Intermediary", "Final"]):
            sim_logger.log_agent_action(message)
        else:
            sim_logger.log_agent_action(message)
    
    # Replace the built-in print function
    import builtins
    builtins.print = smart_print 