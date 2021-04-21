Installation
------------

strym requires Python 3.6 or later. We recommend to use Anaconda_ and Python 3.7.5.

PyPI
^^^^

Install strym from PyPI_ using::

    conda create -n strym python=3.7.5
    conda activate strym
    pip install -r https://github.com/jmscslgroup/strym/releases/download/0.4.3/requirements_strym.txt
    pip install strym


``-U`` is short for ``--upgrade``.
If you get a ``Permission denied`` error, use ``pip install -U strym --user`` instead.


Development Version
^^^^^^^^^^^^^^^^^^^

To work with the latest development version, install from GitHub_ using::

    pip install git+https://github.com/jmscslgroup/strym

or::

    git clone https://github.com/jmscslgroup/strym
    pip install -e strym

``-e`` is short for ``--editable`` and links the package to the original cloned
location such that pulled changes are also reflected in the environment.


Dependencies
^^^^^^^^^^^^

- `numpy <https://docs.scipy.org/>`_, `scipy <https://docs.scipy.org/>`_, `pandas <https://pandas.pydata.org/>`_, `scikit-learn <https://scikit-learn.org/>`_, `matplotlib <https://matplotlib.org/>`_.

Software Requirements
^^^^^^^^^^^^^^^^^^^^^^

- Python 3.6, Python 3.7.5 is recommended.
- For an issue related to Windows, please look at `Issue #8 <https://github.com/jmscslgroup/strym/issues/8>`_.

Note about installation on RASPBERRY PI for CAN Data Logging
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you are going to install the package on RASPBERRY PI, you will need to install pre-compiled binaries for NumPy otherwise you may encounter huge inconvenience while building NumPy wheels for Raspberry PI.

Hardware Requirements for CAN Logging
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- comma.ai_ CAN-USB Panda board.
- A suitable comma.ai_ Giraffee Connector. Check comma.ai_ website for suitable version of Giraffee connector.
- A modern vehicle with CAN Bus available such as Toyota RAV4, Toyota CHR, etc.

Creating vritual environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
I recommending creating a python virtual environment for installing ``strym``.
You can use Anaconda to create virtual environment. Steps for doing so can be found elsewhere on internet.
Alternatively, you can also use ``virtualenv`` python package to do so.
    



Jupyter Notebook
^^^^^^^^^^^^^^^^

To run the tutorials in a notebook locally, please install::

   conda install notebook

and run ``jupyter notebook`` in the terminal. If you get the error ``Not a directory: 'xdg-settings'``,
use ``jupyter notebook --no-browser`` instead and open the url manually (or use this
`bugfix <https://github.com/jupyter/notebook/issues/3746#issuecomment-444957821>`_).


If you run into issues, do not hesitate to approach us or raise a `GitHub issue`_.

.. _Anaconda: https://docs.anaconda.com/anaconda/install/
.. _PyPI: https://pypi.org/project/strym
.. _Github: https://github.com/jmscslgroup/strym
.. _`Github issue`: https://github.com/jmscslgroup/strym/issues/new/choose
.. _comma.ai: https://comma.ai/
