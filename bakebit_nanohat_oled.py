#!/usr/bin/env python

'''

This script loosely based on the original bakebit_nanonhat_oled.py provided 
by Friendlyarm. It has been updated to support a scalable menu structure and
a number of additional features to support the WLANPi initiative. 

History:
 
 0.03 - Added Switch classic/rconsole mode and USB interface listing (28/06/19)
 0.04 - Added button labels & menu scrolling (28/06/19)
 0.05 - Added check for rconsole installation
        Changed name from rconsole to wconsole (needs new wconsole files)
        Added clear_display() function
        Added standard display dialogue function (29/06/19)
 0.06 - Added simple table fuction & refactored several functions to use it
        Updated nav buttons to have optional new label 
        Added menu verion display (30/06/19)
 0.07 - Added confirmation options to restart option menu selections (01/07/19)
 0.08 - Added check for interfaces in monitor mode 
        Added scrolling in simple tables (02/07/2019)

To do:
    1. Error handling to log?
    2. New display function to handle multiple pages
    3. Scrolling on simple pages
    4. Add monitor mode indicator to wlan interface listing if appropriate


'''

import bakebit_128_64_oled as oled
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import time
import sys
import subprocess
import signal
import os
import socket
import types
import re

__version__ = "0.08 (alpha)"
__author__  = "wifinigel@gmail.com"

############################
# Set display size
############################
width=128
height=64

############################
# Set page sleep control
############################
pageSleep=300
pageSleepCountdown=pageSleep

####################################
# Initialize the SEEED OLED display
####################################
oled.init()
#Set display to normal mode (i.e non-inverse mode)
oled.setNormalDisplay()      
oled.setHorizontalMode()

#######################################
# Initialize drawing & fonts variables
#######################################

# This variable is shared between activities and is set to True if a
# drawing action in already if progress (e.g. by another activity). An activity
# happens during each cycle of the main while loop or when a buttton is pressed
# (This does not appear to be threading or process spawning)
drawing_in_progress = False

#####################################
# Create global draw/image objects
#####################################
image = Image.new('1', (width, height))
draw = ImageDraw.Draw(image)

#######################
# Define display fonts
#######################
smartFont = ImageFont.truetype('DejaVuSansMono-Bold.ttf', 10);
font11    = ImageFont.truetype('DejaVuSansMono.ttf', 11);
font12    = ImageFont.truetype('DejaVuSansMono.ttf', 12);
fontb12   = ImageFont.truetype('DejaVuSansMono-Bold.ttf', 12);
font14    = ImageFont.truetype('DejaVuSansMono.ttf', 14);
fontb14   = ImageFont.truetype('DejaVuSansMono-Bold.ttf', 14);
fontb24   = ImageFont.truetype('DejaVuSansMono-Bold.ttf', 24);

#######################################
# Initialize various global variables
#######################################
is_menu_shown = True          # True when menu currently shown on display
shutdown_in_progress = False  # True when shutdown or reboot started
screen_cleared = False        # True when display cleared (e.g. screen save)
current_menu_location = [0]   # Pointer to current location in menu structure
option_selected = 0           # Content of currently selected menu level
sig_fired = False             # Set to True when button handler fired
home_page_name = "Home"       # Display name for top level menu
current_mode = "classic"      # Currently selected mode (e.g. wconsole/classic)
nav_bar_top = 55              # top pixel of nav bar
current_scroll_selection = 0  # where we currently are in scrolling table
table_displayed = False       # True if we're currently in a table
table_list_length = 0         # Total length of currently displayed table

#######################################
# Initialize file variables
#######################################
wconsole_mode_file = '/etc/wconsole/wconsole.on'
wconsole_switcher_file = '/etc/wconsole/wconsole_switcher'
ifconfig_file = '/sbin/ifconfig'
iw_file = '/usr/sbin/iw'


# check our current mode
if os.path.isfile(wconsole_mode_file):
    current_mode = 'wconsole'


#############################
# Get current IP for display
#############################
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

##########################
# Draw navigation buttons
##########################
def nav_button(label, position):
    global draw
    global nav_bar_top
    draw.text((position,nav_bar_top),label,font=smartFont,fill=255)
    return
    
