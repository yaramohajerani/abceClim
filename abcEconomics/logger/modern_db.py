# Replacement for db.py to work with python3.8+
import datetime
import json
import os
import threading
import multiprocessing
import time
import re
from collections import defaultdict
import pandas as pd

from .online_variance import OnlineVariance
import queue


class ModernDbDatabase:
    """ database handler using direct CSV export """

    def __init__(self, directory, name, in_sok, trade_log, plugin=None, pluginargs=[]):
        super().__init__()

        # setting up directory
        self.directory = directory
        if directory is not None:
            if directory == 'auto':
                os.makedirs(os.path.abspath('.') + '/result/', exist_ok=True)
                self.directory = (os.path.abspath('.') + '/result/' + name + '_' +
                             datetime.datetime.now().strftime("%Y-%m-%d_%H-%M"))
            else:
                self.directory = directory
            
            # Try to create directory, if it exists find next version number
            try:
                os.makedirs(self.directory)
            except OSError:
                self.directory = self._get_next_versioned_directory(self.directory)
                os.makedirs(self.directory)

        self.panels = {}
        self.in_sok = in_sok
        self.data = defaultdict(list)
        self.trade_log_data = []
        self.trade_log = trade_log

        self.aggregation = defaultdict(lambda: defaultdict(OnlineVariance))
        self.aggregates_data = defaultdict(list)
        self.round = 0

        self.plugin = plugin
        self.pluginargs = pluginargs

    def run(self):
        if self.plugin is not None:
            self.plugin = self.plugin(*self.pluginargs)
        
        # Skip database initialization if directory is None
        if self.directory is None:
            while True:
                try:
                    msg = self.in_sok.get(timeout=120)
                except queue.Empty:
                    print("simulation.finalize() must be specified at the end of simulation")
                    msg = self.in_sok.get()
                if msg == "close":
                    break
            return

        while True:
            try:
                msg = self.in_sok.get(timeout=120)
            except queue.Empty:
                print("simulation.finalize() must be specified at the end of simulation")
                msg = self.in_sok.get()

            if msg[0] == 'snapshot_agg':
                _, round, group, data_to_write = msg
                if self.round == round:
                    for key, value in data_to_write.items():
                        self.aggregation[group][key].update(value)
                else:
                    self.make_aggregation_and_write()
                    self.round = round
                    for key, value in data_to_write.items():
                        self.aggregation[group][key].update(value)

            elif msg[0] == 'trade_log':
                if self.trade_log:
                    for (good, seller, buyer, price), quantity in msg[1].items():
                        self.trade_log_data.append({
                            'round': msg[2],
                            'good': good,
                            'seller': seller,
                            'buyer': buyer,
                            'price': price,
                            'quantity': quantity
                        })

            elif msg[0] == 'log':
                _, group, name, round, data_to_write, subround_or_serial = msg
                table_key = f'panel_{group}_{subround_or_serial}'
                
                # Prepare data row
                row_data = {
                    'round': str(round),
                    'name': str(name),
                    **{k: v for k, v in data_to_write.items()}
                }
                
                self.data[table_key].append(row_data)

            elif msg == "close":
                break

            else:
                try:
                    getattr(self.plugin, msg[0])(*msg[1], **msg[2])
                except AttributeError:
                    raise AttributeError(
                        "abcEconomics_db error '%s' command unknown" % msg)

        # Final processing
        self.make_aggregation_and_write()
        
        try:
            self.plugin.close()
        except AttributeError:
            pass
            
        if self.directory is not None:
            self.export_to_csv()

    def make_aggregation_and_write(self):
        for group, table in self.aggregation.items():
            result = {'round': self.round}
            for key, data in table.items():
                result[key + '_ttl'] = data.sum()
                result[key + '_mean'] = data.mean()
                result[key + '_std'] = data.std()
            
            self.aggregates_data[f'aggregate_{group}'].append(result)
            self.aggregation[group].clear()

    def export_to_csv(self):
        """Export all collected data to CSV files using pandas"""
        try:
            total_files_exported = 0
            
            # Export panel data
            for table_name, data_list in self.data.items():
                if data_list:
                    df = pd.DataFrame(data_list)
                    
                    # Clean up table name for CSV filename
                    csv_name = table_name.replace('panel_', '').replace('___', '_')
                    csv_path = os.path.join(self.directory, f'panel_{csv_name}.csv')
                    
                    try:
                        df.to_csv(csv_path, index=False)
                        print(f"✓ Exported {len(df)} rows to panel_{csv_name}.csv")
                        total_files_exported += 1
                    except Exception as e:
                        print(f"✗ Error exporting {table_name}: {e}")

            # Export trade log data
            if self.trade_log_data:
                trade_df = pd.DataFrame(self.trade_log_data)
                trade_path = os.path.join(self.directory, 'trade_log.csv')
                try:
                    trade_df.to_csv(trade_path, index=False)
                    print(f"✓ Exported {len(trade_df)} trade records to trade_log.csv")
                    total_files_exported += 1
                except Exception as e:
                    print(f"✗ Error exporting trade log: {e}")

            # Export aggregated data
            for group_key, data_list in self.aggregates_data.items():
                if data_list:
                    agg_df = pd.DataFrame(data_list)
                    agg_path = os.path.join(self.directory, f'{group_key}.csv')
                    try:
                        agg_df.to_csv(agg_path, index=False)
                        print(f"✓ Exported {len(agg_df)} rows to {group_key}.csv")
                        total_files_exported += 1
                    except Exception as e:
                        print(f"✗ Error exporting {group_key}: {e}")

            print(f"\n📊 Export Summary:")
            print(f"   • {total_files_exported} CSV files created")
            print(f"   • All data saved to: {self.directory}")

        except Exception as e:
            print(f"✗ Error in CSV export: {e}")
            import traceback
            traceback.print_exc()

    def finalize(self, data):
        self.in_sok.put('close')
        while self.is_alive():
            time.sleep(0.05)
        self._write_description_file(data)

    def _write_description_file(self, data):
        if self.directory is not None:
            with open(os.path.abspath(self.directory + '/description.txt'), 'w') as description:
                description.write(json.dumps(
                    data,
                    indent=4,
                    skipkeys=True,
                    default=lambda x: 'not_serializeable'))

    def _get_next_versioned_directory(self, directory):
        """
        Find the next available version number for a directory using pattern: basename (1), (2), (3), etc.
        """
        parent_dir = os.path.dirname(directory)
        base_name = os.path.basename(directory)
        
        # Pattern to match numbered versions: "basename (1)", "basename (2)", etc.
        pattern = re.compile(rf'^{re.escape(base_name)} \((\d+)\)$')
        
        highest_version = 0
        
        try:
            # List all items in the parent directory
            for item in os.listdir(parent_dir if parent_dir else '.'):
                match = pattern.match(item)
                if match:
                    version = int(match.group(1))
                    highest_version = max(highest_version, version)
        except OSError:
            # If we can't list the directory, just use version 1
            pass
        
        # Return the next version number
        next_version = highest_version + 1
        return f"{directory} ({next_version})"


class ModernThreadingDatabase(ModernDbDatabase, threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ModernMultiprocessingDatabase(ModernDbDatabase, multiprocessing.Process):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs) 