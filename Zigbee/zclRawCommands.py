# !/usr/bin/env python3
# coding: utf-8 -*-
#
# Author: pipiche38
#

import struct
from Modules.sendZigateCommand import raw_APS_request
from Modules.tools import get_and_inc_ZCL_SQN
from Zigbee.encoder_tools import decode_endian_data

DEFAULT_ACK_MODE = False

# General Command Frame

# Read Attributes Command
def rawaps_read_attribute_req(self, nwkid, EpIn, EpOut, Cluster, direction, manufacturer_spec, manufacturer, Attr, ackIsDisabled=DEFAULT_ACK_MODE):
    self.log.logging("zclCommand", "Debug", "rawaps_read_attribute_req %s %s %s %s %s %s %s %s" % (nwkid, EpIn, EpOut, Cluster, direction, manufacturer_spec, manufacturer, Attr))

    cmd = "00"  # Read Attribute Command Identifier

    # Cluster Frame:
    # 0b xxxx xxxx
    #           |- Frame Type: Cluster Specific (0x00)
    #          |-- Manufacturer Specific False
    #         |--- Command Direction: Client to Server (0)
    #       | ---- Disable default response: True
    #    |||- ---- Reserved : 0x000
    #

    cluster_frame = 0b00010000
    if manufacturer_spec == "01":
        cluster_frame += 0b00000100

    fcf = "%02x" % cluster_frame
    sqn = get_and_inc_ZCL_SQN(self, nwkid)
    payload = fcf
    if manufacturer_spec == "01":
        payload += manufacturer[4:2] + manufacturer[:2]
    payload += sqn + cmd
    idx = 0
    while idx < len(Attr):
        attribute = Attr[idx : idx + 4]
        idx += 4
        payload += "%04x" % struct.unpack(">H", struct.pack("H", int(attribute, 16)))[0]
    raw_APS_request(self, nwkid, EpOut, Cluster, "0104", payload, zigate_ep=EpIn, ackIsDisabled=ackIsDisabled)
    return sqn


# Write Attributes
def rawaps_write_attribute_req(self, nwkid, EPin, EPout, cluster, manuf_id, manuf_spec, attribute, data_type, data, ackIsDisabled=DEFAULT_ACK_MODE):
    self.log.logging("zclCommand", "Debug", "rawaps_write_attribute_req %s %s %s %s %s %s %s %s %s" % (nwkid, EPin, EPout, cluster, manuf_id, manuf_spec, attribute, data_type, data))
    cmd = "02"

    cluster_frame = 0b00010000  # The frame type sub-field SHALL be set to indicate a global command (0b00)
    if (
        manuf_spec == "01"
    ):  # The manufacturer specific sub-field SHALL be set to 0 if this command is being used to Write Attributes defined for any cluster in the ZCL or 1 if this command is being used to write manufacturer specific attributes
        cluster_frame += 0b00000100
    fcf = "%02x" % cluster_frame
    sqn = get_and_inc_ZCL_SQN(self, nwkid)
    payload = fcf
    if manuf_spec == "01":
        payload += "%04x" % struct.unpack(">H", struct.pack("H", int(manuf_id, 16)))[0]
    payload += sqn + cmd
    payload += "%04x" % struct.unpack(">H", struct.pack("H", int(attribute, 16)))[0]  # Attribute Id
    payload += data_type  # Attribute Data Type
    if data_type in ("10", "18", "20", "28", "30"):  # Attribute Data
        payload += data
    elif data_type in ("09", "16", "21", "29", "31"):
        payload += "%04x" % struct.unpack(">H", struct.pack("H", int(data, 16)))[0]
    elif data_type in ("22", "2a"):
        payload += "%06x" % struct.unpack(">i", struct.pack("I", int(data, 16)))[0]
    elif data_type in ("23", "2b", "39"):
        payload += "%08x" % struct.unpack(">f", struct.pack("I", int(data, 16)))[0]
    else:
        payload += data
    self.log.logging("zclCommand", "Debug", "rawaps_write_attribute_req ==== payload: %s" % (payload))

    raw_APS_request(self, nwkid, EPout, cluster, "0104", payload, zigpyzqn=sqn, zigate_ep=EPin, ackIsDisabled=ackIsDisabled)
    return sqn


