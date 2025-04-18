#!/usr/bin/env python3
import subprocess
import re
import time
import signal
import sys
from collections import deque
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import matplotlib
from matplotlib.patches import Rectangle
matplotlib.use('TkAgg')  # Use TkAgg backend which is more compatible


# Set up signal handler for graceful exit
def signal_handler(sig, frame):
    print('\nExiting System Monitor. Goodbye!')
    sys.exit(0)

# Register the signal handler
signal.signal(signal.SIGINT, signal_handler)


class SensorData:
    """Class to handle sensor data collection and parsing"""
    
    def __init__(self):
        self.cpu_temps = {}
        self.fan_speeds = {}
        self.storage_temps = {}
        self.other_temps = {}
        self.max_data_points = 60  # Store 60 data points (1 minute at 1 second intervals)
        
        # Initialize history dictionaries
        self.cpu_temp_history = {}
        self.fan_speed_history = {}
        self.storage_temp_history = {}
        self.other_temp_history = {}
        
        # Maximum fan speeds (will be updated from sensors output)
        self.max_fan_speeds = {}
        
    def update(self):
        """Update all sensor data"""
        try:
            # Run sensors command
            output = subprocess.check_output(['sensors'], universal_newlines=True)
            
            # Parse the output
            self._parse_sensors_output(output)
            
            # Update histories
            self._update_histories()
            
            return True
        except Exception as e:
            print(f"Error updating sensor data: {e}")
            return False
            
    def _parse_sensors_output(self, output):
        """Parse the output of the sensors command"""
        current_adapter = "unknown"
        
        # Clear current data
        self.cpu_temps.clear()
        self.fan_speeds.clear()
        self.storage_temps.clear()
        self.other_temps.clear()
        
        for line in output.splitlines():
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
                
            # Check if this is an adapter line
            if "Adapter:" in line:
                parts = line.split(":", 1)
                if len(parts) > 0:
                    current_adapter = parts[0].strip()
                continue
                
            # Parse temperature data
            if "Core" in line and "°C" in line:
                match = re.search(r'(Core \d+):\s+\+(\d+\.\d+)°C', line)
                if match:
                    core, temp = match.groups()
                    self.cpu_temps[core] = float(temp)
            
            elif "Package id" in line and "°C" in line:
                match = re.search(r'(Package id \d+):\s+\+(\d+\.\d+)°C', line)
                if match:
                    package, temp = match.groups()
                    self.cpu_temps[package] = float(temp)
            
            # Parse fan speed data
            elif "fan" in line.lower() and "RPM" in line:
                # Look for pattern like: fan1:        2125 RPM  (min =    0 RPM, max = 3700 RPM)
                match = re.search(r'(fan\d+):\s+(\d+) RPM\s+(?:\(min\s+=\s+\d+ RPM,\s+max\s+=\s+(\d+) RPM\))?', line)
                if match:
                    fan, speed, max_speed = match.groups()
                    speed = int(speed)
                    self.fan_speeds[fan] = speed
                    
                    # Update max fan speed if available
                    if max_speed:
                        self.max_fan_speeds[fan] = int(max_speed)
                    elif fan not in self.max_fan_speeds:
                        # Default max speed if not specified
                        self.max_fan_speeds[fan] = 4000
            
            # Parse storage temperature
            elif current_adapter and "nvme" in current_adapter.lower() and "Composite" in line and "°C" in line:
                match = re.search(r'Composite:\s+\+(\d+\.\d+)°C', line)
                if match:
                    temp = match.group(1)
                    self.storage_temps["NVMe"] = float(temp)
            
            # Parse other temperatures
            elif "temp" in line.lower() and "°C" in line and "Core" not in line and "Package" not in line:
                match = re.search(r'(temp\d+):\s+\+(\d+\.\d+)°C', line)
                if match:
                    sensor, temp = match.groups()
                    self.other_temps[f"{current_adapter}_{sensor}"] = float(temp)
    
    def _update_histories(self):
        """Update the history deques for all sensors"""
        # Update CPU temperature histories
        for core, temp in self.cpu_temps.items():
            if core not in self.cpu_temp_history:
                self.cpu_temp_history[core] = deque(maxlen=self.max_data_points)
            self.cpu_temp_history[core].append(temp)
        
        # Update fan speed histories
        for fan, speed in self.fan_speeds.items():
            if fan not in self.fan_speed_history:
                self.fan_speed_history[fan] = deque(maxlen=self.max_data_points)
            self.fan_speed_history[fan].append(speed)
        
        # Update storage temperature histories
        for storage, temp in self.storage_temps.items():
            if storage not in self.storage_temp_history:
                self.storage_temp_history[storage] = deque(maxlen=self.max_data_points)
            self.storage_temp_history[storage].append(temp)
        
        # Update other temperature histories
        for sensor, temp in self.other_temps.items():
            if sensor not in self.other_temp_history:
                self.other_temp_history[sensor] = deque(maxlen=self.max_data_points)
            self.other_temp_history[sensor].append(temp)


