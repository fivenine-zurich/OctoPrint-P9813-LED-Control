# coding=utf-8
from __future__ import absolute_import
import octoprint.plugin

from flask import jsonify

import time
import threading

from octoprint_P9813LedControl.ledstrip import LEDStrip


class P9813LedControlPlugin(octoprint.plugin.SettingsPlugin,
                            octoprint.plugin.AssetPlugin,
                            octoprint.plugin.TemplatePlugin,
                            octoprint.plugin.SimpleApiPlugin):

    lights_on = True  # Lights should be on by default, makes sense.
    torch_on = False  # Torch is off by default, because who would want that?

    torch_timer = None  # Timer for torch function
    return_timer = None  # Timer object when we want to return to idle.

    # Idle, startup, progress etc. Used to put the old effect back on settings change/light switch
    current_state = 'startup'
    led = LEDStrip(13, 12)

    def get_api_commands(self):
        # Simple API plugin
        return dict(
            toggle_lights=[],
            activate_torch=[],
        )

    def on_api_get(self, request=None):
        return jsonify(
            lights_status=self.get_lights_status(),
            torch_status=self.get_torch_status()
        )

    def on_api_command(self, command, data):
        if command == 'toggle_lights':
            self.toggle_lights()
            return self.on_api_get()
        elif command == 'activate_torch':
            self.activate_torch()
            return self.on_api_get()

    def toggle_lights(self):
        # Switch from False -> True or True -> False
        # Switch from False -> True or True -> False
        self.lights_on = False if self.lights_on else True
        self.update_effect('on' if self.lights_on else 'off')
        self._logger.debug("Toggling lights to {}".format(
            'on' if self.lights_on else 'off'))

    def activate_torch(self):
        if self.torch_timer and self.torch_timer.is_alive():
            self.torch_timer.cancel()

        self._logger.debug("Starting timer for {} secs, to deativate torch".format(
            self._settings.get_int(['torch_timer'])))
        self.torch_timer = threading.Timer(
            int(self._settings.get_int(['torch_timer'])), self.deactivate_torch)
        self.torch_timer.daemon = True
        self.torch_timer.start()
        self.torch_on = True
        self.update_effect('torch')

    def deactivate_torch(self):
        self._logger.debug(
            "Deactivating torch mode, torch on currently: {}".format(self.torch_on))
        if self.torch_on:
            self.update_effect(self.current_state)
            self.torch_on = False

    def update_effect(self, mode_name, value=None):
        self._logger.debug(
            "Update Effect: {}".format(mode_name))

        if self.return_timer is not None and self.return_timer.is_alive():
            self.return_timer.cancel()

        if mode_name != 'torch' and self.torch_on:
            self.torch_on = False

        if mode_name in ['on']:
            self.led.setcolourwhite()
            return

        if mode_name == 'off':
            self.led.setcolouroff()
            return

        if mode_name == 'torch':
            if self.torch_on:
                self.led.setcolourwhite()
            else:
                self.led.setcolouroff()
                return

    def get_lights_status(self):
        return self.lights_on

    def get_torch_status(self):
        return self.torch_on

    def on_settings_save(self, data):
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)

    # ~~ SettingsPlugin mixin

    def get_settings_defaults(self):
        return dict(
            startup_enabled=True,
            startup_color='#00ff00',
            startup_delay='75',

            idle_enabled=True,
            idle_color='#00ccf0',
            idle_delay='75',

            disconnected_enabled=True,
            disconnected_color='#000000',
            disconnected_delay='25',

            failed_enabled=True,
            failed_effect='Pulse',
            failed_color='#ff0000',
            failed_delay='10',

            success_enabled=True,
            success_effect='Rainbow',
            success_color='#000000',
            success_delay='25',
            success_return_idle='0',

            paused_enabled=True,
            paused_effect='Bounce',
            paused_color='#0000ff',
            paused_delay='40',

            progress_print_enabled=True,
            progress_print_color_base='#000000',
            progress_print_color='#00ff00',

            printing_enabled=False,
            printing_effect='Solid Color',
            printing_color='#ffffff',
            printing_delay=1,

            progress_heatup_enabled=True,
            progress_heatup_color_base='#0000ff',
            progress_heatup_color='#ff0000',
            progress_heatup_tool_enabled=True,
            progress_heatup_bed_enabled=True,
            progress_heatup_tool_key=0,

            torch_enabled=True,
            torch_effect='Solid Color',
            torch_color='#ffffff',
            torch_delay=1,
            torch_timer=15,
        )

    # ~~ AssetPlugin mixin

    def get_assets(self):
        # Define your plugin's asset files to automatically include in the
        # core UI here.
        return dict(
            js=["js/P9813LedControl.js"],
            css=["css/P9813LedControl.css", "css/fontawesome5_stripped.css"],
            less=["less/P9813LedControl.less"]
        )

    def get_template_configs(self):
        return [
            dict(type="settings", name="P9813 LED Control",
                 template="ledcontrol_settings.jinja2", custom_bindings=False),
            dict(type="navbar", name="P9813 LED Control",
                 template="ledcontrol_navbar.jinja2", custom_bindings=False)
        ]

        # ~~ Softwareupdate hook

    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return dict(
            P9813LedControl=dict(
                displayName="P9813 LED Control",
                displayVersion=self._plugin_version,

                # version check: github repository
                type="github_release",
                user="Tobias Herrmann",
                repo="P9813 LED Control",
                current=self._plugin_version,

                # update method: pip
                pip="https://github.com/fiveninedigital/OctoPrint-P9813-LED-Control/archive/{target_version}.zip"
            )
        )


__plugin_pythoncompat__ = ">=3,<4"


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = P9813LedControlPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
