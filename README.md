# Keithley JV Measurement Application

A GUI application for current-voltage (JV) characterization of solar cells using Keithley instruments and Arduino relay control.

(image.png)

## Features

- **Arduino Integration**: Controls up to 8 relays for multi-pixel measurements
- **Keithley Communication**: Interfaces with Keithley 2400 series Source Measure Units (SMUs)
- **Data Visualization**: Real-time plotting of J-V curves
- **Parameter Configuration**:
  - Voltage range and sweep settings
  - Device area input
  - Scan direction (Forward/Reverse/Both)
  - Dark measurement capability
- **Data Export**:
  - Automatic saving of raw J-V data
  - Performance metrics table (Jsc, Voc, FF, PCE)
  - CSV export of results

## Installation

1. **Install Requirements**:

   ```bash
   pip install -r requirements.txt
   ```

2. Dependencies:
   NI-VISA drivers (for Keithley communication)
   Arduino IDE (for relay control firmware)

3. Hardware Setup:
   Connect Keithley via GPIB-USB interface
   Connect Arduino with relay board
   Configure solar simulator trigger (if used)

## Usage

1. Connection Setup:
   Select Arduino COM port and click "Connect"
   Choose data directory for saving results

2. Measurement Parameters:
   Voltage Range: -0.1V to 1.2V (default)
   Sweep Rate: 100 mV/s (default)
   Pixel Range: 1-8 (customizable)

3. Operation:
   Enter device name and parameters
   Select scan direction and measurement type
   Start/Stop measurements using dedicated buttons
   Export results to CSV when complete

### Notes

    Requires proper GPIB address configuration for Keithley
    Arduino relay control code must be loaded separately
    Dark measurements disable solar simulator trigger
    Supports both forward and reverse J-V scans
