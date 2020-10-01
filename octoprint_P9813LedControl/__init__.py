# coding=utf-8
from __future__ import absolute_import
import octoprint.plugin

from flask import jsonify

import time
import threading

from octoprint_P9813LedControl.ledstrip import LEDStrip

BLOCKING_TEMP_GCODES = ["M109", "M190"]
ON_AT_COMMAND = 'WS_LIGHTSON'
OFF_AT_COMMAND = 'WS_LIGHTSOFF'
AT_COMMANDS = [ON_AT_COMMAND, OFF_AT_COMMAND]


class P9813LedControlPlugin(
        octoprint.plugin.StartupPlugin,
        octoprint.plugin.ShutdownPlugin,
        octoprint.plugin.SettingsPlugin,
        octoprint.plugin.AssetPlugin,
        octoprint.plugin.TemplatePlugin,
        octoprint.plugin.SimpleApiPlugin,
        octoprint.plugin.ProgressPlugin,
        octoprint.plugin.EventHandlerPlugin,
        octoprint.plugin.RestartNeedingPlugin):

    lights_on = False  # Lights are off by default
    torch_on = False  # Torch is off by default, because who would want that?

    torch_timer = None  # Timer for torch function
    return_timer = None  # Timer object when we want to return to idle.
    auto_off_timer = None  # Timer object for turning the lights off

    # Idle, startup, progress etc. Used to put the old effect back on settings change/light switch
    current_state = 'off'

    # True when heating is detected, options below are helpers for tracking heatup.
    heating = False
    temp_target = 0
    current_heater_heating = None
    tool_to_target = 0  # Overridden by the plugin settings

    led = None

    supported_events = {
        'Connected': 'idle',
        'Disconnected': 'disconnected',
        'PrintFailed': 'failed',
        'PrintDone': 'success',
        'PrintPaused': 'paused'
    }

    def on_after_startup(self):
        self.restart_strip()
        self.update_effect("off")

    def return_to_idle(self):
        self.update_effect('idle')

    def return_to_off(self):
        self.update_effect('off')

    def on_event(self, event, payload):
        if self.led == None:
            self.restart_strip()

        try:
            self.update_effect(self.supported_events[event])
        except KeyError:  # The event isn't supported
            pass

    # Shutdown plugin
    def on_shutdown(self):
        self.update_effect('off')

    def on_print_progress(self, storage, path, progress):
        if progress == 100 or self.current_state == 'success' or self.heating:
            return

        if self._settings.get_boolean(['printing_enabled']):
            self.update_effect('printing')
            return

        self.update_effect('progress_print', progress)

    def get_api_commands(self):
        # Simple API plugin
        return dict(
            toggle_lights=[],
            activate_torch=[],
            get_status=[]
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
        elif command == 'get_status':
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
            self.torch_on = False
            self.update_effect(self.current_state)

    def update_effect(self, mode_name, value=None, m150=None):
        if self.return_timer is not None and self.return_timer.is_alive():
            self.return_timer.cancel()

        if self.auto_off_timer is not None and self.auto_off_timer.is_alive():
            self.auto_off_timer.cancel()

        if mode_name in ['on']:
            self.led.setcolourwhite()
            self.lights_on = True
            self._logger.debug("Turning lights on")
            return

        if mode_name in ['off', 'disconnected']:
            self.led.setcolouroff()
            self.lights_on = False
            self._logger.debug("Turning lights off")
            return

        if 'torch' in mode_name:
            if self.torch_on:
                self.led.setcolourwhite()
            else:
                self.led.setcolouroff()
            return

        if 'idle' in mode_name and self._settings.get_boolean(['idle_enabled']):
            self.setModeColor(mode_name)

            auto_off_time = self._settings.get_int(
                ['auto_off_time'])
            if auto_off_time > 0:
                self.auto_off_timer = threading.Timer(
                    auto_off_time, self.return_to_off)
                self.auto_off_timer.daemon = True
                self.auto_off_timer.start()
            return

        if 'paused' in mode_name and self._settings.get_boolean(['paused_enabled']):
            self.setModeColor(mode_name)
            return

        if 'failed' in mode_name and self._settings.get_boolean(['failed_enabled']):
            self.setModeColor(mode_name)
            return

        if 'success' in mode_name and self._settings.get_boolean(['success_enabled']):
            self.setModeColor(mode_name)

            return_idle_time = self._settings.get_int(['success_return_idle'])
            if return_idle_time > 0:
                self.return_timer = threading.Timer(
                    return_idle_time, self.return_to_idle)
                self.return_timer.daemon = True
                self.return_timer.start()
            return

        if 'progress_heatup' in mode_name and self._settings.get_boolean(['progress_heatup_enabled']):
            self.setModeColor(mode_name)
            return

        if 'progress' in mode_name:
            if not value:
                self._logger.warning(
                    "No value supplied with progress style effect, ignoring")
                return

            self.setModeColor(mode_name)
            self.current_state = '{} {}'.format(mode_name, value)

    def get_lights_status(self):
        return (self.lights_on or self.torch_on)

    def get_torch_status(self):
        return self.torch_on

    def setModeColor(self, mode):
        color = self._settings.get(['{}_color'.format(mode)]).strip('#')
        self._logger.debug(
            "Setting {} color to #{}".format(mode, color))

        self.lights_on = True
        self.led.setcolourhex(color)

    def restart_strip(self):
        self._logger.debug("Restarting Lights")

        if self.led is not None:
            self.led.cleanup()

        self.led = LEDStrip(self._settings.get_int(
            ['ledgpio_clk']), self._settings.get_int(['ledgpio_data']))
        self.led.setcolouroff()

    @ staticmethod
    def calculate_heatup_progress(current, target):
        return round((current / target) * 100)

    def process_gcode_q(self, comm_instance, phase, cmd, cmd_type, gcode, subcode=None, tags=None, *args, **kwargs):
        if not self._settings.get_boolean(['progress_heatup_bed_enabled']) and not self._settings.get_boolean(['progress_heatup_tool_enabled']) and not self._settings.get_boolean(['intercept_m150']):
            return

        if gcode in BLOCKING_TEMP_GCODES and (self._settings.get_boolean(['progress_heatup_bed_enabled']) or self._settings.get_boolean(['progress_heatup_tool_enabled'])):
            bed_or_tool = {
                'M109': 'T{}'.format(self.tool_to_target) if self._settings.get_boolean(['progress_heatup_tool_enabled']) else None,
                'M190': 'B' if self._settings.get_boolean(['progress_heatup_bed_enabled']) else None
            }
            if (gcode in BLOCKING_TEMP_GCODES) and bed_or_tool[gcode]:
                self.heating = True
                self.current_heater_heating = bed_or_tool[gcode]
            else:
                self.heating = False
        else:
            self.heating = False

        if gcode == 'M150' and self._settings.get_boolean(['intercept_m150']):
            self.update_effect('M150', m150=cmd)
            return None,

        return

    def temperatures_received(self, comm_instance, parsed_temperatures, *args, **kwargs):
        if self.heating and self.current_heater_heating:
            try:
                current_temp, target_temp = parsed_temperatures[self.current_heater_heating]
            except KeyError:
                self._logger.error("Could not find temperature of tool T{}, not able to show heatup progress.".format(
                    self.current_heater_heating))
                self.heating = False
                return
            if target_temp:  # Sometimes we don't get everything, so to update more frequently we'll store the target
                self.temp_target = target_temp
            if self.temp_target > 0:  # Prevent ZeroDivisionError, or showing progress when target is zero
                self.update_effect('progress_heatup', self.calculate_heatup_progress(
                    current_temp, self.temp_target))
        return parsed_temperatures

    def process_at_command(self, comm, phase, command, parameters, tags=None, *args, **kwargs):
        if command not in AT_COMMANDS or not self._settings.get(['at_command_reaction']):
            return

        if command == ON_AT_COMMAND:
            self._logger.debug("Recieved gcode @ command for lights on")
            self.lights_on = True
            self.update_effect('on')
        elif command == OFF_AT_COMMAND:
            self._logger.debug("Recieved gcode @ command for lights off")
            self.lights_on = False
            self.update_effect('off')

    # ~~ SettingsPlugin mixin

    def get_settings_defaults(self):
        return dict(
            ledgpio_clk=13,
            ledgpio_data=12,

            idle_enabled=True,
            idle_color='#00ccf0',
            idle_delay='75',

            failed_enabled=True,
            failed_color='#ff0000',
            failed_delay='10',

            success_enabled=True,
            success_color='#000000',
            success_delay='25',
            success_return_idle='0',

            paused_enabled=True,
            paused_color='#0000ff',
            paused_delay='40',

            progress_print_enabled=True,
            progress_print_color_base='#000000',
            progress_print_color='#00ff00',

            printing_enabled=False,
            printing_color='#ffffff',
            printing_delay=1,

            progress_heatup_enabled=True,
            progress_heatup_color='#ff0000',
            progress_heatup_tool_enabled=True,
            progress_heatup_bed_enabled=True,
            progress_heatup_tool_key=0,

            auto_off_time=600,

            torch_enabled=True,
            torch_color='#ffffff',
            torch_delay=1,
            torch_timer=15,
        )

    # Settings plugin
    def on_settings_save(self, data):
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)

        self.tool_to_target = self._settings.get_int(
            ['progress_heatup_tool_key'])
        if not self.tool_to_target:
            self.tool_to_target = 0

        self.restart_strip()

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
                 template="ledcontrol_navbar.jinja2", custom_bindings=True)
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
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.comm.protocol.gcode.queued": __plugin_implementation__.process_gcode_q,
        "octoprint.comm.protocol.temperatures.received": __plugin_implementation__.temperatures_received,
        "octoprint.comm.protocol.atcommand.sending": __plugin_implementation__.process_at_command
    }
