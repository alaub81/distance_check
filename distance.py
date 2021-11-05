#!/usr/bin/python3
import systemd.daemon
import time, board
import adafruit_hcsr04
import smtplib, ssl
import paho.mqtt.client as mqtt

### Variables
# Define the GPIO Pins (Dx)
sonar = adafruit_hcsr04.HCSR04(trigger_pin=board.D5, echo_pin=board.D6)
# Measurement every x Seconds
wait = 180
# How many measurements should be used for mean value
measurements = 30
# Warning when mean value is smaller then x cm
warning = 100

# Mailserver configuration
# Mail Server Port
smtp_port = 587
# SMTP Server address
smtp_server = "your.mailserver.tld"
# Sender E-Mail address (also used for authentification)
sender_email = "yourmailaddress"
# Receiver E-Mail address
receiver_email = "receivermailaddress"
# Your E-Mail account password
smtp_password = "YourPassWord"

# MQTT Connection
# Enable / Disable MQTT Connection (True / False)
mqttconnection = False
# MQTT connection facts...
broker = "FQDN / IP ADDRESS"
mqtt_port = 8883
mqttclientid = "clientid-hcsr04-homie"
clientid = "clientid-hcsr04"
clientname = "Clientname HC-SR04 Sensor"
nodes="hcsr04"
mqtt_username = "mosquitto"
mqtt_password = "password"
insecure = True
qos = 1
retain_message = True
# Retry to connect to mqtt broker
mqttretry = 5


### Functions
def mailing(value):
  message = """\
FROM: {}
TO: {}
Subject: Wert zu niedrig


Die Hoehe ist zu niedrig. Bitte pruefen:
Hoehe ist: {:.0f} cm

This message is sent from Python.""".format(sender_email,receiver_email,value)
  context = ssl.create_default_context()
  with smtplib.SMTP(smtp_server, smtp_port) as server:
    server.starttls(context=context)
    server.login(sender_email, smtp_password)
    server.sendmail(sender_email, receiver_email, message)

def publish(topic, payload):
  client.publish("homie/" + clientid + "/" + topic,payload,qos,retain_message)

def on_connect(client, userdata, flags, rc):
  print("MQTT Connection established, Returned code=",rc)
  # homie client config
  publish("$state","init")
  publish("$homie","4.0")
  publish("$name",clientname)
  publish("$nodes",nodes)
  # homie node config
  publish(nodes + "/$name","HC-SR04 Sensor")
  publish(nodes + "/$properties","distance")
  publish(nodes + "/distance/$name","Distance")
  publish(nodes + "/distance/$unit","cm")
  publish(nodes + "/distance/$datatype","float")
  publish(nodes + "/distance/$settable","false")
  # homie stae ready
  publish("$state","ready")

def on_disconnect(client, userdata, rc):
  print("MQTT Connection disconnected, Returned code=",rc)

def sensorpublish(distance):
  publish(nodes + "/distance","{:.2f}".format(distance))

### do the stuff
mailsent = False

#MQTT Connection
if mqttconnection == True:
  mqttattempts = 0
  while mqttattempts < mqttretry:
    try:
      client=mqtt.Client(mqttclientid)
      client.username_pw_set(mqtt_username, mqtt_password)
      client.tls_set(cert_reqs=ssl.CERT_NONE) #no client certificate needed
      client.tls_insecure_set(insecure)
      client.will_set("homie/" + clientid + "/$state","lost",qos,retain_message)
      client.connect(broker, mqtt_port)
      client.loop_start()
      mqttattempts = mqttretry
    except :
      print("Could not establish MQTT Connection! Try again " + str(mqttretry - mqttattempts) + "x times")
      mqttattempts += 1
      if mqttattempts == mqttretry:
        print("Could not connect to MQTT Broker! exit...")
        exit (0)
      time.sleep(5)
  client.on_connect = on_connect
  client.on_disconnect = on_disconnect

# Tell systemd that our service is ready
systemd.daemon.notify('READY=1')

# finaly the loop
while True:
  try:
    list = []
    attempts = measurements 
    while attempts > 0:
      try:
        #print("Distance: %.2f cm" % sonar.distance)
        list.append(sonar.distance)
        attempts -= 1
        time.sleep(0.1)
        #print(list)
      except RuntimeError:
        print("Retrying Measurement!")

    list.pop(0)
    #print(list)
    mean = sum(list)/len(list)
    #print("Distance: %.2f cm" % mean)
    if mqttconnection == True:
      sensorpublish(mean)

    if mean <= warning and mailsent == False:
      #print("Distance Warning: %.2f cm" % mean)
      mailing(mean)
      mailsent = True

    if mean >= warning and mailsent == True:
      #print("Distance Warning off: %.2f cm" % mean)
      mailsent = False

    time.sleep(wait)

  except RuntimeError:
    print("Retrying Main Array!")

  except KeyboardInterrupt:
    print("Goodbye!")
    if mqttconnection == True:
      # At least close MQTT Connection
      publish("$state","disconnected")
      time.sleep(1)
      client.disconnect()
      client.loop_stop()
    exit (0)

if mqttconnection == True:
  # At least close MQTT Connection
  print("Script stopped")
  publish("$state","disconnected")
  time.sleep(1)
  client.disconnect()
  client.loop_stop()
