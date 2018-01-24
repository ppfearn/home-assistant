"""
Hive Integration - Platform
BK-1.0:2017-06-26_2125
"""
import logging, json
import voluptuous as vol
from datetime import datetime
from datetime import timedelta
import requests, operator

from homeassistant.util import Throttle
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.discovery import load_platform

REQUIREMENTS = ['requests==2.11.1']

_LOGGER = logging.getLogger(__name__)
DOMAIN = 'hive'

Hive_Node_Update_Interval_Default = 120
MINUTES_BETWEEN_LOGONS = 15

Current_Node_Attribute_Values = {"Header" : "HeaderText"}

class Hive_Devices:
    Hub = []
    Thermostat = []
    BoilerModule = []
    Plug = []
    Light = []
    MotionSensor = []

class Hive_Products:
    Heating = []
    HotWater = []
    Light = []
    Plug = []
    MotionSensor = []
    
class Hive_Session:
    SessionID = ""
    Session_Logon_DateTime = datetime(2017,1,1,12,0,0)
    UserName = ""
    Password = ""
    Postcode = ""
    Timezone = ""
    CountryCode = ""
    Locale = ""
    TemperatureUnit = ""
    Devices = Hive_Devices()
    Products = Hive_Products()
    Update_Interval_Seconds = Hive_Node_Update_Interval_Default
    LastUpdate = datetime(2017,1,1,12,0,0)
    Logging = False
    hass = None

class Hive_API_URLS:
    GlobalLogin = ""
    Base = ""
    Weather = ""
    HolidayMode = ""
    Devices = ""
    Products = ""
    Nodes = ""


class Hive_API_Headers:
    Accept_Key = ""
    Accept_Value = ""
    ContentType_Key = ""
    ContentType_Value = ""
    SessionID_Key = ""
    SessionID_Value = ""

class Hive_API_Details:
    URLs = Hive_API_URLS()
    Headers = Hive_API_Headers()
    PlatformName = ""
    
HiveAPI_Details = Hive_API_Details()
HiveSession_Current = Hive_Session()

        
def Initialise_App():
    HiveAPI_Details.PlatformName = ""

    HiveAPI_Details.URLs.GlobalLogin = "https://beekeeper.hivehome.com/1.0/global/login"
    HiveAPI_Details.URLs.Base = ""
    HiveAPI_Details.URLs.Weather = "https://weather-prod.bgchprod.info/weather"
    HiveAPI_Details.URLs.HolidayMode = "/holiday-mode"
    HiveAPI_Details.URLs.Devices = "/devices"
    HiveAPI_Details.URLs.Products = "/products"
    HiveAPI_Details.URLs.Nodes = "/nodes"

    HiveAPI_Details.Headers.Accept_Key = "Accept"
    HiveAPI_Details.Headers.Accept_Value = "*/*"
    HiveAPI_Details.Headers.ContentType_Key = "content-type"
    HiveAPI_Details.Headers.ContentType_Value = "application/json"
    HiveAPI_Details.Headers.SessionID_Key = "authorization"
    HiveAPI_Details.Headers.SessionID_Value = None


def Hive_API_JsonCall (RequestType, RequestURL, JsonStringContent, LoginRequest):
    API_Headers = {HiveAPI_Details.Headers.ContentType_Key:HiveAPI_Details.Headers.ContentType_Value,HiveAPI_Details.Headers.Accept_Key:HiveAPI_Details.Headers.Accept_Value,HiveAPI_Details.Headers.SessionID_Key:HiveAPI_Details.Headers.SessionID_Value}
    JSON_Response = ""
    FullRequestURL = ""

    if LoginRequest == True:
        FullRequestURL = RequestURL
    else:
        FullRequestURL = HiveAPI_Details.URLs.Base + RequestURL
    
    try:
        if RequestType == "POST":
            JSON_Response = requests.post(FullRequestURL, data=JsonStringContent, headers=API_Headers)
        elif RequestType == "GET":
            JSON_Response = requests.get(FullRequestURL, data=JsonStringContent, headers=API_Headers)
        elif RequestType == "PUT":
            JSON_Response = requests.put(FullRequestURLL, data=JsonStringContent, headers=API_Headers)
        else:
            _LOGGER.error("Unknown RequestType : %s", RequestType)
    except:
        JSON_Response = "No response to JSON Hive API request"

    return JSON_Response


def Hive_API_Logon():
    LoginDetailsFound = True
    HiveSession_Current.SessionID = None

    JsonStringContent = '{"username": "' + HiveSession_Current.UserName + '","password": "' + HiveSession_Current.Password + '"}'
    API_Response_Login = Hive_API_JsonCall ("POST", HiveAPI_Details.URLs.GlobalLogin, JsonStringContent, True)
    API_Response_Login_Parsed = json.loads(API_Response_Login.text)

    if 'token' in API_Response_Login_Parsed and 'user' in API_Response_Login_Parsed and 'platform' in API_Response_Login_Parsed:
        HiveAPI_Details.Headers.SessionID_Value = API_Response_Login_Parsed["token"]
        HiveSession_Current.SessionID = HiveAPI_Details.Headers.SessionID_Value
        HiveSession_Current.Session_Logon_DateTime = datetime.now()

        if 'endpoint' in API_Response_Login_Parsed['platform']:
            HiveAPI_Details.URLs.Base = API_Response_Login_Parsed['platform']['endpoint']
        else:
            LoginDetailsFound = False

        if 'name' in API_Response_Login_Parsed['platform']:
             HiveAPI_Details.PlatformName = API_Response_Login_Parsed['platform']['name']
        else:
            LoginDetailsFound = False


        if 'locale' in API_Response_Login_Parsed['user']:
             HiveSession_Current.Locale = API_Response_Login_Parsed['user']['locale']
        else:
            LoginDetailsFound = False

        if 'countryCode' in API_Response_Login_Parsed['user']:
             HiveSession_Current.CountryCode = API_Response_Login_Parsed['user']['countryCode']
        else:
            LoginDetailsFound = False

        if 'timezone' in API_Response_Login_Parsed['user']:
             HiveSession_Current.Timezone = API_Response_Login_Parsed['user']['timezone']
        else:
            LoginDetailsFound = False

        if 'postcode' in API_Response_Login_Parsed['user']:
             HiveSession_Current.Postcode = API_Response_Login_Parsed['user']['postcode']
        else:
            LoginDetailsFound = False

        if 'temperatureUnit' in API_Response_Login_Parsed['user']:
             HiveSession_Current.TemperatureUnit = API_Response_Login_Parsed['user']['temperatureUnit']
        else:
            LoginDetailsFound = False
    else:
        LoginDetailsFound = False

    if LoginDetailsFound == False:
        HiveSession_Current.SessionID = None
        _LOGGER.error("Hive API login failed with error : %s", API_Response_Login)

def Check_Hive_API_Logon():
    CurrentTime = datetime.now()
    SecondsSinceLastLogon = (HiveSession_Current.Session_Logon_DateTime - CurrentTime).total_seconds()
    MinutesSinceLastLogon = int(round(SecondsSinceLastLogon / 60))

    if MinutesSinceLastLogon >= MINUTES_BETWEEN_LOGONS:
        Hive_API_Logon()
    elif HiveSession_Current.SessionID == None:
        Hive_API_Logon()

def NodeDataUpdated_FireBusEvent(NodeID, DeviceType):
    FireEvents = True
    if FireEvents == True:
        HiveSession_Current.hass.bus.fire('Event_Hive_NewNodeData', {DeviceType:NodeID})

def Hive_API_Get_Nodes_RL(NodeID, DeviceType):
    NodesUpdated = False
    CurrentTime = datetime.now()
    SecondsSinceLastUpdate = (CurrentTime - HiveSession_Current.LastUpdate).total_seconds()
    if SecondsSinceLastUpdate >= HiveSession_Current.Update_Interval_Seconds:
        HiveSession_Current.LastUpdate = CurrentTime
        NodesUpdated = Hive_API_Get_Nodes(NodeID, DeviceType)
    return NodesUpdated

def Hive_API_Get_Nodes_NL():
    Hive_API_Get_Nodes("NoID", "NoDeviceType")
    
def Hive_API_Get_Nodes(NodeID, DeviceType):
    Get_Nodes_Successful = True
    Get_Devices_Successful = False
    Get_Products_Successful = False

    Check_Hive_API_Logon()
        
    if HiveSession_Current.SessionID != None:
        tmp_devices_Hub = []
        tmp_devices_Thermostat = []
        tmp_devices_BoilerModule = []
        tmp_devices_Plug = []
        tmp_devices_Light = []
        tmp_devices_MotionSensor = []

        tmp_products_Heating = []
        tmp_products_HotWater = []
        tmp_products_Light = []
        tmp_products_Plug = []
        tmp_products_MotionSensor = []

        try:
            API_Response_Devices = Hive_API_JsonCall ("GET", HiveAPI_Details.URLs.Devices, "", False)
            HiveDevices_Parsed = json.loads(API_Response_Devices.text)

            for aDevice in HiveDevices_Parsed:
                if "type" in aDevice:
                    if aDevice["type"] == "hub":
                        tmp_devices_Hub.append(aDevice)
                    if aDevice["type"] == "thermostatui":
                        tmp_devices_Thermostat.append(aDevice)
                    if aDevice["type"] == "boilermodule":
                        tmp_devices_BoilerModule.append(aDevice)
                    if aDevice["type"] == "activeplug":
                        tmp_devices_Plug.append(aDevice)
                    if aDevice["type"] == "warmwhitelight" or aDevice["type"] == "tuneablelight" or aDevice["type"] == "colourtuneablelight":
                        tmp_devices_Light.append(aDevice)
                    if aDevice["type"] == "motionsensor":
                        tmp_devices_MotionSensor.append(aDevice)
 
            Get_Devices_Successful = True
        except:
            Get_Devices_Successful = False
            _LOGGER.error("Error parsing Hive Devices")


        try:
            API_Response_Devices = Hive_API_JsonCall ("GET", HiveAPI_Details.URLs.Products, "", False)
            HiveProducts_Parsed = json.loads(API_Response_Devices.text)

            for aProduct in HiveProducts_Parsed:
                if "type" in aProduct:
                    if aProduct["type"] == "heating":
                        tmp_products_Heating.append(aProduct)
                    if aProduct["type"] == "hotwater":
                        tmp_products_HotWater.append(aProduct)
                    if aProduct["type"] == "activeplug":
                        tmp_products_Plug.append(aProduct)
                    if aProduct["type"] == "warmwhitelight" or aProduct["type"] == "tuneablelight" or aProduct["type"] == "colourtuneablelight":
                        tmp_products_Light.append(aProduct)
                    if aProduct["type"] == "motionsensor":
                        tmp_products_MotionSensor.append(aProduct)


            Get_Devices_Successful = True
        except:
            Get_Devices_Successful = False
            _LOGGER.error("Error parsing Hive Products")
            

        try:
            if len(tmp_devices_Hub) > 0:
                HiveSession_Current.Devices.Hub = tmp_devices_Hub
            if len(tmp_devices_Thermostat) > 0:
                HiveSession_Current.Devices.Thermostat = tmp_devices_Thermostat
            if len(tmp_devices_BoilerModule) > 0: 
                HiveSession_Current.Devices.BoilerModule = tmp_devices_BoilerModule
            if len(tmp_devices_Plug) > 0:
                HiveSession_Current.Devices.Plug = tmp_devices_Plug
            if len(tmp_devices_Light) > 0:
                HiveSession_Current.Devices.Light = tmp_devices_Light
            if len(tmp_devices_MotionSensor) > 0:
                HiveSession_Current.Devices.MotionSensor = tmp_devices_MotionSensor


            if len(tmp_products_Heating) > 0:
                HiveSession_Current.Products.Heating = tmp_products_Heating
            if len(tmp_products_HotWater) > 0:
                HiveSession_Current.Products.HotWater = tmp_products_HotWater
            if len(tmp_products_Plug) > 0:
                HiveSession_Current.Products.Plug = tmp_products_Plug
            if len(tmp_products_Light) > 0:
                HiveSession_Current.Products.Light = tmp_products_Light
            if len(tmp_products_MotionSensor) > 0:
                HiveSession_Current.Products.MotionSensor = tmp_products_MotionSensor

        except:
            Get_Nodes_Successful = False
            _LOGGER.error("Error adding discovered Products / Devices")
    else:
        Get_Nodes_Successful = False
        _LOGGER.error("No Session ID")

    if Get_Nodes_Successful == True:
        NodeDataUpdated_FireBusEvent(NodeID, DeviceType)

    return Get_Nodes_Successful

