# battery_control_model
This code implements a rules-based battery control model and produces an interface using Bokeh, an interactive data visualization library for Python.
This battery system provides support to an electric vehicle (EV) charging station, enabling an increased number of cars to charge simultaneously.

In this code, each car is assumed to consume 11 kW, and the charging station has a capacity of 88 kW.

Features
-User Input Interface: The Bokeh interface allows users to input the battery's maximum capacity, its efficiency, and the number of cars at the charging station.
-State of Charge Visualization: Users can observe the state of charge (SOC) of the battery over the first 6 hours through a bar chart. This chart uses electricity prices for the following day, fetched via the ENTSO-E API, ensuring the battery charges fully during the cheapest hours within this interval.
-Battery Behavior Simulation: By adjusting the inputs, users can test the charging and discharging logic rules and see the battery's behavior in the remaining hours on a separate graph.
-Power Assurance Display: The interface also visualizes the power supplied by the grid, the power provided by the battery, and the total power, which is the sum of the grid and battery power.

Installation
To run this project, ensure you have Python (preferably through Anaconda) and the necessary dependencies installed. Follow these steps:

Clone the Repository:
git clone https://github.com/JoaoRibeiro197/battery_control_model.git
cd battery_control_model

Install Required Packages:
pip install bokeh
pip install requests

Usage
Run the Bokeh Server:
bokeh serve --show InterfaceBOKEHfinal2.py

Configuration
Battery Parameters: Configure the battery's maximum capacity and efficiency through the interface.
Number of Cars: Specify the number of cars at the charging station to simulate different scenarios.

License
This project is licensed under the MIT License. See the LICENSE file for more details.

Contact
For any questions or feedback, feel free to reach out via email at jpsribeiro2003@gmail.com.
