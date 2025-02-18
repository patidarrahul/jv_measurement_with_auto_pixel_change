import csv
import os
import sys
import pyvisa
import numpy as np
import time
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QGridLayout, QCheckBox, QSizePolicy,
    QPushButton, QLineEdit, QLabel, QComboBox, QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import serial
import time
import serial.tools.list_ports

# Configure the Arduino serial connection
baud_rate = 9600




# Function to control a relay




class KeithleyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
       
        self.arduino = None
        self.rm = pyvisa.ResourceManager()
        self.keithley = None
        self.is_measuring = False
        self.measurement_count = 0
        
        self.data_directory = ""  # To store the selected data directory

    def initUI(self):
        self.setWindowTitle("Keithley JV Measurement")

        # Central widget
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        # Main layout
        main_layout = QHBoxLayout()

        # Left layout (Inputs and plot)
        left_layout = QVBoxLayout()

        # Arduino connection layout
        arduino_layout = QHBoxLayout()

        # Arduino port selection
        arduino_label = QLabel("Arduino Port:")
        arduino_layout.addWidget(arduino_label)

        self.arduino_port_combo = QComboBox(self)
        self.arduino_port_combo.addItems(self.get_available_ports())  # Populate with available ports
        self.arduino_port_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  # Make dropdown fill the space
        arduino_layout.addWidget(self.arduino_port_combo)

        # Arduino connect button
        self.connect_button = QPushButton("Connect to Arduino", self)
        self.connect_button.clicked.connect(self.connect_to_arduino)
        arduino_layout.addWidget(self.connect_button)

        # Add Arduino layout to the top of the left layout
        left_layout.addLayout(arduino_layout)


        # Data directory layout
        data_directory_layout = QHBoxLayout()

        # Data directory selection button
        self.select_directory_button = QPushButton("Select Data Directory", self)
        self.select_directory_button.clicked.connect(self.select_directory)
        data_directory_layout.addWidget(self.select_directory_button)

        # Data directory display field
        self.data_directory_display = QLineEdit(self)
        self.data_directory_display.setReadOnly(True)  # Make it read-only
        data_directory_layout.addWidget(self.data_directory_display)

        left_layout.addLayout(data_directory_layout)

        # Use a grid layout to arrange settings in two columns
        settings_layout = QGridLayout()

        # Column 1, Row 0
        settings_layout.addWidget(QLabel("Device Name:"), 0, 0)
        self.device_name_input = QLineEdit(self)
        settings_layout.addWidget(self.device_name_input, 0, 1)

        # Column 1, Row 1
        settings_layout.addWidget(QLabel("Voltage Min (V):"), 1, 0)
        self.voltage_min_input = QLineEdit(self)
        self.voltage_min_input.setText("-0.1")
        settings_layout.addWidget(self.voltage_min_input, 1, 1)

        # Column 1, Row 2
        settings_layout.addWidget(QLabel("Voltage Max (V):"), 2, 0)
        self.voltage_max_input = QLineEdit(self)
        self.voltage_max_input.setText("1.2")
        settings_layout.addWidget(self.voltage_max_input, 2, 1)

        # Column 1, Row 3
        settings_layout.addWidget(QLabel("Sweep Rate (mV/sec):"), 3, 0)
        self.sweep_rate_input = QLineEdit(self)
        self.sweep_rate_input.setText("100")
        settings_layout.addWidget(self.sweep_rate_input, 3, 1)

        # Column 1, Row 4
        settings_layout.addWidget(QLabel("Step Size (V):"), 4, 0)
        self.step_size_input = QLineEdit(self)
        self.step_size_input.setText("0.01")  # Default step size
        settings_layout.addWidget(self.step_size_input, 4, 1)

        # Column 2, Row 0
        settings_layout.addWidget(QLabel("Area (cm²):"), 0, 2)
        self.area_input = QLineEdit(self)
        self.area_input.setText("0.09")
        settings_layout.addWidget(self.area_input, 0, 3)

        # Column 2, Row 1
        settings_layout.addWidget(QLabel("Scan Direction:"), 1, 2)
        self.scan_direction_combo = QComboBox(self)
        self.scan_direction_combo.addItems(["Forward", "Reverse", "Both"])
        self.scan_direction_combo.setCurrentIndex(2)
        settings_layout.addWidget(self.scan_direction_combo, 1, 3)

        # Column 2, Row 2
        settings_layout.addWidget(QLabel("Pixel From:"), 2, 2)
        self.pixel_from_input = QLineEdit(self)
        self.pixel_from_input.setText("1")  # Default value
        settings_layout.addWidget(self.pixel_from_input, 2, 3)

        # Column 2, Row 3
        settings_layout.addWidget(QLabel("Pixel To:"), 3, 2)
        self.pixel_to_input = QLineEdit(self)
        self.pixel_to_input.setText("3")  # Default value
        settings_layout.addWidget(self.pixel_to_input, 3, 3)

        # Column 2, Row 4
        settings_layout.addWidget(QLabel("Pre-Sweep Delay (s):"), 4, 2)
        self.pre_sweep_delay_input = QLineEdit(self)
        self.pre_sweep_delay_input.setText("5")  # Default pre-sweep delay (in seconds)
        settings_layout.addWidget(self.pre_sweep_delay_input, 4, 3)

        # Column 2, Row 5 (or next available row)
        settings_layout.addWidget(QLabel("Dark Measurement:"), 5, 2)
        self.dark_measurement_checkbox = QCheckBox(self)
        settings_layout.addWidget(self.dark_measurement_checkbox, 5, 3)





        # Add the settings_layout to the left_layout
        left_layout.addLayout(settings_layout)

        # Start button
        self.start_button = QPushButton("Start Measurement", self)
        self.start_button.clicked.connect(self.measure_in_loop)
        left_layout.addWidget(self.start_button)

        # Stop button (with red background)
        self.stop_button = QPushButton("Stop Measurement", self)
        self.stop_button.clicked.connect(self.stop_measurement)
        self.stop_button.setStyleSheet("background-color: red; color: white;")
        left_layout.addWidget(self.stop_button)

        # Plot area
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        left_layout.addWidget(self.canvas)

        # Right layout (Table for performance metrics)
        right_layout = QVBoxLayout()

        self.table_widget = QTableWidget(self)
        self.table_widget.setColumnCount(8)
        self.table_widget.setHorizontalHeaderLabels(
            ["Measurement #", "File Name", "Pixel Number", "Scan Direction", "Jsc (mA/cm²)", "Voc (V)", "FF", "PCE (%)"])

        right_layout.addWidget(self.table_widget)

        # Add the export button after the table widget in the right layout
        self.export_button = QPushButton("Export to CSV", self)
        self.export_button.clicked.connect(self.export_table_to_csv)
        right_layout.addWidget(self.export_button)

        # Combine left and right layouts
        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)

        self.central_widget.setLayout(main_layout)


    def control_relay(self, relay_number, state):
        command = f'{relay_number} {state}\n'  # Create the command string
        self.arduino.write(command.encode())  # Send the command to the Arduino
        time.sleep(0.5)  # Wait a bit for the Arduino to process
    def select_directory(self):
        # Open a dialog to select a directory
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.data_directory = directory
            self.data_directory_display.setText(directory)  # Update the display field
            print(f"Data will be saved to: {self.data_directory}")

    def measure_in_loop(self):
    
        

        # Check if the Arduino connection is still open
        if not self.arduino:
            QMessageBox.warning(self, "Error", f"Arduino is not connected. Please check the connection and try again.")
            return
        # Check if the necessary fields are filled out
        if not all([self.data_directory, self.device_name_input.text(), self.scan_direction_combo.currentText(), 
                    self.area_input.text(), self.sweep_rate_input.text(), self.voltage_min_input.text(), self.voltage_max_input.text()]):
            QMessageBox.warning(self, "Error", "All Fields are required")
            return


        # Turn on relays
        pixel_from = int(self.pixel_from_input.text())
        pixel_to = int(self.pixel_to_input.text())

        # validation
        if pixel_from < 1 or pixel_to > 8 or pixel_from > pixel_to:
            QMessageBox.warning(self, "Error", "Please enter valid Pixel From and Pixel To values.")
            return


        for i in range(pixel_from - 1, pixel_to):  # Adjusted to use the pixel range

           self.control_relay(i, 1)  # Turn on relay i
           self.start_measurement(pixel_number=i+1)
           self.control_relay(i, 0)  # Turn off relay i
           time.sleep(1)



    def start_measurement(self, pixel_number):
        # Initialize the Keithley connection and start the measurement process
        self.is_measuring = True
        
        # Get device name
        device_name = self.device_name_input.text()
        
        # Reading user inputs
        voltage_min = float(self.voltage_min_input.text())
        voltage_max = float(self.voltage_max_input.text())
        area = float(self.area_input.text())
        sweep_rate = float(self.sweep_rate_input.text()) / 1000  # Sweep rate in V/s
        step_size = float(self.step_size_input.text())  # Step size in Volts
        scan_direction = self.scan_direction_combo.currentText()
        pre_sweep_delay = float(self.pre_sweep_delay_input.text())  # Pre-sweep delay in seconds
        is_dark_measurement = self.dark_measurement_checkbox.isChecked()  # Check if dark measurement



        self.keithley = self.rm.open_resource('GPIB::24::INSTR')
        self.keithley.write("*RST")  # Reset Keithley
        self.keithley.write(':ROUT:TERM REAR')  # Set to use back terminals
        



        self.keithley.write(":SOUR:FUNC VOLT")
        self.keithley.write(":SENS:FUNC 'CURR'")
        self.keithley.write(':SENS:CURR:PROT .10')  # Set current range to auto

        # Prepare for measurement
        self.keithley.write(":OUTP ON")


        # Clear previous plot
        self.ax.clear()


        voltage_range = voltage_max - voltage_min
        total_time = voltage_range / sweep_rate  # Total time in seconds
        num_points = int(voltage_range / step_size) + 1  # Number of points
        # Calculate the actual time per step
        time_per_step = total_time / (num_points - 1)

        # Check if dark measurement
        if not is_dark_measurement:
            # Turn on the solar simulator if not a dark measurement
            self.keithley.write(':SOUR2:TTL 0')
            # Pre-sweep delay
            time.sleep(pre_sweep_delay)  # Delay before starting the measurement

        # Perform measurement
        if scan_direction in ["Forward"]:
            voltages = np.arange(voltage_min, voltage_max, step_size)
            currents = []
            for v in voltages:
                if not self.is_measuring:
                    break
                self.keithley.write(f":SOUR:VOLT {v}")
                time.sleep(time_per_step) 
                
                # Properly parse the response
                response = self.keithley.query(":READ?")
                values = response.split(',')
                try:
                    current = float(values[1])  # Adjust index based on Keithley's return format
                    current_density = current/area
                    currents.append(current_density)
                except (ValueError, IndexError) as e:
                    print(f"Error parsing response: {e}")
                    currents.append(0)

                # Ensure voltages and currents arrays match in length
                if len(currents) > len(voltages):
                    currents.pop()  # Remove the last entry if lengths don't match

                # Update plot
                self.ax.plot(voltages[:len(currents)], currents, 'b-')
                self.canvas.draw()
                
                # Process events to update the UI
                QApplication.processEvents()

            # Calculate performance metrics
            jsc = self.calculate_jsc(voltages, currents, area)
            voc = self.calculate_voc(voltages, currents)
            ff = self.calculate_ff(voltages, currents, voc, jsc)
            pce = self.calculate_pce(jsc, voc, ff)

            # Update table with the new measurement
            self.update_table(device_name, pixel_number, scan_direction, jsc, voc, ff, pce)

            # store the data
            if is_dark_measurement == False:
                file_name = f"{device_name}_Pixel_{pixel_number}_FWD.txt"
            else:
                file_name = f"{device_name}_Pixel_{pixel_number}_FWD_DARK.txt"
            file_path = os.path.join(self.data_directory, file_name)

            with open(file_path, 'w') as f:
                # Write performance parameters at the top
                f.write(f"Dark Measurement: {is_dark_measurement}\n")
                f.write(f"Device Name: {device_name}\n")
                f.write(f"Pixel: {pixel_number}\n")
                f.write(f"Jsc (mA/cm²): {jsc:.2f}\n")
                f.write(f"Voc (V): {voc:.2f}\n")
                f.write(f"FF: {ff:.2f}\n")
                f.write(f"PCE (%): {pce:.2f}\n\n")

                # Write column headers
                f.write("Voltage (V)\tCurrent (A)\n")

                # Write voltage and current data
                for v, c in zip(voltages, currents):
                    f.write(f"{v:.6f}\t{c:.6e}\n")



        elif scan_direction in ["Reverse"]:
            voltages = np.arange(voltage_max, voltage_min, -step_size)
            currents = []
           
            for v in voltages:
                if not self.is_measuring:
                    break
                self.keithley.write(f":SOUR:VOLT {v}")
                time.sleep(time_per_step)
                
                response = self.keithley.query(":READ?")
                values = response.split(',')
                try:
                    current = float(values[1])
                    current_density = current/area
                    currents.append(current_density)
                except (ValueError, IndexError) as e:
                    print(f"Error parsing response: {e}")
                    currents.append(0)

                # Ensure voltages and currents arrays match in length
                if len(currents) > len(voltages):
                    currents.pop()  # Remove the last entry if lengths don't match

                # Update plot
                self.ax.plot(voltages[:len(currents)], currents, 'r-')
                self.canvas.draw()

                # Process events to update the UI
                QApplication.processEvents()


            # Calculate performance metrics
            jsc = self.calculate_jsc(voltages, currents, area)
            voc = self.calculate_voc(voltages, currents)
            ff = self.calculate_ff(voltages, currents, voc, jsc)
            pce = self.calculate_pce(jsc, voc, ff)

            # Update table with the new measurement
            self.update_table(device_name, pixel_number, scan_direction, jsc, voc, ff, pce)

            # store the data
            device_name = self.device_name_input.text()
            if is_dark_measurement == False:
                file_name = f"{device_name}_Pixel_{pixel_number}_RS.txt"
            else:
                file_name = f"{device_name}_Pixel_{pixel_number}_RS_DARK.txt"
            file_path = os.path.join(self.data_directory, file_name)

            with open(file_path, 'w') as f:
                # Write performance parameters at the top
                f.write(f"Dark Measurement: {is_dark_measurement}\n")
                f.write(f"Device Name: {device_name}\n")
                f.write(f"Pixel: {pixel_number}\n")
                f.write(f"Jsc (mA/cm²): {jsc:.2f}\n")
                f.write(f"Voc (V): {voc:.2f}\n")
                f.write(f"FF: {ff:.2f}\n")
                f.write(f"PCE (%): {pce:.2f}\n\n")

                # Write column headers
                f.write("Voltage (V)\tCurrent (A)\n")

                # Write voltage and current data
                for v, c in zip(voltages, currents):
                    f.write(f"{v:.6f}\t{c:.6e}\n")
        elif scan_direction in ["Both"]:

            # Forward Scan
            forward_currents = []
            forward_voltages = np.arange(voltage_min, voltage_max, step_size)
        
            for v in forward_voltages:
                if not self.is_measuring:
                    break
                self.keithley.write(f":SOUR:VOLT {v}")
                time.sleep(time_per_step) 
                
                # Properly parse the response
                response = self.keithley.query(":READ?")
                values = response.split(',')
                try:
                    current = float(values[1])  # Adjust index based on Keithley's return format
                    current_density = current/area
                    forward_currents.append(current_density)
                except (ValueError, IndexError) as e:
                    print(f"Error parsing response: {e}")
                    forward_currents.append(0)

                # Update plot
                self.ax.plot(forward_voltages[:len(forward_currents)], forward_currents, 'b-')
                self.canvas.draw()
                
                # Process events to update the UI
                QApplication.processEvents()
            
            # Calculate performance metrics
            jsc = self.calculate_jsc(forward_voltages, forward_currents, area)
            voc = self.calculate_voc(forward_voltages, forward_currents)
            ff = self.calculate_ff(forward_voltages, forward_currents, voc, jsc)
            pce = self.calculate_pce(jsc, voc, ff)

            
            # Update table with the new measurement
            scan_direction = "Forward"
            self.update_table(device_name, pixel_number, scan_direction, jsc, voc, ff, pce)

            # store the data
            device_name = self.device_name_input.text()
            if is_dark_measurement == False:
                file_name = f"{device_name}_Pixel_{pixel_number}_FWD.txt"
            else:
                file_name = f"{device_name}_Pixel_{pixel_number}_FWD_DARK.txt"
            file_path = os.path.join(self.data_directory, file_name)

            with open(file_path, 'w') as f:
                # Write performance parameters at the top
                f.write(f"Dark Measurement: {is_dark_measurement}\n")
                f.write(f"Device Name: {device_name}\n")
                f.write(f"Pixel: {pixel_number}\n")
                f.write(f"Jsc (mA/cm²): {jsc:.2f}\n")
                f.write(f"Voc (V): {voc:.2f}\n")
                f.write(f"FF: {ff:.2f}\n")
                f.write(f"PCE (%): {pce:.2f}\n\n")

                # Write column headers
                f.write("Voltage (V)\tCurrent (A)\n")

                # Write voltage and current data
                for v, c in zip(forward_voltages, forward_currents):
                    f.write(f"{v:.6f}\t{c:.6e}\n")

            # Reverse Scan
            reverse_currents = []
            reverse_voltages = np.arange(voltage_max, voltage_min, -step_size)
            for v in reverse_voltages:
                if not self.is_measuring:
                    break
                self.keithley.write(f":SOUR:VOLT {v}")
                time.sleep(time_per_step)  # Use 1 second delay or sweep_rate if preferred
                
                response = self.keithley.query(":READ?")
                values = response.split(',')
                try:
                    current = float(values[1])
                    current_density = current/area
                    reverse_currents.append(current_density)
                except (ValueError, IndexError) as e:
                    print(f"Error parsing response: {e}")
                    reverse_currents.append(0)

                # Update plot
                self.ax.plot(list(reverse_voltages)[:len(reverse_currents)], reverse_currents, 'r-')
                self.canvas.draw()

                # Process events to update the UI
                QApplication.processEvents()


            # Calculate performance metrics
            jsc = self.calculate_jsc(reverse_voltages, reverse_currents, area)
            voc = self.calculate_voc(reverse_voltages, reverse_currents)
            ff = self.calculate_ff(reverse_voltages, reverse_currents, voc, jsc)
            pce = self.calculate_pce(jsc, voc, ff)

            
            # Update table with the new measurement
            scan_direction = "Reverse"
            self.update_table(device_name, pixel_number, scan_direction, jsc, voc, ff, pce)

            # store the data
            device_name = self.device_name_input.text()
            if is_dark_measurement == False:
                file_name = f"{device_name}_Pixel_{pixel_number}_REV.txt"   
            else:
                file_name = f"{device_name}_Pixel_{pixel_number}_RS_DARK.txt"

            file_path = os.path.join(self.data_directory, file_name)

            with open(file_path, 'w') as f:
                # Write performance parameters at the top
                f.write(f"Dark Measurement: {is_dark_measurement}\n")
                f.write(f"Device Name: {device_name}\n")
                f.write(f"Pixel: {pixel_number}\n")
                f.write(f"Jsc (mA/cm²): {jsc:.2f}\n")
                f.write(f"Voc (V): {voc:.2f}\n")
                f.write(f"FF: {ff:.2f}\n")
                f.write(f"PCE (%): {pce:.2f}\n\n")

                # Write column headers
                f.write("Voltage (V)\tCurrent (A)\n")

                # Write voltage and current data
                for v, c in zip(reverse_voltages, reverse_currents):
                    f.write(f"{v:.6f}\t{c:.6e}\n")


        self.keithley.write(':SOUR2:TTL 1') # Turn off the solar simulator 
        self.keithley.write(":OUTP OFF")


    def calculate_jsc(self, voltages, currents, area):
        jsc = max(currents) / area * 1000  # Convert to mA/cm²
        return jsc

    def calculate_voc(self, voltages, currents):
        for i in range(len(currents) - 1):
            if currents[i] > 0 and currents[i + 1] < 0:
                voc = voltages[i]
                return voc
        return 0

    def calculate_ff(self, voltages, currents, voc, jsc):
        if voc == 0 or jsc == 0:
            ff = 0  # Avoid division by zero
        else:
            p_max = max(np.array(voltages) * np.array(currents))
            ff = p_max / (voc * jsc)
        return ff

    def calculate_pce(self, jsc, voc, ff):
        if jsc == 0 or voc == 0 or ff == 0:
            pce = 0  # Avoid invalid multiplication
        else:
            pce = (jsc * voc * ff) / 10  # Convert to %
        return pce

    def update_table(self, device_name, pixel_number, scan_direction, jsc, voc, ff, pce):
        self.measurement_count += 1
        row_position = self.table_widget.rowCount()
        self.table_widget.insertRow(row_position)

        self.table_widget.setItem(row_position, 0, QTableWidgetItem(str(self.measurement_count)))
        self.table_widget.setItem(row_position, 1, QTableWidgetItem(device_name))
        self.table_widget.setItem(row_position, 2, QTableWidgetItem(str(pixel_number)))
        self.table_widget.setItem(row_position, 3, QTableWidgetItem(scan_direction))
        self.table_widget.setItem(row_position, 4, QTableWidgetItem(f"{jsc:.2f}"))
        self.table_widget.setItem(row_position, 5, QTableWidgetItem(f"{voc:.2f}"))
        self.table_widget.setItem(row_position, 6, QTableWidgetItem(f"{ff:.2f}"))
        self.table_widget.setItem(row_position, 7, QTableWidgetItem(f"{pce:.2f}"))

        
    def export_table_to_csv(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv);;All Files (*)", options=options)
        if file_path:
            with open(file_path, 'w', newline='') as file:
                writer = csv.writer(file)
                # Write the headers
                headers = [self.table_widget.horizontalHeaderItem(i).text() for i in range(self.table_widget.columnCount())]
                writer.writerow(headers)

                # Write the data rows
                for row in range(self.table_widget.rowCount()):
                    row_data = []
                    for column in range(self.table_widget.columnCount()):
                        item = self.table_widget.item(row, column)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            print(f"Table data exported to {file_path}")


    def stop_measurement(self):
        self.is_measuring = False
        if self.keithley:
            try:
                self.keithley.write(":OUTPUT OFF")  # Disable the output
                self.keithley.write(':SOUR2:TTL 1')  # Turn off the solar simulator
            except Exception as e:
                print(f"Error stopping the measurement: {e}")
    
    def get_available_ports(self):
        ports = serial.tools.list_ports.comports()
        ports = ['COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9']
        return ports

    def connect_to_arduino(self):
        # Configure the Arduino serial connection
        selected_port = self.arduino_port_combo.currentText()
        
        try:

            # what if arduio is connected to a port
            if self.arduino:
                QMessageBox.warning(self, "Error", f"Arduino is already connected!")
            else:
                self.arduino = serial.Serial(selected_port, baud_rate, timeout=1)
                QMessageBox.information(self, "Connection Successful", f"Connected to Arduino on {selected_port}")
        except serial.SerialException as e:
            QMessageBox.warning(self, "Connection Failed", f"Could not open {selected_port}. Error: {str(e)}")


    def closeEvent(self, event):
        self.stop_measurement()
        self.arduino.close()
        if self.keithley:
            self.keithley.close()
        super().closeEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = KeithleyApp()
    ex.show()
    sys.exit(app.exec_())
