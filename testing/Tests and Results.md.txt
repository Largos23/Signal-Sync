Test 1: Writing a program on the Pi that outputs a custom colour to the addressable LEDs and, at the same time, outputs a message to an LCD of what colour it was
The user has control through switches which colour is output. This test code can be seen under test 1 in the appendix; it has been slightly abbreviated to limit the number of options from 8 to 2.
Results:
This test checked many boxes for the main program that the Pi would eventually run. It required an understanding of how the GPIO pins of the Pi function and the wiring required for the switches to function properly. The LCD and the code used at the time didn’t carry through to the later stages of the project, but they were critical in setting up some of the needed frameworks. 
 
Test 2: Writing a Program to test out UART communication
This required setup on the Raspberry Pi and the EFR32G28; the setup Pi involved configuring the UART port to be hardware enabled. On the EFR32G28, we used its MIKROE pin rails to install UART drivers in the IDE and enable their use.
Results:
This test was extremely critical in opening the possibilities of the project being a success. Without an established communication protocol between devices, there was no way to combine radio signals' sending and receiving with the Pi's processing. The initial test attached in the appendix uses a Pi command line program called Minicom to view serial communication. The test sends a message from the radio board when it powers up and then simply mirrors the characters typed in the keyboard back to the user on screen.

Test 3: Using the Radio Abstract Interface Layer (RAIL) to send and receive packets
This test utilized two programs: one is a sample program provided by Simplicity Studio for testing purposes, and the other is Tera Term. Tera Term allows you to instruct devices on what to do from its command line program. 
Results:
With the Tera Term software running and connected to the EFR32G28, you can simply type ‘help’ to receive a list of instructions. Through these instructions, we were able to set one of our devices to transmit packets and the other to receive and display the packets that were being received. This important test was used to visualize the packet transmission process. 


Test 4: Custom radio testing and return RSSI
This test involved setting custom packets to be sent over the Radio at the 915 MHz frequency tuned to use the modulation scheme of 2-level Gaussian Frequency Shift Keying. 

Results:
Transmitting at this frequency and adding the RSSI to the packets gave us a vision of what our messages need to be coded to send. The packet carried 16 unique hex values we could set to whatever was required. We only need to send 3: one for the payload length, one for the device ID, and one for the match code; the RSSI value was tacked on at the end of the packet transmission. This code is the foundation of UART integration with the board to send packets that can change based on user input but also for the test dummy boards we are using. The code for our test boards is in the appendix under test 4.

Test 5: LCD output
This test was used to get the LCD to perform the required outputs. The LCD uses a common Pi and Python drawing interface to output, which was needed to set everything up properly.

Results:
The LCD was found to be able to use SPI for the output and I2C for its touch functionality. The touch features will remain unused for now, but it is possible to code them with custom instructions. For this test, we used the regular draw commands to get the LCD to output values in a way that makes sense. One of these tests can be seen in the appendix under test 5.

Test 6: Range testing
Once the devices could be tested with an output to the display, a simple walking test was performed to observe the range in a realistic indoor environment.

Results:
In a real environment with one of the radio boards on the move and the other stationary, we estimated the range to be about 40 meters in radius. This was through a solid concrete wall and not in free space. This test was also used to see the sensitivity of the radio board receiver. The measurements started to fall off at around –90dB, and the bounds of the display were adjusted to reflect this fact.

Test 7: Autostart of the device
As an electronic device with a potentially embedded microcontroller, the device, when powered automatically, must run the program we need.
Results:
Using a native program for the Pi called crontab, it was simple to get out Python script to run whenever the device powered on. This is done by calling crontab from the command line and editing it to include a line that includes your file name and path to run at reboot. 
