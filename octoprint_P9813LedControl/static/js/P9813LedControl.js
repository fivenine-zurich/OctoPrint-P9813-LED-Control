$(function () {
    function P9813LedControlStatusViewModel(parameters) {
        var self = this;
        self.settingsViewModel = parameters[0];

        self.torch_enabled = ko.observable(true);

        var light_icon = $("#lightIcon");
        var switch_icon = $("#toggleSwitch");
        var torch_icon = $("#torchIcon");

        function update_light_status(response) {
            if (response.lights_status) {
                light_icon
                    .removeClass("far-custom text-error")
                    .addClass("fas-custom text-success");
                switch_icon
                    .removeClass("fa-toggle-off text-error")
                    .addClass("fa-toggle-on text-success");
            } else {
                light_icon
                    .removeClass("fas-custom text-success")
                    .addClass("far-custom text-error");
                switch_icon
                    .removeClass("fa-toggle-on text-success")
                    .addClass("fa-toggle-off text-error");
            }
            if (response.torch_status) {
                torch_icon.attr(
                    "src",
                    "plugin/P9813LedControl/static/svg/flashlight.svg"
                );
            } else {
                torch_icon.attr(
                    "src",
                    "plugin/P9813LedControl/static/svg/flashlight-outline.svg"
                );
            }
        }

        self.toggle_lights = function () {
            OctoPrint.simpleApiCommand("P9813LedControl", "toggle_lights").done(
                update_light_status
            );
        };

        self.activate_torch = function () {
            var torch_time = self.settingsViewModel.settings.plugins.P9813LedControl.torch_timer();
            OctoPrint.simpleApiCommand(
                "P9813LedControl",
                "activate_torch"
            ).done(update_light_status);
            setTimeout(self.torch_off, parseInt(torch_time, 10) * 1000);
        };

        self.torch_off = function () {
            torch_icon.attr(
                "src",
                "plugin/P9813LedControl/static/svg/flashlight-outline.svg"
            );
        };

        self.onBeforeBinding = function () {
            self.torch_enabled(
                self.settingsViewModel.settings.plugins.P9813LedControl.torch_enabled()
            );
        };

        self.onSettingsBeforeSave = function () {};
    }

    OCTOPRINT_VIEWMODELS.push({
        construct: P9813LedControlStatusViewModel,
        dependencies: ["settingsViewModel"],
        elements: ["#navbar_plugin_P9813LedControl"],
    });

    function P9813LedControlSettingsViewModel(parameters) {
        var self = this;
    }

    OCTOPRINT_VIEWMODELS.push({
        construct: P9813LedControlSettingsViewModel,
        dependencies: ["settingsViewModel"],
    });
});