def Private_Get_Heating_Min_Temperature(NodeID, DeviceType):
    Heating_MinTemp_Default = 5
    Heating_MinTemp_Return = 0
    Heating_MinTemp_tmp = 0
    Heating_MinTemp_Found = False

    Heating_MinTemp_tmp = Heating_MinTemp_Default
            
    if Heating_MinTemp_Found == True:
        Current_Node_Attribute_Values["Heating_Min_Temperature_" + NodeID] = Heating_MinTemp_tmp
        Heating_MinTemp_Return = Heating_MinTemp_tmp
    else:
        if ("Heating_Min_Temperature_" + NodeID) in Current_Node_Attribute_Values:
            Heating_MinTemp_Return = Current_Node_Attribute_Values.get("Heating_Min_Temperature_" + NodeID)
        else:
            Heating_MinTemp_Return = Heating_MinTemp_Default

    return Heating_MinTemp_Return

def Private_Get_Heating_Max_Temperature(NodeID, DeviceType):
    Heating_MaxTemp_Default = 32
    Heating_MaxTemp_Return = 0
    Heating_MaxTemp_tmp = 0
    Heating_MaxTemp_Found = False
        
    Heating_MaxTemp_tmp = Heating_MaxTemp_Default
            
    if Heating_MaxTemp_Found == True:
        Current_Node_Attribute_Values["Heating_Max_Temperature_" + NodeID] = Heating_MaxTemp_tmp
        Heating_MaxTemp_Return = Heating_MaxTemp_tmp
    else:
        if ("Heating_Max_Temperature_" + NodeID) in Current_Node_Attribute_Values:
            Heating_MaxTemp_Return = Current_Node_Attribute_Values.get("Heating_Max_Temperature_" + NodeID)
        else:
            Heating_MaxTemp_Return = Heating_MaxTemp_Default

    return Heating_MaxTemp_Return
    
def Private_Get_Heating_CurrentTemp(NodeID, DeviceType):
    NodeIndex = -1

    Heating_CurrentTemp_Return = 0
    Heating_CurrentTemp_tmp = 0
    Heating_CurrentTemp_Found = False
   
    
    if len(HiveSession_Current.Products.Heating) > 0:
        for x in range(0, len(HiveSession_Current.Products.Heating)):
            if "id" in HiveSession_Current.Products.Heating[x]:
                if HiveSession_Current.Products.Heating[x]["id"] == NodeID:
                    NodeIndex = x
                    break

        if NodeIndex != -1:
            if "props" in HiveSession_Current.Products.Heating[NodeIndex] and "temperature" in HiveSession_Current.Products.Heating[NodeIndex]["props"]:
                Heating_CurrentTemp_tmp = HiveSession_Current.Products.Heating[NodeIndex]["props"]["temperature"]
                Heating_CurrentTemp_Found = True
            
    if Heating_CurrentTemp_Found == True:
        Current_Node_Attribute_Values["Heating_CurrentTemp_" + NodeID] = Heating_CurrentTemp_tmp
        Heating_CurrentTemp_Return = Heating_CurrentTemp_tmp
    else:
        if ("Heating_CurrentTemp_" + NodeID) in Current_Node_Attribute_Values:
            Heating_CurrentTemp_Return = Current_Node_Attribute_Values.get("Heating_CurrentTemp_" + NodeID)
        else:
            Heating_CurrentTemp_Return = 0

    return Heating_CurrentTemp_Return
    
def Private_Get_Heating_CurrentTemp_State_Attributes(NodeID, DeviceType):
    State_Attributes = {}
    Temperature_Current = 0
    Temperature_Target = 0
    Temperature_Difference = 0
    
    if len(HiveSession_Current.Products.Heating) > 0:
        Temperature_Current = Private_Get_Heating_CurrentTemp(NodeID, DeviceType)
        Temperature_Target = Private_Get_Heating_TargetTemp(NodeID, DeviceType)
        
        if Temperature_Target > Temperature_Current:
            Temperature_Difference = Temperature_Target - Temperature_Current
        
            State_Attributes.update({"Current Temperature": Temperature_Current})
            State_Attributes.update({"Target Temperature": Temperature_Target})
            State_Attributes.update({"Temperature Difference": Temperature_Difference})
    return State_Attributes

def Private_Get_Heating_TargetTemp(NodeID, DeviceType):
    NodeIndex = -1

    Heating_TargetTemp_Return = 0
    Heating_TargetTemp_tmp = 0
    Heating_TargetTemp_Found = False

    if len(HiveSession_Current.Products.Heating) > 0:
        for x in range(0, len(HiveSession_Current.Products.Heating)):
            if "id" in HiveSession_Current.Products.Heating[x]:
                if HiveSession_Current.Products.Heating[x]["id"] == NodeID:
                    NodeIndex = x
                    break

        if NodeIndex != -1:
            Heating_Mode_Current = Private_Get_Heating_Mode(NodeID, DeviceType)
            if Heating_Mode_Current == "SCHEDULE":
                if 'props' in HiveSession_Current.Products.Heating[NodeIndex] and 'scheduleOverride' in HiveSession_Current.Products.Heating[NodeIndex]["props"]:
                    if HiveSession_Current.Products.Heating[NodeIndex]["props"]["scheduleOverride"] == True:
                        if "state" in HiveSession_Current.Products.Heating[NodeIndex] and "target" in HiveSession_Current.Products.Heating[NodeIndex]["state"]:
                            Heating_TargetTemp_tmp = HiveSession_Current.Products.Heating[NodeIndex]["state"]["target"]
                            Heating_TargetTemp_Found = True
                    else:
                        ScheduleNowAndNext = Private_Get_Schedule_NowAndNext(HiveSession_Current.Products.Heating[NodeIndex]["state"]["schedule"])
                        if 'now' in ScheduleNowAndNext:
                            if 'value' in ScheduleNowAndNext["now"] and 'target' in ScheduleNowAndNext["now"]["value"]:
                                Heating_TargetTemp_tmp = ScheduleNowAndNext["now"]["value"]["target"]
                                Heating_TargetTemp_Found = True
            else:
                if "state" in HiveSession_Current.Products.Heating[NodeIndex] and "target" in HiveSession_Current.Products.Heating[NodeIndex]["state"]:
                    Heating_TargetTemp_tmp = HiveSession_Current.Products.Heating[NodeIndex]["state"]["target"]
                    Heating_TargetTemp_Found = True
        
    if Heating_TargetTemp_Found == True:
        Current_Node_Attribute_Values["Heating_TargetTemp_" + NodeID] = Heating_TargetTemp_tmp
        Heating_TargetTemp_Return = Heating_TargetTemp_tmp
    else:
        if ("Heating_TargetTemp_" + NodeID) in Current_Node_Attribute_Values:
            Heating_TargetTemp_Return = Current_Node_Attribute_Values.get("Heating_TargetTemp_" + NodeID)
        else:
            Heating_TargetTemp_Return = 0

    return Heating_TargetTemp_Return
    
def Private_Get_Heating_TargetTemperature_State_Attributes(NodeID, DeviceType):
    State_Attributes = {}

    return State_Attributes

def Private_Get_Heating_State(NodeID, DeviceType):
    Heating_State_Return = "OFF"
    Heating_State_tmp = "OFF"
    Heating_State_Found = False

    if len(HiveSession_Current.Products.Heating) > 0:
        Temperature_Current = Private_Get_Heating_CurrentTemp(NodeID, DeviceType)
        Temperature_Target = Private_Get_Heating_TargetTemp(NodeID, DeviceType)
        Heating_Boost = Private_Get_Heating_Boost(NodeID, DeviceType)
        Heating_Mode = Private_Get_Heating_Mode(NodeID, DeviceType)
        
        if Heating_Mode == "SCHEDULE" or Heating_Mode == "MANUAL" or Heating_Boost == "ON":
            if Temperature_Current < Temperature_Target:
                Heating_State_tmp = "ON"
                Heating_State_Found = True
            else:
                Heating_State_tmp = "OFF"
                Heating_State_Found = True
        else:
            Heating_State_tmp = "OFF"
            Heating_State_Found = True
    
    if Heating_State_Found == True:
        Current_Node_Attribute_Values["Heating_State_" + NodeID] = Heating_State_tmp
        Heating_State_Return = Heating_State_tmp
    else:
        if ("Heating_State_" + NodeID) in Current_Node_Attribute_Values:
            Heating_State_Return = Current_Node_Attribute_Values.get("Heating_State_" + NodeID)
        else:
            Heating_State_Return = "UNKNOWN"
                
    return Heating_State_Return
    
def Private_Get_Heating_State_State_Attributes(NodeID, DeviceType):
    NodeIndex = -1
    State_Attributes = {}

    Heating_Mode_Current = Private_Get_Heating_Mode(NodeID, DeviceType)

    if len(HiveSession_Current.Products.Heating) > 0:
        for x in range(0, len(HiveSession_Current.Products.Heating)):
            if "id" in HiveSession_Current.Products.Heating[x]:
                if HiveSession_Current.Products.Heating[x]["id"] == NodeID:
                    NodeIndex = x
                    break

    if Heating_Mode_Current == "SCHEDULE":
        ScheduleNowAndNext = Private_Get_Schedule_NowAndNext(HiveSession_Current.Products.Heating[NodeIndex]["state"]["schedule"])
        if 'next' in ScheduleNowAndNext:
            if 'value' in ScheduleNowAndNext["next"] and 'start' in ScheduleNowAndNext["next"] and 'target' in ScheduleNowAndNext["next"]["value"]:
                NextTarget = ScheduleNowAndNext["next"]["value"]["target"]
                NextStart = ScheduleNowAndNext["next"]["start"]
                State_Attributes.update({"Next" : str(NextTarget) + " : " + Private_MinutesToTime(NextStart)})
        if 'now' in ScheduleNowAndNext:
            if 'value' in ScheduleNowAndNext["now"] and 'start' in ScheduleNowAndNext["now"] and 'target' in ScheduleNowAndNext["now"]["value"]:
                NowTarget = ScheduleNowAndNext["now"]["value"]["target"]
                NowtStart = ScheduleNowAndNext["now"]["start"]
                NextStart = ScheduleNowAndNext["next"]["start"]
                State_Attributes.update({"Now" : str(NowTarget) + " : " + Private_MinutesToTime(NowtStart) + " - " + Private_MinutesToTime(NextStart)})
    else:
        State_Attributes.update({"Schedule not active": ""})

    return State_Attributes

