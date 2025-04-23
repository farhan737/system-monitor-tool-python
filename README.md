# System Sensor Monitor

A real-time system monitoring application that visualizes hardware sensor data with interactive graphs. **This application is designed for Linux systems only.**

## Features

- Real-time monitoring of CPU temperatures
- Fan speed tracking with percentage indicators
- Storage temperature monitoring
- Other system temperature sensors visualization
- Dark theme UI with responsive graphs
- Automatic data collection and parsing from system sensors
- Run with a simple command from anywhere in your terminal
- Graceful exit with Ctrl+C

## Requirements

- Linux operating system
- Python 3.6+
- `lm-sensors` package installed on your system
- Matplotlib
- NumPy
- Tkinter (for the graphical interface)

## Installation

1. Make sure you have the `lm-sensors` package installed:
   ```
   sudo apt-get install lm-sensors
   ```

2. Install Tkinter if you don't have it already:
   ```
   sudo apt-get install python3-tk
   ```

3. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up the `sysmon` command for easy access:
   ```
   # Make the scripts executable
   chmod +x system_monitor.py
   chmod +x sysmon
   
   # Create a bin directory in your home folder (if it doesn't exist)
   mkdir -p ~/bin
   
   # Copy the sysmon script to your bin directory
   cp sysmon ~/bin/
   
   # Add ~/bin to your PATH (if not already there)
   echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
   
   # Reload your shell configuration
   source ~/.bashrc
   ```

## Usage

Run the application with:
```
sysmon
```

Or directly with:
```
python3 system_monitor.py
```

The application will display real-time graphs of your system's sensor data, updated every second.

To exit the application, press `Ctrl+C` in the terminal.

## Tabs

- **CPU**: Shows temperature data for all CPU cores and package
- **Fans**: Displays fan speed as percentage bars with RPM values
- **Storage**: Shows NVMe and other storage device temperatures
- **Other**: Displays other system temperature sensors
