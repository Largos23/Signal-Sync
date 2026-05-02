import time
import os
import RPi.GPIO as GPIO
import serial
import re
import sys 
import logging
import math
import spidev as SPI
sys.path.append("..")
from lib import LCD_1inch28,Touch_1inch28
from PIL import Image,ImageDraw,ImageFont
import board
import neopixel
import digitalio

# ----------------- Setup -----------------
# Raspberry Pi pin configuration:
RST = 27
DC = 25
BL = 18

TP_INT = 4

Mode = 0
logging.basicConfig(level=logging.DEBUG)
global Flag

''' Warning!!!Don't  creation of multiple displayer objects!!! '''
disp = LCD_1inch28.LCD_1inch28()
# Initialize library.
disp.Init()
# Clear display.
disp.clear()

image1 = Image.new("RGB", (disp.width, disp.height), "WHITE")
draw = ImageDraw.Draw(image1)
font = ImageFont.load_default()

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

device_id = 0x25  # ID of this Pi's device
devices = {}

# Switch state input pins
switch_pins = [
    (24, 0),  # S1
    (13, 1),  # S2
    (6,  2),  # S3
    (5,  3),  # S4
    (23, 4),  # S5
    (16, 5),  # S6
    (20, 6),  # S7
    (21, 7)   # S8
]

# GPIO button input pins (for logging/demo)
input_pins = [24, 13, 6, 5, 23, 16, 20, 21]
for pin in input_pins:
    GPIO.setup(pin, GPIO.IN)

# GPIO outputs (e.g., LEDs)
# GPIO.setup(26, GPIO.OUT)
GPIO.setup(19, GPIO.OUT)

# Serial port
ser = serial.Serial('/dev/serial0', 115200, timeout=1)
ser.flush()

# Button cooldowns
last_trigger_time = {pin: 0 for pin in [23, 16, 20, 21]}
cooldown_duration = 10  # seconds
last_draw_time = 0
draw_interval = 0.3
last_print_time = 0
NEOPIXEL_PIN = board.D12
pixels = neopixel.NeoPixel(NEOPIXEL_PIN,8, auto_write=False)


# ----------------- Helpers -----------------
def parse_packet_line(line):
    try:
        rssi_part = re.search(r'RSSI=([-0-9]+)', line)
        rssi = int(rssi_part.group(1)) if rssi_part else None

        hex_values = re.findall(r'0x[0-9A-Fa-f]{2}', line)
        if len(hex_values) >= 3:
            length = int(hex_values[0], 16)
            parsed_device_id = int(hex_values[1], 16)
            match_code = int(hex_values[2], 16)
        else:
            return None

        return {
            'length': length,
            'device_id': parsed_device_id,
            'match_code': match_code,
            'rssi': rssi
        }

    except Exception as e:
        print(f"Parse error: {e}")
        return None

def get_switch_state():
    state = 0
    for pin, bit_position in switch_pins:
        if GPIO.input(pin) == False:  # active-low
            state |= (1 << bit_position)
    return state

def rssi_to_radius(rssi, rssi_min=-110, rssi_max=-20, min_radius=20, max_radius=120):
    # Clamp RSSI to expected bounds
    rssi = max(min(rssi, rssi_max), rssi_min)
   
    # Normalize RSSI to 0–1
    norm = (rssi - rssi_min) / (rssi_max - rssi_min)
   
    # Invert it so -40 (strong) = small radius, -90 = big radius
    norm = 1 - norm
   
    # Scale to radius range
    return int(min_radius + norm * (max_radius - min_radius))

BIT_COLORS = {
    0: "red",
    1: "green",
    2: "blue",
    3: "yellow",
    4: "purple",
    5: "cyan",
    6: "orange",
    7: "pink"
}

COLOR_RGB = {
    0: (10,0,0),
    1: (0,10,0),
    2: (0,0,10),
    3: (30,30,0),
    4: (30,0,30),
    5: (0,30,30),
    6: (30,10,0),
    7: (30,5,10)
}
def get_matched_colors(shared):
    colors = []
    for i in range(8):
        if (shared >> i) & 1:
            colors.append(BIT_COLORS[i])
    return colors
def get_current_color(color_list, interval=0.5):
    if not color_list:
        return "black"
    index = int(time.time() / interval) % len(color_list)
    return color_list[index]

def show_splash_screen():
    draw.rectangle((0, 0, 240, 240), fill="black")
    draw.text((40, 80), "SIGNAL SYNC", fill="white", font=font)
    draw.text((60, 130), "System Initializing...", fill="gray", font=font)
    disp.ShowImage(image1)
    time.sleep(2)  # show for 2 seconds
show_splash_screen()