def Private_Get_Heating_Mode(NodeID, DeviceType):
    NodeIndex = -1

    Heating_Mode_Return = "UNKNOWN"
    Heating_Mode_tmp = "UNKNOWN"
    Heating_Mode_Found = False
 
    
    if len(HiveSession_Current.Products.Heating) > 0:
        for x in range(0, len(HiveSession_Current.Products.Heating)):
            if "id" in HiveSession_Current.Products.Heating[x]:
                if HiveSession_Current.Products.Heating[x]["id"] == NodeID:
                    NodeIndex = x
                    break

        if NodeIndex != -1:
            if "state" in HiveSession_Current.Products.Heating[NodeIndex] and "mode" in HiveSession_Current.Products.Heating[NodeIndex]["state"]:
                Heating_Mode_tmp = HiveSession_Current.Products.Heating[NodeIndex]["state"]["mode"]
                if Heating_Mode_tmp == "BOOST":
                    if "props" in HiveSession_Current.Products.Heating[NodeIndex] and "previous" in HiveSession_Current.Products.Heating[NodeIndex]["props"] and "mode" in HiveSession_Current.Products.Heating[NodeIndex]["props"]["previous"]:
                        Heating_Mode_tmp = HiveSession_Current.Products.Heating[NodeIndex]["props"]["previous"]["mode"]
                Heating_Mode_Found = True
    
    if Heating_Mode_Found == True:
        Current_Node_Attribute_Values["Heating_Mode_" + NodeID] = Heating_Mode_tmp
        Heating_Mode_Return = Heating_Mode_tmp
    else:
        if ("Heating_Mode_" + NodeID) in Current_Node_Attribute_Values:
            Heating_Mode_Return = Current_Node_Attribute_Values.get("Heating_Mode_" + NodeID)
        else:
            Heating_Mode_Return = "UNKNOWN"
            _LOGGER.error("Heating Mode not found")
                
    return Heating_Mode_Return
  
def Private_Get_Heating_Mode_State_Attributes(NodeID, DeviceType):
    State_Attributes = Private_Get_Heating_State_State_Attributes(NodeID, DeviceType)

    return State_Attributes
    
def Private_Get_Heating_Operation_Mode_List(NodeID, DeviceType):
    HiveHeating_operation_list = ["SCHEDULE", "MANUAL", "OFF"]
    return HiveHeating_operation_list
    
def Private_Get_Heating_Boost(NodeID, DeviceType):
    NodeIndex = -1

    Heating_Boost_Return = "UNKNOWN"
    Heating_Boost_tmp = "UNKNOWN"
    Heating_Boost_Found = False
    
    if len(HiveSession_Current.Products.Heating) > 0:
        for x in range(0, len(HiveSession_Current.Products.Heating)):
            if "id" in HiveSession_Current.Products.Heating[x]:
                if HiveSession_Current.Products.Heating[x]["id"] == NodeID:
                    NodeIndex = x
                    break

        if NodeIndex != -1:
            if "state" in HiveSession_Current.Products.Heating[NodeIndex] and "boost" in HiveSession_Current.Products.Heating[NodeIndex]["state"]:
                Heating_Boost_tmp = HiveSession_Current.Products.Heating[NodeIndex]["state"]["boost"]
                if Heating_Boost_tmp == None:
                    Heating_Boost_tmp = "OFF"
                else:
                    Heating_Boost_tmp = "ON"
                Heating_Boost_Found = True

    if Heating_Boost_Found == True:
        Current_Node_Attribute_Values["Heating_Boost_" + NodeID] = Heating_Boost_tmp
        Heating_Boost_Return = Heating_Boost_tmp
    else:
        if ("Heating_Boost_" + NodeID) in Current_Node_Attribute_Values:
            Heating_Boost_Return = Current_Node_Attribute_Values.get("Heating_Boost_" + NodeID)
        else:
            Heating_Boost_Return = "UNKNOWN"
            _LOGGER.error("Heating Boost not found")
            
    return Heating_Boost_Return

def Private_Get_Heating_Boost_State_Attributes(NodeID, DeviceType):
    State_Attributes = {}
    
    if Private_Get_Heating_Boost(NodeID, DeviceType) == "ON":
        NodeIndex = -1

        Heating_Boost_tmp = "UNKNOWN"
        Heating_Boost_Found = False
    
        if len(HiveSession_Current.Products.Heating) > 0:
            for x in range(0, len(HiveSession_Current.Products.Heating)):
                if "id" in HiveSession_Current.Products.Heating[x]:
                    if HiveSession_Current.Products.Heating[x]["id"] == NodeID:
                        NodeIndex = x
                        break

            if NodeIndex != -1:
                if "state" in HiveSession_Current.Products.Heating[NodeIndex] and "boost" in HiveSession_Current.Products.Heating[NodeIndex]["state"]:
                    Heating_Boost_tmp = HiveSession_Current.Products.Heating[NodeIndex]["state"]["boost"]
                    Heating_Boost_Found = True
    
        if Heating_Boost_Found == True:
            State_Attributes.update({"Boost ends in": (str(Heating_Boost_tmp) + " minutes")})

    return State_Attributes    
    
def Private_Get_HotWater_Mode(NodeID, DeviceType):
    NodeIndex = -1

    HotWater_Mode_Return = "UNKNOWN"
    HotWater_Mode_tmp = "UNKNOWN"
    HotWater_Mode_Found = False

   
    if len(HiveSession_Current.Products.HotWater) > 0:
        for x in range(0, len(HiveSession_Current.Products.HotWater)):
            if "id" in HiveSession_Current.Products.HotWater[x]:
                if HiveSession_Current.Products.HotWater[x]["id"] == NodeID:
                    NodeIndex = x
                    break

        if NodeIndex != -1:
            if "state" in HiveSession_Current.Products.HotWater[NodeIndex] and "mode" in HiveSession_Current.Products.HotWater[NodeIndex]["state"]:
                HotWater_Mode_tmp = HiveSession_Current.Products.HotWater[NodeIndex]["state"]["mode"]
                if HotWater_Mode_tmp == "BOOST":
                    if "props" in HiveSession_Current.Products.HotWater[NodeIndex] and "previous" in HiveSession_Current.Products.HotWater[NodeIndex]["props"] and "mode" in HiveSession_Current.Products.HotWater[NodeIndex]["props"]["previous"]:
                        HotWater_Mode_tmp = HiveSession_Current.Products.HotWater[NodeIndex]["props"]["previous"]["mode"]
                elif HotWater_Mode_tmp == "MANUAL":
                    HotWater_Mode_tmp = "ON"
                HotWater_Mode_Found = True
            
    if HotWater_Mode_Found == True:
        Current_Node_Attribute_Values["HotWater_Mode_" + NodeID] = HotWater_Mode_tmp
        HotWater_Mode_Return = HotWater_Mode_tmp
    else:
        if ("HotWater_Mode_" + NodeID) in Current_Node_Attribute_Values:
            HotWater_Mode_Return = Current_Node_Attribute_Values.get("HotWater_Mode_" + NodeID)
        else:
            HotWater_Mode_Return = "UNKNOWN"
            _LOGGER.error("HotWater Mode not found")

    return HotWater_Mode_Return
    
def Private_Get_HotWater_Mode_State_Attributes(NodeID, DeviceType):
    State_Attributes = Private_Get_HotWater_State_State_Attributes(NodeID, DeviceType)


    return State_Attributes
 
def Private_Get_HotWater_Operation_Mode_List(NodeID, DeviceType):
    HiveHotWater_operation_list = ["SCHEDULE", "ON", "OFF"]
    return HiveHotWater_operation_list
    
def Private_Get_HotWater_Boost(NodeID, DeviceType):
    NodeIndex = -1

    HotWater_Boost_Return = "UNKNOWN"
    HotWater_Boost_tmp = "UNKNOWN"
    HotWater_Boost_Found = False
    
    if len(HiveSession_Current.Products.HotWater) > 0:
        for x in range(0, len(HiveSession_Current.Products.HotWater)):
            if "id" in HiveSession_Current.Products.HotWater[x]:
                if HiveSession_Current.Products.HotWater[x]["id"] == NodeID:
                    NodeIndex = x
                    break

        if NodeIndex != -1:
            if "state" in HiveSession_Current.Products.HotWater[NodeIndex] and "boost" in HiveSession_Current.Products.HotWater[NodeIndex]["state"]:
                HotWater_Boost_tmp = HiveSession_Current.Products.HotWater[NodeIndex]["state"]["boost"]
                if HotWater_Boost_tmp == None:
                    HotWater_Boost_tmp = "OFF"
                else:
                    HotWater_Boost_tmp = "ON"
                HotWater_Boost_Found = True
                            
    if HotWater_Boost_Found == True:
        Current_Node_Attribute_Values["HotWater_Boost_" + NodeID] = HotWater_Boost_tmp
        HotWater_Boost_Return = HotWater_Boost_tmp
    else:
        if ("HotWater_Boost_" + NodeID) in Current_Node_Attribute_Values:
            HotWater_Boost_Return = Current_Node_Attribute_Values.get("HotWater_Boost_" + NodeID)
        else:
            HotWater_Boost_Return = "UNKNOWN"
            _LOGGER.error("HotWater Boost not found")

    return HotWater_Boost_Return
    
def Private_Get_HotWater_Boost_State_Attributes(NodeID, DeviceType):
    State_Attributes = {}
    
    if Private_Get_HotWater_Boost(NodeID, DeviceType) == "ON":
        NodeIndex = -1

        HotWater_Boost_tmp = "UNKNOWN"
        HotWater_Boost_Found = False
    
        if len(HiveSession_Current.Products.HotWater) > 0:
            for x in range(0, len(HiveSession_Current.Products.HotWater)):
                if "id" in HiveSession_Current.Products.HotWater[x]:
                    if HiveSession_Current.Products.HotWater[x]["id"] == NodeID:
                        NodeIndex = x
                        break

            if NodeIndex != -1:
                if "state" in HiveSession_Current.Products.HotWater[NodeIndex] and "boost" in HiveSession_Current.Products.HotWater[NodeIndex]["state"]:
                    HotWater_Boost_tmp = HiveSession_Current.Products.HotWater[NodeIndex]["state"]["boost"]
                    HotWater_Boost_Found = True
    
        if HotWater_Boost_Found == True:
            State_Attributes.update({"Boost ends in": (str(HotWater_Boost_tmp) + " minutes")})

    return State_Attributes   
    
