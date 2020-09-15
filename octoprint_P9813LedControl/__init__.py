# coding=utf-8
from __future__ import absolute_import
import octoprint.plugin


class P9813ledcontrolPlugin(octoprint.plugin.SettingsPlugin,
                            octoprint.plugin.AssetPlugin,
                            octoprint.plugin.TemplatePlugin,
                            octoprint.plugin.SimpleApiPlugin):

    lights_on = True  # Lights should be on by default, makes sense.
    torch_on = False  # Torch is off by default, because who would want that?

    torch_timer = None  # Timer for torch function
    return_timer = None  # Timer object when we want to return to idle.

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

    def toggle_lights(self):
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

    def get_lights_status(self):
        return self.lights_on

    def get_torch_status(self):
        return self.torch_on

    # ~~ SettingsPlugin mixin

    def get_settings_defaults(self):
        return dict(
            # put your plugin's default settings here
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
                pip="https://github.com/you/P9813LEDControl/archive/{target_version}.zip"
            )
        )


__plugin_pythoncompat__ = ">=3,<4"


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = P9813ledcontrolPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
