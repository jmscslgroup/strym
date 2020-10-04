|PyPI| |PyPIDownloads| |Travis| |Docs|

Strym - A data-analytic tool for CAN-bus messages
============================================================

.. image::  https://raw.githubusercontent.com/jmscslgroup/strym/master/strym_big.png
   :width: 300px
   :align: left

**Strym** is a python package that provides APIs to interface with comma.ai_ panda to log data and visualize them in real-time.


There are two kinds of functionality that **Strym** provides:
(i) Aalysis and visualization of CAN Bus messages from a CSV Formatted file captured using libpanda_ on vehicles like Toyota, Honda, etc.
(ii) Real-time visualization of CAN data through comma.ai Panda and Giraffe connector, however, this functionality has not been developed further
in favor of libpanda_.

|
|
|
|

Philosophy behind Strym
^^^^^^^^^^^^^^^^^^^^^^^^

Strym data is capable of handling timeseries data obtained from Comma.ai Panda and Giraffe Connector. Most functions and methods in ``strym`` expects timeseries data of following format


+--------------+---------+
| Time         | Message |
+--------------+---------+
| 1.597350e+09 | 43.3    |
+--------------+---------+
| 1.597350e+09 | 43.2    |
+--------------+---------+
| ⋮            | ⋮       |
+--------------+---------+
| 1.597350e+09 | 44.4    |
+--------------+---------+

Here, data should be of type ``Pandas.DataFrame`` with two columns: Time and Message.

However, scope of strym is not limited to timeseries data obtained from comma.ai_ Panda. 
Any timeseries data of above format is capable of harnessing methods available in strym.




Contributing to the project
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Feel free to submit an `issue <https://github.com/jmscslgroup/strym/issues/new/choose>`_
or send us an `email <mailto:rahulbhadani@email.arizona.edu>`_. 
If you like to contribute to this project, please fork this repository to your GitHub account,
create a new branch for yourself and send a pull request for the merge. After reviewing the changes,
we will decide if this is a good place to add your changes.
Your help to improve strym is highly appreciated.

Licensing
^^^^^^^^^^

| License: MIT License 
| Copyright Rahul Bhadani, Jonathan Sprinkle, Arizona Board of Regents
| Initial Date: Nov 12, 2019
| Permission is hereby granted, free of charge, to any person obtaining 
| a copy of this software and associated documentation files 
| (the "Software"), to deal in the Software without restriction, including
| without limitation the rights to use, copy, modify, merge, publish,
| distribute, sublicense, and/or sell copies of the Software, and to 
| permit persons to whom the Software is furnished to do so, subject 
| to the following conditions:

| The above copyright notice and this permission notice shall be 
| included in all copies or substantial portions of the Software.

| THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF 
| ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED 
| TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A 
| PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT 
| SHALL THE AUTHORS, COPYRIGHT HOLDERS OR ARIZONA BOARD OF REGENTS
| BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN 
| AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
| OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE 
| OR OTHER DEALINGS IN THE SOFTWARE.

.. toctree::
   :caption: Main
   :maxdepth: 1
   :hidden:
    
   about
   installation
   changelog
   references

.. toctree::
   :caption: Tutorials
   :maxdepth: 1
   :hidden:

   getting_started
   youtube
   CANBasics
   Strym_Tutorial
   Strymmap_Example
   Strym_phasespace_demo
   Strymread_example
   Steering
   Speed_Acceleration_Phasespace_Generation
   Retrieving_State_Space
   Metadata_from_a_drive_collection
   Meta_example
   Max_Min_Acceleration
   Lead_vehicles_information
   ACC_Analysis
   Arizona_Vanderbilt_MiniTest1
   AutoEncoderBasedDenoising
   CANDataAnalysis_Fuel_Edition
   CANDataAnalysis_using_strymread
   CollectVelocityandAcceleration
   Dataframe_subsetting_and_slicing
   DriveCharacteristics
   GatherVelocityData
   HondaPilotDataThroughput
   HondaPilotFuelConsumptionCorrelation
   
.. toctree::
   :caption: API
   :maxdepth: 1
   :hidden:

   api_strym
   api_strymread
   api_strymmap
   api_phasespace
   api_dashboard
   api_meta
   tools
   
.. toctree::
   :caption: Example Datasets
   :maxdepth: 1
   :hidden:

.. |PyPI| image:: https://img.shields.io/pypi/v/strym.svg
   :target: https://pypi.org/project/strym

.. |PyPIDownloads| image:: https://pepy.tech/badge/strym
   :target: https://pepy.tech/project/strym

.. |Travis| image:: https://travis-ci.com/jmscslgroup/strym.svg?branch=master
   :target: https://travis-ci.com/jmscslgroup/strym/
   
.. |Docs| image:: https://raw.githubusercontent.com/jmscslgroup/strym/master/strym_badge.svg
   :target: https://jmscslgroup.github.io/strym/


.. _strym: https://jmscslgroup.github.io/strym/

.. _libpanda: https://jmscslgroup.github.io/libpanda/

.. _comma.ai: https://comma.ai/

.. |br| raw:: html

  <br/>

.. |meet| raw:: html

  <!-- Calendly link widget begin -->
  <link href="https://assets.calendly.com/assets/external/widget.css" rel="stylesheet">
  <script src="https://assets.calendly.com/assets/external/widget.js" type="text/javascript"></script>
  <a href="" onclick="Calendly.initPopupWidget({url: 'https://calendly.com/strym'});return false;">here</a>
  <!-- Calendly link widget end -->