def Private_Get_HotWater_State(NodeID, DeviceType):
    NodeIndex = -1

    HotWater_State_Return = "OFF"
    HotWater_State_tmp = "OFF"
    HotWater_State_Found = False
    HotWater_Mode_Current = Private_Get_HotWater_Mode(NodeID, DeviceType)
  
    if len(HiveSession_Current.Products.HotWater) > 0:
        for x in range(0, len(HiveSession_Current.Products.HotWater)):
            if "id" in HiveSession_Current.Products.HotWater[x]:
                if HiveSession_Current.Products.HotWater[x]["id"] == NodeID:
                    NodeIndex = x
                    break

        if NodeIndex != -1:
            if "state" in HiveSession_Current.Products.HotWater[NodeIndex] and "status" in HiveSession_Current.Products.HotWater[NodeIndex]["state"]:
                HotWater_State_tmp = HiveSession_Current.Products.HotWater[NodeIndex]["state"]["status"]
                if HotWater_State_tmp == None:
                    HotWater_State_tmp = "OFF"
                else:
                    if HotWater_Mode_Current == "SCHEDULE":
                        if Private_Get_HotWater_Boost(NodeID, DeviceType) == "ON":
                            HotWater_State_tmp = "ON"
                            HotWater_State_Found = True
                        else:
                            if "state" in HiveSession_Current.Products.HotWater[NodeIndex] and "schedule" in HiveSession_Current.Products.HotWater[NodeIndex]["state"]:
                                ScheduleNowAndNext = Private_Get_Schedule_NowAndNext(HiveSession_Current.Products.HotWater[NodeIndex]["state"]["schedule"])
                                if 'now' in ScheduleNowAndNext:
                                    if 'value' in ScheduleNowAndNext["now"] and 'status' in ScheduleNowAndNext["now"]["value"]:
                                        HotWater_State_tmp = ScheduleNowAndNext["now"]["value"]["status"]
                                        HotWater_State_Found = True
                    else:
                        HotWater_State_Found = True

                

    if HotWater_State_Found == True:
        Current_Node_Attribute_Values["HotWater_State_" + NodeID] = HotWater_State_tmp
        HotWater_State_Return = HotWater_State_tmp
    else:
        if ("HotWater_State_" + NodeID) in Current_Node_Attribute_Values:
            HotWater_State_Return = Current_Node_Attribute_Values.get("HotWater_State_" + NodeID)
        else:
            HotWater_State_Return = "UNKNOWN"
            
    return HotWater_State_Return
    
def Private_Get_HotWater_State_State_Attributes(NodeID, DeviceType):
    NodeIndex = -1
    State_Attributes = {}

    HotWater_Mode_Current = Private_Get_HotWater_Mode(NodeID, DeviceType)

    if len(HiveSession_Current.Products.HotWater) > 0:
        for x in range(0, len(HiveSession_Current.Products.HotWater)):
            if "id" in HiveSession_Current.Products.HotWater[x]:
                if HiveSession_Current.Products.HotWater[x]["id"] == NodeID:
                    NodeIndex = x
                    break
    if HotWater_Mode_Current == "SCHEDULE":
        ScheduleNowAndNext = Private_Get_Schedule_NowAndNext(HiveSession_Current.Products.HotWater[NodeIndex]["state"]["schedule"])
        if 'next' in ScheduleNowAndNext:
            if 'value' in ScheduleNowAndNext["next"] and 'start' in ScheduleNowAndNext["next"] and 'status' in ScheduleNowAndNext["next"]["value"]:
                NextStatus = ScheduleNowAndNext["next"]["value"]["status"]
                NextStart = ScheduleNowAndNext["next"]["start"]
                State_Attributes.update({"Next" : NextStatus + " : " + Private_MinutesToTime(NextStart)})
        if 'now' in ScheduleNowAndNext:
            if 'value' in ScheduleNowAndNext["now"] and 'start' in ScheduleNowAndNext["now"] and 'status' in ScheduleNowAndNext["now"]["value"]:
                NowStatus = ScheduleNowAndNext["now"]["value"]["status"]
                NowtStart = ScheduleNowAndNext["now"]["start"]
                NextStart = ScheduleNowAndNext["next"]["start"]
                State_Attributes.update({"Now" : NowStatus + " : " + Private_MinutesToTime(NowtStart) + " - " + Private_MinutesToTime(NextStart)})
    else:
        State_Attributes.update({"Schedule not active": ""})

    return State_Attributes

def Private_Get_Thermostat_BatteryLevel(NodeID, DeviceType):
    NodeIndex = -1

    Thermostat_BatteryLevel_Return = 0
    Thermostat_BatteryLevel_tmp = 0
    Thermostat_BatteryLevel_Found = False
    
    if len(HiveSession_Current.Devices.Thermostat) > 0:
        for x in range(0, len(HiveSession_Current.Devices.Thermostat)):
            if "id" in HiveSession_Current.Devices.Thermostat[x]:
                if HiveSession_Current.Devices.Thermostat[x]["id"] == NodeID:
                    NodeIndex = x
                    break

        if NodeIndex != -1:
            if "props" in HiveSession_Current.Devices.Thermostat[NodeIndex] and "battery" in HiveSession_Current.Devices.Thermostat[NodeIndex]["props"]:
                Thermostat_BatteryLevel_tmp = HiveSession_Current.Devices.Thermostat[NodeIndex]["props"]["battery"]
                Thermostat_BatteryLevel_Found = True
            
    if Thermostat_BatteryLevel_Found == True:
        Current_Node_Attribute_Values["Thermostat_BatteryLevel_" + NodeID] = Thermostat_BatteryLevel_tmp
        Thermostat_BatteryLevel_Return = Thermostat_BatteryLevel_tmp
    else:
        if ("Thermostat_BatteryLevel_" + NodeID) in Current_Node_Attribute_Values:
            Thermostat_BatteryLevel_Return = Current_Node_Attribute_Values.get("Thermostat_BatteryLevel_" + NodeID)
        else:
            Thermostat_BatteryLevel_Return = 0
            
    return Thermostat_BatteryLevel_Return

def Private_Get_Light_State(NodeID, DeviceType, NodeName):
    NodeIndex = -1

    Light_State_Return = "UNKNOWN"
    Light_State_tmp = "UNKNOWN"
    Light_State_Found = False

    if len(HiveSession_Current.Products.Light) > 0:
        for x in range(0, len(HiveSession_Current.Products.Light)):
            if "id" in HiveSession_Current.Products.Light[x]:
                if HiveSession_Current.Products.Light[x]["id"] == NodeID:
                    NodeIndex = x
                    break

        if NodeIndex != -1:
            if "state" in HiveSession_Current.Products.Light[NodeIndex] and "status" in \
                    HiveSession_Current.Products.Light[NodeIndex]["state"]:
                Light_State_tmp = HiveSession_Current.Products.Light[NodeIndex]["state"]["status"]
                Light_State_Found = True

    if Light_State_Found == True:
        Current_Node_Attribute_Values["Light_State_" + HiveSession_Current.Products.Light[NodeIndex]["id"]] = Light_State_tmp
        Light_State_Return = Light_State_tmp
    else:
        if ("Light_State_" + HiveSession_Current.Products.Light[NodeIndex]["id"]) in Current_Node_Attribute_Values:
            Light_State_Return = Current_Node_Attribute_Values.get("Light_State_" + HiveSession_Current.Products.Light[NodeIndex]["id"])
        else:
            Light_State_Return = "UNKNOWN"

    if HiveSession_Current.Logging == True:
        _LOGGER.warning("State is %s", Light_State_Return)
    if Light_State_Return == "ON":
        return True
    else:
        return False

def Private_Get_Light_Brightness(NodeID, DeviceType, NodeName):
    NodeIndex = -1

    Tmp_Brightness_Return = 0
    Light_Brightness_Return = 0
    Light_Brightness_tmp = 0
    Light_Brightness_Found = False

    if len(HiveSession_Current.Products.Light) > 0:
        for x in range(0, len(HiveSession_Current.Products.Light)):
            if "id" in HiveSession_Current.Products.Light[x]:
                if HiveSession_Current.Products.Light[x]["id"] == NodeID:
                    NodeIndex = x
                    break

        if NodeIndex != -1:
            if "state" in HiveSession_Current.Products.Light[NodeIndex] and "brightness" in \
                    HiveSession_Current.Products.Light[NodeIndex]["state"]:
                Light_Brightness_tmp = HiveSession_Current.Products.Light[NodeIndex]["state"]["brightness"]
                Light_Brightness_Found = True

    if Light_Brightness_Found == True:
        Current_Node_Attribute_Values["Light_Brightness_" + HiveSession_Current.Products.Light[NodeIndex]["id"]] = Light_Brightness_tmp
        Tmp_Brightness_Return = Light_Brightness_tmp
        Light_Brightness_Return = ((Tmp_Brightness_Return / 100) * 255)
    else:
        if ("Light_Brightness_" + HiveSession_Current.Products.Light[NodeIndex]["id"]) in Current_Node_Attribute_Values:
            Tmp_Brightness_Return = Current_Node_Attribute_Values.get("Light_Brightness_" + HiveSession_Current.Products.Light[NodeIndex]["id"])
            Light_Brightness_Return = ((Tmp_Brightness_Return / 100) * 255)
        else:
            Light_Brightness_Return = 0

    if HiveSession_Current.Logging == True:
        _LOGGER.warning("Brightness is %s percent", Tmp_Brightness_Return)
    return Light_Brightness_Return

def Private_Get_Light_Min_Color_Temp(NodeID, DeviceType, NodeName):
    NodeIndex = -1

    Light_Min_Color_Temp_Tmp = 0
    Light_Min_Color_Temp_Return = 0
    Light_Min_Color_Temp_Found = False

    if len(HiveSession_Current.Products.Light) > 0:
        for x in range(0, len(HiveSession_Current.Products.Light)):
            if "id" in HiveSession_Current.Products.Light[x]:
                if HiveSession_Current.Products.Light[x]["id"] == NodeID:
                    NodeIndex = x
                    break

        if NodeIndex != -1:
            if "props" in HiveSession_Current.Products.Light[NodeIndex] and "colourTemperature" in \
                    HiveSession_Current.Products.Light[NodeIndex]["props"] and "max" in \
                    HiveSession_Current.Products.Light[NodeIndex]["props"]["colourTemperature"]:
                Light_Min_Color_Temp_Tmp = HiveSession_Current.Products.Light[NodeIndex]["props"]["colourTemperature"]["max"]
                Light_Min_Color_Temp_Found = True


    if Light_Min_Color_Temp_Found == True:
        Current_Node_Attribute_Values["Light_Min_Color_Temp_" + HiveSession_Current.Products.Light[NodeIndex]["id"]] = Light_Min_Color_Temp_Tmp
        Light_Min_Color_Temp_Return = round((1 / Light_Min_Color_Temp_Tmp) * 1000000)
    else:
        if ("Light_Min_Color_Temp_" + HiveSession_Current.Products.Light[NodeIndex]["id"]) in Current_Node_Attribute_Values:
            Light_Min_Color_Temp_Return = Current_Node_Attribute_Values.get("Light_Min_Color_Temp_" + HiveSession_Current.Products.Light[NodeIndex]["id"])
        else:
            Light_Min_Color_Temp_Return = 0

    return Light_Min_Color_Temp_Return

