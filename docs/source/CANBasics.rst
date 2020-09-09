CAN for Vehicle Diagnostics and Beyond
=======================================================================
The controller area network is a serial communication protocol developed by Bosch and unveiled in 1986 at a Society of automotive Engineers (SAE) conference. It was developed within the automotive sector to allow several electronic control units on a vehicle to share important control data. An ECU prepares and broadcasts data targeted for a particular unit within the vehicle on-board network. Each unit receives the broadcasted message and check for acceptance and then decides whether to honor the message or reject them. Each message has a particular identifier that decides its priority and significance. Some are based on industry-wide standards while others are proprietary. A standard CAN message looks like as follows

.. image:: https://raw.githubusercontent.com/jmscslgroup/strym/master/docs/source/can_bus_diagram.io.png


In our hardware/software ecosystem consisting of libpanda_ and strym, libpanda captures the CAN messages and stores as CSV file where each rows consists of Message ID, Bus ID, Message Length, and CAN message in Hex format. Each hex message may consist of multiple signals, for example on Message ID 37, we might get two signals: yaw rate and acceleration. The recipe to decode hex messages into identifiable signals is included in DBC file conforming to a particular vehicle's make and model.




DBC File
---------

DBC file consists of a recipe of encoding-decoding rules to decode/encode hex messages for the CAN bus. Each vehicle model/make has a distinct DBC file. DBC file also contains further remarks and semantics about CAN message values. A standard rule for coding/decoding CAN messages in DBC file looks like as follows:

.. image:: https://raw.githubusercontent.com/jmscslgroup/strym/master/docs/source/dbc_structure.png

.. _libpanda: https://jmscslgroup.github.io/libpanda/
