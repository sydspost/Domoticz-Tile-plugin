#!/usr/bin/python3 
#
# Tile 
#
# Author : Syds Post
# Version: 1.0.0
# Date   : 13-1-2025
#
"""
<plugin key="Tile" name="Tile" author="Syds Post" version="1.0.0" wikilink="http://www.domoticz.com/wiki/plugins/plugin.html" externallink="https://www.tile.com/">
    <description>
        <h2>Tile</h2><br/>
        This plugin collects the distance from your home to your Tile devices<br/>
        <h3>Features</h3>
        <ul style="list-style-type:square">
            <li>Calculates distance between Tile Tracker and the location set in your Domoticz settings (Settings -> Settings -> System)</li>
            <li>Stores the distance in a distance device</li>
        </ul>
        <h3>Devices</h3>
        <ul style="list-style-type:square">
            <li>All Tile trackers should be supported</li>
        </ul>
        <h3>Configuration</h3>
        Create a Tile account on www.tile.com, remember your emailadres en password, and fill in below<br/>
    </description>
    <params>
        <param field="Username" label="Username" width="200px" required="true"/>
        <param field="Password" label="Password" width="200px" required="true"/>
        <param field="Mode1" label="API key" width="350px" required="true"/>
        <param field="Mode6" label="Debug" width="150px">
            <options>
                <option label="None" value="0" default="true" />
                <option label="Python Only" value="2"/>
                <option label="Basic Debugging" value="62"/>
                <option label="Basic+Messages" value="126"/>
                <option label="Queue" value="128"/>
                <option label="Connections Only" value="16"/>
                <option label="Connections+Queue" value="144"/>
                <option label="All" value="-1"/>
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz as Domoticz
import googlemaps
import time
import threading
import urllib.request
import json
from datetime import datetime
from uuid import uuid4

class BasePlugin:
    enabled = False
    homeLocation=()         # (lat, lon) of home adress
    client_uuid=None        # Client UUID
    url=None                # url op Tile API
    endpoint=None           # Tile API's endpoint
    headers={}              # Tile API's headers
    cookie=None             # Tile API's cookie
    gmaps=None              # gmaps connection
    runCounter=0            # # times heartbeat executed
    maxRuns=3               # initial max time handlethread is executed

    def __init__(self):
        self.client_uuid = str(uuid4())
        self.url='https://production.tile-api.com'
        self.headers={ 'tile_app_id': 'ios-tile-production', \
                       'tile_app_version': '2.89.1.4774', \
                       'tile_client_uuid': self.client_uuid }
        return

    def onStart(self):
        Domoticz.Log("Tile plugin started")
        if Parameters["Mode6"] != "0":
            Domoticz.Debugging(int(Parameters["Mode6"]))
            Domoticz.Log("Debugger started, use 'telnet 0.0.0.0 4444' to connect")
            # DumpConfigToLog()
        
        # Set initial heartbeat 
        Domoticz.Heartbeat(6)

        # Create icons if not existing
        if 'Tile' not in Images:
            try:
                Domoticz.Image(Filename='images.zip').Create()
            except:
                Domoticz.Log('Could not upload icons, images.zip not found in plugin file folder')
        
        # get home location out of Domoticz settings
        if not "Location" in Settings:
            Domoticz.Log("Location nog set in Preferences")
            return False
        else:
            homeLocation = Settings["Location"].split(";")
            self.homeLocation = (float(homeLocation[0]), float(homeLocation[1]))
            Domoticz.Log("Home location :" + str(self.homeLocation))

        # initialize googlemaps API
        try:
            self.gmaps = googlemaps.Client(key=Parameters["Mode1"])
        except:
            Domoticz.Log('Error: Google maps not accessable')

        # Find devices that already exist, create those that don't
        # Getting Tiles

        # Create session
        try:
            self.endpoint = '/api/v1/clients/' + self.client_uuid
            data = { 'app_id': 'ios-tile-production', \
                     'app_version': '2.89.1.4774', \
                     'locale': 'en_US' }
            data = urllib.parse.urlencode(data).encode("utf-8")
    
            req = urllib.request.Request(url=self.url+self.endpoint, headers=self.headers, method='PUT')
    
            with urllib.request.urlopen(req, data=data) as f:
                response = f.read()
    
            # Login to Tile API
            self.endpoint = self.endpoint + '/sessions'
            data = { 'email': 'sydspost@gmail.com', \
                     'password': 'X!do2019' }
    
            data = urllib.parse.urlencode(data).encode("utf-8")
    
            req = urllib.request.Request(url=self.url+self.endpoint, headers=self.headers, method='POST')
    
            with urllib.request.urlopen(req, data=data) as f:
                response = f.read()
                self.cookie = f.info().get_all('Set-Cookie')[0]
    
            # Get Tiles
            self.endpoint = '/api/v1/tiles/tile_states'
            self.headers['Cookie']=self.cookie
    
            req = urllib.request.Request(url=self.url+self.endpoint, headers=self.headers, method='GET')
    
            with urllib.request.urlopen(req) as f:
                response = json.loads(f.read().decode(encoding="utf-8").replace("'",'"'))
    
            # Get Tile details, update Devices or create Devices if not exists yet
            for tile in response["result"]:
                self.endpoint = '/api/v1/tiles/' + tile["tile_id"]
    
                req = urllib.request.Request(url=self.url+self.endpoint, headers=self.headers, method='GET')
    
                with urllib.request.urlopen(req) as f:
                    response = json.loads(f.read().decode(encoding="utf-8").replace("'",'"'))
                    tileLocation=(response["result"]["last_tile_state"]["latitude"], response["result"]["last_tile_state"]["longitude"])
                    Domoticz.Log('Tilelocation '+str(tileLocation))
    
                    deviceFound = False
                    for Device in Devices:
                        if ((response["result"]["name"] == Devices[Device].DeviceID)):
                            Devices[Device].Update(nValue=self.distance(tileLocation), sValue=str(self.distance(tileLocation)), TimedOut=False)
                            deviceFound = True
                            Domoticz.Debug("onStart:Tile '"+response["result"]["name"]+"', device updated.")
                            Domoticz.Log("onStart:Tile '"+response["result"]["name"]+"', device updated.")
    
                    if deviceFound == False:
                        Domoticz.Device(Name=response["result"]["name"], DeviceID=response["result"]["name"], TypeName="Distance", Unit=len(Devices)+1, Type=243, Subtype=27, Switchtype=0, Image=Images["Tile"].ID, Used=1).Create()
                        Domoticz.Debug("Tile '"+response["result"]["name"]+"', device was not found, created.")
                        Domoticz.Log("Tile '"+response["result"]["name"]+"', device was not found, created.")
        except:
            Domoticz.Log('Error: Tiles API not accessable')
 
        # Create/Start update thread
        self.updateThread = threading.Thread(name="TileUpdateThread", target=BasePlugin.handleThread, args=(self,))
        self.updateThread.start()

    def onStop(self):
        Domoticz.Log("onStop called")
        while (threading.active_count() > 1):
            time.sleep(1.0)

    def onConnect(self, Connection, Status, Description):
        Domoticz.Log("onConnect called")

    def onMessage(self, Connection, Data):
        Domoticz.Log("onMessage called")

    def onCommand(self, DeviceID, Unit, Command, Level, Color):
        Domoticz.Log("onCommand called for Device " + str(DeviceID) + " Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called")

    def onHeartbeat(self):
        # Domoticz.Log("onHeartbeat called time="+str(time.time()))
        self.runCounter+=1

        if self.runCounter <= self.maxRuns:
            return False

        self.runCounter=0

        # Create/Start update thread
        self.updateThread = threading.Thread(name="TileUpdateThread", target=BasePlugin.handleThread, args=(self,))
        self.updateThread.start()

    def handleThread(self):
        leastDistance=[]
        distance=0

        try:
            Domoticz.Debug("in handlethread")
            
            # Get Tiles
            self.endpoint = '/api/v1/tiles/tile_states'
    
            req = urllib.request.Request(url=self.url+self.endpoint, headers=self.headers, method='GET')
    
            with urllib.request.urlopen(req) as f:
                response = json.loads(f.read().decode(encoding="utf-8").replace("'",'"'))
    
    
            # Update or create Tile devices
            for tile in response["result"]:
                self.endpoint = '/api/v1/tiles/' + tile["tile_id"]
    
                req = urllib.request.Request(url=self.url+self.endpoint, headers=self.headers, method='GET')
    
                with urllib.request.urlopen(req) as f:
                    response = json.loads(f.read().decode(encoding="utf-8").replace("'",'"'))
                    tileLocation=(response["result"]["last_tile_state"]["latitude"], response["result"]["last_tile_state"]["longitude"])
                    Domoticz.Log('Tilelocation '+str(tileLocation))
    
                    deviceFound = False
                    for Device in Devices:
                        if ((response["result"]["name"] == Devices[Device].DeviceID)):
                            distance=self.distance(tileLocation)
                            Devices[Device].Update(nValue=distance, sValue=str(distance), TimedOut=False)
                            leastDistance.append(distance)
                            deviceFound = True
                            Domoticz.Debug("Handlethread:Tile '"+response["result"]["name"]+"', device updated.")
                            Domoticz.Log("Handlethread:Tile '"+response["result"]["name"]+"', device updated.")
    
                    if deviceFound == False:
                        Domoticz.Device(Name=response["result"]["name"], DeviceID=response["result"]["name"], TypeName="Distance", Unit=len(Devices)+1, Type=243, Subtype=27, Switchtype=0, Image=Images["Tile"].ID, Used=1).Create()
                        Domoticz.Debug("Tile '"+response["result"]["name"]+"', device was not found, created.")
                        leastDistance.append(self.distance(tileLocation))

        except Exception as err:
            Domoticz.Log('Error: Tile API not accessable')
            Domoticz.Error("handleThread: "+str(err)+' line '+format(sys.exc_info()[-1].tb_lineno))
        
        self.distanceInterval(min(leastDistance))

    
    def distance(self, tileLocation):
       distanceMatrix = self.gmaps.distance_matrix(origins=tileLocation, destinations=self.homeLocation, mode="driving", units="metric")

       return int(distanceMatrix["rows"][0]["elements"][0]["distance"]["value"])*100

    def distanceInterval(self, distance):
        if distance > 10000 and distance < 100000:
            self.maxRuns = 1
        elif distance > 100000 and distance < 500000:
            self.maxRuns = 10
        elif distance > 500000 and distance < 1000000:
            self.maxRuns = 60
        else:
            self.maxRuns = 600
        Domoticz.Log('maxRuns p/heartbeat set to: '+self.maxRuns)

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(DeviceID, Unit, Command, Level, Color):
    global _plugin
    _plugin.onCommand(DeviceID, Unit, Command, Level, Color)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

# Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for DeviceName in Devices:
        Device = Devices[DeviceName]
        Domoticz.Debug("Device ID:       '" + str(Device.DeviceID) + "'")
        Domoticz.Debug("--->Unit Count:      '" + str(Device.Unit) + "'")
        for UnitNo in Device.Unit:
            Unit = Device.Unit[UnitNo]
            Domoticz.Debug("--->Unit:           " + str(UnitNo))
            Domoticz.Debug("--->Unit Name:     '" + Unit.Name + "'")
            Domoticz.Debug("--->Unit nValue:    " + str(Unit.nValue))
            Domoticz.Debug("--->Unit sValue:   '" + Unit.sValue + "'")
            Domoticz.Debug("--->Unit LastLevel: " + str(Unit.LastLevel))
    return