def Private_Get_Light_Max_Color_Temp(NodeID, DeviceType, NodeName):
    NodeIndex = -1

    Light_Max_Color_Temp_Tmp = 0
    Light_Max_Color_Temp_Return = 0
    Light_Max_Color_Temp_Found = False

    if len(HiveSession_Current.Products.Light) > 0:
        for x in range(0, len(HiveSession_Current.Products.Light)):
            if "id" in HiveSession_Current.Products.Light[x]:
                if HiveSession_Current.Products.Light[x]["id"] == NodeID:
                    NodeIndex = x
                    break

        if NodeIndex != -1:
            if "props" in HiveSession_Current.Products.Light[NodeIndex] and "colourTemperature" in \
                    HiveSession_Current.Products.Light[NodeIndex]["props"] and "min" in \
                    HiveSession_Current.Products.Light[NodeIndex]["props"]["colourTemperature"]:
                Light_Max_Color_Temp_Tmp = HiveSession_Current.Products.Light[NodeIndex]["props"]["colourTemperature"]["min"]
                Light_Max_Color_Temp_Found = True

    if Light_Max_Color_Temp_Found == True:
        Current_Node_Attribute_Values["Light_Max_Color_Temp_" + HiveSession_Current.Products.Light[NodeIndex]["id"]] = Light_Max_Color_Temp_Tmp
        Light_Max_Color_Temp_Return = round((1 / Light_Max_Color_Temp_Tmp) * 1000000)
    else:
        if ("Light_Max_Color_Temp_" + HiveSession_Current.Products.Light[NodeIndex]["id"]) in Current_Node_Attribute_Values:
            Light_Max_Color_Temp_Return = Current_Node_Attribute_Values.get("Light_Max_Color_Temp_" + HiveSession_Current.Products.Light[NodeIndex]["id"])
        else:
            Light_Max_Color_Temp_Return = 0

    return Light_Max_Color_Temp_Return

def Private_Get_Light_Color_Temp(NodeID, DeviceType, NodeName):
    NodeIndex = -1

    Light_Color_Temp_Tmp = 0
    Light_Color_Temp_Return = 0
    Light_Color_Temp_Found = False

    if len(HiveSession_Current.Products.Light) > 0:
        for x in range(0, len(HiveSession_Current.Products.Light)):
            if "id" in HiveSession_Current.Products.Light[x]:
                if HiveSession_Current.Products.Light[x]["id"] == NodeID:
                    NodeIndex = x
                    break

        if NodeIndex != -1:
            if "state" in HiveSession_Current.Products.Light[NodeIndex] and "colourTemperature" in \
                    HiveSession_Current.Products.Light[NodeIndex]["state"]:
                Light_Color_Temp_Tmp = HiveSession_Current.Products.Light[NodeIndex]["state"]["colourTemperature"]
                Light_Color_Temp_Found = True

    if Light_Color_Temp_Found == True:
        Current_Node_Attribute_Values["Light_Color_Temp_" + HiveSession_Current.Products.Light[NodeIndex]["id"]] = Light_Color_Temp_Tmp
        Light_Color_Temp_Return = round((1 / Light_Color_Temp_Tmp) * 1000000)
    else:
        if ("Light_Color_Temp_" + HiveSession_Current.Products.Light[NodeIndex]["id"]) in Current_Node_Attribute_Values:
            Light_Color_Temp_Return = Current_Node_Attribute_Values.get("Light_Color_Temp_" + HiveSession_Current.Products.Light[NodeIndex]["id"])
        else:
            Light_Color_Temp_Return = 0

    if HiveSession_Current.Logging == True:
        _LOGGER.warning("Colour temperature is %s", Light_Color_Temp_Return)
    return Light_Color_Temp_Return

def Private_Get_Smartplug_State(NodeID, DeviceType, NodeName):
    NodeIndex = -1

    Smartplug_State_Tmp = "UNKNOWN"
    Smartplug_State_Return = "UNKNOWN"
    Smartplug_State_Found = False

    if len(HiveSession_Current.Products.Plug) > 0:
        for x in range(0, len(HiveSession_Current.Products.Plug)):
            if "id" in HiveSession_Current.Products.Plug[x]:
                if HiveSession_Current.Products.Plug[x]["id"] == NodeID:
                    NodeIndex = x
                    break

        if NodeIndex != -1:
            if "state" in HiveSession_Current.Products.Plug[NodeIndex] and "status" in \
                    HiveSession_Current.Products.Plug[NodeIndex]["state"]:
                Smartplug_State_Tmp = HiveSession_Current.Products.Plug[NodeIndex]["state"]["status"]
                Smartplug_State_Found = True

    if Smartplug_State_Found == True:
        Current_Node_Attribute_Values["Smartplug_State_" + HiveSession_Current.Products.Plug[NodeIndex]["id"]] = Smartplug_State_Tmp
        Smartplug_State_Return = Smartplug_State_Tmp
    else:
        if ("Smartplug_State_" + HiveSession_Current.Products.Plug[NodeIndex]["id"]) in Current_Node_Attribute_Values:
            Smartplug_State_Return = Current_Node_Attribute_Values.get("Smartplug_State_" + HiveSession_Current.Products.Plug[NodeIndex]["id"])
        else:
            Smartplug_State_Return = "UNKNOWN"

    if HiveSession_Current.Logging == True:
        _LOGGER.warning("State is %s", Smartplug_State_Return)
    if Smartplug_State_Return == "ON":
        return True
    else:
        return False

def Private_Get_Smartplug_Power_Comsumption(NodeID, DeviceType, NodeName):
    NodeIndex = -1

    Smartplug_Current_Power_Tmp = 0
    Smartplug_Current_Power_Return = 0
    Smartplug_Current_Power_Found = False

    if len(HiveSession_Current.Products.Plug) > 0:
        for x in range(0, len(HiveSession_Current.Products.Plug)):
            if "id" in HiveSession_Current.Products.Plug[x]:
                if HiveSession_Current.Products.Plug[x]["id"] == NodeID:
                    NodeIndex = x
                    break

        if NodeIndex != -1:
            if "props" in HiveSession_Current.Products.Plug[NodeIndex] and "powerConsumption" in \
                    HiveSession_Current.Products.Plug[NodeIndex]["props"]:
                Smartplug_Current_Power_Tmp = HiveSession_Current.Products.Plug[NodeIndex]["props"]["powerConsumption"]
                Smartplug_Current_Power_Found = True

    if Smartplug_Current_Power_Found == True:
        Current_Node_Attribute_Values["Smartplug_Current_Power_" + HiveSession_Current.Products.Plug[NodeIndex]["id"]] = Smartplug_Current_Power_Tmp
        Smartplug_Current_Power_Return = Smartplug_Current_Power_Tmp
    else:
        if ("Smartplug_Current_Power_" + HiveSession_Current.Products.Plug[NodeIndex]["id"]) in Current_Node_Attribute_Values:
            Smartplug_Current_Power_Return = Current_Node_Attribute_Values.get("Smartplug_Current_Power_" + HiveSession_Current.Products.Plug[NodeIndex]["id"])
        else:
            Smartplug_Current_Power_Return = 0

    if HiveSession_Current.Logging == True:
        _LOGGER.warning("Power consumption is %s", Smartplug_Current_Power_Return)
    return Smartplug_Current_Power_Return

### - Currently not supported by Beekeeper API, Uncomment when support is added.
#def Private_Get_Smartplug_Today_Energy(NodeID):
#    NodeIndex = -1
#    Smartplug_Today_Energy_Tmp = 0
#    Smartplug_Today_Energy_Return = 0
#    Smartplug_Today_Energy_Found = False

#    if len(HiveSession_Current.Nodes.Plug) > 0:
#        for x in range(0, len(HiveSession_Current.Nodes.Plug)):
#            if "id" in HiveSession_Current.Nodes.Plug[x]:
#                if HiveSession_Current.Nodes.Plug[x]["id"] == NodeID:
#                    NodeIndex = x
#                    break

#       if NodeIndex != -1:
#            if "features" in HiveSession_Current.Nodes.Plug[NodeIndex] and "energy_usage_measurement_device_v1" in \
#                    HiveSession_Current.Nodes.Plug[NodeIndex]["features"] and "energyConsumed" in \
#                    HiveSession_Current.Nodes.Plug[NodeIndex]["features"]["energy_usage_measurement_device_v1"] \
#                    and "displayValue" in HiveSession_Current.Nodes.Plug[NodeIndex]["features"]["energy_usage_measurement_device_v1"]["energyConsumed"]:
#                Smartplug_Today_Energy_Tmp = HiveSession_Current.Nodes.Plug[NodeIndex]["features"]["energy_usage_measurement_device_v1"]["energyConsumed"]["displayValue"]
#                Smartplug_Today_Energy_Found = True

#           if Smartplug_Today_Energy_Found == True:
#               Current_Node_Attribute_Values["Smartplug_Today_Energy_" + HiveSession_Current.Nodes.Plug[NodeIndex]["id"]] = Smartplug_Today_Energy_Tmp
#               Smartplug_Today_Energy_Return = Smartplug_Today_Energy_Tmp
#           else:
#               if ("Smartplug_Today_Energy_" + HiveSession_Current.Nodes.Plug[NodeIndex]["id"]) in Current_Node_Attribute_Values:
#                   Smartplug_Today_Energy_Return = Current_Node_Attribute_Values.get("Smartplug_Today_Energy_" + HiveSession_Current.Nodes.Plug[NodeIndex]["id"])
#               else:
#                   Smartplug_Today_Energy_Return = 0
#
#        return Smartplug_Today_Energy_Return
###
        
def Private_Hive_API_Set_Temperature(NodeID, DeviceType, NewTemperature):
    Check_Hive_API_Logon()

    SetModeSuccess = False
    API_Response_SetTemperature = ""

    if HiveSession_Current.SessionID != None:
        NodeIndex = -1
        if len(HiveSession_Current.Products.Heating) > 0:
            for x in range(0, len(HiveSession_Current.Products.Heating)):
                if "id" in HiveSession_Current.Products.Heating[x]:
                    if HiveSession_Current.Products.Heating[x]["id"] == NodeID:
                        NodeIndex = x
                        break

            if NodeIndex != -1:
                if "id" in HiveSession_Current.Products.Heating[NodeIndex]:
                    JsonStringContent = '{"target":' + str(NewTemperature) + '}'

                    HiveAPI_URL = HiveAPI_Details.URLs.Nodes + "/heating/" + HiveSession_Current.Products.Heating[NodeIndex]["id"]
                    API_Response_SetTemperature = Hive_API_JsonCall ("POST", HiveAPI_URL, JsonStringContent, False)

                    if str(API_Response_SetTemperature) == "<Response [200]>":
                        Hive_API_Get_Nodes(NodeID, DeviceType)
                        NodeDataUpdated_FireBusEvent(NodeID, DeviceType)
                        SetModeSuccess = True

    return SetModeSuccess


