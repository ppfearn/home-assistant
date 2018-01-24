"""
Hive Integration - sensor
BK-1.0:2017-06-25_1345
"""
import logging, json
import voluptuous as vol
from datetime import datetime
from datetime import timedelta

from homeassistant.const import TEMP_CELSIUS, TEMP_FAHRENHEIT, CONF_USERNAME, CONF_PASSWORD, ATTR_TEMPERATURE
from homeassistant.components.sensor import ENTITY_ID_FORMAT
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.discovery import load_platform
import custom_components.hive as hive
from homeassistant.loader import get_component

DEPENDENCIES = ['hive']

_LOGGER = logging.getLogger(__name__)

        
def setup_platform(hass, config, add_devices, DeviceList, discovery_info=None):
    """Setup Hive sensor devices"""
    HiveComponent = get_component('hive')

    if len(DeviceList) > 0:
        for aDevice in DeviceList:
            if "HA_DeviceType" in aDevice and "Hive_NodeID" in aDevice and "Hive_NodeName" in aDevice:
                if aDevice["HA_DeviceType"] == "Hive_Device_Heating_CurrentTemperature":
                    add_devices([Hive_Device_Heating_CurrentTemperature(hass, HiveComponent.HiveObjects_Global, aDevice["Hive_NodeID"], aDevice["Hive_NodeName"], aDevice["HA_DeviceType"])])
                if aDevice["HA_DeviceType"] == "Hive_Device_Heating_TargetTemperature":
                    add_devices([Hive_Device_Heating_TargetTemperature(hass, HiveComponent.HiveObjects_Global, aDevice["Hive_NodeID"], aDevice["Hive_NodeName"], aDevice["HA_DeviceType"])])
                if aDevice["HA_DeviceType"] == "Hive_Device_Heating_State":
                    add_devices([Hive_Device_Heating_State(hass, HiveComponent.HiveObjects_Global, aDevice["Hive_NodeID"], aDevice["Hive_NodeName"], aDevice["HA_DeviceType"])])
                if aDevice["HA_DeviceType"] == "Hive_Device_Heating_Mode":
                    add_devices([Hive_Device_Heating_Mode(hass, HiveComponent.HiveObjects_Global, aDevice["Hive_NodeID"], aDevice["Hive_NodeName"], aDevice["HA_DeviceType"])])
                if aDevice["HA_DeviceType"] == "Hive_Device_Heating_Boost":
                    add_devices([Hive_Device_Heating_Boost(hass, HiveComponent.HiveObjects_Global, aDevice["Hive_NodeID"], aDevice["Hive_NodeName"], aDevice["HA_DeviceType"])])
                if aDevice["HA_DeviceType"] == "Hive_Device_HotWater_State":
                    add_devices([Hive_Device_HotWater_State(hass, HiveComponent.HiveObjects_Global, aDevice["Hive_NodeID"], aDevice["Hive_NodeName"], aDevice["HA_DeviceType"])])
                if aDevice["HA_DeviceType"] == "Hive_Device_HotWater_Mode":
                    add_devices([Hive_Device_HotWater_Mode(hass, HiveComponent.HiveObjects_Global, aDevice["Hive_NodeID"], aDevice["Hive_NodeName"], aDevice["HA_DeviceType"])])
                if aDevice["HA_DeviceType"] == "Hive_Device_HotWater_Boost":
                    add_devices([Hive_Device_HotWater_Boost(hass, HiveComponent.HiveObjects_Global, aDevice["Hive_NodeID"], aDevice["Hive_NodeName"], aDevice["HA_DeviceType"])])
                if aDevice["HA_DeviceType"] == "Hive_Device_Thermostat_BatteryLevel":
                    add_devices([Hive_Device_Thermostat_BatteryLevel(hass, HiveComponent.HiveObjects_Global, aDevice["Hive_NodeID"], aDevice["Hive_NodeName"], aDevice["HA_DeviceType"])])

        