class SystemMonitor:
    """Main system monitor class"""
    
    def __init__(self):
        self.sensor_data = SensorData()
        
        # Create figure with subplots
        plt.style.use('dark_background')
        self.fig, self.axes = plt.subplots(2, 2, figsize=(12, 8))
        self.fig.suptitle('System Sensor Monitor', fontsize=16)
        
        # Flatten axes for easier access
        self.axes = self.axes.flatten()
        
        # Set up subplots
        self.cpu_ax = self.axes[0]
        self.fan_ax = self.axes[1]
        self.storage_ax = self.axes[2]
        self.other_ax = self.axes[3]
        
        # Set titles and labels
        self.cpu_ax.set_title('CPU Temperature')
        self.cpu_ax.set_ylabel('Temperature (°C)')
        self.cpu_ax.set_ylim(30, 100)
        self.cpu_ax.grid(True, linestyle='--', alpha=0.7)
        
        self.fan_ax.set_title('Fan Speeds')
        self.fan_ax.set_ylabel('Speed (%)')
        self.fan_ax.set_ylim(0, 100)
        self.fan_ax.grid(True, linestyle='--', alpha=0.7)
        
        self.storage_ax.set_title('Storage Temperature')
        self.storage_ax.set_ylabel('Temperature (°C)')
        self.storage_ax.set_ylim(20, 80)
        self.storage_ax.grid(True, linestyle='--', alpha=0.7)
        
        self.other_ax.set_title('Other Temperatures')
        self.other_ax.set_ylabel('Temperature (°C)')
        self.other_ax.set_ylim(20, 80)
        self.other_ax.grid(True, linestyle='--', alpha=0.7)
        
        # Set common x-axis properties
        for ax in self.axes:
            ax.set_xlabel('Time (s)')
            ax.set_xlim(0, 60)
        
        # Dictionary to store line objects
        self.cpu_lines = {}
        self.storage_lines = {}
        self.other_lines = {}
        
        # Fan speed visualization elements
        self.fan_boxes = {}
        self.fan_texts = {}
        
        # Initial update to get data
        self.sensor_data.update()
        
        # Create animation
        self.ani = FuncAnimation(
            self.fig, self.update, interval=1000, 
            blit=False, cache_frame_data=False
        )
        
        # Adjust layout
        plt.tight_layout()
        self.fig.subplots_adjust(top=0.9)
        
    def update(self, frame):
        """Update function for animation"""
        # Update sensor data
        self.sensor_data.update()
        
        # Update CPU temperature plot
        self._update_plot(
            self.cpu_ax, 
            self.cpu_lines, 
            self.sensor_data.cpu_temp_history, 
            'temperature'
        )
        
        # Update fan speed indicators
        self._update_fan_indicators()
        
        # Update storage temperature plot
        self._update_plot(
            self.storage_ax, 
            self.storage_lines, 
            self.sensor_data.storage_temp_history, 
            'temperature'
        )
        
        # Update other temperature plot
        self._update_plot(
            self.other_ax, 
            self.other_lines, 
            self.sensor_data.other_temp_history, 
            'temperature'
        )
        
        # Add timestamp
        plt.figtext(
            0.5, 0.01, 
            f'Last update: {time.strftime("%H:%M:%S")}', 
            ha='center'
        )
        
        return self.axes
    
    def _update_fan_indicators(self):
        """Update the fan speed box indicators"""
        # Clear the plot if needed
        if set(self.fan_boxes.keys()) != set(self.sensor_data.fan_speeds.keys()):
            self.fan_ax.clear()
            self.fan_boxes.clear()
            self.fan_texts.clear()
            
            # Reset title and labels
            self.fan_ax.set_title('Fan Speeds')
            self.fan_ax.set_ylabel('Speed (%)')
            self.fan_ax.set_ylim(0, 100)
            self.fan_ax.set_xlim(0, 1)
            self.fan_ax.grid(False)
            
            # Remove x-axis ticks and labels
            self.fan_ax.set_xticks([])
        
        # If no fan data, return
        if not self.sensor_data.fan_speeds:
            return
            
        # Calculate positions for fan boxes
        num_fans = len(self.sensor_data.fan_speeds)
        box_width = 0.8 / num_fans
        margin = 0.1
        
        # Update or create each fan indicator
        for i, (fan, speed) in enumerate(self.sensor_data.fan_speeds.items()):
            # Calculate percentage of max speed
            max_speed = self.sensor_data.max_fan_speeds.get(fan, 4000)
            percentage = min(100, (speed / max_speed) * 100)
            
            # Calculate box position
            x_pos = margin + i * box_width
            
            # Create or update box
            if fan in self.fan_boxes:
                # Update existing box
                self.fan_boxes[fan].set_height(percentage)
                self.fan_texts[fan].set_text(f"{fan}: {speed} RPM\n({percentage:.1f}%)")
            else:
                # Create new box
                box = Rectangle(
                    (x_pos, 0), box_width * 0.8, percentage,
                    facecolor=plt.cm.tab10.colors[i % 10],
                    edgecolor='white',
                    alpha=0.8
                )
                self.fan_ax.add_patch(box)
                self.fan_boxes[fan] = box
                
                # Add text label
                text = self.fan_ax.text(
                    x_pos + box_width * 0.4, 105,
                    f"{fan}: {speed} RPM\n({percentage:.1f}%)",
                    ha='center', va='bottom',
                    fontsize=9
                )
                self.fan_texts[fan] = text
    
    def _update_plot(self, ax, lines_dict, data_dict, data_type):
        """Update a specific plot with new data"""
        # If no data, skip updating
        if not data_dict:
            return
            
        # Clear the plot if the data keys have changed
        if set(lines_dict.keys()) != set(data_dict.keys()):
            ax.clear()
            lines_dict.clear()
            
            # Reset title and labels
            if data_type == 'temperature':
                ax.set_ylabel('Temperature (°C)')
                if 'CPU' in ax.get_title():
                    ax.set_ylim(30, 100)
                else:
                    ax.set_ylim(20, 80)
            
            ax.set_title(ax.get_title())
            ax.set_xlabel('Time (s)')
            ax.set_xlim(0, 60)
            ax.grid(True, linestyle='--', alpha=0.7)
        
        # Create a color cycle
        colors = plt.cm.tab10.colors
        
        # X-axis data (time)
        x_data = np.arange(60)
        
        # Update or create each line
        for i, (key, data_queue) in enumerate(data_dict.items()):
            data = list(data_queue)
            
            # Pad data if less than max length
            if len(data) < 60:
                data = [data[0]] * (60 - len(data)) + data
            
            # Get the color for this line
            color = colors[i % len(colors)]
            
            if key in lines_dict:
                # Update existing line
                lines_dict[key].set_ydata(data)
            else:
                # Create new line
                line, = ax.plot(x_data, data, label=key, linewidth=2, color=color)
                lines_dict[key] = line
        
        # Update legend if there are lines
        if lines_dict:
            ax.legend(loc='upper left', fontsize='small')
    
    def run(self):
        """Run the monitor"""
        plt.show()


if __name__ == '__main__':
    print("Starting System Monitor. Press Ctrl+C to exit.")
    monitor = SystemMonitor()
    monitor.run()
