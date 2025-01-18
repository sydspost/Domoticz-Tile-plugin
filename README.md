# Domoticz---Tile-plugin
Domoticz - Tile plugin


This plugin collects the distance from your home to your Tile devices<br/>

Features
- Calculates distance between Tile Tracker and the location set in your Domoticz settings (Settings -> Settings -> System)
- Stores the distance in a distance device

Devices
- All Tile trackers should be supported, only tested Tile Mate

Configuration
- Create a Tile account on www.tile.com, remember your emailadres en password, and fill in plugin settins
- Generate a Google maps API key, and fill in plugin settings.

Read the complete story on https://www.sydspost.nl/index.php/2025/01/18/domoticz-plugin-for-tile-trackers/

Requirements
- python 3.12.3 or later
- googlemaps library (https://github.com/googlemaps/google-maps-services-python)
- Tile account
- Google maps API key

Installation
- pip3 install -u googlemaps
- cd ~/domoticz/plugins/
- git clone https://github.com/sydspost/Domoticz-Tile-plugin.git
- mv Domoticz-Tile-plugin tile
- chmod +x ./tile/plugin.py
  
API Key
Each Google Maps Web Service request requires an API key or client ID. API keys are generated in the 'Credentials' page of the 'APIs & Services' tab of Google Cloud console.

For even more information on getting started with Google Maps Platform and generating/restricting an API key, see Get Started with Google Maps Platform in the docs https://googlemaps.github.io/google-maps-services-python/docs/index.html.

Important: This key should be kept secret on your server.

Tile account
Create your Tile account on www.tile.com