def back_button(label="Back"):
    nav_button(label, 100)
    return

def next_button(label="Next"):
    nav_button(label,50)
    return

def down_button(label="Down"):
    nav_button(label, 0)
    return

##############################################
# Page & menu functions
##############################################
def clear_display():

    '''
    Paint display black prior to painting new page
    '''
    
    global width
    global height
    global draw
    
    # Draw a black filled box to clear the display.
    draw.rectangle((0,0,width,height), outline=0, fill=0)

def display_dialog_msg(msg_list, back_button_req=0):

    '''
    display informational dialog box
    '''
    
    global draw
    global oled
    global drawing_in_progress
    global is_menu_shown
    
    drawing_in_progress = True
    
    # Clear display prior to painting new item
    clear_display()
    
    # set start points for text
    x=0
    y=0
    
    for msg in msg_list:
        draw.text((x, y),  msg,  font=fontb14, fill=255)
        y +=16
    
    if back_button_req:
        back_button()
    
    oled.drawImage(image)
    
    is_menu_shown = False
    drawing_in_progress = False
    
    return True

def display_simple_table(item_list, back_button_req=0, title=''):

    #FIXME: this needs scrolling if num items > 4. Add contextual up/down
    #       labels to buttons
    #FIXME: Add optional title?

    global drawing_in_progress
    global draw
    global oled
    global is_menu_shown
    global current_scroll_selection
    global table_displayed
    global table_list_length

    drawing_in_progress = True
    table_displayed = True
    
    # Clear display prior to painting new item
    clear_display()

    y = 0
    x = 0
    font_offset = 0
    font_size = 12
    item_length_max = 20
    table_display_max = 4
    scrolling_req = False
    
    # write title if present
    if title != '':
        draw.text((x, y + font_offset), title.center(item_length_max, " "),  font=smartFont, fill=255)
        font_offset += font_size
        table_display_max -=1
    
    table_list_length = len(item_list)
    
    # if we're going to scroll of the end of the list, adjust pointer
    if current_scroll_selection + table_display_max > table_list_length:
        current_scroll_selection -=1
    
    # modify list to display if scrolling required
    if table_list_length > table_display_max:
    
        table_bottom_entry = current_scroll_selection + table_display_max
        item_list = item_list[current_scroll_selection: table_bottom_entry]

        # show down if not at end of list in display window
        if table_bottom_entry < table_list_length:
            down_button()

        
        # show an up button if not at start of list
        if current_scroll_selection > 0:
            next_button(label="Up")
    
    for item in item_list:
    
        if len(item) > item_length_max:
            item = item[0:item_length_max]

        draw.text((x, y + font_offset), item,  font=smartFont, fill=255)
        
        font_offset += font_size
    
    # Back button
    if back_button_req:
        back_button(label="Exit")
    
    oled.drawImage(image)
    
    is_menu_shown = False
    drawing_in_progress = False
    
    return

