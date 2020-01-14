# Copyright (c) 2020 Aldo Hoeben / fieldOfView
# OctoPrintPlugin is released under the terms of the AGPLv3 or higher.

from collections import OrderedDict
from typing import Any, Tuple, Dict

class OctoPrintPowerPlugins():

    def __init__(self) -> None:
        self._available_plugs = OrderedDict()

    def parsePluginData(self, plugin_data: Dict[str, Any]):
        self._available_plugs = OrderedDict()

        # plugins that only support a single plug
        for (plugin_id, plugin_name) in [
            ("psucontrol", "PSU Control"),
            ("mystromswitch", "MyStrom Switch")
        ]:
            if plugin_id in plugin_data:
                if plugin_id != "mystromswitch" or plugin_data[plugin_id]["ip"]:
                    plug = OrderedDict([
                        ("plugin", plugin_id),
                        ("name", plugin_name)
                    ])
                    self._available_plugs[self._createPlugId(plug)] = plug

        # plugins that have a `label` and `ip` specified in `arrSmartplugs`
        for (plugin_id, plugin_name, additional_data) in [
            ("tplinksmartplug", "TP-Link Smartplug", []), # ip
            ("orvibos20", "Orvibo S20", []), # ip
            ("wemoswitch", "Wemo Switch", []), # ip
            ("tuyasmartplug", "Tuya Smartplug", []), # label
            ("domoticz", "Domoticz", ["idx"]), # ip, idx
            ("tasmota", "Tasmota", ["idx", "username", "password"]), # ip, idx, username, password
        ]:
            if plugin_id in plugin_data and "arrSmartplugs" in plugin_data[plugin_id]:
                for plug_data in plugin_data[plugin_id]["arrSmartplugs"]:
                    if plug_data["ip"] and plug_data["label"]:
                        plug = OrderedDict([
                            ("plugin", plugin_id),
                            ("name", ("%s (%s)" % (plug_data["label"], plugin_name))),
                            ("label", plug_data["label"]),
                            ("ip", plug_data["ip"])
                        ])
                        for key in additional_data:
                            plug[key] = plug_data[key]
                        self._available_plugs[self._createPlugId(plug)] = plug

        # `tasmota_mqtt` has a slightly different settings dialect
        if "tasmota_mqtt" in plugin_data:
            plugin_id = "tasmota_mqtt"
            plugin_name = "Tasmota MQTT"
            for plug_data in plugin_data[plugin_id]["arrRelays"]:
                if plug_data["topic"] and plug_data["relayN"] != "":
                    plug = OrderedDict([
                        ("plugin", plugin_id),
                        ("name", "%s/%s (%s)" % (plug_data["topic"], plug_data["relayN"], plugin_name)),
                        ("topic", plug_data["relayN"]),
                        ("relayN", plug_data["relayN"])
                    ])
                    self._available_plugs[self._createPlugId(plug)] = plug

    def _createPlugId(self, plug_data: Dict[str, Any]) -> str:
        interesting_bits = [v for (k, v) in plug_data.items() if k != "name"]
        return "/".join(interesting_bits)

    def getAvailablePowerPlugs(self) -> Dict[str, Any]:
        return self._available_plugs

    def getSetStateCommand(self, plug_id: str, state: bool) -> Tuple[str, Dict[str, Any]]:
        if plug_id not in self._available_plugs:
            return ("", {})

        plugin_id = self._available_plugs[plug_id]["plugin"]
        end_point = "plugin/" + plugin_id

        if plugin_id == "psucontrol":
            return (end_point, OrderedDict([("command", "turnPSUOn" if state else "turnPSUOff")]))

        if plugin_id == "mystromswitch":
            return (end_point, OrderedDict([("command", "enableRelais" if state else "disableRelais")]))

        plug_data = self._available_plugs[plug_id]
        command = OrderedDict([("command", "turnOn" if state else "turnOff")])
        arguments = []
        if plugin_id in ["tplinksmartplug", "orvibos20", "wemoswitch"]:
            # ip
            arguments = ["ip"]
        elif plugin_id == "domoticz":
            # ip, idx
            arguments = ["ip", "idx"]
        elif plugin_id == "tasmota_mqtt":
            # topic, relayN
            arguments = ["topic", "relayN"]
        elif plugin_id == "tasmota":
            # ip, idx, username, password
            arguments = ["ip", "idx", "username", "password"]
        elif plugin_id == "tuyasmartplug":
            # label
            arguments = ["label"]

        for key in arguments:
            command[key] = plug_data[key]

        return (end_point, command)