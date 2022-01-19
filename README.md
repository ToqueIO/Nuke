# Nuke
ToqueIO Nuke tools is a collection of tools designed to assist in enhancing your workflows within nuke.  
The primary idea behind these tools is to have tools that have been created with an artist's workflow 
in mind in an attempt to have the tools integrate as seamlessly as possible into your day-to-day work
## Installation
To install the Nuke tools you will need to add in the location the code to your local init or menu
This can be done via your user directory.

Common locations of your .nuke folder  
**Linux:** /home/username/.nuke  
**Windows:** c:/users/username/.nuke  
**Mac:** /Users/username/.nuke  

Inside that directory you will need to modify/create your menu.py file

You can then add in this to your menu.py
```python
import nuke
# The path entered should be the directory where you have placed the repository code
# If you placed the code in /toqueIO/Nuke then you would put this
nuke.pluginAddPath('/toqueIO/Nuke')
```

Official Discord: https://discord.gg/UJJrcnKGRK