# Write Attributes No Response
def zcl_raw_write_attributeNoResponse(self, nwkid, EPin, EPout, cluster, manuf_id, manuf_spec, attribute, data_type, data, ackIsDisabled=DEFAULT_ACK_MODE):
    self.log.logging("zclCommand", "Debug", "zcl_raw_write_attributeNoResponse %s %s %s %s %s %s %s %s %s" % (nwkid, EPin, EPout, cluster, manuf_id, manuf_spec, attribute, data_type, data))
    cmd = "05"

    cluster_frame = 0b00010000  # The frame type sub-field SHALL be set to indicate a global command (0b00)
    if (
        manuf_spec == "01"
    ):  # The manufacturer specific sub-field SHALL be set to 0 if this command is being used to Write Attributes defined for any cluster in the ZCL or 1 if this command is being used to write manufacturer specific attributes
        cluster_frame += 0b00000100
    fcf = "%02x" % cluster_frame
    sqn = get_and_inc_ZCL_SQN(self, nwkid)
    payload = fcf
    if manuf_spec == "01":
        payload += "%04x" % struct.unpack(">H", struct.pack("H", int(manuf_id, 16)))[0]
    payload += sqn + cmd
    payload += "%04x" % struct.unpack(">H", struct.pack("H", int(attribute, 16)))[0]  # Attribute Id
    payload += data_type  # Attribute Data Type
    if data_type in ("10", "18", "20", "28", "30"):  # Attribute Data
        payload += data
    elif data_type in ("09", "16", "21", "29", "31"):
        payload += "%04x" % struct.unpack(">H", struct.pack("H", int(data, 16)))[0]
    elif data_type in ("22", "2a"):
        payload += "%06x" % struct.unpack(">i", struct.pack("I", int(data, 16)))[0]
    elif data_type in ("23", "2b", "39"):
        payload += "%08x" % struct.unpack(">i", struct.pack("I", int(data, 16)))[0]
    else:
        payload += data
    self.log.logging("zclCommand", "Debug", "rawaps_write_attribute_req ==== payload: %s" % (payload))

    raw_APS_request(self, nwkid, EPout, cluster, "0104", payload, zigpyzqn=sqn, zigate_ep=EPin, ackIsDisabled=ackIsDisabled)
    return sqn
    
    
# Configure Reporting
def zcl_raw_configure_reporting_requestv2(self, nwkid, epin, epout, cluster, direction, manufacturer_spec, manufacturer, attribute_reporting_configuration, ackIsDisabled=DEFAULT_ACK_MODE):
    self.log.logging("zclCommand", "Debug", "zcl_raw_configure_reporting_requestv2 %s %s %s %s %s %s %s %s" % (nwkid, epin, epout, cluster, direction, manufacturer_spec, manufacturer, attribute_reporting_configuration))

    cmd = "06"  # Configure Reporting Command Identifier

    # Cluster Frame:
    # 0b xxxx xxxx
    #           |- Frame Type: Cluster Specific (0x00)
    #          |-- Manufacturer Specific False
    #         |--- Command Direction: Client to Server (0)
    #       | ---- Disable default response: True
    #    |||- ---- Reserved : 0x000
    #

    cluster_frame = 0b00010000
    if manufacturer_spec == "01":
        cluster_frame += 0b00000100

    fcf = "%02x" % cluster_frame
    sqn = get_and_inc_ZCL_SQN(self, nwkid)
    payload = fcf
    if manufacturer_spec == "01":
        payload += "%04x" % struct.unpack(">H", struct.pack("H", int(manufacturer, 16)))[0]
    payload += sqn + cmd

    self.log.logging("zclCommand", "Debug", "zcl_raw_configure_reporting_requestv2  payload: %s" % payload)
    for x in attribute_reporting_configuration:
        self.log.logging("zclCommand", "Debug", "zcl_configure_reporting_requestv2 record: %s" % str(x))
        payload += direction
        payload += "%04x" % struct.unpack(">H", struct.pack("H", int(x["Attribute"], 16)))[0]
        payload += x["DataType"]
        payload += "%04x" % struct.unpack(">H", struct.pack("H", int(x["minInter"], 16)))[0]
        payload += "%04x" % struct.unpack(">H", struct.pack("H", int(x["maxInter"], 16)))[0]
        if "rptChg" in x:
            payload += decode_endian_data(x["rptChg"], x["DataType"])

        # payload +=  "%04x" % struct.unpack(">H", struct.pack("H",int(x['timeOut'],16)))[0]
        self.log.logging("zclCommand", "Debug", "zcl_raw_configure_reporting_requestv2  payload: %s" % payload)

    raw_APS_request(self, nwkid, epout, cluster, "0104", payload, zigpyzqn=sqn, zigate_ep=epin, ackIsDisabled=ackIsDisabled)
    return sqn


