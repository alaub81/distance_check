# distance_check
Python 3 script for measuring the distance with a Raspberry Pi and HC-SR04 Sensor. 
It sends his data to a MQTT Broker and warns you by sending an E-Mail when the distance is lower then value X. All you have to do is download the distance.py and use it as single standalone script or with the systemd service file `distance.service` as systemd deamon.

# Prerequirements
Installation of libraries and other stuff which is needed for the script:
```
apt install python3-pip libgpiod2 python3-systemd python3-paho-mqtt -y
pip3 install adafruit-circuitpython-hcsr04
pip3 install --upgrade setuptools

```
# Installation

```
cd /usr/local/sbin
wget https://raw.githubusercontent.com/alaub81/distance_check/main/distance.py
chmod +x /usr/local/sbin/distance.py
```
Now edit the Script and configure the variables on top of it. After configuration, you could just start the script for a first testrun.
if you are using a raspberry pi zero w, you have to run it as pi user:
```
sudo -u pi distance.py
```

# Systemd Script
```
cd /etc/systemd/system
wget https://github.com/alaub81/distance_check/raw/main/distance.service
systemctl daemon-reload
systemctl start distance.service
systemctl enable distance.service
```
That's it 
