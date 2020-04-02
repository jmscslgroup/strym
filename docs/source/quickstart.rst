Quick Start
===================================================

Strym data is capable of handling timeseries data obtained from Comma.ai Panda and Giraffe Connector.
Most functions and methods in :cod:`strym` expects timeseries data of following format

+---+--------------------+---------+
|   | Time               | Message |
+---+--------------------+---------+
| 1 | 1582056042.5040324 | 2.0     |
+---+--------------------+---------+
| 2 | 1582056043.5040324 | 2.1     |
+---+--------------------+---------+
| 3 | 1582056044.5040324 | 2.12    |
+---+--------------------+---------+
| 4 | 1582056045.5040324 | 1.98    |
+---+--------------------+---------+
| 5 | 1582056046.5040324 | 1.6     |
+---+--------------------+---------+

Here, data should be of type Pandas.DataFrame with two columns: Time and Message.

However, scope of :code:`strym` is not limited to timeseries data obtained from comma.ai Panda. Any timeseries data of above format is capable of harnessing methods available in :code:`strym`.


You can use **Strym** for quick visualization by importing :code:`strymread`:

.. code-block:: python

    import strym
    from strym import strymread
    from strym import ranalyze
    import matplotlib.pyplot as plt
    import pandas as pd
    from pylab import rcParams
    import strym.DBC_Read_Tools as dbc
    import numpy as np
    plt.rcParams["figure.figsize"] = (16,8)
    rcParams.update({'font.size': 40})
    dbcfile = '/home/ivory/VersionControl/Jmscslgroup/strym/examples/newToyotacode.dbc'
    r =strymread(csvfile="/home/ivory/CyverseData/JmscslgroupData/PandaData/2020_02_18/2020-02-18-13-00-42-209119__CAN_Messages.csv", dbcfile=dbcfile)

    # visualiza message counts
    r.count()

.. image:: https://raw.githubusercontent.com/jmscslgroup/strym/master/docs/source/count.png
   :width: 800
   
.. code-block:: python

    # plot speed data
    speed = r.speed()
    strym.plt_ts(speed, title="Speed Plot")

.. image:: https://raw.githubusercontent.com/jmscslgroup/strym/master/docs/source/speed.png
   :width: 800
   
.. code-block:: python

    # get rate statistics of every by message ID
    u = r.frequency

.. code-block:: python

    # synchronize two timeseries messages
    ts_yaw_rate = r.yaw_rate()
    ts_speed = r.speed()
    ## integrate yaw rate to get the heading
    ts_yaw = strym.integrate(ts_yaw_rate
    interpolated_speed, interpolated_yaw = strym.ts_sync(ts_speed, ts_yaw)
    plt.plot(interpolated_speed['Time'], interpolated_speed['Message'], ".", alpha=0.3)
    plt.plot(ts_speed['Time'], ts_speed['Message'], ".", alpha=0.4)
    plt.legend(['Interpolated Speed (Km/h)', 'Original Speed (Km/h)'])
    plt.xlabel('Time (seconds)')
    plt.ylabel('Message')
    plt.plot(interpolated_yaw['Time'], interpolated_yaw['Message'], ".", alpha=0.3)
    plt.plot(ts_yaw['Time'], ts_yaw['Message'], ".", alpha=0.4)
    plt.legend(['Interpolated Yaw (degree/s)', 'Original Yaw (degree/s)'])
    plt.xlabel('Time (seconds)')
    plt.ylabel('Message')

.. image:: https://raw.githubusercontent.com/jmscslgroup/strym/master/docs/source/speed_interpolated.png
   :width: 800
   
.. image:: https://raw.githubusercontent.com/jmscslgroup/strym/master/docs/source/yaw_interpolated.png
   :width: 800
.. code-block:: python

    # Plot the trajectory based on kinematic model, yaw rate and speed
    T = r.trajectory()
    plt.plot(T['X'], T['Y'])
    plt.legend(['Interpolated Yaw (degree/s)', 'Original Yaw (degree/s)'])
    plt.xlabel('X [m]')
    plt.ylabel('Y [m]')
    
.. image:: https://raw.githubusercontent.com/jmscslgroup/strym/master/docs/source/trajectory.png
   :width: 800