# Discover Attributes

# Cluster 0004: Groups

def zcl_raw_add_group_membership(self, nwkid, epin, epout, GrpId, ackIsDisabled=DEFAULT_ACK_MODE):
    self.log.logging("zclCommand", "Log", "zcl_raw_add_group_membership %s %s %s %s" % (nwkid, epin, epout, GrpId))
    
    cmd = "00"
    cluster = "0004"
    cluster_frame = 0b00010001
    
    fcf = "%02x" % cluster_frame
    sqn = get_and_inc_ZCL_SQN(self, nwkid)
    payload = fcf
    payload += sqn + cmd + "%04x" % (struct.unpack(">H", struct.pack("H", int(GrpId, 16)))[0]) + "00"
    raw_APS_request(self, nwkid, epout, cluster, "0104", payload, zigpyzqn=sqn, zigate_ep=epin, ackIsDisabled=ackIsDisabled)
    return sqn
    

def zcl_raw_check_group_member_ship(self, nwkid, epin, epout, GrpId, ackIsDisabled=DEFAULT_ACK_MODE):
    self.log.logging("zclCommand", "Log", "zcl_raw_check_group_member_ship %s %s %s %s" % (nwkid, epin, epout, GrpId))
    
    cmd = "01"
    cluster = "0004"
    cluster_frame = 0b00010001

    fcf = "%02x" % cluster_frame
    sqn = get_and_inc_ZCL_SQN(self, nwkid)
    payload = fcf
    payload += sqn + cmd + "%04x" % (struct.unpack(">H", struct.pack("H", int(GrpId, 16)))[0])
    raw_APS_request(self, nwkid, epout, cluster, "0104", payload, zigpyzqn=sqn, zigate_ep=epin, ackIsDisabled=ackIsDisabled)
    return sqn


def zcl_raw_look_for_group_member_ship(self, nwkid, epin, epout, nbgroup, group_list, ackIsDisabled=DEFAULT_ACK_MODE):
    self.log.logging("zclCommand", "Log", "zcl_raw_look_for_group_member_ship %s %s %s %s %s" % (nwkid, epin, epout, nbgroup, group_list))
    
    cmd = "02"
    cluster = "0004"
    cluster_frame = 0b00010001

    fcf = "%02x" % cluster_frame
    sqn = get_and_inc_ZCL_SQN(self, nwkid)
    payload = fcf
    
    payload += sqn + cmd + nbgroup  

    idx = 0
    while  idx < int(nbgroup,16)*4:
        payload += decode_endian_data( group_list[ idx : idx + 4 ], "21")
        idx += 4

    raw_APS_request(self, nwkid, epout, cluster, "0104", payload, zigpyzqn=sqn, zigate_ep=epin, ackIsDisabled=ackIsDisabled)
    return sqn


def zcl_raw_remove_group_member_ship(self, nwkid, epin, epout, GrpId, ackIsDisabled=DEFAULT_ACK_MODE):
    self.log.logging("zclCommand", "Log", "zcl_raw_remove_group_member_ship %s %s %s %s" % (nwkid, epin, epout, GrpId))
    
    cmd = "03"
    cluster = "0004"
    cluster_frame = 0b00010001

    fcf = "%02x" % cluster_frame
    sqn = get_and_inc_ZCL_SQN(self, nwkid)
    payload = fcf
    payload += sqn + cmd + "%04x" % (struct.unpack(">H", struct.pack("H", int(GrpId, 16)))[0])
    raw_APS_request(self, nwkid, epout, cluster, "0104", payload, zigpyzqn=sqn, zigate_ep=epin, ackIsDisabled=ackIsDisabled)
    return sqn