##############################################
# Main function to draw menu navigation pages
##############################################
def draw_page():
    global drawing_in_progress
    global image
    global draw
    global oled
    global font
    global fontb12
    global font14
    global smartFont
    global width
    global height
    global width
    global height
    global pageSleepCountdown
    global current_menu_location
    global is_menu_shown
    global option_selected 
    global option_number_selected
    global menu
    global home_page_name
    
    # Drawing already in progress - return
    if drawing_in_progress:
        return

    # signal we are drawing
    drawing_in_progress = True
 
    ################################################
    # show menu list based on current menu position
    ################################################
    
    #FIXME: This feels clunky. Would be best to access menu locations
    #       via evaluated location rather than crawling over menu
    
    menu_structure = menu
    location_search = []
    depth = 0
    section_name = [home_page_name]

    # Crawl the menu structure until we hit the current specified location
    while current_menu_location != location_search:

        # List that will be used to build menu items to display
        menu_list = []
        
        # Current menu location choice specified in list format:
        #  current_menu_location = [2,1]
        #
        # As we move though menu depths, inpsect next level of
        # menu structure
        node = current_menu_location[depth]
        
        # figure out the number of menu options at this menu level
        number_menu_choices = len(menu_structure)
               
        if node == number_menu_choices:
        
            # we've fallen off the end of menu choices, fix item by zeroing
            node = 0
            current_menu_location[depth] = 0
            
        
        location_search.append(node)
        
        item_counter = 0

        for menu_item in menu_structure:
        
            item_name = menu_item['name']
            
            # this is the currently selected item, pre-pend name with '*'
            if (item_counter == node):
                section_name.append(item_name)
                item_name = "*" + item_name
            
            menu_list.append((item_name))
            
            item_counter = item_counter + 1
        
        depth = depth + 1
        
        # move down to next level of menu structure & repeat for new level
        menu_structure = menu_structure[node]['action']
        
        
    option_number_selected = node
    option_selected = menu_structure
    
    # if we're at the top of the menu tree, show the home page title
    if depth == 1:
        page_title = ("[ " + home_page_name + " ]").center(17, " ")
    else:
        # otherwise show the name of the parent menu item
        page_title = ("[ " + section_name[-2] + " ]").center(17, " ")
    
    # Clear display prior to painting new item
    clear_display()
    
    # paint the page title
    draw.text((1, 1), page_title,  font=fontb12, fill=255)
    
    # vertical starting point for menu (under title) & incremental offset for
    # subsequent items
    y=15
    y_offset=13
    
    # define display window limit for menu table
    table_window = 3
    
    # determine the menu list to show based on current selection and window limits
    if (len(menu_list) > table_window):
    
        if (option_number_selected >= table_window):
            menu_list = menu_list[(option_number_selected - (table_window - 1)): option_number_selected + 1]
        else:
            menu_list = menu_list[0 : table_window]
    
    # paint the menu items, highlighting selected menu item
    for menu_item in menu_list:
    
        rect_fill=0
        text_fill=255
    
        # this is selected menu item: highlight it and remove * character
        if (menu_item[0] == '*'):
            rect_fill=255
            text_fill=0
            menu_item = menu_item[1:len(menu_item)]
            
        # convert menu item to std width format with nav indicator
        menu_item = "{:<17}>".format(menu_item)
    
        draw.rectangle((0, y, 127, y+y_offset), outline=0, fill=rect_fill)
        draw.text((1, y+1), menu_item,  font=font11, fill=text_fill)
        y += y_offset  
    
    # add nav buttons
    down_button()
    next_button()
    # Don't show back button at top level of menu
    if depth != 1:
        back_button()
    
    oled.drawImage(image)

    drawing_in_progress = False

####################################
# dispatcher (menu) functions here
####################################
def show_summary():

    global width
    global height
    global draw
    global oled
    global is_menu_shown
         
    IPAddress = get_ip()
    cmd = "top -bn1 | grep load | awk '{printf \"CPU Load: %.2f\", $(NF-2)}'"
    CPU = subprocess.check_output(cmd, shell = True )
    cmd = "free -m | awk 'NR==2{printf \"Mem: %s/%sMB %.2f%%\", $3,$2,$3*100/$2 }'"
    MemUsage = subprocess.check_output(cmd, shell = True )
    cmd = "df -h | awk '$NF==\"/\"{printf \"Disk: %d/%dGB %s\", $3,$2,$5}'"
    Disk = subprocess.check_output(cmd, shell = True )
    tempI = int(open('/sys/class/thermal/thermal_zone0/temp').read());
    
    if tempI>1000:
        tempI = tempI/1000
    tempStr = "CPU TEMP: %sC" % str(tempI)

    results = [
        "IP: " + str(IPAddress),
        str(CPU),
        str(MemUsage),
        str(Disk),
        tempStr
    ]
    
    display_simple_table(results, back_button_req=1)
    
    return

def show_date():

    global width
    global height
    global draw
    global oled
    global is_menu_shown
    
    drawing_in_progress = True
    
    # Clear display prior to painting new item
    clear_display()

    text = time.strftime("%A")
    draw.text((1,2),text,font=font14,fill=255)
    text = time.strftime("%e %b %Y")
    draw.text((1,17),text,font=font14,fill=255)
    text = time.strftime("%X")
    draw.text((1,30),text,font=fontb24,fill=255)
    
    # Back button
    back_button()
        
    oled.drawImage(image)
    
    is_menu_shown = False
    drawing_in_progress = False

