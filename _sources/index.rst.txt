.. Strym documentation master file, created by
   sphinx-quickstart on Mon Feb 17 18:26:51 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.


===================================================
Strym - A data-analytic tool for CAN-bus messages
===================================================
.. image::  https://raw.githubusercontent.com/jmscslgroup/strym/master/strym_big.png
   :width: 300px
   :align: left

**Strym** is a python package that provides APIs to interface with COMMA.AI panda to log data and visualize them in real-time.


|
|

There are two kinds of functionality that **Strym** provides:

1. Aalysis and visualization of CAN Bus messages from a CSV Formatted file captured using libpanda_ on vehicles like Toyota, Honda, etc.
2. Real-time visualization of CAN data through comma.ai Panda and Giraffe connector, however, this functionality has not been developed further
in favor of libpanda_

|
|
.. toctree::
    :hidden: 
    
    readme
    quickstart
    youtube
    api_docs
    changelog

.. include:: quickstart.rst

.. _libpanda: https://jmscslgroup.github.io/libpanda/