def zcl_raw_remove_all_groups(self, nwkid, epin, epout, ackIsDisabled=DEFAULT_ACK_MODE):
    self.log.logging("zclCommand", "Log", "zcl_raw_remove_group_member_ship %s %s %s" % (nwkid, epin, epout))
    
    cmd = "05"
    cluster = "0004"
    cluster_frame = 0b00010001

    fcf = "%02x" % cluster_frame
    sqn = get_and_inc_ZCL_SQN(self, nwkid)
    payload = fcf
    payload += sqn + cmd
    raw_APS_request(self, nwkid, epout, cluster, "0104", payload, zigpyzqn=sqn, zigate_ep=epin, ackIsDisabled=ackIsDisabled)
    return sqn


def zcl_raw_send_group_member_ship_identify(self, nwkid, epin, epout, GrpId, ackIsDisabled=DEFAULT_ACK_MODE):
    self.log.logging("zclCommand", "Log", "zcl_raw_send_group_member_ship_identify %s %s %s %s" % (nwkid, epin, epout, GrpId))

    cmd = "06"
    cluster = "0004"
    cluster_frame = 0b00010001

    fcf = "%02x" % cluster_frame
    sqn = get_and_inc_ZCL_SQN(self, nwkid)
    payload = fcf
    payload += sqn + cmd + "%04x" % (struct.unpack(">H", struct.pack("H", int(GrpId, 16)))[0])
    raw_APS_request(self, nwkid, epout, cluster, "0104", payload, zigpyzqn=sqn, zigate_ep=epin, ackIsDisabled=ackIsDisabled)
    return sqn



# Cluster 0006: On/Off
######################
def raw_zcl_zcl_onoff(self, nwkid, EPIn, EpOut, command, effect="", groupaddrmode=False, ackIsDisabled=DEFAULT_ACK_MODE):
    self.log.logging("zclCommand", "Log", "raw_zcl_zcl_onoff %s %s %s %s %s %s" % (nwkid, EPIn, EpOut, command, effect, groupaddrmode))

    Cluster = "0006"
    ONOFF_COMMANDS = {
        "Off": 0x00,
        "On": 0x01,
        "Toggle": 0x02,
        "OffWithEffect": 0x40,
        "OnWithRecallGlobalScene": 0x41,
        "OnWithTimedOff": 0x42,
    }
    if command not in ONOFF_COMMANDS:
        return

    # Cluster Frame:
    # 0b xxxx xxxx
    #           |- Frame Type: Cluster Specific (0x01)
    #          |-- Manufacturer Specific False
    #         |--- Command Direction: Client to Server (0)
    #       | ---- Disable default response: True
    #    |||- ---- Reserved : 0x000
    #
    cluster_frame = 0b00010001

    sqn = get_and_inc_ZCL_SQN(self, nwkid)
    payload = "%02x" % cluster_frame + sqn + "%02x" % ONOFF_COMMANDS[command] + effect

    raw_APS_request(self, nwkid, EpOut, Cluster, "0104", payload, zigpyzqn=sqn, zigate_ep=EPIn, groupaddrmode=groupaddrmode, ackIsDisabled=ackIsDisabled)
    return sqn


# Cluster 0008: Level Control
#############################