def show_interfaces():

    # FIXME: what about instances with > 3/4 interfaces?
    # FIXME: move get_interface_info in to this function?

    '''
    Return a list of interfaces found to be up, with IP address if available
    '''

    global ifconfig_file
    global iw_file

    try:
        ifconfig_info = subprocess.check_output(ifconfig_file, shell=True)
    except Exception as ex:
        interfaces= [ "Err: ifconfig error" ]
        display_simple_table(interfaces, back_button_req=1)
        return

    # Extract interface info
    interface_re = re.findall('^(\w+?)\: flags(.*?)RX packets', ifconfig_info, re.DOTALL|re.MULTILINE)
    if interface_re is None:
        interfaces = [ "Error: match error"]
    else:
        interfaces = []
        for result in interface_re:
        
            # save the interface name
            interface_name = result[0]
            
            # look at the rest of the interface info & extract IP if available
            interface_info = result[1]
            
            inet_search = re.search("inet (.+?) ", interface_info, re.MULTILINE)
            if inet_search is None:
                ip_address = "No IP address"
                
                # do check if this is an interface in monitor mode
                if (re.search("wlan\d", interface_name, re.MULTILINE)):

                    # fire up 'iw' for this interface (hmmm..is this a bit of an un-necessary ovehead?)
                    iw_info = subprocess.check_output('{} {} info'.format(iw_file, interface_name), shell=True)

                    if re.search("type monitor", iw_info, re.MULTILINE):
                        ip_address = "(Mon mode)"           
            else:
                ip_address = inet_search.group(1)
            
            interfaces.append( interface_name + ": " + ip_address )

    display_simple_table(interfaces, back_button_req=1, title="--Interfaces--")

def show_usb():

    # FIXME: what about when no devices detected?
    # FIXME: what about instances with > 3/4 interfaces?
    # FIXME: move get_usb_info in to this function?
    
    '''
    Return a list of non-Linux USB interfaces found with the lsusb command
    '''

    lsusb = '/usr/bin/lsusb | /bin/grep -v Linux | /usr/bin/cut -d\  -f7-'
    lsusb_info = []

    try:
        lsusb_output = subprocess.check_output(lsusb, shell=True)
        lsusb_info = lsusb_output.split('\n')
    except Exception as ex:
        error_descr = "Issue getting usb info using lsusb command"
        interfaces= [ "Err: lsusb error" ]
        display_simple_table(interfaces, back_button_req=1)
        return
        
    interfaces = []

    for result in lsusb_info:
    
        # chop down the string to fit the display
        result = result[0:19]
    
        interfaces.append(result)
        
    if len(interfaces) == 0:
        interfaces.append("No devices detected")
    
    display_simple_table(interfaces, back_button_req=1, title='--USB Interfaces--')
    
    return

def show_menu_ver():

    global __version__
    
    display_simple_table(["Menu version:", __version__], back_button_req=1)
    

def shutdown():

    global oled
    global shutdown_in_progress
    global screen_cleared
    
    display_dialog_msg(['Shutting down...'], back_button_req=0)
    time.sleep(1)

    oled.clearDisplay()
    screen_cleared = True
    
    os.system('systemctl poweroff')
    shutdown_in_progress = True
    return

def reboot():

    global oled
    global shutdown_in_progress
    global screen_cleared
    
    display_dialog_msg(['Rebooting...'], back_button_req=0)
    time.sleep(1)

    oled.clearDisplay()
    screen_cleared = True
    
    os.system('systemctl reboot')
    shutdown_in_progress = True
    return