class Hive_Device_Heating_CurrentTemperature(Entity):
    """Hive Heating current temperature Sensor"""

    def __init__(self, hass, HiveComponent_HiveObjects, NodeID, NodeName, DeviceType):
        """Initialize the sensor."""
        self.HiveObjects = HiveComponent_HiveObjects
        self.NodeID = NodeID
        self.NodeName = NodeName
        self.DeviceType = DeviceType

        SetEntityID = "Hive_Current_Temperature"
        if self.NodeName != None:
            SetEntityID = SetEntityID + "_" + self.NodeName
        self.entity_id = ENTITY_ID_FORMAT.format(SetEntityID.lower())

        def handle_event(event):
            tmp_attribute = None
            self.schedule_update_ha_state()

        hass.bus.listen('Event_Hive_NewNodeData', handle_event)

    @property
    def name(self):
        """Return the name of the sensor."""
        FriendlyName = "Current Temperature"
        if self.NodeName != None:
            FriendlyName = self.NodeName + " " + FriendlyName

        return FriendlyName

    @property
    def force_update(self):
        """Return True if state updates should be forced."""
        return False
    
    @property
    def state(self):
        """Return the state of the sensor."""
        return self.HiveObjects.Get_Heating_CurrentTemp(self.NodeID, self.DeviceType)
        
    @property
    def state_attributes(self):
        """Return the state attributes"""
        return self.HiveObjects.Get_Heating_CurrentTemp_State_Attributes(self.NodeID, self.DeviceType)

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self.HiveObjects.UpdateData(self.NodeID, self.DeviceType)