def draw_all_devices(received_id, switch_state):
    draw.rectangle((0, 0, 240, 240), fill="black")# clear screen
    draw.polygon([(120,2),(116,10),(124,10)], fill="white")
    draw.text((100, 12), f"ID: {device_id}", fill="white", font=font)  # Your device ID at the top
    
    if not devices:
        draw.text((60,100), "SIGNAL SYNC", fill="white", font=font)
        disp.ShowImage(image1)
        return

    center_x, center_y = 120, 120
        
    for received_id, data in devices.items():
        rssi = data['rssi']
        match_code = data['match_code']
        shared = switch_state & match_code
        matched_colors = get_matched_colors(shared)
        color = get_current_color(matched_colors)
        last_rssi = data.get('last_rssi')
        trend = 'stable'

        # Determine trend
        if last_rssi is not None:
            if abs(rssi - last_rssi) >= 1:
                trend = 'closer' if rssi > last_rssi else 'away'   

        radius = rssi_to_radius(rssi)
        device_label = f"{received_id}"

        draw.ellipse(
            (center_x - radius, center_y - radius,
            center_x + radius, center_y + radius),
            outline=color,
            width=3
            
        )
        angle_offset = (received_id %12) *30
        angle_rad = math.radians(angle_offset)
        label_distance = radius + 20
        label_x = center_x + int(label_distance * math.cos(angle_rad))
        label_y = center_y + int(label_distance * math.sin(angle_rad))
        draw.text((label_x, label_y), device_label, fill=color, font=font)
        draw.line(
            (center_x + radius * math.cos(angle_rad), center_y + radius * math.sin(angle_rad),
             label_x, label_y),
            fill=color,
            width=1
            )
                        # Draw movement arrow (triangle)
        if trend == 'closer':
            arrow = [
                (label_x + 4, label_y - 12),
                (label_x, label_y - 4),
                (label_x + 8, label_y - 4)
            ]
            draw.polygon(arrow, fill=color)
        elif trend == 'away':
            arrow = [
                (label_x + 4, label_y + 18),
                (label_x, label_y + 10),
                (label_x + 8, label_y + 10)
            ]
            draw.polygon(arrow, fill=color)

    disp.ShowImage(image1)
    
# ----------------- Main Loop -----------------
print("Ready. Monitoring buttons + UART + switch state...\n")

try:
    while True:
        current_time = time.time()        
        # Handle button presses (demo)
        for pin in last_trigger_time:
            if GPIO.input(pin) == False and (current_time - last_trigger_time[pin]) > cooldown_duration:
                print(f"Button on pin {pin} pressed")
                last_trigger_time[pin] = current_time
                GPIO.output(19, True)

        # Turn off LED after cooldown
        if GPIO.input(19) and (current_time - last_trigger_time[23]) > cooldown_duration:
            GPIO.output(19, False)

        # Get switch state and send over UART
        switch_state = get_switch_state()
        if current_time - last_print_time > 1.5:
            message = f"ID:{device_id} STATE:{switch_state:08b}\n"
            ser.write(bytes([device_id, switch_state]))
            print("sent over serial:", message.strip())
            last_print_time = current_time
            
        pixels.fill((0,0,0))
        for i in range(16):
            if(switch_state >> i) & 1:
                pixels[i] = COLOR_RGB[i]
                
        pixels.show()

        # Receive from UART
        try:
            line = ser.read_until(b'\n').decode(errors='ignore').strip()           
            if line:
                print(f"received: {line}")

                parsed = parse_packet_line(line)
                if not parsed:
                    continue

                received_id = parsed['device_id']
                match_code = parsed['match_code']
                rssi = parsed['rssi']

                # Update or add device to tracking
                if received_id not in devices:
                    devices[received_id] = {
                        'match_code': match_code,
                        'rssi': rssi,
                        'last_rssi': None,
                        'last_seen': time.time(),
                    }
                else:
                    # move current rssi into last_rssi before updating
                    devices[received_id]['last_rssi'] = devices[received_id].get('rssi', rssi)
                    devices[received_id]['rssi'] = rssi
                    devices[received_id]['match_code'] = match_code
                    devices[received_id]['last_seen'] = time.time()
                    print(f"ID {received_id}: {devices[received_id]}")
                    
            # Cleanup inactive devices (e.g., after 10 seconds of silence)
            INACTIVITY_TIMEOUT = 5  # seconds

            current_time = time.time()
            to_remove = []

            for received_id, data in devices.items():
                if current_time - data.get('last_seen', 0) > INACTIVITY_TIMEOUT:
                    to_remove.append(received_id)

            for received_id in to_remove:
                print(f"[TIMEOUT] Removing inactive device {received_id}")
                del devices[received_id]
                
            if current_time - last_draw_time > draw_interval:
                draw_all_devices(received_id, switch_state)
                last_draw_time = current_time
                
            time.sleep(0.001)


                                           
        except Exception as e:
            print(f"Serial read error: {e}")
        
       
        time.sleep(0.1)

except KeyboardInterrupt:
    print("Exiting cleanly...")
    #disp.module_exit()
    pixels.fill((0,0,0))
    pixels.show()
    GPIO.cleanup()
    ser.close()
