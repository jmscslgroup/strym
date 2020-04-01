=========
Changelog
=========

0.1.3 - 2020-Apr-01
-----------------
- Bux fix. Refer to commit 9ef1a95

0.1.2 - 2020-Apr-01
-----------------
- A function to resample non-uniformly sampled timeseries to uniformly sampled timeseries data
- A function to differentiate timeseries data based on spline derivative method
- A function to denoise timeseries data based on moving average
- A function to perform temporal-splitting of timeseries dataframe
- A function to return centroid of a phase-space cluster
- A function to calculate average distance of a phase-space cluster from its centroid
- Plotting utility for temporal violin plot
- Can retrieve a timeseries message by given message ID/signal ID or message name/signal name

0.1.1 - 2020-Mar-30
--------------------
- class :code:`strymread`
   - Get the message count
   - Functions to retrieve yaw, acceleration, steer torque, steer rate, steering angle, steering fraction, wheel speeds, longitudinal and laternal measurements from Radar traces
   - Get datarate statistics from CAN data
   - Plot trajectory of driving based on Kinematic model
- timeseries-sync of two timeseries data of different and non-uniform sampling period
- Off-the-shelf integration function for timeseries data
- Function to analyze data rate throughput of a particular message.
- Visualize data distributionb through violin plot

0.1
-----
- Added a new class :code:`strymread`
   - Added basic functionality to Parse CSV-formatted CAN data captured usin comma.ai Panda and Giraffe connector.
   - Plot timeseries data by message name

unreleased
-----------
* Real-time capturing and visualization of CAN data using comma.ai Panda and Giraffe connector.