def Private_Hive_API_Set_Heating_Mode(NodeID, DeviceType, NewMode):
    Check_Hive_API_Logon()

    SetModeSuccess = False
    API_Response_SetMode = ""

    if HiveSession_Current.SessionID != None:
        NodeIndex = -1
        if len(HiveSession_Current.Products.Heating) > 0:
            for x in range(0, len(HiveSession_Current.Products.Heating)):
                if "id" in HiveSession_Current.Products.Heating[x]:
                    if HiveSession_Current.Products.Heating[x]["id"] == NodeID:
                        NodeIndex = x
                        break

            if NodeIndex != -1:
                if "id" in HiveSession_Current.Products.Heating[NodeIndex]:
                    if NewMode == "SCHEDULE":
                        JsonStringContent = '{"mode": "SCHEDULE"}'
                    elif NewMode == "MANUAL":
                        JsonStringContent = '{"mode": "MANUAL"}'
                    elif NewMode == "OFF":
                        JsonStringContent = '{"mode": "OFF"}'

                    if NewMode == "SCHEDULE" or NewMode == "MANUAL" or NewMode == "OFF":
                        HiveAPI_URL = HiveAPI_Details.URLs.Nodes + "/heating/" + HiveSession_Current.Products.Heating[NodeIndex]["id"]
                        API_Response_SetMode = Hive_API_JsonCall ("POST", HiveAPI_URL, JsonStringContent, False)

                        if str(API_Response_SetMode) == "<Response [200]>":
                            Hive_API_Get_Nodes(NodeID, DeviceType)
                            NodeDataUpdated_FireBusEvent(NodeID, DeviceType)
                            SetModeSuccess = True

    return SetModeSuccess


def Private_Hive_API_Set_HotWater_Mode(NodeID, DeviceType, NewMode):
    Check_Hive_API_Logon()

    SetModeSuccess = False
    API_Response_SetMode = ""

    if HiveSession_Current.SessionID != None:
        NodeIndex = -1
        if len(HiveSession_Current.Products.HotWater) > 0:
            for x in range(0, len(HiveSession_Current.Products.HotWater)):
                if "id" in HiveSession_Current.Products.HotWater[x]:
                    if HiveSession_Current.Products.HotWater[x]["id"] == NodeID:
                        NodeIndex = x
                        break

            if NodeIndex != -1:
                if "id" in HiveSession_Current.Products.HotWater[NodeIndex]:
                    if NewMode == "SCHEDULE":
                        JsonStringContent = '{"mode": "SCHEDULE"}'
                    elif NewMode == "ON":
                        JsonStringContent = '{"mode": "MANUAL"}'
                    elif NewMode == "OFF":
                        JsonStringContent = '{"mode": "OFF"}'

                    if NewMode == "SCHEDULE" or NewMode == "ON" or NewMode == "OFF":
                        HiveAPI_URL = HiveAPI_Details.URLs.Nodes + "/hotwater/" + HiveSession_Current.Products.HotWater[NodeIndex]["id"]
                        API_Response_SetMode = Hive_API_JsonCall ("POST", HiveAPI_URL, JsonStringContent, False)

                        if str(API_Response_SetMode) == "<Response [200]>":
                            Hive_API_Get_Nodes(NodeID, DeviceType)
                            NodeDataUpdated_FireBusEvent(NodeID, DeviceType)
                            SetModeSuccess = True

    return SetModeSuccess
        
def Private_Hive_API_Set_Light_TurnON(NodeID, DeviceType, NodeDeviceType, NodeName, NewBrightness, NewColorTemp):
    NodeIndex = -1

    Check_Hive_API_Logon()

    SetModeSuccess = False
    API_Response_SetLight = ""
    
    if HiveSession_Current.SessionID != None:
        if len(HiveSession_Current.Products.Light) > 0:
            for x in range(0, len(HiveSession_Current.Products.Light)):
                if "id" in HiveSession_Current.Products.Light[x]:
                    if HiveSession_Current.Products.Light[x]["id"] == NodeID:
                        NodeIndex = x
                        break
            if NodeIndex != -1:
                if NewBrightness == None and NewColorTemp == None:
                    JsonStringContent = '{"status": "ON"}'
                elif NewBrightness != None and NewColorTemp == None:
                    JsonStringContent = '{"status": "ON", "brightness": ' + str(NewBrightness) + '}'
                elif NewColorTemp != None and NewBrightness == None:
                    JsonStringContent = '{"colourTemperature": ' + str(NewColorTemp) + '}'
#                elif NewRGBColor != None and NewColorTemp == None and NewBrightness == None:
#                    JsonStringContent = '{"rgbcolour": ' + NewRGBColour + '}'

                HiveAPI_URL = HiveAPI_Details.URLs.Nodes + '/' + NodeDeviceType + '/' + HiveSession_Current.Products.Light[NodeIndex]["id"]
                API_Response_SetLight = Hive_API_JsonCall("POST", HiveAPI_URL, JsonStringContent, False)

            if str(API_Response_SetLight) == "<Response [200]>":
                Hive_API_Get_Nodes(NodeID, DeviceType)
                NodeDataUpdated_FireBusEvent(NodeID, DeviceType)
                SetModeSuccess = True

    return SetModeSuccess

def Private_Hive_API_Set_Light_TurnOFF(NodeID, DeviceType, NodeDeviceType, NodeName):
    NodeIndex = -1

    Check_Hive_API_Logon()

    SetModeSuccess = False
    API_Response_SetLight = ""

    if HiveSession_Current.SessionID != None:
        if len(HiveSession_Current.Products.Light) > 0:
            for x in range(0, len(HiveSession_Current.Products.Light)):
                if "id" in HiveSession_Current.Products.Light[x]:
                    if HiveSession_Current.Products.Light[x]["id"] == NodeID:
                        NodeIndex = x
                        break
            if NodeIndex != -1:
                JsonStringContent = '{"status": "OFF"}'
                HiveAPI_URL = HiveAPI_Details.URLs.Nodes + '/' + NodeDeviceType + '/' + HiveSession_Current.Products.Light[NodeIndex]["id"]
                API_Response_SetLight = Hive_API_JsonCall("POST", HiveAPI_URL, JsonStringContent, False)
            else:
                _LOGGER.error("Unable to control %s", NodeName)

            if str(API_Response_SetLight) == "<Response [200]>":
                Hive_API_Get_Nodes(NodeID, DeviceType)
                NodeDataUpdated_FireBusEvent(NodeID, DeviceType)
                SetModeSuccess = True

    return SetModeSuccess

def Private_Hive_API_Set_Smartplug_TurnON(NodeID, DeviceType, NodeName, NodeDeviceType):
    NodeIndex = -1

    Check_Hive_API_Logon()

    SetModeSuccess = False
    API_Response_SetPlug = ""

    if HiveSession_Current.SessionID != None:
        if len(HiveSession_Current.Products.Plug) > 0:
            for x in range(0, len(HiveSession_Current.Products.Plug)):
                if "id" in HiveSession_Current.Products.Plug[x]:
                    if HiveSession_Current.Products.Plug[x]["id"] == NodeID:
                        NodeIndex = x
                        break
            if NodeIndex != -1:
                JsonStringContent = '{"status": "ON"}'
                HiveAPI_URL = HiveAPI_Details.URLs.Nodes + '/' + NodeDeviceType + '/' + HiveSession_Current.Products.Plug[NodeIndex]["id"]
                API_Response_SetPlug = Hive_API_JsonCall("POST", HiveAPI_URL, JsonStringContent, False)
            else:
                _LOGGER.error("Unable to control %s", NodeName)

            if str(API_Response_SetPlug) == "<Response [200]>":
                Hive_API_Get_Nodes(NodeID, DeviceType)
                NodeDataUpdated_FireBusEvent(NodeID, DeviceType)
                SetModeSuccess = True

    return SetModeSuccess

def Private_Hive_API_Set_Smartplug_TurnOFF(NodeID, DeviceType, NodeName, NodeDeviceType):
    NodeIndex = -1

    Check_Hive_API_Logon()

    SetModeSuccess = False
    API_Response_SetPlug = ""

    if HiveSession_Current.SessionID != None:
        if len(HiveSession_Current.Products.Plug) > 0:
            for x in range(0, len(HiveSession_Current.Products.Plug)):
                if "id" in HiveSession_Current.Products.Plug[x]:
                    if HiveSession_Current.Products.Plug[x]["id"] == NodeID:
                        NodeIndex = x
                        break
            if NodeIndex != -1:
                JsonStringContent = '{"status": "OFF"}'
                HiveAPI_URL = HiveAPI_Details.URLs.Nodes + '/' + NodeDeviceType + '/' + HiveSession_Current.Products.Plug[NodeIndex]["id"]
                API_Response_SetPlug = Hive_API_JsonCall("POST", HiveAPI_URL, JsonStringContent, False)
            else:
                _LOGGER.error("Unable to control %s", NodeName)

            if str(API_Response_SetPlug) == "<Response [200]>":
                Hive_API_Get_Nodes(NodeID, DeviceType)
                NodeDataUpdated_FireBusEvent(NodeID, DeviceType)
                SetModeSuccess = True

    return SetModeSuccess

def Private_MinutesToTime(MinutesToConvert):
    HoursConverted, MinutesConverted = divmod(MinutesToConvert, 60)
    ConvertedTime = datetime.strptime(str(HoursConverted) + ":" + str(MinutesConverted), "%H:%M")
    ConvertedTime_String = ConvertedTime.strftime("%H:%M")
    return ConvertedTime_String

def Private_Convert_DateTime_StateDisplayString(DateTimeToConvert):
    ReturnString = ""
    SecondsDifference = (datetime.now() - DateTimeToConvert).total_seconds()
        
    if SecondsDifference < 60:
        ReturnString = str(round(SecondsDifference)) + " seconds ago"
    elif SecondsDifference >= 60 and SecondsDifference <= (60 * 60):
        ReturnString = str(round(SecondsDifference / 60)) + " minutes ago"
    elif SecondsDifference > (60 * 60) and SecondsDifference <= (60 * 60 * 24):
        ReturnString = DateTimeToConvert.strftime('%H:%M')
    else:
        ReturnString = DateTimeToConvert.strftime('%H:%M %d-%b-%Y')
    
    return ReturnString

def Private_Epoch_TimeMilliseconds_To_datetime(EpochStringMilliseconds):
    EpochStringseconds = EpochStringMilliseconds / 1000
    DateTimeUTC = datetime.fromtimestamp(EpochStringseconds)
    return DateTimeUTC

