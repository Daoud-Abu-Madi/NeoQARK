# NeoQARK



## **How to Download and Install the Tool**

### 1. **Ensure the tool is installed in the correct path**
```bash
cd /usr/local/bin
```



### 2. **Download the Tool**
Run the following commands to download the tool:
```bash
sudo git clone https://github.com/DaoudM2003/NeoQARK.git
cd NeoQARK
```
### 3. **Move to bin**
```bash
sudo mv NeoQARK /usr/local/bin 
```

### 4. **Crete Virtual enviroment**
```bash
python3 -m venv env1
source env1/bin/activate

```

### 5. **Download the jar**
```bash
sudo apt-get install default-jdk
jar --version
```

### 5. **Set Up The NeoQARK Tool , in NeoQARK Directory**
```bash
pip3 install -r requirements.txt
pip3 install .
pip install --upgrade --force-reinstall .
```