def zcl_raw_level_move_to_level(self, nwkid, EPIn, EPout, command, level="00", move_mode="00", rate="FF", step_mode="00", step_size="01", transition="0010", groupaddrmode=False, ackIsDisabled=DEFAULT_ACK_MODE):
    self.log.logging("zclCommand", "Debug", "zcl_raw_level_move_to_level %s %s %s %s %s %s %s %s %s %s" % (nwkid, EPIn, EPout, command, level, move_mode, rate, step_mode, step_size, transition))

    Cluster = "0008"
    LEVEL_COMMANDS = {"MovetoLevel": 0x00, "Move": 0x01, "Step": 0x02, "Stop": 0x03, "MovetoLevelWithOnOff": 0x04, "MoveWithOnOff": 0x05, "StepWithOnOff": 0x06, "Stop2": 0x07}
    if command not in LEVEL_COMMANDS:
        return

    # Cluster Frame:
    # 0b xxxx xxxx
    #           |- Frame Type: Cluster Specific (0x01)
    #          |-- Manufacturer Specific False
    #         |--- Command Direction: Client to Server (0)
    #       | ---- Disable default response: True
    #    |||- ---- Reserved : 0x000
    #
    cluster_frame = 0b00010001

    sqn = get_and_inc_ZCL_SQN(self, nwkid)
    payload = "%02x" % cluster_frame + sqn + "%02x" % LEVEL_COMMANDS[command]
    if command in ("MovetoLevel", "MovetoLevelWithOnOff"):
        payload += level + "%04x" % (struct.unpack(">H", struct.pack("H", int(transition, 16)))[0])
    elif command == ("Move", "MoveWithOnOff"):
        payload += move_mode + rate
    elif command == ("Step", "StepWithOnOff"):
        payload += step_mode + step_size + "%04x" % (struct.unpack(">H", struct.pack("H", int(transition, 16)))[0])

    raw_APS_request(self, nwkid, EPout, Cluster, "0104", payload, zigpyzqn=sqn, zigate_ep=EPIn, groupaddrmode=groupaddrmode, ackIsDisabled=ackIsDisabled)
    return sqn


# Cluster 0102: Window Covering
################################


def zcl_raw_window_covering(self, nwkid, EPIn, EPout, command, level="00", percentage="00", groupaddrmode=False, ackIsDisabled=DEFAULT_ACK_MODE):
    self.log.logging("zclCommand", "Debug", "zcl_raw_window_covering %s %s %s %s %s" % (nwkid, EPout, command, level, percentage))

    Cluster = "0102"
    WINDOW_COVERING_COMMANDS = {"Up": 0x00, "Down": 0x01, "Stop": 0x02, "GoToLiftValue": 0x04, "GoToLiftPercentage": 0x05, "GoToTiltValue": 0x07, "GoToTiltPercentage": 0x08}
    if command not in WINDOW_COVERING_COMMANDS:
        return

    # Cluster Frame:
    # 0b xxxx xxxx
    #           |- Frame Type: Cluster Specific (0x01)
    #          |-- Manufacturer Specific False
    #         |--- Command Direction: Client to Server (0)
    #       | ---- Disable default response: True
    #    |||- ---- Reserved : 0x000
    #
    cluster_frame = 0b00010001

    sqn = get_and_inc_ZCL_SQN(self, nwkid)
    payload = "%02x" % cluster_frame + sqn + "%02x" % WINDOW_COVERING_COMMANDS[command]
    if command in ("MovetoLevel", "MovetoLevelWithOnOff"):
        payload += level
    elif command == ("GoToLiftValue", "GoToTiltValue"):
        payload += percentage

    raw_APS_request(self, nwkid, EPout, Cluster, "0104", payload, zigpyzqn=sqn, zigate_ep=EPIn, groupaddrmode=groupaddrmode, ackIsDisabled=ackIsDisabled)
    return sqn


# Cluster 0300: Color


