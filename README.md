# OctoPrint P9813 LED Control

Adds support for controlling and displaying printer status with P9813 controller based LED's connected to a Raspberry Pi.

## Setup

Install via the bundled [Plugin Manager](https://docs.octoprint.org/en/master/bundledplugins/pluginmanager.html)
or manually using this URL:

    https://github.com/fiveninedigital/OctoPrint-P9813-LED-Control/archive/master.zip

**TODO:** Describe how to install your plugin, if more needs to be done than just installing it via pip or through
the plugin manager.

## Configuration

**TODO:** Describe your plugin's configuration options (if any).

## Development

Setup local OctoPrint installation and install the plugin for local development.

```sh
virtualenv --python=/usr/bin/python3 venv3
source venv3/bin/activate
pip install "OctoPrint>=1.4.0rc1"
pip install -e ./
```

Start the local OctoPrint instance.

```sh
source venv3/bin/activate
octoprint serve --debug
```

### Thanks

This plugin is based on the excellent [OctoPrint WS281x LED Status Plugin](https://github.com/cp2004/OctoPrint-WS281x_LED_Status).
