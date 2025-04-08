**NeoQARK**
===========



**How to Download and Install the Tool**
----------------------------------------


**1.Download the Tool**

.. code-block:: bash

   cd /usr/local/bin
   sudo git clone https://github.com/DaoudM2003/NeoQARK.git
   sudo chown -R user_name NeoQARK
   cd NeoQARK



**2.Crete Virtual enviroment**

.. code-block:: bash

   sudo python3 -m venv env1
   source env1/bin/activate



**3.Setup The NeoQARK Tool in qark directory**

.. code-block:: bash

   sudo apt-get install default-jdk
   jar --version
   pip install -r requirements.txt
   pip install .
   pip install --upgrade --force-reinstall . 