def zcl_raw_move_color(self, nwkid, EPIn, EPout, command, temperature=None, hue=None, saturation=None, colorX=None, colorY=None, transition="0010", groupaddrmode=False, ackIsDisabled=DEFAULT_ACK_MODE):

    self.log.logging("zclCommand", "Debug", "zcl_raw_move_color %s %s %s %s %s %s %s %s %s %s %s" % (nwkid, EPIn, EPout, command, temperature, hue, saturation, colorX, colorY, transition, ackIsDisabled))

    COLOR_COMMANDS = {
        # "MovetoHue": 0x00,
        # "MoveHue": 0x01,
        # "StepHue": 0x02,
        # "MovetoSaturation": 0x03,
        # "MoveSaturation": 0x04,
        # "StepSaturation": 0x05,
        "MovetoHueandSaturation": 0x06,  # zcl_move_hue_and_saturation(self, nwkid, EPout, hue, saturation, transition="0010", ackIsDisabled=DEFAULT_ACK_MODE)
        "MovetoColor": 0x07,  # zcl_move_to_colour(self, nwkid, EPout, colorX, colorY, transition="0010", ackIsDisabled=DEFAULT_ACK_MODE)
        # "MoveColor": 0x08,
        # "StepColor": 0x09,
        "MovetoColorTemperature": 0x0A,  # zcl_move_to_colour_temperature( self, nwkid, EPout, temperature, transition="0010", ackIsDisabled=DEFAULT_ACK_MODE)
        # "EnhancedMovetoHue": 0x40,
        # "EnhancedMoveHue": 0x41,
        # "EnhancedStepHue": 0x42,
        # "EnhancedMovetoHueandSaturation": 0x43,
        # "ColorLoopSet": 0x44,
        # "StopMoveStep": 0x47,
        # "MoveCOlorTemperature": 0x4b,
        # "StepColorTemperature": 0x4c
    }

    Cluster = "0300"
    if command not in COLOR_COMMANDS:
        self.log.logging("zclCommand", "Debug", "zcl_raw_move_color command %s not implemented yet!!" % command)
        return

    cluster_frame = 0b00010001
    sqn = get_and_inc_ZCL_SQN(self, nwkid)

    payload = "%02x" % cluster_frame + sqn + "%02x" % COLOR_COMMANDS[command]

    if command == "MovetoHueandSaturation" and hue and saturation:
        payload += hue
        payload += saturation
        payload += "%04x" % (struct.unpack(">H", struct.pack("H", int(transition, 16)))[0])

    elif command == "MovetoColor" and colorX and colorY:
        payload += "%04x" % (struct.unpack(">H", struct.pack("H", int(colorX, 16)))[0])
        payload += "%04x" % (struct.unpack(">H", struct.pack("H", int(colorY, 16)))[0])
        payload += "%04x" % (struct.unpack(">H", struct.pack("H", int(transition, 16)))[0])

    elif command == "MovetoColorTemperature" and temperature:
        payload += "%04x" % (struct.unpack(">H", struct.pack("H", int(temperature, 16)))[0])
        payload += "%04x" % (struct.unpack(">H", struct.pack("H", int(transition, 16)))[0])

    raw_APS_request(self, nwkid, EPout, Cluster, "0104", payload, zigpyzqn=sqn, zigate_ep=EPIn, groupaddrmode=groupaddrmode, ackIsDisabled=ackIsDisabled)
    return sqn


# Cluster 0500: IAS

# Cluster 0500 ( 0x0400 )


def zcl_raw_ias_zone_enroll_response(self, nwkid, EPin, EPout, response_code, zone_id, groupaddrmode=False, ackIsDisabled=DEFAULT_ACK_MODE):
    Cluster = "0500"
    cmd = "00"
    cluster_frame = 0b00010001
    sqn = get_and_inc_ZCL_SQN(self, nwkid)
    payload = "%02x" % cluster_frame + sqn + cmd + response_code + zone_id
    raw_APS_request(self, nwkid, EPout, Cluster, "0104", payload, zigpyzqn=sqn, zigate_ep=EPin, groupaddrmode=groupaddrmode, ackIsDisabled=ackIsDisabled)
    return sqn


def zcl_raw_ias_initiate_normal_operation_mode(self, nwkid, EPin, EPout, groupaddrmode=False, ackIsDisabled=DEFAULT_ACK_MODE):

    cmd = "01"
    Cluster = "0500"
    cluster_frame = 0b00010001
    sqn = get_and_inc_ZCL_SQN(self, nwkid)
    payload = "%02x" % cluster_frame + sqn + cmd
    raw_APS_request(self, nwkid, EPout, Cluster, "0104", payload, zigpyzqn=sqn, zigate_ep=EPin, groupaddrmode=groupaddrmode, ackIsDisabled=ackIsDisabled)
    return sqn


def zcl_raw_ias_initiate_test_mode(self, nwkid, EPin, EPout, duration="01", current_zone_sensitivy_level="01", groupaddrmode=False, ackIsDisabled=DEFAULT_ACK_MODE):

    cmd = "02"
    Cluster = "0500"
    cluster_frame = 0b00010001
    sqn = get_and_inc_ZCL_SQN(self, nwkid)
    payload = "%02x" % cluster_frame + sqn + cmd + duration + current_zone_sensitivy_level
    raw_APS_request(self, nwkid, EPout, Cluster, "0104", payload, zigpyzqn=sqn, zigate_ep=EPin, groupaddrmode=groupaddrmode, ackIsDisabled=ackIsDisabled)
    return sqn