def Private_Get_Schedule_NowAndNext(HiveAPI_Schedule):
    Schedule_NowAndNext = {}
    DateTime_Now = datetime.now()
    Minutes_Since_Midnight = int((DateTime_Now - DateTime_Now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds() / 60)
    DateTime_Now_Day_int = DateTime_Now.today().weekday()
    DateTime_Yesterday_Day = "sunday"
    DateTime_Now_Day = "monday"
    DateTime_Tomorrow_Day = "tuesday"

    if DateTime_Now_Day_int == 0:
        DateTime_Yesterday_Day = "sunday"
        DateTime_Now_Day = "monday"
        DateTime_Tomorrow_Day = "tuesday"
    elif DateTime_Now_Day_int == 1:
        DateTime_Yesterday_Day = "monday"
        DateTime_Now_Day = "tuesday"
        DateTime_Tomorrow_Day = "wednesday"
    elif DateTime_Now_Day_int == 2:
        DateTime_Yesterday_Day = "tuesday"
        DateTime_Now_Day = "wednesday"
        DateTime_Tomorrow_Day = "thursday"
    elif DateTime_Now_Day_int == 3:
        DateTime_Yesterday_Day = "wednesday"
        DateTime_Now_Day = "thursday"
        DateTime_Tomorrow_Day = "friday"
    elif DateTime_Now_Day_int == 4:
        DateTime_Yesterday_Day = "thursday"
        DateTime_Now_Day = "friday"
        DateTime_Tomorrow_Day = "saturday"
    elif DateTime_Now_Day_int == 5:
        DateTime_Yesterday_Day = "friday"
        DateTime_Now_Day = "saturday"
        DateTime_Tomorrow_Day = "sunday"
    elif DateTime_Now_Day_int == 6:
        DateTime_Yesterday_Day = "saturday"
        DateTime_Now_Day = "sunday"
        DateTime_Tomorrow_Day = "monday"

    YesterdayDay_Value = HiveAPI_Schedule[DateTime_Yesterday_Day]
    YesterdayDay_Value_Sorted = sorted(YesterdayDay_Value, key = operator.itemgetter('start'), reverse=False)
    YesterdayDay_Value_Sorted_Count = len(YesterdayDay_Value_Sorted)

    CurrentDay_Value = HiveAPI_Schedule[DateTime_Now_Day]
    CurrentDay_Value_Sorted = sorted(CurrentDay_Value, key = operator.itemgetter('start'), reverse=False)
    CurrentDay_Value_Sorted_Count = len(CurrentDay_Value_Sorted)

    TomorrowDay_Value = HiveAPI_Schedule[DateTime_Tomorrow_Day]
    TomorrowDay_Value_Sorted = sorted(TomorrowDay_Value, key = operator.itemgetter('start'), reverse=False)
    TomorrowDay_Value_Sorted_Count = len(TomorrowDay_Value_Sorted)

    Schedule_Now = None
    Schedule_Next = None

    for x in range(0, CurrentDay_Value_Sorted_Count):
        if "start" in CurrentDay_Value_Sorted[x]:
            if x == 0 and Minutes_Since_Midnight < CurrentDay_Value_Sorted[x]["start"]:
                if "start" in YesterdayDay_Value_Sorted[YesterdayDay_Value_Sorted_Count - 1]:
                    Schedule_Now = YesterdayDay_Value_Sorted[YesterdayDay_Value_Sorted_Count - 1]
                    Schedule_Next = CurrentDay_Value_Sorted[x]
            elif (x + 1) == CurrentDay_Value_Sorted_Count and Minutes_Since_Midnight >= CurrentDay_Value_Sorted[x]["start"]:
                Schedule_Now = CurrentDay_Value_Sorted[x]
                if TomorrowDay_Value_Sorted_Count > 0:
                    if "start" in TomorrowDay_Value_Sorted[0]:
                        Schedule_Next = TomorrowDay_Value_Sorted[0]
            else:
                if Minutes_Since_Midnight >= CurrentDay_Value_Sorted[x]["start"] and Minutes_Since_Midnight < CurrentDay_Value_Sorted[x + 1]["start"]:
                    Schedule_Now = CurrentDay_Value_Sorted[x]
                    Schedule_Next = CurrentDay_Value_Sorted[x + 1]


    Schedule_NowAndNext['now'] = Schedule_Now
    Schedule_NowAndNext['next'] = Schedule_Next

    return Schedule_NowAndNext

def setup(hass, config):
    """Setup the Hive platform"""
    Initialise_App()

    HiveSession_Current.hass = hass

    HiveSession_Current.UserName = None
    HiveSession_Current.Password = None
    
    hive_config = config[DOMAIN]

    if "username" in hive_config and "password" in hive_config:
        HiveSession_Current.UserName = config[DOMAIN]['username']
        HiveSession_Current.Password = config[DOMAIN]['password']
    else:
        _LOGGER.error("Missing UserName or Password in config")
    
    if "minutes_between_updates" in hive_config:
        tmp_MINUTES_BETWEEN_UPDATES = config[DOMAIN]['minutes_between_updates']
    else:
        tmp_MINUTES_BETWEEN_UPDATES = 2
        
    Hive_Node_Update_Interval = tmp_MINUTES_BETWEEN_UPDATES * 60

    if "logging" in hive_config:
        if config[DOMAIN]['logging'] == True:
            HiveSession_Current.Logging = True
            _LOGGER.warning("Logging is Enabled")
        else:
            HiveSession_Current.Logging = False
    else:
        HiveSession_Current.Logging = False
    

    if HiveSession_Current.UserName is None or HiveSession_Current.Password is None:
        _LOGGER.error("Missing UserName or Password in Hive Session details")
    else:
        Hive_API_Logon()
        if HiveSession_Current.SessionID != None:
            HiveSession_Current.Update_Interval_Seconds = Hive_Node_Update_Interval
            Hive_API_Get_Nodes_NL()

    ConfigDevices = []
    
    if "devices" in hive_config:
        ConfigDevices = config[DOMAIN]['devices']

    DEVICECOUNT = 0
        
    DeviceList_Sensor = []
    DeviceList_Climate = []
    DeviceList_Light = []
    DeviceList_Plug = []
    
    if len(HiveSession_Current.Products.Heating) > 0:
        for aProduct in HiveSession_Current.Products.Heating:
            if "id" in aProduct and "state" in aProduct and "name" in aProduct["state"]:
                NodeName = aProduct["state"]["name"]
                if len(HiveSession_Current.Products.Heating) == 1:
                    NodeName = None
                if len(ConfigDevices) == 0 or (len(ConfigDevices) > 0 and "hive_heating" in ConfigDevices):
                    DEVICECOUNT = DEVICECOUNT + 1
                    DeviceList_Climate.append({'HA_DeviceType': 'Hive_Device_Heating', 'Hive_NodeID': aProduct["id"], 'Hive_NodeName': NodeName})
                if len(ConfigDevices) == 0 or (len(ConfigDevices) > 0 and "hive_heating_currenttemperature" in ConfigDevices):
                    DEVICECOUNT = DEVICECOUNT + 1
                    DeviceList_Sensor.append({'HA_DeviceType': 'Hive_Device_Heating_CurrentTemperature', 'Hive_NodeID': aProduct["id"], 'Hive_NodeName': NodeName})
                if len(ConfigDevices) == 0 or (len(ConfigDevices) > 0 and "hive_heating_targettemperature" in ConfigDevices):    
                    DEVICECOUNT = DEVICECOUNT + 1
                    DeviceList_Sensor.append({'HA_DeviceType': 'Hive_Device_Heating_TargetTemperature', 'Hive_NodeID': aProduct["id"], 'Hive_NodeName': NodeName})
                if len(ConfigDevices) == 0 or (len(ConfigDevices) > 0 and "hive_heating_state" in ConfigDevices):
                    DEVICECOUNT = DEVICECOUNT + 1
                    DeviceList_Sensor.append({'HA_DeviceType': 'Hive_Device_Heating_State', 'Hive_NodeID': aProduct["id"], 'Hive_NodeName': NodeName})
                if len(ConfigDevices) == 0 or (len(ConfigDevices) > 0 and "hive_heating_mode" in ConfigDevices):
                    DEVICECOUNT = DEVICECOUNT + 1
                    DeviceList_Sensor.append({'HA_DeviceType': 'Hive_Device_Heating_Mode', 'Hive_NodeID': aProduct["id"], 'Hive_NodeName': NodeName})
                if len(ConfigDevices) == 0 or (len(ConfigDevices) > 0 and "hive_heating_boost" in ConfigDevices):
                    DEVICECOUNT = DEVICECOUNT + 1
                    DeviceList_Sensor.append({'HA_DeviceType': 'Hive_Device_Heating_Boost', 'Hive_NodeID': aProduct["id"], 'Hive_NodeName': NodeName})

    if len(HiveSession_Current.Products.HotWater) > 0:
        for aProduct in HiveSession_Current.Products.HotWater:
            if "id" in aProduct and "state" in aProduct and "name" in aProduct["state"]:
                NodeName = aProduct["state"]["name"]
                if len(HiveSession_Current.Products.HotWater) == 1:
                    NodeName = None
                if len(ConfigDevices) == 0 or (len(ConfigDevices) > 0 and "hive_hotwater" in ConfigDevices):
                    DEVICECOUNT = DEVICECOUNT + 1
                    DeviceList_Climate.append({'HA_DeviceType': 'Hive_Device_HotWater', 'Hive_NodeID': aProduct["id"], 'Hive_NodeName': NodeName})
                if len(ConfigDevices) == 0 or (len(ConfigDevices) > 0 and "hive_hotwater_state" in ConfigDevices):
                    DEVICECOUNT = DEVICECOUNT + 1
                    DeviceList_Sensor.append({'HA_DeviceType': 'Hive_Device_HotWater_State', 'Hive_NodeID': aProduct["id"], 'Hive_NodeName': NodeName})
                if len(ConfigDevices) == 0 or (len(ConfigDevices) > 0 and "hive_hotwater_mode" in ConfigDevices):
                    DEVICECOUNT = DEVICECOUNT + 1
                    DeviceList_Sensor.append({'HA_DeviceType': 'Hive_Device_HotWater_Mode', 'Hive_NodeID': aProduct["id"], 'Hive_NodeName': NodeName})
                if len(ConfigDevices) == 0 or (len(ConfigDevices) > 0 and "hive_hotwater_boost" in ConfigDevices):
                    DEVICECOUNT = DEVICECOUNT + 1
                    DeviceList_Sensor.append({'HA_DeviceType': 'Hive_Device_HotWater_Boost', 'Hive_NodeID': aProduct["id"], 'Hive_NodeName': NodeName})
                                        
    if len(HiveSession_Current.Devices.Thermostat) > 0:
        for aDevice in HiveSession_Current.Devices.Thermostat:
            if "id" in aDevice and "state" in aDevice and "name" in aDevice["state"]:
                NodeName = aDevice["state"]["name"]
                if len(HiveSession_Current.Devices.Thermostat) == 1:
                    NodeName = None
                if len(ConfigDevices) == 0 or (len(ConfigDevices) > 0 and "hive_thermostat_batterylevel" in ConfigDevices):
                    DEVICECOUNT = DEVICECOUNT + 1
                    DeviceList_Sensor.append({'HA_DeviceType': 'Hive_Device_Thermostat_BatteryLevel', 'Hive_NodeID': aDevice["id"], 'Hive_NodeName': NodeName})

    if len(HiveSession_Current.Products.Light) > 0:
        for aProduct in HiveSession_Current.Products.Light:
            if "id" in aProduct and "state" in aProduct and "name" in aProduct["state"]:
                if len(ConfigDevices) == 0 or (len(ConfigDevices) > 0 and "hive_active_light" in ConfigDevices):
                    DEVICECOUNT = DEVICECOUNT + 1
                    if "type" in aProduct:
                        Hive_Light_DeviceType = aProduct["type"]
                        if HiveSession_Current.Logging == True:
                            _LOGGER.warning("Adding %s, %s to device list", aProduct["type"], aProduct["state"]["name"] )
                        DeviceList_Light.append({'HA_DeviceType': 'Hive_Device_Light', 'Hive_Light_DeviceType': Hive_Light_DeviceType, 'Hive_NodeID': aProduct["id"], 'Hive_NodeName': aProduct["state"]["name"]})

    if len(HiveSession_Current.Products.Plug) > 0:
        for aProduct in HiveSession_Current.Products.Plug:
            if "id" in aProduct and "state" in aProduct and "name" in aProduct["state"]:
                if len(ConfigDevices) == 0 or (len(ConfigDevices) > 0 and "hive_active_plug" in ConfigDevices):
                    DEVICECOUNT = DEVICECOUNT + 1
                    if "type" in aProduct:
                        Hive_Plug_DeviceType = aProduct["type"]
                        if HiveSession_Current.Logging == True:
                            _LOGGER.warning("Adding %s, %s to device list", aProduct["type"], aProduct["state"]["name"])
                        DeviceList_Plug.append({'HA_DeviceType': 'Hive_Device_Plug', 'Hive_Plug_DeviceType': Hive_Plug_DeviceType, 'Hive_NodeID': aProduct["id"], 'Hive_NodeName': aProduct["state"]["name"]})


    global HiveObjects_Global

    try:
        HiveObjects_Global = HiveObjects()
    except RuntimeError:
        return False
            
    if len(DeviceList_Sensor) > 0 or len(DeviceList_Climate) > 0 or len(DeviceList_Light) > 0 or len(DeviceList_Plug) > 0:
        if len(DeviceList_Sensor) > 0:
            load_platform(hass, 'sensor', DOMAIN, DeviceList_Sensor)
        if len(DeviceList_Climate) > 0:
            load_platform(hass, 'climate', DOMAIN, DeviceList_Climate)
        if len(DeviceList_Light) > 0:
            load_platform(hass, 'light', DOMAIN, DeviceList_Light)
        if len(DeviceList_Plug) > 0:
            load_platform(hass, 'switch', DOMAIN, DeviceList_Plug)
        return True


class HiveObjects():
    def __init__(self):
        """Initialize HiveObjects."""

    def UpdateData(self, NodeID, DeviceType):
        Hive_API_Get_Nodes_RL(NodeID, DeviceType)

    def Get_Heating_Min_Temperature(self, NodeID, DeviceType):
        return Private_Get_Heating_Min_Temperature(NodeID, DeviceType)

    def Get_Heating_Max_Temperature(self, NodeID, DeviceType):
        return Private_Get_Heating_Max_Temperature(NodeID, DeviceType)
        
    def Get_Heating_CurrentTemp(self, NodeID, DeviceType):
        return Private_Get_Heating_CurrentTemp(NodeID, DeviceType)
        
    def Get_Heating_CurrentTemp_State_Attributes(self, NodeID, DeviceType):
        return Private_Get_Heating_CurrentTemp_State_Attributes(NodeID, DeviceType)
        
    def Get_Heating_TargetTemp(self, NodeID, DeviceType):
        return Private_Get_Heating_TargetTemp(NodeID, DeviceType)
        
    def Get_Heating_TargetTemperature_State_Attributes(self, NodeID, DeviceType):
        return Private_Get_Heating_TargetTemperature_State_Attributes(NodeID, DeviceType)
        
    def Set_Heating_TargetTemp(self, NodeID, DeviceType, NewTemperature):
        if NewTemperature is not None:
            SetTempResult = Private_Hive_API_Set_Temperature(NodeID, DeviceType, NewTemperature)
        
    def Get_Heating_State(self, NodeID, DeviceType):
        return Private_Get_Heating_State(NodeID, DeviceType)
        
    def Get_Heating_State_State_Attributes(self, NodeID, DeviceType):
        return Private_Get_Heating_State_State_Attributes(NodeID, DeviceType)
        
    def Get_Heating_Mode(self, NodeID, DeviceType):
        return Private_Get_Heating_Mode(NodeID, DeviceType)
        
    def Set_Heating_Mode(self, NodeID, DeviceType, NewOperationMode):
        SetModeResult = Private_Hive_API_Set_Heating_Mode(NodeID, DeviceType, NewOperationMode)
        
    def Get_Heating_Mode_State_Attributes(self, NodeID, DeviceType):
        return Private_Get_Heating_Mode_State_Attributes(NodeID, DeviceType)
        
    def Get_Heating_Operation_Mode_List(self, NodeID, DeviceType):
        return Private_Get_Heating_Operation_Mode_List(NodeID, DeviceType)

    def Get_Heating_Boost(self, NodeID, DeviceType):
        return Private_Get_Heating_Boost(NodeID, DeviceType)
        
    def Get_Heating_Boost_State_Attributes(self, NodeID, DeviceType):
        return Private_Get_Heating_Boost_State_Attributes(NodeID, DeviceType)
        
    def Get_HotWater_State(self, NodeID, DeviceType):
        return Private_Get_HotWater_State(NodeID, DeviceType)
        
    def Get_HotWater_State_State_Attributes(self, NodeID, DeviceType):
        return Private_Get_HotWater_State_State_Attributes(NodeID, DeviceType)
        
    def Get_HotWater_Mode(self, NodeID, DeviceType):
        return Private_Get_HotWater_Mode(NodeID, DeviceType)
        
    def Get_HotWater_Mode_State_Attributes(self, NodeID, DeviceType):
        return Private_Get_HotWater_Mode_State_Attributes(NodeID, DeviceType)
        
    def Set_HotWater_Mode(self, NodeID, DeviceType, NewOperationMode):
        SetModeResult = Private_Hive_API_Set_HotWater_Mode(NodeID, DeviceType, NewOperationMode)
        
    def Get_HotWater_Operation_Mode_List(self, NodeID, DeviceType):
        return Private_Get_HotWater_Operation_Mode_List(NodeID, DeviceType)
        
    def Get_HotWater_Boost(self, NodeID, DeviceType):
        return Private_Get_HotWater_Boost(NodeID, DeviceType)
        
    def Get_HotWater_Boost_State_Attributes(self, NodeID, DeviceType):
        return Private_Get_HotWater_Boost_State_Attributes(NodeID, DeviceType)
        
    def Get_Thermostat_BatteryLevel(self, NodeID, DeviceType):
        return Private_Get_Thermostat_BatteryLevel(NodeID, DeviceType)
        
    def Get_Light_State(self, NodeID, DeviceType, NodeName):
        if HiveSession_Current.Logging == True:
            _LOGGER.warning("Getting status for  %s", NodeName)
        return Private_Get_Light_State(NodeID, DeviceType, NodeName)

    def Get_Light_Min_Color_Temp(self, NodeID, DeviceType, NodeName):
        return Private_Get_Light_Min_Color_Temp(NodeID, DeviceType, NodeName)

    def Get_Light_Max_Color_Temp(self, NodeID, DeviceType, NodeName):
        return Private_Get_Light_Max_Color_Temp(NodeID, DeviceType, NodeName)

    def Get_Light_Brightness(self, NodeID, DeviceType, NodeName):
        if HiveSession_Current.Logging == True:
            _LOGGER.warning("Getting brightness for  %s", NodeName)
        return Private_Get_Light_Brightness(NodeID, DeviceType, NodeName)

    def Get_Light_Color_Temp(self, NodeID, DeviceType, NodeName):
        if HiveSession_Current.Logging == True:
            _LOGGER.warning("Getting colour temperature for  %s", NodeName)
        return Private_Get_Light_Color_Temp(NodeID, DeviceType, NodeName)

    def Set_Light_TurnON(self, NodeID, DeviceType, NodeDeviceType, NodeName, NewBrightness, NewColorTemp):
        if HiveSession_Current.Logging == True:
            if NewBrightness == None and NewColorTemp == None:
                _LOGGER.warning("Switching %s light on", NodeName)
            elif NewBrightness != None and NewColorTemp == None:
                _LOGGER.warning("New Brightness is %s", NewBrightness)
            elif NewBrightness == None and NewColorTemp != None:
                _LOGGER.warning("New Colour Temprature is %s", NewColorTemp)
        SetModeResult =  Private_Hive_API_Set_Light_TurnON(NodeID, DeviceType, NodeDeviceType, NodeName, NewBrightness, NewColorTemp)

    def Set_Light_TurnOFF(self, NodeID, DeviceType, NodeDeviceType, NodeName):
        if HiveSession_Current.Logging == True:
                _LOGGER.warning("Switching %s light off", NodeName)
        return Private_Hive_API_Set_Light_TurnOFF(NodeID, DeviceType, NodeDeviceType, NodeName)
        
    def Get_Smartplug_State(self, NodeID, DeviceType, NodeName):
        if HiveSession_Current.Logging == True:
            _LOGGER.warning("Getting status for %s", NodeName)
        return Private_Get_Smartplug_State(NodeID, DeviceType, NodeName)

    def Get_Smartplug_Power_Consumption(self, NodeID, DeviceType, NodeName):
        if HiveSession_Current.Logging == True:
            _LOGGER.warning("Getting current power consumption for %s", NodeName)
        return Private_Get_Smartplug_Power_Comsumption(NodeID, DeviceType, NodeName)

### - Currently not supported by Beekeeper API, Uncomment when support is available.
#    def Get_Smartplug_Today_Energy(self, NodeID, DeviceType, NodeName):
#        if HiveSession_Current.Logging == True:
#            _LOGGER.warning("Getting energy consumed today for %s", NodeName)
#        return Private_Get_Smartplug_Today_Energy(NodeID)
###
    def Set_Smartplug_TurnON(self, NodeID, DeviceType, NodeName, NodeDeviceType):
        if HiveSession_Current.Logging == True:
            _LOGGER.warning("Switching %s on", NodeName)
        return Private_Hive_API_Set_Smartplug_TurnON(NodeID, DeviceType, NodeName, NodeDeviceType)

    def Set_Smartplug_TurnOFF(self, NodeID, DeviceType, NodeName, NodeDeviceType):
        if HiveSession_Current.Logging == True:
            _LOGGER.warning("Switching %s off", NodeName)
        return Private_Hive_API_Set_Smartplug_TurnOFF(NodeID, DeviceType, NodeName, NodeDeviceType)