def wconsole_switcher():

    global oled
    global shutdown_in_progress
    global screen_cleared
    global current_mode
    global wconsole_switcher_file
    
    # check wconsole is available
    if not os.path.isfile(wconsole_switcher_file):
        
        display_dialog_msg(['Wconsole not', 'available'], back_button_req=1)
        
        is_menu_shown = False
        return
    
    # wconsole switcher was detected, so assume it's installed
    
    display_dialog_msg(['Booting...', '(new mode)'], back_button_req=0)
    time.sleep(1)
    oled.clearDisplay()
    screen_cleared = True
    
    
    if current_mode == "classic":
        # if in classic mode, switch to wconsole
        subprocess.call(wconsole_switcher_file + " on", shell=True)
    elif current_mode == "wconsole":
        subprocess.call(wconsole_switcher_file + " off", shell=True)
    else:
        print "Hit unknown mode in wconsole switcher"
        return
        
    drawing_in_progress = False
    
    os.system('systemctl reboot')
    shutdown_in_progress = True
    return

#######################
# other functions here
#######################

def menu_down():

    global current_menu_location
    global menu
    global is_menu_shown
    global table_displayed
    global current_scroll_selection
    
    # If we are in a table, scroll down (unless at bottom of list)
    if table_displayed:
        current_scroll_selection +=1
        return
    
    # Menu not currently shown, do nothing
    if is_menu_shown == False:
        return

    # pop the last menu list item, increment & push back on
    current_selection = current_menu_location.pop()
    current_selection = current_selection +1
    current_menu_location.append(current_selection)
    
    draw_page()
    

def menu_right():

    global current_menu_location
    global menu
    global option_number_selected
    global option_selected
    global is_menu_shown
    global table_displayed
    global current_scroll_selection
    
    # If we are in a table, scroll up (unless at top of list)
    if table_displayed:
        if current_scroll_selection == 0:
            return
        else:
            current_scroll_selection -=1
            return
    
    # Check if the "action" field at the current location is an 
    # array or a function.
    
    # if we have an array, append the current selection and re-draw menu
    if (type(option_selected) is list):
        current_menu_location.append(0)
        draw_page()
    elif (isinstance(option_selected, types.FunctionType)):
    # if we have a function (dispatcher), execute it
        is_menu_shown = False
        option_selected()

def menu_left():

    global current_menu_location
    global menu
    global option_number_selected
    global option_selected
    global is_menu_shown
    global table_displayed
    global current_scroll_selection
    global table_list_length
    
    # If we're in a table we need to exit, reset table scroll counters
    # and draw the menu for our current level
    if table_displayed:
        current_scroll_selection = 0
        table_list_length = 0
        table_displayed = False
        is_menu_shown = True
        draw_page()
        return

    if is_menu_shown:

        # check to make sure we aren't at top of menu structure
        if len(current_menu_location) == 1:
            return
        else:
            current_menu_location.pop()
            draw_page()
    else:
        is_menu_shown = True
        draw_page()

def go_up():

    # executed when the '..' navigation item is selected

    global current_menu_location
    global is_menu_shown
    
    is_menu_shown = True
    
    if len(current_menu_location) == 1:
        # we must be at top level, do nothing
        return
    else:
        # Take off last level of menu structure to go up
        # Set index to 0 so top menu item selected
        current_menu_location.pop()
        current_menu_location[-1] = 0
        
        draw_page()

#######################
# menu structure here
#######################
if current_mode == "wconsole":

    menu = [
        { "name": "1.Status", "action": [
                { "name": "1.Interfaces", "action": show_interfaces},
                { "name": "2.USB Devices", "action": show_usb},
                { "name": "3.Version", "action": show_menu_ver},
            ]
        },
        { "name":"2.Actions", "action": [
                { "name": "1.Classic Mode",   "action": [
                    { "name": "Cancel", "action": go_up},
                    { "name": "Confirm", "action": wconsole_switcher},
                    ]
                },
                { "name": "2.Reboot",   "action": [
                    { "name": "Cancel", "action": go_up},
                    { "name": "Confirm", "action": reboot},
                    ]
                },
            ]
        },            
    ]
    
    # Ensure home menu title shows we are in wconsole mode
    home_page_name = "Wconsole"
    
