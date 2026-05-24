# Novatek

Effortlessly connect, discover, and monitor your Novatek-Electro Wi-Fi power meter or voltage relay in Home Assistant with this fully local LAN integration. It talks directly to supported EM-125, EM-125S, EM-126T, EM-126TS, and EM-129 devices over the documented HTTP API and keeps everyday polling on your network instead of in a vendor cloud.

## Features

- **Local LAN integration:** Direct HTTP communication with the device, no vendor cloud required for normal operation.
- **Automatic discovery:** Supports DHCP discovery for compatible hostnames.
- **UI-based setup:** Config-flow based, with no YAML required.
- **Broad device support:** Recognizes EM-125, EM-125S, EM-126T, EM-126TS, and EM-129 models.
- **Energy dashboard ready:** Exposes active energy as a `total_increasing` energy sensor suitable for Home Assistant Energy.
- **Rich electrical telemetry:** Voltage, current, frequency, active/apparent power, active energy (total, daily, weekly, monthly), apparent energy.
- **Relay control:** Turn the load relay on/off directly from Home Assistant.
- **Device status and fault monitoring:** Dedicated binary sensors for APV countdowns, WiFi/NTP/cloud connectivity, and all hardware fault flags.
- **Flexible installation:** Install through HACS or manually under `custom_components/novatek`.

## Requirements

- Home Assistant `2024.4.0` or newer
- A Novatek-Electro EM-125/EM-126/EM-129 family device reachable from Home Assistant over HTTP
- The device password used for its built-in web/API login
- Network access from Home Assistant to the device on your LAN

## Installation

### Via HACS (recommended)

1. Open HACS -> Integrations -> menu -> **Custom repositories**.
2. Add this repository URL with category **Integration**.
3. Install **Novatek**.
4. Restart Home Assistant.

### Manual

1. Copy `custom_components/novatek` into your Home Assistant config directory under `custom_components/`.
2. Restart Home Assistant.

## Setup

### DHCP discovery (automatic)

1. Make sure the device is on the same LAN as Home Assistant.
2. Home Assistant will detect the device automatically in **Settings -> Devices & services**.
3. Open the discovered **Novatek** entry and enter the device password.

### Manual setup

1. Go to **Settings -> Devices & services -> Add integration** and search for **Novatek**.
2. Enter the device IP address and password.

## Authentication

The device uses a local SHA-1 challenge-response login flow.

- The integration first reads the model identifier and a per-session salt from the device.
- It then computes `SHA1(<model_name> + <password> + <salt>)` and exchanges that for a session ID.
- All subsequent requests are performed locally against the authenticated session.

After setup, day-to-day polling stays entirely local over your LAN.

## Entities

### Sensors

| Entity | Unit | Notes |
|---|---|---|
| Voltage | V | |
| Current | A | |
| Frequency | Hz | |
| Active power | W | |
| Apparent power | VA | |
| Active energy | Wh → kWh | Total accumulated |
| Active energy today | Wh → kWh | Resets at midnight on device |
| Active energy this week | Wh → kWh | |
| Active energy this month | Wh → kWh | |
| Apparent energy | VAh | |
| Auto-reconnect countdown | s | Diagnostic — seconds until APV reconnect |
| Temperature | °C | EM-126T / EM-126TS only |

### Switch

| Entity | Notes |
|---|---|
| Load relay | Turns the load on or off |

### Buttons

| Entity | Category | Notes |
|---|---|---|
| Reset energy counters | Config | Resets all energy totals on the device |
| Reboot device | Config | Reboots the device firmware |

### Binary sensors

**Device state** (`sys_flag`): load relay state, APV voltage/current/power/frequency countdowns, manual control, schedule control, vacation lock, front panel lock, NTP sync, Wi-Fi connected, cloud service, NTP service.

**Faults** (`faul_flag`): overvoltage, undervoltage, voltage > 290 V, overcurrent, current > 17 A, overpower, overfrequency, underfrequency, temperature sensor fault/open/short, relay fault, RTC fault, operating time limit, APV reconnect limits, not calibrated, settings corrupted.

## Caveats

- The device only allows one active web/API session at a time. Opening the device's own web UI will invalidate Home Assistant's session, and vice versa. The current update will fail and the next scheduled poll will re-authenticate automatically.
- DHCP discovery matches hostnames advertising as `em-129*`, `em-126*`, `em-125*`, and `novatek*`.
- For reliable connectivity, keep Home Assistant on the same LAN as the device or assign the device a static IP via DHCP reservation to avoid disruption during lease renewal.
- The polling interval is fixed at `5` seconds.
- Resetting energy counters via the **Reset energy counters** button will cause all energy sensors to drop to zero. Home Assistant's long-term statistics recorder handles this automatically.

## Supported Devices

| Model | Temperature sensor |
|---|---|
| EM-125 | No |
| EM-125S | No |
| EM-126T | Yes |
| EM-126TS | Yes |
| EM-129 | No |
