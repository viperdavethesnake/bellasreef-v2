# Bella's Reef - Temperature Service

## Overview

The Temperature Service is a dedicated microservice responsible for managing and monitoring 1-wire temperature sensors (like the DS18B20) within the Bella's Reef ecosystem. It provides a simple, focused API for discovering sensors, reading current temperatures, and managing probe configurations in the database.

This service is designed to run on a Raspberry Pi with connected 1-wire sensors.

## Features

-   **Sensor Discovery:** Automatically detects all connected 1-wire sensors.
-   **Real-time Readings:** Provides on-demand temperature readings (in Celsius).
-   **Configuration Management:** Stores probe nicknames, roles, and settings in the central database.
-   **Hardware Check:** Includes an endpoint to diagnose the 1-wire subsystem.
-   **Enable/Disable:** Can be completely disabled via an environment variable.
-   **Secure:** API endpoints are protected by a static bearer token.

---

## Getting Started

### Prerequisites

-   A Raspberry Pi with Raspberry Pi OS.
-   Python 3.8+
-   PostgreSQL database accessible from the Pi.
-   1-wire temperature sensors (DS18B20) physically connected to the Pi's GPIO pins.

### 1. Enable 1-Wire Interface

You must enable the 1-wire kernel module.

1.  Open the boot configuration file:
    ```bash
    sudo nano /boot/config.txt
    ```
2.  Add the following line to the bottom of the file. This configures the 1-wire bus to use GPIO pin 4 (the default for this service).
    ```
    dtoverlay=w1-gpio,gpiopin=4
    ```
3.  Save the file (`Ctrl+X`, then `Y`, then `Enter`).
4.  Reboot the Raspberry Pi for the changes to take effect:
    ```bash
    sudo reboot
    ```

### 2. Setup

The setup script automates the creation of the virtual environment and installation of dependencies.

1.  **Navigate to the project root** on your Raspberry Pi.
2.  **Run the setup script:**
    ```bash
    ./scripts/setup_temp.sh
    ```
    This will:
    - Check if the service is enabled in the `.env` file.
    - Create a Python virtual environment at `temp/bellasreef-temp-venv`.
    - Install all required Python packages.
    - Copy `temp/env.example` to `temp/.env` if it doesn't exist.

### 3. Configuration

Before starting the service, you must configure it by editing the `.env` file.

1.  **Open the environment file:**
    ```bash
    nano temp/.env
    ```
2.  **Update the following required variables:**
    -   `TEMP_ENABLED`: Must be `true` for the service to run.
    -   `DATABASE_URL`: The full connection string for your PostgreSQL database.
    -   `SERVICE_TOKEN`: A secure, secret token for API authentication. **Do not use the default.** Generate a new one with `openssl rand -hex 32`.

### 4. Start the Service

Once configured, you can start the service.

```bash
./scripts/start_temp.sh
```

The service will be running and accessible at `http://<your-pi-ip>:8001`.

---

## API Endpoints

-   **`GET /probe/health`** (Public): A public endpoint to check if the service is running.
-   **`GET /probe/discover`**: Discovers and returns the hardware IDs of all attached 1-wire sensors. No authentication required.
-   **`GET /probe/check`**: Checks the status of the 1-wire subsystem. No authentication required.
-   **`GET /probe/list`**: Lists all probes configured in the database. Requires authentication.
-   **`POST /probe/`**: Creates a new probe configuration in the database. Requires authentication.
-   **`GET /probe/{hardware_id}/current`**: Gets the current temperature from the specified probe. Requires authentication.
-   **`GET /probe/{hardware_id}/history`**: (Stub) A placeholder for future history functionality. Requires authentication.

Full interactive documentation is available at the `/docs` endpoint (e.g., `http://localhost:8001/docs`) when the service is running.

---

## Troubleshooting

-   **Service Fails to Start:**
    -   Ensure `TEMP_ENABLED` is set to `true` in `temp/.env`.
    -   Verify your `DATABASE_URL` is correct.
    -   Make sure all dependencies were installed correctly by running the setup script.

-   **`NoSensorFoundError` or `KernelModuleLoadError`:**
    -   Double-check that you have enabled the `w1-gpio` overlay in `/boot/config.txt` and rebooted.
    -   Verify your sensor wiring. The data line must be connected to the correct GPIO pin (default is 4).
    -   Use the `/probe/check` endpoint to get diagnostic information.

-   **Authentication Errors (403 Forbidden):**
    -   Make sure you are including the `Authorization` header with the `Bearer` token.
    -   Verify the `SERVICE_TOKEN` in your request matches the one in `temp/.env`.