# Domoticz-Tile-plugin
Domoticz - Tile plugin


This plugin collects the distance from your home to your Tile devices<br/>

Features
- Calculates distance between Tile Tracker and the location set in your Domoticz settings (Settings -> Settings -> System)
- Stores the distance in a distance device

Devices
- All Tile trackers should be supported, only tested Tile Mate

Configuration
- Create a Tile account on www.tile.com, remember your emailadres en password, and fill in plugin settins

Read the complete story on https://www.sydspost.nl/index.php/2025/01/18/domoticz-plugin-for-tile-trackers/

Requirements
- python 3.12.3 or later
- haversine library (https://pypi.org/project/haversine/)
- Tile account

Installation
- pip3 install -u haversine
- cd ~/domoticz/plugins/
- git clone https://github.com/sydspost/Domoticz-Tile-plugin.git
- mv Domoticz-Tile-plugin tile
- chmod +x ./tile/plugin.py
  
Tile account
Create your Tile account on www.tile.com
