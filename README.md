# wlanpi-nanohat-oled
WLANPi OLED display menu/navigation system

This project aims to provide a more useful and flexible front-panel menu/navigation system for the WLANPi than is provided by default with the unit. This will allow more useful information to be displayed and various modes and settings to be configured from the front panel when network access if not available/possible.

The project is currently a single Python script that has been created using the principles of operation shown in the default file supplied with the hardware unit. The file, by default, is called "bakebit_nanohat_oled.py" and will continue with the same name in this project.

## Status

This project is still in an early development cycle, so code is likely to change (and break) often.

## Installation

If you would like to have a look at the current menu system on your WLANPi, download the "bakebit_nanohat_oled.py" file from this project and copy it to your WLANPi directory "/home/wlanpi/NanoHatOLED/BakeBit/Software/Python". It's probably a good idea to make a backup of you existing "bakebit_nanohat_oled.py" before copying in the new file.

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


