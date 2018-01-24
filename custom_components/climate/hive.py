"""
Hive Integration - climate
BK-1.0:2017-06-25_1345
"""
import logging, json
import voluptuous as vol
from datetime import datetime
from datetime import timedelta


from homeassistant.components.climate import (ClimateDevice, PLATFORM_SCHEMA, ENTITY_ID_FORMAT)
from homeassistant.const import TEMP_CELSIUS, ATTR_TEMPERATURE
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.discovery import load_platform
import custom_components.hive as hive
from homeassistant.loader import get_component

DEPENDENCIES = ['hive']

_LOGGER = logging.getLogger(__name__)

                
def setup_platform(hass, config, add_devices, DeviceList, discovery_info=None):
    """Setup Hive climate devices"""
    HiveComponent = get_component('hive')
    
    if len(DeviceList) > 0:
        for aDevice in DeviceList:
            if "HA_DeviceType" in aDevice and "Hive_NodeID" in aDevice and "Hive_NodeName" in aDevice:
                if aDevice["HA_DeviceType"] == "Hive_Device_Heating":
                    add_devices([Hive_Device_Heating(hass, HiveComponent.HiveObjects_Global, aDevice["Hive_NodeID"], aDevice["Hive_NodeName"], aDevice["HA_DeviceType"])])
                if aDevice["HA_DeviceType"] == "Hive_Device_HotWater":
                    add_devices([Hive_Device_HotWater(hass, HiveComponent.HiveObjects_Global, aDevice["Hive_NodeID"], aDevice["Hive_NodeName"], aDevice["HA_DeviceType"])])

class Hive_Device_Heating(ClimateDevice):
    """Hive Heating Device"""

    def __init__(self, hass, HiveComponent_HiveObjects, NodeID, NodeName, DeviceType):
        """Initialize the Heating device."""
        self.HiveObjects = HiveComponent_HiveObjects
        self.NodeID = NodeID
        self.NodeName = NodeName
        self.DeviceType = DeviceType

        SetEntityID = "Hive_Heating"
        if self.NodeName != None:
            SetEntityID = SetEntityID + "_" + self.NodeName
        self.entity_id = ENTITY_ID_FORMAT.format(SetEntityID.lower())

        def handle_event(event):
            Event_String = str(event)

            tmp_attribute = None
            self.schedule_update_ha_state()

        hass.bus.listen('Event_Hive_NewNodeData', handle_event)

    @property
    def name(self):
        """Return the name of the heating device"""
        FriendlyName = "Heating"
        if self.NodeName != None:
            FriendlyName = self.NodeName + " " + FriendlyName

        return FriendlyName

    @property
    def force_update(self):
        """Return True if state updates should be forced."""
        return False
    
    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement which this heating device uses."""
        return TEMP_CELSIUS

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self.HiveObjects.Get_Heating_CurrentTemp(self.NodeID, self.DeviceType)

    @property
    def target_temperature(self):
        """Return the target temperature"""
        return self.HiveObjects.Get_Heating_TargetTemp(self.NodeID, self.DeviceType)

    @property
    def min_temp(self):
        """Return minimum temperature."""
        return self.HiveObjects.Get_Heating_Min_Temperature(self.NodeID, self.DeviceType)

    @property
    def max_temp(self):
        """Return the maximum temperature"""
        return self.HiveObjects.Get_Heating_Max_Temperature(self.NodeID, self.DeviceType)

    @property
    def operation_list(self):
        """List of the operation modes"""
        return self.HiveObjects.Get_Heating_Operation_Mode_List(self.NodeID, self.DeviceType)

    @property
    def current_operation(self):
        """Return current mode"""
        return self.HiveObjects.Get_Heating_Mode(self.NodeID, self.DeviceType)

    def set_operation_mode(self, operation_mode):
        """Set new Heating mode"""
        self.HiveObjects.Set_Heating_Mode(self.NodeID, self.DeviceType, operation_mode)
        
    def set_temperature(self, **kwargs):
        """Set new target temperature"""
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            NewTemperature = kwargs.get(ATTR_TEMPERATURE)
            self.HiveObjects.Set_Heating_TargetTemp(self.NodeID, self.DeviceType, NewTemperature)

    def update(self):
        """Update all Node data frome Hive"""
        self.HiveObjects.UpdateData(self.NodeID, self.DeviceType)

        
class Hive_Device_HotWater(ClimateDevice):
    """Hive HotWater Device"""
    def __init__(self, hass, HiveComponent_HiveObjects, NodeID, NodeName, DeviceType):
        """Initialize the HotWater device."""
        self.HiveObjects = HiveComponent_HiveObjects
        self.NodeID = NodeID
        self.NodeName = NodeName
        self.DeviceType = DeviceType

        SetEntityID = "Hive_HotWater"
        self.entity_id = ENTITY_ID_FORMAT.format(SetEntityID.lower())


        def handle_event(event):
            tmp_attribute = None
            self.schedule_update_ha_state()

        hass.bus.listen('Event_Hive_NewNodeData', handle_event)

    @property
    def name(self):
        """Return the name of the HotWater device"""
        FriendlyName = "Hot Water"
        return FriendlyName

    @property
    def force_update(self):
        """Return True if state updates should be forced."""
        return False
    
    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement which this HotWater device uses."""
        return TEMP_CELSIUS

    @property
    def operation_list(self):
        """List of the operation modes"""
        return self.HiveObjects.Get_HotWater_Operation_Mode_List(self.NodeID, self.DeviceType)

    @property
    def current_operation(self):
        """Return current mode"""
        return self.HiveObjects.Get_HotWater_Mode(self.NodeID, self.DeviceType)

    def set_operation_mode(self, operation_mode):
        """Set new HotWater mode"""
        self.HiveObjects.Set_HotWater_Mode(self.NodeID, self.DeviceType, operation_mode)
        
    def update(self):
        """Update all Node data frome Hive"""
        self.HiveObjects.UpdateData(self.NodeID, self.DeviceType)
