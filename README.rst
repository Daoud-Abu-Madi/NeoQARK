# NeoQARK



## **How to Download and Install the Tool**





### 1. **Ensure the tool is installed in the correct path**
```
cd /usr/local/bin
```


### 2. **Download the Tool  Run the following commands to download the tool:**
```
sudo git clone https://github.com/DaoudM2003/NeoQARK.git
cd NeoQARK
```


### 3. **Move to bin**
```
sudo mv NeoQARK /usr/local/bin 
```


### 4. **Crete Virtual enviroment**
```
python3 -m venv env1
source env1/bin/activate
```

### 5. **Download the jar**
```
sudo apt-get install default-jdk
jar --version
```

### 5. **Set Up The NeoQARK Tool , in NeoQARK Directory**
```
pip3 install -r requirements.txt
pip3 install .
pip install --upgrade --force-reinstall .
```
