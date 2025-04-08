**NeoQARK**
===========



**How to Download and Install the Tool**
----------------------------------------



**1.Ensure the tool is installed in the correct path**

.. code-block:: bash

    cd /usr/local/bin



**2.Download the Tool**

.. code-block:: bash

   sudo git clone https://github.com/DaoudM2003/NeoQARK.git
   cd NeoQARK




**3.Move to bin**

.. code-block:: bash

   sudo mv NeoQARK /usr/local/bin




**4.Crete Virtual enviroment**

.. code-block:: bash

   python3 -m venv env1
   source env1/bin/activate



**5.Setup The NeoQARK Tool**

.. code-block:: bash

   sudo apt-get install default-jdk
   jar --version
   pip3 install -r requirements.txt
   pip3 install .
   pip install --upgrade --force-reinstall . 
