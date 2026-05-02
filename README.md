# 📡 Signal Sync

> A handheld RF tracking device that lets people discover others with shared interests at large events — no smartphone or internet required.

**Capstone Project | Conestoga College**  
Electronics Engineering Technology (Telecommunications) & Computer Engineering Technology  
**Team:** Carson Soers (Hardware) · Edward Estacion (Software)

---

## 🎯 What It Does

Signal Sync is a wearable device that broadcasts and receives sub-1GHz radio signals to help users find others nearby who share the same interest. Each user selects one of 8 interest settings using physical switches. The device then:

- Transmits a unique packet over **915 MHz** (2-GFSK modulation) containing its **Device ID** and **match code**
- Receives packets from nearby devices and computes signal strength (**RSSI**)
- Displays other devices as **concentric rings** on a circular LCD — ring size reflects proximity
- Lights up **NeoPixel LEDs** in the colour(s) matching shared interests
- Automatically removes devices that go out of range (5-second inactivity timeout)

No app. No login. No internet. Just pick up a device, flip a switch, and find your people.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────┐
│                   User Device                       │
│                                                     │
│  [8 DIP Switches] ──► [Raspberry Pi Zero W]        │
│                              │                      │
│                         UART Serial                 │
│                              │                      │
│                    [EFR32ZG28 Radio Board]          │
│                       915 MHz RF ◄──────────────►  │
│                    (Other Devices)                  │
│                                                     │
│  Raspberry Pi also drives:                          │
│   • Waveshare 1.28" Round LCD  (SPI)               │
│   • NeoPixel LED Strip         (GPIO D12)           │
│   • Push Buttons               (GPIO)               │
└─────────────────────────────────────────────────────┘
```

**Data flow:**  
Switches → Pi reads state → Pi sends `[Device ID, Match Code]` over UART → Radio board transmits RF packet → Other devices receive → RSSI + IDs sent back to Pi via UART → Pi updates LCD display

---

## 🧰 Hardware

| Component | Role |
|-----------|------|
| Raspberry Pi Zero W | Main processor — runs Python, drives LCD & LEDs, handles UART |
| Silicon Labs EFR32ZG28 | Sub-GHz radio (915 MHz, 2-GFSK) — handles all RF Tx/Rx |
| Waveshare 1.28" Round Touch LCD | Circular radar-style display showing nearby devices |
| NeoPixel LED Strip (8 LEDs) | Colour-coded interest indicators |
| 8x DIP Switches | User interest selection (1 bit per interest, 0x00–0xFF) |
| Push Buttons | Auxiliary controls |

**Key Electrical Details:**
- Switches use 10kΩ pull-up resistors to a 5V rail (active-low GPIO reads)
- LCD connected via SPI; Touch via I2C (touch unused in final build)
- Radio board connected to Pi via hardware UART (`/dev/serial0`, 115200 baud)
- LED strip data line on GPIO D12

---

## 💻 Software

### Raspberry Pi — Python (`raspberry-pi/main.py`)
- Reads 8-bit switch state from GPIO
- Sends `[Device ID, Match Code]` bytes over UART every 1.5 seconds
- Parses incoming UART packets (regex extracts Device ID, Match Code, RSSI)
- Tracks active devices in a dictionary; removes inactive ones after 5 seconds
- Draws radar display on circular LCD using PIL:
  - Ring radius = function of RSSI (stronger signal → smaller ring = closer device)
  - Ring colour = bitwise AND of local and remote match codes → shared interests
  - Arrows indicate whether a device is getting closer or moving away
- Drives NeoPixels with colours mapped to each active interest bit

### EFR32ZG28 — C / Simplicity Studio (`firmware/`)
**`RxTxCode.c`** (production firmware):
- Listens for 2-byte UART message from Pi `[Device ID, Match Code]`
- Inserts values into a 16-byte RAIL payload
- Transmits at 915 MHz every 5 seconds via a sleep timer
- On packet receive, formats `Device ID, Match Code, RSSI` and sends back to Pi over UART

**`DummyTxCode.c`** (test transmitter):
- Standalone dummy transmitter used during range and packet testing
- Transmits a fixed payload every 10 seconds; logs received packets to console

---

## 📶 RF Packet Structure

| Byte | Content |
|------|---------|
| 0 | Payload length (15) |
| 1 | Device ID |
| 2 | Match Code (interest bitmask) |
| 3–14 | Padding / future use |
| RSSI | Appended by RAIL on receive |

Interest matching uses a **bitwise AND**: if `local_match & remote_match != 0`, at least one shared interest exists. Each set bit maps to a colour (red, green, blue, yellow, purple, cyan, orange, pink).

---

## 📁 Repository Structure

```
SignalSync/
├── README.md
├── firmware/                   # C code for EFR32ZG28 (Simplicity Studio)
│   ├── RxTxCode.c              # Production Rx/Tx firmware
│   └── DummyTxCode.c           # Test transmitter
├── raspberry-pi/               # Python code for Raspberry Pi Zero W
│   ├── main.py                 # Production application
│   └── test/
│       └── Test1Code.py        # Early GPIO + LED + OLED prototype
├── docs/                       # Project documentation
│   ├── FinalReportProposal.pdf
│   ├── ProjectSchematic.pdf
│   ├── RadioBoardSchematics.pdf
│   ├── LCD_Schematic.pdf
│   ├── Pseudocode_and_Flowcharts.pdf
│   └── SprintBacklog.xlsx
├── hardware/
│   └── PrototypingNotes.md     # Protoboard wiring notes
└── testing/
    └── TestsAndResults.md      # Test descriptions and outcomes
```

---

## 🧪 Testing Summary

| Test | Description | Result |
|------|-------------|--------|
| 1 | GPIO + switches + NeoPixel colour output | ✅ Passed |
| 2 | UART communication between Pi and EFR32 | ✅ Passed |
| 3 | RAIL packet Tx/Rx using Simplicity Studio + Tera Term | ✅ Passed |
| 4 | Custom 915 MHz packets with RSSI readback | ✅ Passed |
| 5 | Round LCD SPI output with PIL drawing | ✅ Passed |
| 6 | Indoor range test (walking test) | ✅ ~40m through concrete wall |
| 7 | Autostart on Pi boot via crontab | ✅ Passed |

---

## ⚙️ Setup & Running

### Raspberry Pi
```bash
# Install dependencies
pip install RPi.GPIO pyserial Pillow spidev neopixel adafruit-blinka

# Run manually
python3 raspberry-pi/main.py

# Autostart on boot (production)
# Add to crontab: @reboot python3 /path/to/main.py
```

### EFR32ZG28 Firmware
1. Open **Simplicity Studio 5**
2. Import project from `firmware/`
3. Flash `RxTxCode.c` to the radio board via USB J-Link
4. Connect UART pins to Pi GPIO 14/15 (TX/RX) — cross-wired

---

## 📋 Constraints & Standards

- Transmits at **915 MHz** (sub-1GHz, avoids crowded 2.4GHz band)
- Complies with **RSS-Gen** (Canadian RF device requirements)
- Designed with **IEC 62368-1** safety principles in mind
- RSSI range calibrated for **−20 dBm to −110 dBm**; display adjusted for indoor falloff at ~−90 dBm

---

## 📄 License

This project was developed as a Capstone project at Conestoga College. All rights reserved by the authors.

---

*Built with ❤️ by Carson Soers & Edward Estacion — Conestoga College, 2024–2025*