# Cluster 0501 IAS ACE ( 0x0111, 0x0112)


IAS_ACE_COMMANDS = {
    "Arm": 0x00,
    #'Bypass': 0x01,
    #'Emergency': 0x02,
    #'Fire': 0x03,
    #'Panic': 0x04,
    #'GetZoneID Map': 0x05,
    #'GetZoneInformation': 0x06,
    #'GetPanelStatus': 0x07,
    #'GetBypassedZoneList': 0x08,
    #'GetZoneStatus': 0x09
}


def zcl_raw_ias_ace_commands_arm(self, EPin, EPout, nwkid, arm_mode, arm_code, zone_id, groupaddrmode=False, ackIsDisabled=DEFAULT_ACK_MODE):

    cmd = IAS_ACE_COMMANDS["Arm"]
    Cluster = "0501"
    cluster_frame = 0b00010001
    sqn = get_and_inc_ZCL_SQN(self, nwkid)
    payload = "%02x" % cluster_frame + sqn + cmd + "%02x" % arm_mode + "%02x" % arm_code + "%02x" % zone_id
    raw_APS_request(self, nwkid, EPout, Cluster, "0104", payload, zigpyzqn=sqn, zigate_ep=EPin, groupaddrmode=groupaddrmode, ackIsDisabled=ackIsDisabled)
    return sqn


# Cluster 0502 IAS WD

IAS_WD_COMMANDS = {"StartWarning": "00", "Squawk": "01"}


def zcl_raw_ias_wd_command_start_warning(self, EPin, EPout, nwkid, warning_mode=0x00, strobe_mode=0x01, siren_level=0x01, warning_duration=0x0001, strobe_duty=0x00, strobe_level=0x00, groupaddrmode=False, ackIsDisabled=DEFAULT_ACK_MODE):
    self.log.logging("zclCommand", "Debug", "zcl_raw_ias_wd_command_start_warning %s %s %s %s %s %s %s" % (nwkid, warning_mode, strobe_mode, siren_level, warning_duration, strobe_duty, strobe_level))

    cmd = IAS_WD_COMMANDS["StartWarning"]
    Cluster = "0502"
    cluster_frame = 0b00010001
    sqn = get_and_inc_ZCL_SQN(self, nwkid)

    # Warnindg mode , Strobe, Sirene Level
    field1 = 0x00
    field1 = field1 & 0xF0 | (warning_mode << 4)
    field1 = field1 & 0xF7 | ((strobe_mode & 0x01) << 2)
    field1 = field1 & 0xFC | (siren_level & 0x03)

    payload = "%02x" % cluster_frame + sqn + cmd
    payload += "%02x" % field1 + "%04x" % struct.unpack(">H", struct.pack("H", warning_duration))[0] + "%02x" % (strobe_duty) + "%02x" % (strobe_level)
    raw_APS_request(self, nwkid, EPout, Cluster, "0104", payload, zigpyzqn=sqn, zigate_ep=EPin, groupaddrmode=groupaddrmode, ackIsDisabled=ackIsDisabled)
    return sqn


def zcl_raw_ias_wd_command_squawk(self, EPin, EPout, nwkid, squawk_mode, strobe, squawk_level, groupaddrmode=False, ackIsDisabled=DEFAULT_ACK_MODE):
    self.log.logging("zclCommand", "Debug", "zcl_raw_ias_wd_command_squawk %s %s %s %s" % (nwkid, squawk_mode, strobe, squawk_level))

    cmd = IAS_WD_COMMANDS["Squawk"]
    Cluster = "0502"
    cluster_frame = 0b00010001
    sqn = get_and_inc_ZCL_SQN(self, nwkid)

    field1 = 0x0000
    field1 = field1 & 0xF0 | (squawk_mode << 4)
    field1 = field1 & 0xF7 | ((strobe & 0x01) << 3)
    field1 = field1 & 0xFC | (squawk_level & 0x03)
    payload = "%02x" % cluster_frame + sqn + cmd + "%02x" % field1

    raw_APS_request(self, nwkid, EPout, Cluster, "0104", payload, zigpyzqn=sqn, zigate_ep=EPin, groupaddrmode=groupaddrmode, ackIsDisabled=ackIsDisabled)
    return sqn