class Hive_Device_Heating_TargetTemperature(Entity):
    """Hive Heating target temperature Sensor"""

    def __init__(self, hass, HiveComponent_HiveObjects, NodeID, NodeName, DeviceType):
        """Initialize the sensor."""
        self.HiveObjects = HiveComponent_HiveObjects
        self.NodeID = NodeID
        self.NodeName = NodeName
        self.DeviceType = DeviceType

        SetEntityID = "Hive_Target_Temperature"
        if self.NodeName != None:
            SetEntityID = SetEntityID + "_" + self.NodeName
        self.entity_id = ENTITY_ID_FORMAT.format(SetEntityID.lower())

        def handle_event(event):
            tmp_attribute = None
            self.schedule_update_ha_state()

        hass.bus.listen('Event_Hive_NewNodeData', handle_event)

    @property
    def name(self):
        """Return the name of the sensor."""
        FriendlyName = "Target Temperature"
        if self.NodeName != None:
            FriendlyName = self.NodeName + " " + FriendlyName

        return FriendlyName

    @property
    def force_update(self):
        """Return True if state updates should be forced."""
        return True
        
    @property
    def state(self):
        """Return the state of the sensor."""
        return self.HiveObjects.Get_Heating_TargetTemp(self.NodeID, self.DeviceType)
        
    @property
    def state_attributes(self):
        """Return the state attributes"""
        return self.HiveObjects.Get_Heating_TargetTemperature_State_Attributes(self.NodeID, self.DeviceType)

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement to display."""
        return TEMP_CELSIUS
        
#    @property
#    def temperature_unit(self):
#        """The unit of measurement used by the platform."""
#        return TEMP_FAHRENHEIT

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self.HiveObjects.UpdateData(self.NodeID, self.DeviceType)

class Hive_Device_Heating_State(Entity):
    """Hive Heating current state (On / Off)"""

    def __init__(self, hass, HiveComponent_HiveObjects, NodeID, NodeName, DeviceType):
        """Initialize the sensor."""
        self.HiveObjects = HiveComponent_HiveObjects
        self.NodeID = NodeID
        self.NodeName = NodeName
        self.DeviceType = DeviceType

        SetEntityID = "Hive_Heating_State"
        if self.NodeName != None:
            SetEntityID = SetEntityID + "_" + self.NodeName
        self.entity_id = ENTITY_ID_FORMAT.format(SetEntityID.lower())

        def handle_event(event):
            tmp_attribute = None
            self.schedule_update_ha_state()

        hass.bus.listen('Event_Hive_NewNodeData', handle_event)

    @property
    def name(self):
        """Return the name of the sensor."""
        FriendlyName = "Heating State"
        if self.NodeName != None:
            FriendlyName = self.NodeName + " " + FriendlyName

        return FriendlyName
        
    @property
    def force_update(self):
        """Return True if state updates should be forced."""
        return False
    
    @property
    def state(self):
        """Return the state of the sensor."""
        return self.HiveObjects.Get_Heating_State(self.NodeID, self.DeviceType)
        
    @property
    def state_attributes(self):
        """Return the state attributes."""
        return self.HiveObjects.Get_Heating_State_State_Attributes(self.NodeID, self.DeviceType)
        
    @property
    def icon(self):
        """Return the icon to use."""
        DeviceIcon = 'mdi:radiator'

        return DeviceIcon

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self.HiveObjects.UpdateData(self.NodeID, self.DeviceType)

class Hive_Device_Heating_Mode(Entity):
    """Hive Heating current Mode (SCHEDULE / MANUAL / OFF)"""

    def __init__(self, hass, HiveComponent_HiveObjects, NodeID, NodeName, DeviceType):
        """Initialize the sensor."""
        self.HiveObjects = HiveComponent_HiveObjects
        self.NodeID = NodeID
        self.NodeName = NodeName
        self.DeviceType = DeviceType

        SetEntityID = "Hive_Heating_Mode"
        if self.NodeName != None:
            SetEntityID = SetEntityID + "_" + self.NodeName
        self.entity_id = ENTITY_ID_FORMAT.format(SetEntityID.lower())


        def handle_event(event):
            tmp_attribute = None
            self.schedule_update_ha_state()

        hass.bus.listen('Event_Hive_NewNodeData', handle_event)

    @property
    def name(self):
        """Return the name of the sensor."""
        FriendlyName = "Heating Mode"
        if self.NodeName != None:
            FriendlyName = self.NodeName + " " + FriendlyName

        return FriendlyName
        
    @property
    def force_update(self):
        """Return True if state updates should be forced."""
        return False
    
    @property
    def state(self):
        """Return the state of the sensor."""
        return self.HiveObjects.Get_Heating_Mode(self.NodeID, self.DeviceType)
        
    @property
    def state_attributes(self):
        """Return the state attributes."""
        return self.HiveObjects.Get_Heating_Mode_State_Attributes(self.NodeID, self.DeviceType)
        
    @property
    def icon(self):
        """Return the icon to use."""
        DeviceIcon = 'mdi:radiator'

        return DeviceIcon

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self.HiveObjects.UpdateData(self.NodeID, self.DeviceType)

class Hive_Device_Heating_Boost(Entity):
    """Hive Heating current Boost (ON / OFF)"""

    def __init__(self, hass, HiveComponent_HiveObjects, NodeID, NodeName, DeviceType):
        """Initialize the sensor."""
        self.HiveObjects = HiveComponent_HiveObjects
        self.NodeID = NodeID
        self.NodeName = NodeName
        self.DeviceType = DeviceType

        SetEntityID = "Hive_Heating_Boost"
        if self.NodeName != None:
            SetEntityID = SetEntityID + "_" + self.NodeName
        self.entity_id = ENTITY_ID_FORMAT.format(SetEntityID.lower())

        def handle_event(event):
            tmp_attribute = None
            self.schedule_update_ha_state()

        hass.bus.listen('Event_Hive_NewNodeData', handle_event)

    @property
    def name(self):
        """Return the name of the sensor."""
        FriendlyName = "Heating Boost"
        if self.NodeName != None:
            FriendlyName = self.NodeName + " " + FriendlyName

        return FriendlyName
        
    @property
    def force_update(self):
        """Return True if state updates should be forced."""
        return False
    
    @property
    def state(self):
        """Return the state of the sensor."""
        return self.HiveObjects.Get_Heating_Boost(self.NodeID, self.DeviceType)
        
    @property
    def state_attributes(self):
        """Return the state attributes."""
        return self.HiveObjects.Get_Heating_Boost_State_Attributes(self.NodeID, self.DeviceType)
        
    @property
    def icon(self):
        """Return the icon to use."""
        DeviceIcon = 'mdi:radiator'

        return DeviceIcon

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self.HiveObjects.UpdateData(self.NodeID, self.DeviceType)
 
            
class Hive_Device_HotWater_State(Entity):
    """Hive Hot water current state (On / Off)"""

    def __init__(self, hass, HiveComponent_HiveObjects, NodeID, NodeName, DeviceType):
        """Initialize the sensor."""
        self.HiveObjects = HiveComponent_HiveObjects
        self.NodeID = NodeID
        self.NodeName = NodeName
        self.DeviceType = DeviceType

        SetEntityID = "Hive_Hot_Water_State"
        if self.NodeName != None:
            SetEntityID = SetEntityID + "_" + self.NodeName
        self.entity_id = ENTITY_ID_FORMAT.format(SetEntityID.lower())

        def handle_event(event):
            tmp_attribute = None
            self.schedule_update_ha_state()

        hass.bus.listen('Event_Hive_NewNodeData', handle_event)

    @property
    def name(self):
        """Return the name of the sensor."""
        FriendlyName = "Hot Water State"
        if self.NodeName != None:
            FriendlyName = self.NodeName + " " + FriendlyName

        return FriendlyName
        
    @property
    def force_update(self):
        """Return True if state updates should be forced."""
        return False

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.HiveObjects.Get_HotWater_State(self.NodeID, self.DeviceType)
        
    @property
    def state_attributes(self):
        """Return the state attributes."""
        return self.HiveObjects.Get_HotWater_State_State_Attributes(self.NodeID, self.DeviceType)
        
    @property
    def icon(self):
        """Return the icon to use."""
        DeviceIcon = 'mdi:water-pump'

        return DeviceIcon

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self.HiveObjects.UpdateData(self.NodeID, self.DeviceType)

class Hive_Device_HotWater_Mode(Entity):
    """Hive HotWater current Mode (SCHEDULE / ON / OFF)"""

    def __init__(self, hass, HiveComponent_HiveObjects, NodeID, NodeName, DeviceType):
        """Initialize the sensor."""
        self.HiveObjects = HiveComponent_HiveObjects
        self.NodeID = NodeID
        self.NodeName = NodeName
        self.DeviceType = DeviceType

        SetEntityID = "Hive_Hot_Water_Mode"
        if self.NodeName != None:
            SetEntityID = SetEntityID + "_" + self.NodeName
        self.entity_id = ENTITY_ID_FORMAT.format(SetEntityID.lower())

        def handle_event(event):
            tmp_attribute = None
            self.schedule_update_ha_state()

        hass.bus.listen('Event_Hive_NewNodeData', handle_event)

    @property
    def name(self):
        """Return the name of the sensor."""
        FriendlyName = "Hot Water Mode"
        if self.NodeName != None:
            FriendlyName = self.NodeName + " " + FriendlyName

        return FriendlyName
        
    @property
    def force_update(self):
        """Return True if state updates should be forced."""
        return False
    
    @property
    def state(self):
        """Return the state of the sensor."""
        return self.HiveObjects.Get_HotWater_Mode(self.NodeID, self.DeviceType)
        
    @property
    def state_attributes(self):
        """Return the state attributes."""
        return self.HiveObjects.Get_HotWater_Mode_State_Attributes(self.NodeID, self.DeviceType)
        
    @property
    def icon(self):
        """Return the icon to use."""
        DeviceIcon = 'mdi:water-pump'

        return DeviceIcon

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self.HiveObjects.UpdateData(self.NodeID, self.DeviceType)

class Hive_Device_HotWater_Boost(Entity):
    """Hive HotWater current Boost (ON / OFF)"""

    def __init__(self, hass, HiveComponent_HiveObjects, NodeID, NodeName, DeviceType):
        """Initialize the sensor."""
        self.HiveObjects = HiveComponent_HiveObjects
        self.NodeID = NodeID
        self.NodeName = NodeName
        self.DeviceType = DeviceType

        SetEntityID = "Hive_Hot_Water_Boost"
        if self.NodeName != None:
            SetEntityID = SetEntityID + "_" + self.NodeName
        self.entity_id = ENTITY_ID_FORMAT.format(SetEntityID.lower())

        def handle_event(event):
            tmp_attribute = None
            self.schedule_update_ha_state()

        hass.bus.listen('Event_Hive_NewNodeData', handle_event)

    @property
    def name(self):
        """Return the name of the sensor."""
        FriendlyName = "Hot Water Boost"
        if self.NodeName != None:
            FriendlyName = self.NodeName + " " + FriendlyName

        return FriendlyName
        
    @property
    def force_update(self):
        """Return True if state updates should be forced."""
        return False
    
    @property
    def state(self):
        """Return the state of the sensor."""
        return self.HiveObjects.Get_HotWater_Boost(self.NodeID, self.DeviceType)
        
    @property
    def state_attributes(self):
        """Return the state attributes."""
        return self.HiveObjects.Get_HotWater_Boost_State_Attributes(self.NodeID, self.DeviceType)
        
    @property
    def icon(self):
        """Return the icon to use."""
        DeviceIcon = 'mdi:water-pump'

        return DeviceIcon

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self.HiveObjects.UpdateData(self.NodeID, self.DeviceType)
        
class Hive_Device_Thermostat_BatteryLevel(Entity):
    """Hive Thermostat device current battery level sensor"""

    def __init__(self, hass, HiveComponent_HiveObjects, NodeID, NodeName, DeviceType):
        """Initialize the sensor."""
        self.HiveObjects = HiveComponent_HiveObjects
        self.NodeID = NodeID
        self.NodeName = NodeName
        self.DeviceType = DeviceType

        SetEntityID = "Hive_Thermostat_Battery_Level"
        if self.NodeName != None:
            SetEntityID = SetEntityID + "_" + self.NodeName
        self.entity_id = ENTITY_ID_FORMAT.format(SetEntityID.lower())

        self.BatteryLevel = None

        def handle_event(event):
            tmp_attribute = None
            self.schedule_update_ha_state()

        hass.bus.listen('Event_Hive_NewNodeData', handle_event)

    @property
    def name(self):
        """Return the name of the sensor."""
        FriendlyName = "Thermostat Battery Level"
        if self.NodeName != None:
            FriendlyName = self.NodeName + " " + FriendlyName

        return FriendlyName

    @property
    def force_update(self):
        """Return True if state updates should be forced."""
        return True

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement which this thermostat uses."""
        return "%"

    @property
    def state(self):
        """Return the state of the sensor."""
        self.BatteryLevel = self.HiveObjects.Get_Thermostat_BatteryLevel(self.NodeID, self.DeviceType)
        return self.BatteryLevel
        
    @property
    def icon(self):
        """Return the icon to use."""
        DeviceIcon = 'mdi:battery'
        
        if self.BatteryLevel >= 95 and self.BatteryLevel <= 100:
            DeviceIcon = 'mdi:battery'
        elif self.BatteryLevel >= 85 and self.BatteryLevel < 95:
            DeviceIcon = 'mdi:battery-90'
        elif self.BatteryLevel >= 75 and self.BatteryLevel < 85:
            DeviceIcon = 'mdi:battery-80'
        elif self.BatteryLevel >= 65 and self.BatteryLevel < 75:
            DeviceIcon = 'mdi:battery-70'
        elif self.BatteryLevel >= 55 and self.BatteryLevel < 65:
            DeviceIcon = 'mdi:battery-60'
        elif self.BatteryLevel >= 45 and self.BatteryLevel < 55:
            DeviceIcon = 'mdi:battery-50'
        elif self.BatteryLevel >= 35 and self.BatteryLevel < 45:
            DeviceIcon = 'mdi:battery-40'
        elif self.BatteryLevel >= 25 and self.BatteryLevel < 35:
            DeviceIcon = 'mdi:battery-30'
        elif self.BatteryLevel >= 15 and self.BatteryLevel < 25:
            DeviceIcon = 'mdi:battery-20'
        elif self.BatteryLevel > 5 and self.BatteryLevel < 15:
            DeviceIcon = 'mdi:battery-10'
        elif self.BatteryLevel <= 5:
            DeviceIcon = 'mdi:battery-outline'
        
        return DeviceIcon
        
    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self.HiveObjects.UpdateData(self.NodeID, self.DeviceType)