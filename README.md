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