else:
    # assume classic mode
    menu = [
          { "name": "1.Status", "action": [
                { "name": "1.Summary", "action": show_summary},
                { "name": "2.Date/Time", "action": show_date},
                { "name": "3.Interfaces", "action": show_interfaces},
                { "name": "4.USB Devices", "action": show_usb},
                { "name": "5.Version", "action": show_menu_ver},
            ]
          },
          { "name":"2.Actions", "action": [
                { "name": "1.Reboot",   "action": [
                    { "name": "Cancel", "action": go_up},
                    { "name": "Confirm", "action": reboot},
                    ]
                },
                { "name": "2.Wconsole Mode",   "action": [
                    { "name": "Cancel", "action": go_up},
                    { "name": "Confirm", "action": wconsole_switcher},
                    ]
                },
                { "name": "3.Shutdown", "action": [
                    { "name": "Cancel", "action": go_up},
                    { "name": "Confirm", "action": shutdown},
                    ]
                },
            ]
          }
    ]

# Set up handlers to process key pressses
def receive_signal(signum, stack):

    global pageSleepCountdown
    global pageSleep
    global current_menu_location
    global shutdown_in_progress
    global screen_cleared
    global sig_fired

    if (sig_fired):
        # signal handler already in progress, ignore this one
        return

    #user pressed a button, reset the sleep counter
    pageSleepCountdown = pageSleep 
    
    if drawing_in_progress or shutdown_in_progress:
        return
    
    # if display has been switched off to save screen, power back on and show home menu
    if screen_cleared:
        screen_cleared = False
        pageSleepCountdown = pageSleep
        return
    
    # Key 1 pressed - Down key
    if signum == signal.SIGUSR1:
        sig_fired = True
        menu_down()
        sig_fired = False
        return
        

    # Key 2 pressed - Right/Selection key
    if signum == signal.SIGUSR2:
        sig_fired = True    
        menu_right()
        sig_fired = False
        return

    # Key 3 pressed - Left/Back key
    if signum == signal.SIGALRM:  
        sig_fired = True
        menu_left()
        sig_fired = False
        return

###############################################################################
#
# ****** MAIN *******
#
###############################################################################

# First time around (power-up), draw logo on display
image0 = Image.open('wlanprologo.png').convert('1')
oled.drawImage(image0)
time.sleep(2)

# Set signal handlers for button presses - these fire every time a button
# is pressed
signal.signal(signal.SIGUSR1, receive_signal)
signal.signal(signal.SIGUSR2, receive_signal)
signal.signal(signal.SIGALRM, receive_signal)

##############################################################################
# Constant 'while' loop to paint images on display or execute actions in
# response to selections made with buttons. When any of the 3 WLANPi buttons
# are pressed, I believe the signal handler takes over the Python interpreter
# and executes the code associated with the button. The original flow continues
# once the button press action has been completed. 
# 
# The current sleep period of the while loop is ignored when a button is 
# pressed.
# 
# All global variables defined outside of the while loop are preserved and may 
# read/set as required. The same variables are available for read/write even
# when a button is pressed and an interrupt occurs: no additional thread or
# interpreter with its own set of vars appears to be launched. For this reason,
# vars may be used to signal between the main while loop and any button press
# activitie to indicate that processes such as screen paints are in progress.
#
# Despite the sample code suggesting threading is used I do not believe this
# is the case, based on testing with variable scopes and checking for process
# IDs when different parts of the script are executing.
##############################################################################
while True:
    try:
        
        if shutdown_in_progress or screen_cleared or drawing_in_progress:
            
            # we don't really want to do anything at the moment, lets 
            # nap and loop around
            time.sleep(1)
            continue
        
        # Draw a menu or execute current action (dispatcher)
        if is_menu_shown == False:
            # no menu shown, so must be executing action. 
            # Re-run current action to refresh screen 
            option_selected()
        else:
            # lets try drawing our page (or refresh if already painted)
            draw_page()
        
        # if screen timeout is zero, clear it if not already done (blank the 
        # display to reduce screenburn)
        if pageSleepCountdown == 0 and screen_cleared == False:
            oled.clearDisplay()
            screen_cleared = True

        pageSleepCountdown = pageSleepCountdown - 1

        # have a nap before we start our next loop
        time.sleep(1)
        
    except KeyboardInterrupt:
        break
    except IOError:
        print ("Error")
