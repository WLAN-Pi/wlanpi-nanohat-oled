# wlanpi-nanohat-oled
WLANPi OLED display menu/navigation system

This project aims to provide a more useful and flexible front-panel menu/navigation system for the WLANPi than is provided by default with the unit. This will allow more useful information to be displayed and various modes and settings to be configured from the front panel when network access if not available/possible.

The project is currently a single Python script that has been created using the principles of operation shown in the default file supplied with the hardware unit. The file, by default, is called "bakebit_nanohat_oled.py" and will continue with the same name in this project.

## Status

This project is now ready for beta tetsting. No further significant changes are anticipated in the short term.

## Installation

If you would like to have a look at the current menu system on your WLANPi, download the "bakebit_nanohat_oled.py" file from this project and copy it to your WLANPi directory "/home/wlanpi/NanoHatOLED/BakeBit/Software/Python". It's probably a good idea to make a backup of you existing "bakebit_nanohat_oled.py" before copying in the new file.

Once the file is in position check that the file is owned by the root user and is executable by root. The following commands should do the trick:

```
 cd /home/wlanpi/NanoHatOLED/BakeBit/Software/Python/
 sudo chown root:root bakebit_nanohat_oled.py
 sudo chmod 755 bakebit_nanohat_oled.py
```

Once the file is installed, reboot the WLANPi and the new menu system should be visible on the OLED display.

![WLANPi Menu](https://github.com/WLAN-Pi/wlanpi-nanohat-oled/blob/master/images/wlanpi_menu.jpg)

## Menu Structure

As we have only 3 buttons on the front of the WLANPi, an easy-to-use navigation system is quite tricky to provide. The approach adopted uses a hierarchical menu system, with pages of system information accessed from different parts of the menu structure. At any point in time, the display shows either a navigation menu or a page of information.

At the bottom of each screen display, contextual button labels are provided that show the available navigation options.

To move vertically through a menu, a "Down" button is provided. By repeatedly hitting the "Down" button, it is possible to move through all available menu options. If more than one screenful of menu items are avalable, then scrolling down will move through all available options in a circular path. Hitting the "Next" button will move to a sub-menu level, or select a page of information, depending on the current level in the menu structure.

When a menu structure is displayed, a "Back" button is provided to move back up to parent menu items. 

When a page of information is being displayed, an "Exit" button is provided to exit back to the navigation menu. When a page is displayed, if there is more than one screen of information to display, page up/down buttons are provided to allow all information to be reviewed.

The menu navigation system concepts are shown below:


![WLANPi Menu Navigation](https://github.com/WLAN-Pi/wlanpi-nanohat-oled/blob/master/images/Navigation.png)


## Adding to the Menu Navigation Hierarchy

The menu system has been coded to (hopefully) be very straight forward to extend and add new features.

The menu system is defined by a Python hierarchical data structure. By adding new options at the required menu level, new options willl automatically appear in the menu system next time that the WLANPi is booted.

The data structure is shown (with annotations) below:


![WLANPi Menu Data Structure](https://github.com/WLAN-Pi/wlanpi-nanohat-oled/blob/master/images/Menu_Data_Structure.png)

The initial data structure has just 2 menu levels, but could be extended to further depths if required by simply extending the data structure.

The annotations above show the data structure definition, with indicators for the top level menu items and sub-menus hanging off them. My adding more items at the appropriate levels, additional top-level options or completely new sub-menus can be added as required.

### Dispatchers

At the end of each menu path is a dispatcher. This is the name of a function that is called when a menu option at the end of the menu tree is selected. It creates some useful (non-menu) page content to show on the OLED display.

This will generally require a system (Linux) command to be run by the function and present the information in a textual list of some type. 

To get an idea of how to code a dispatcher function, take a look at the source code of bakebit_nanohat_oled.py and you'll see several examples which will be very easy to re-purpose. 

One thing to remember is that you have to be very concise with the output as we have very little screen real-estate to play with. The functions that are used to automagically display the info you may throw at them will try to keep things to a reasonable size and add paging, but they have their limits.


## Global Variables

If you take a look at the source code of bakebit_nanohat_oled.py, you may be a bit horrified by the use of global variables throughout the script. I was too when I first looked at the sample scripts provided with the WLANPi. Unfortunately, they seem to be a necessary evil due to the nature of the whole thing being driven by system interrupts each time a front panel button is pressed.

When a button is pressed, the flow of the script is taken over by the interrupt event and the interpreter processes the function associated with the button signal. Global variables seem to be preserved at all times, so they provide a good way of signalling state between the main script loop and any interrupts that happen when buttons are pressed. It is best to assume that any code you add could get interrupted by the system, so checking state in global variables is a good indication of the state of the system before taking any action.

I've tried to add a bit more of an explanation in the source code notes for anyone who may be interested in this area. A lot of this has been derived from observations and testing during development of the script, so there may still be holes in my knowledge in this area.

## Acknowledgements

Props to Bryce Royal for the early work on this initiative and his ideas around the screen layout.
