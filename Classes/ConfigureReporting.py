#!/usr/bin/env python3
# coding: utf-8 -*-
#
# Author: zaraki673 & pipiche38
#
"""
    Module: ConfigureReporting.py

    Description: Configure Reporting of all connected object, based on their corresponding cluster

"""

from time import time

import Domoticz
from Modules.basicOutputs import ieee_addr_request
from Modules.bindings import bindDevice
from Modules.tools import (get_isqn_datastruct, get_list_isqn_attr_datastruct,
                           getClusterListforEP, is_ack_tobe_disabled,
                           is_attr_unvalid_datastruct, is_bind_ep, is_fake_ep,
                           is_time_to_perform_work, mainPoweredDevice,
                           reset_attr_datastruct, set_isqn_datastruct,
                           set_status_datastruct, set_timestamp_datastruct)
from Modules.zigateConsts import (MAX_LOAD_ZIGATE, ZIGATE_EP,
                                  CFG_RPT_ATTRIBUTESbyCLUSTERS)
from Zigbee.zclCommands import (zcl_configure_reporting_requestv2,
                                zcl_read_report_config_request)

from Classes.ZigateTransport.sqnMgmt import (TYPE_APP_ZCL,
                                             sqn_get_internal_sqn_from_app_sqn)

MAX_ATTR_PER_REQ = 3
CONFIGURE_REPORT_PERFORM_TIME = 21  # Reenforce will be done each xx hours


class ConfigureReporting:
    def __init__(
        self,
        zigbee_communitation,
        PluginConf,
        DeviceConf,
        ZigateComm,
        ListOfDevices,
        Devices,
        log,
        busy,
        FirmwareVersion,
        IEEE2NWK,
        ZigateIEEE,
    ):

        self.zigbee_communitation = zigbee_communitation
        self.pluginconf = PluginConf
        self.DeviceConf = DeviceConf
        self.ControllerLink = ZigateComm
        self.ListOfDevices = ListOfDevices
        self.Devices = Devices
        self.log = log
        self.busy = busy
        self.FirmwareVersion = FirmwareVersion

        # Needed for bind
        self.IEEE2NWK = IEEE2NWK
        self.ControllerIEEE = ZigateIEEE

        # Local
        self.target = []

    def logging(self, logType, message, nwkid=None, context=None):
        self.log.logging("ConfigureReporting", logType, message, nwkid, context)

    def processConfigureReporting(self, NWKID=None):
        """
        processConfigureReporting( self,  NWKID=None)
        Called by heartbeat to configure Reporting of all connected object, based on their corresponding cluster

        Synopsis:
        - for each Device
            if they support Cluster we want to configure Reporting

        """

        now = int(time())
        if NWKID is None:
            if self.busy or self.ControllerLink.loadTransmit() > MAX_LOAD_ZIGATE:
                self.logging(
                    "Debug",
                    "configureReporting - skip configureReporting for now ... system too busy (%s/%s) for %s" % (self.busy, self.ControllerLink.loadTransmit(), NWKID),
                    nwkid=NWKID,
                )
                return  # Will do at the next round
            if not self.target:
                self.target = list(self.ListOfDevices.keys())
        else:
            self.target.clear()
            self.target.append(NWKID)

        for key in self.target:
            # Let's check that we can do a Configure Reporting. Only during the pairing process (NWKID is provided) or we are on the Main Power
            if key == "0000":
                self.target.remove(key)
                continue

            if key not in self.ListOfDevices:
                self.target.remove(key)
                self.logging("Debug", "processConfigureReporting - Unknown key: %s" % key, nwkid=NWKID)
                continue

            if "Status" not in self.ListOfDevices[key]:
                self.target.remove(key)
                self.logging("Debug", "processConfigureReporting - no 'Status' flag for device %s !!!" % key, nwkid=NWKID)
                continue

            if self.ListOfDevices[key]["Status"] != "inDB":
                self.target.remove(key)
                continue

            if NWKID is None:
                if not mainPoweredDevice(self, key):
                    self.target.remove(key)
                    continue  # Not Main Powered!

                if "Health" in self.ListOfDevices[key] and self.ListOfDevices[key]["Health"] == "Not Reachable":
                    self.target.remove(key)
                    continue

                    # if self.ListOfDevices[key]['Model'] != {}:
                    #    if self.ListOfDevices[key]['Model'] == 'TI0001': # Livolo switch
                    #        continue

            cluster_list = CFG_RPT_ATTRIBUTESbyCLUSTERS
            if "Model" in self.ListOfDevices[key] and self.ListOfDevices[key]["Model"] != {} and self.ListOfDevices[key]["Model"] in self.DeviceConf and "ConfigureReporting" in self.DeviceConf[self.ListOfDevices[key]["Model"]]:
                spec_cfgrpt = self.DeviceConf[self.ListOfDevices[key]["Model"]]["ConfigureReporting"]
                cluster_list = spec_cfgrpt
                self.logging(
                    "Debug",
                    "------> CFG_RPT_ATTRIBUTESbyCLUSTERS updated: %s --> %s" % (key, cluster_list),
                    nwkid=key,
                )

            self.logging("Debug", "----> configurereporting - processing %s" % key, nwkid=key)

            manufacturer = "0000"
            manufacturer_spec = "00"
            direction = "00"

            for Ep in self.ListOfDevices[key]["Ep"]:
                if is_fake_ep( self, key, Ep):
                    self.logging("Debug", "------> Configurereporting - Fake Ep %s/%s skiping" % (key, Ep), nwkid=key)
                    continue
                if not is_bind_ep( self, key, Ep):
                    self.logging("Debug", "------> Configurereporting - Not Binding ep %s/%s skiping" % (key, Ep), nwkid=key)
                    continue
 
                self.logging("Debug", "------> Configurereporting - processing %s/%s" % (key, Ep), nwkid=key)
                clusterList = getClusterListforEP(self, key, Ep)
                self.logging(
                    "Debug",
                    "------> Configurereporting - processing %s/%s ClusterList: %s" % (key, Ep, clusterList),
                    nwkid=key,
                )
                for cluster in clusterList:
                    if cluster in ("Type", "ColorMode", "ClusterType"):
                        continue
                    if cluster not in cluster_list:
                        continue
                    if "Model" in self.ListOfDevices[key] and self.ListOfDevices[key]["Model"] != {}:
                        if self.ListOfDevices[key]["Model"] == "lumi.light.aqcn02" and cluster in (
                            "0402",
                            "0403",
                            "0405",
                            "0406",
                        ):
                            continue
                        if self.ListOfDevices[key]["Model"] == "lumi.remote.b686opcn01" and Ep != "01":
                            # We bind only on EP 01
                            self.logging(
                                "Debug",
                                "Do not Configure Reporting lumi.remote.b686opcn01 to Zigate Ep %s Cluster %s" % (Ep, cluster),
                                key,
                            )
                            continue

                    # Bad Hack for now. FOR PROFALUX
                    if self.ListOfDevices[key]["ProfileID"] == "0104" and self.ListOfDevices[key]["ZDeviceID"] == "0201":  # Remote
                        # Do not Configure Reports Remote Command
                        self.logging(
                            "Debug",
                            "----> Do not Configure Reports cluster %s for Profalux Remote command %s/%s" % (cluster, key, Ep),
                            key,
                        )
                        continue

                    self.logging(
                        "Debug2",
                        "--------> Configurereporting - processing %s/%s - %s" % (key, Ep, cluster),
                        nwkid=key,
                    )

                    # Configure Reporting must be done because:
                    # (1) 'ConfigureReporting' do not exist
                    # (2) 'ConfigureReporting' is empty
                    # (3) if reenforceConfigureReporting is enabled and it is time to do the work
                    if NWKID is None and "ConfigureReporting" in self.ListOfDevices[key] and len(self.ListOfDevices[key]["ConfigureReporting"]) != 0:
                        if self.pluginconf.pluginConf["reenforceConfigureReporting"]:
                            if not is_time_to_perform_work(
                                self,
                                "ConfigureReporting",
                                key,
                                Ep,
                                cluster,
                                now,
                                (CONFIGURE_REPORT_PERFORM_TIME * 3600),
                            ):
                                self.logging(
                                    "Debug",
                                    "--------> Not time to perform  %s/%s - %s" % (key, Ep, cluster),
                                    nwkid=key,
                                )
                                continue
                        else:
                            self.logging(
                                "Debug",
                                "-------> ['reenforceConfigureReporting']: %s then skip" % self.pluginconf.pluginConf["reenforceConfigureReporting"],
                            )
                            continue

                    if NWKID is None and (self.busy or self.ControllerLink.loadTransmit() > MAX_LOAD_ZIGATE):
                        self.logging(
                            "Debug",
                            "---> configureReporting - %s skip configureReporting for now ... system too busy (%s/%s) for %s" % (key, self.busy, self.ControllerLink.loadTransmit(), key),
                            nwkid=key,
                        )
                        return  # Will do at the next round

                    self.logging(
                        "Debug",
                        "---> configureReporting - requested for device: %s on Cluster: %s" % (key, cluster),
                        nwkid=key,
                    )

                    # If NWKID is not None, it means that we are asking a ConfigureReporting for a specific device
                    # Which happens on the case of New pairing, or a re-join
                    if NWKID is None and self.pluginconf.pluginConf["allowReBindingClusters"]:
                        ieee_addr_request(self, key)
                        # Correctif 22 Novembre. Delete only for the specific cluster and not the all Set
                        if "Bind" in self.ListOfDevices[key] and Ep in self.ListOfDevices[key]["Bind"] and cluster in self.ListOfDevices[key]["Bind"][Ep]:
                            del self.ListOfDevices[key]["Bind"][Ep][cluster]
                        if "IEEE" in self.ListOfDevices[key]:
                            self.logging(
                                "Debug",
                                "---> configureReporting - requested Bind for %s on Cluster: %s" % (key, cluster),
                                nwkid=key,
                            )
                            bindDevice(self, self.ListOfDevices[key]["IEEE"], Ep, cluster)
                        else:
                            Domoticz.Error("configureReporting - inconsitency on %s no IEEE found : %s " % (key, str(self.ListOfDevices[key])))

                    set_timestamp_datastruct(self, "ConfigureReporting", key, Ep, cluster, int(time()))

                    if "Attributes" not in cluster_list[cluster]:
                        continue

                    ListOfAttributesToConfigure = []
                    for attr in cluster_list[cluster]["Attributes"]:
                        # Check if the Attribute is listed in the Attributes List (provided by the Device
                        # In case Attributes List exists, we have give the list of reported attribute.
                        if cluster == "0300":
                            # We need to evaluate the Attribute on ZDevice basis
                            if self.ListOfDevices[key]["ZDeviceID"] == {}:
                                continue

                            ZDeviceID = self.ListOfDevices[key]["ZDeviceID"]
                            if "ZDeviceID" in cluster_list[cluster]["Attributes"][attr] and (ZDeviceID not in cluster_list[cluster]["Attributes"][attr]["ZDeviceID"] and len(cluster_list[cluster]["Attributes"][attr]["ZDeviceID"]) != 0):
                                self.logging(
                                    "Debug",
                                    "configureReporting - %s/%s skip Attribute %s for Cluster %s due to ZDeviceID %s" % (key, Ep, attr, cluster, ZDeviceID),
                                    nwkid=key,
                                )
                                continue

                        # Check against Attribute List only if the Model is not defined in the Certified Conf.
                        if (
                            ("Model" in self.ListOfDevices[key] and self.ListOfDevices[key]["Model"] != {} and self.ListOfDevices[key]["Model"] not in self.DeviceConf and "Attributes List" in self.ListOfDevices[key])
                            and "Ep" in self.ListOfDevices[key]["Attributes List"]
                            and Ep in self.ListOfDevices[key]["Attributes List"]["Ep"]
                            and cluster in self.ListOfDevices[key]["Attributes List"]["Ep"][Ep]
                            and attr not in self.ListOfDevices[key]["Attributes List"]["Ep"][Ep][cluster]
                        ):
                            self.logging(
                                "Debug",
                                "configureReporting: drop attribute %s" % attr,
                                nwkid=key,
                            )
                            continue

                        if self.FirmwareVersion and int(self.FirmwareVersion, 16) <= int("31c", 16):
                            if is_attr_unvalid_datastruct(self, "ConfigureReporting", key, Ep, cluster, "0000"):
                                continue
                            reset_attr_datastruct(self, "ConfigureReporting", key, Ep, cluster, "0000")

                        if self.FirmwareVersion and int(self.FirmwareVersion, 16) > int("31c", 16):
                            if is_attr_unvalid_datastruct(self, "ConfigureReporting", key, Ep, cluster, attr):
                                continue
                            reset_attr_datastruct(self, "ConfigureReporting", key, Ep, cluster, attr)

                        # Check if we have a Manufacturer Specific Cluster/Attribute. If that is the case, we need to send what we have ,
                        # and then pile what we have until we switch back to non manufacturer specific
                        manufacturer_code = manufacturer_specific_attribute(self, key, cluster, attr, cluster_list[cluster]["Attributes"][attr] )
                        if manufacturer_code:

                            # Send what we have
                            if ListOfAttributesToConfigure:
                                self.prepare_and_send_configure_reporting(
                                    key,
                                    Ep,
                                    cluster_list,
                                    cluster,
                                    direction,
                                    manufacturer_spec,
                                    manufacturer,
                                    ListOfAttributesToConfigure,
                                )

                            self.logging(
                                "Debug",
                                "    Configure Reporting: Manuf Specific Attribute %s" % attr,
                                nwkid=key,
                            )
                            # Process the Attribute
                            ListOfAttributesToConfigure = []
                            manufacturer_spec = "01"

                            ListOfAttributesToConfigure.append(attr)
                            self.prepare_and_send_configure_reporting(
                                key,
                                Ep,
                                cluster_list,
                                cluster,
                                direction,
                                manufacturer_spec,
                                manufacturer_code,
                                ListOfAttributesToConfigure,
                            )

                            # Look for the next attribute and do not assume it is Manuf Specif
                            ListOfAttributesToConfigure = []

                            manufacturer_spec = "00"
                            manufacturer = "0000"

                            continue  # Next Attribute

                        ListOfAttributesToConfigure.append(attr)
                        self.logging(
                            "Debug",
                            "    Configure Reporting %s/%s Cluster %s Adding attr: %s " % (key, Ep, cluster, attr),
                            nwkid=key,
                        )
                    # end of For attr

                    self.prepare_and_send_configure_reporting(
                        key,
                        Ep,
                        cluster_list,
                        cluster,
                        direction,
                        manufacturer_spec,
                        manufacturer,
                        ListOfAttributesToConfigure,
                    )

                    # End for Cluster
            # End for Ep
            self.target.remove(key)
            return  # Only one device at a time
        # End for key

        
        
        
    def prepare_and_send_configure_reporting(self, key, Ep, cluster_list, cluster, direction, manufacturer_spec, manufacturer, ListOfAttributesToConfigure):
        # Ready to send the Command in one shoot or in several.

        maxAttributesPerRequest = MAX_ATTR_PER_REQ
        if self.pluginconf.pluginConf["breakConfigureReporting"]:
            maxAttributesPerRequest = 1

        attribute_reporting_configuration = []
        for attr in ListOfAttributesToConfigure:
            attrType = cluster_list[cluster]["Attributes"][attr]["DataType"]
            minInter = cluster_list[cluster]["Attributes"][attr]["MinInterval"]
            maxInter = cluster_list[cluster]["Attributes"][attr]["MaxInterval"]
            timeOut = cluster_list[cluster]["Attributes"][attr]["TimeOut"]
            chgFlag = cluster_list[cluster]["Attributes"][attr]["Change"]

            if analog_value( int(attrType, 16) ):
                # Analog values: For attributes with 'analog' data type (see 2.6.2), the "rptChg" has the same data type as the attribute. The sign (if any) of the reportable change field is ignored.
                attribute_reporting_record = {
                    "Attribute": attr,
                    "DataType": attrType,
                    "minInter": minInter,
                    "maxInter": maxInter,
                    "rptChg": chgFlag,
                    "timeOut": timeOut,
                }
            elif discrete_value( int(attrType, 16) ):
                # Discrete value: For attributes of 'discrete' data type (see 2.6.2), "rptChg" field is omitted.
                attribute_reporting_record = {
                    "Attribute": attr,
                    "DataType": attrType,
                    "minInter": minInter,
                    "maxInter": maxInter,
                    "timeOut": timeOut,
                }
            elif composite_value( int(attrType, 16) ):
                # Composite value: assumed "rptChg" is omitted
                attribute_reporting_record = {
                    "Attribute": attr,
                    "DataType": attrType,
                    "minInter": minInter,
                    "maxInter": maxInter,
                    "timeOut": timeOut,
                }
            else:
                self.logging(
                    "Error",
                    "prepare_and_send_configure_reporting - Unexpected Data Type: Cluster: %s Attribut: %s DataType: %s" % (cluster, attr, attrType),
                )
                continue

            attribute_reporting_configuration.append(attribute_reporting_record)

            if len(attribute_reporting_configuration) == maxAttributesPerRequest:
                self.send_configure_reporting_attributes_set(
                    key,
                    ZIGATE_EP,
                    Ep,
                    cluster,
                    direction,
                    manufacturer_spec,
                    manufacturer,
                    attribute_reporting_configuration,
                )
                # Reset the Lenght to 0
                attribute_reporting_configuration = []

        # Send remaining records
        if attribute_reporting_configuration:
            self.send_configure_reporting_attributes_set(
                key,
                ZIGATE_EP,
                Ep,
                cluster,
                direction,
                manufacturer_spec,
                manufacturer,
                attribute_reporting_configuration,
            )

    def send_configure_reporting_attributes_set(
        self,
        key,
        ZIGATE_EP,
        Ep,
        cluster,
        direction,
        manufacturer_spec,
        manufacturer,
        attribute_reporting_configuration,
    ):
        self.logging(
            "Debug",
            "--> send_configure_reporting_attributes_set Reporting %s/%s on cluster %s Len: %s Attribute List: %s" % (key, Ep, cluster, len(attribute_reporting_configuration), str(attribute_reporting_configuration)),
            nwkid=key,
        )

        i_sqn = zcl_configure_reporting_requestv2(
            self,
            key,
            ZIGATE_EP,
            Ep,
            cluster,
            direction,
            manufacturer_spec,
            manufacturer,
            attribute_reporting_configuration,
            is_ack_tobe_disabled(self, key),
        )
        for x in attribute_reporting_configuration:
            set_isqn_datastruct(self, "ConfigureReporting", key, Ep, cluster, x["Attribute"], i_sqn)

    # Decode 0x8120
    def read_configure_reporting_response(self, MsgSQN, MsgSrcAddr, MsgSrcEp, MsgClusterId, MsgAttributeId, MsgStatus):
        if self.FirmwareVersion and int(self.FirmwareVersion, 16) >= int("31d", 16) and MsgAttributeId:
            set_status_datastruct(
                self,
                "ConfigureReporting",
                MsgSrcAddr,
                MsgSrcEp,
                MsgClusterId,
                MsgAttributeId,
                MsgStatus,
            )
            if MsgStatus != "00":
                self.logging(
                    "Debug",
                    "Configure Reporting response - ClusterID: %s/%s, MsgSrcAddr: %s, MsgSrcEp:%s , Status: %s" % (MsgClusterId, MsgAttributeId, MsgSrcAddr, MsgSrcEp, MsgStatus),
                    MsgSrcAddr,
                )
            return

        # We got a global status for all attributes requested in this command
        # We need to find the Attributes related to the i_sqn
        i_sqn = sqn_get_internal_sqn_from_app_sqn(self.ControllerLink, MsgSQN, TYPE_APP_ZCL)
        self.logging("Debug", "------- - i_sqn: %0s e_sqn: %s" % (i_sqn, MsgSQN))

        for matchAttributeId in list(get_list_isqn_attr_datastruct(self, "ConfigureReporting", MsgSrcAddr, MsgSrcEp, MsgClusterId)):
            if (
                get_isqn_datastruct(
                    self,
                    "ConfigureReporting",
                    MsgSrcAddr,
                    MsgSrcEp,
                    MsgClusterId,
                    matchAttributeId,
                )
                != i_sqn
            ):
                continue

            self.logging("Debug", "------- - Sqn matches for Attribute: %s" % matchAttributeId)
            set_status_datastruct(
                self,
                "ConfigureReporting",
                MsgSrcAddr,
                MsgSrcEp,
                MsgClusterId,
                matchAttributeId,
                MsgStatus,
            )
            if MsgStatus != "00":
                self.logging(
                    "Debug",
                    "Configure Reporting response - ClusterID: %s/%s, MsgSrcAddr: %s, MsgSrcEp:%s , Status: %s" % (MsgClusterId, matchAttributeId, MsgSrcAddr, MsgSrcEp, MsgStatus),
                    MsgSrcAddr,
                )

    def read_report_configure_request(self, nwkid, epout, cluster_id, attribute_list, manuf_specific="00", manuf_code="0000"):

        nb_attribute = "%02x" % len(attribute_list)
        str_attribute_list = "".join("%04x" % x for x in attribute_list)
        direction = "00"
        # datas = nwkid + ZIGATE_EP + epout + cluster_id + direction + nb_attribute + manuf_specific + manuf_code + str_attribute_list

        zcl_read_report_config_request(
            self,
            nwkid,
            ZIGATE_EP,
            epout,
            cluster_id,
            direction,
            manuf_specific,
            manuf_code,
            nb_attribute,
            str_attribute_list,
            is_ack_tobe_disabled(self, nwkid),
        )

    # decode 0x8122
    def read_report_configure_response(self, MsgData, MsgLQI):  # Read Configure Report response
        MsgSQN = MsgData[0:2]
        MsgNwkId = MsgData[2:6]
        MsgEp = MsgData[6:8]
        MsgClusterId = MsgData[8:12]
        MsgStatus = MsgData[12:14]

        if MsgStatus != "00":

            return

        MsgAttributeDataType = MsgData[14:16]
        MsgAttribute = MsgData[16:20]
        MsgMaximumReportingInterval = MsgData[20:24]
        MsgMinimumReportingInterval = MsgData[24:28]

        self.logging(
            "Log",
            "Read Configure Reporting response - NwkId: %s Ep: %s Cluster: %s Attribute: %s DataType: %s Max: %s Min: %s"
            % (
                MsgNwkId,
                MsgEp,
                MsgClusterId,
                MsgAttribute,
                MsgAttributeDataType,
                MsgMaximumReportingInterval,
                MsgMinimumReportingInterval,
            ),
            MsgNwkId,
        )

def manufacturer_specific_attribute(self, key, cluster, attr, cfg_attribute):
    
    # Return False if the attribute is not a manuf specific, otherwise return the Manufacturer code
    if "ManufSpecific" in cfg_attribute:
        self.logging(
            "Log",
            "manufacturer_specific_attribute - NwkId: %s found attribute: %s Manuf Specific, return ManufCode: %s"
            % (
                key,
                attr,
                cfg_attribute[ "ManufSpecific"]
            ))
        return cfg_attribute[ "ManufSpecific"]
    
    if attr  in ( "4000", "4012",  ) and cluster == "0201" and "Model" in self.ListOfDevices[key] and self.ListOfDevices[key]["Model"] in ("eT093WRO", "eTRV0100"):
        return "1246"
    
    if attr  in ( "fd00", ) and cluster == "0201" and "Model" in self.ListOfDevices[key] and self.ListOfDevices[key]["Model"] in ("AC221", "AC211"):
        return "113c"
    
    if cluster == "fc21" and "Manufacturer" in self.ListOfDevices[key] and self.ListOfDevices[key]["Manufacturer"] == "1110":
        return "1110"
    
    if attr in ( "0030", "0031", ) and cluster == "0406" and "Manufacturer" in self.ListOfDevices[key] and self.ListOfDevices[key]["Manufacturer"] == "100b":
        return "100b"

def discrete_value(data_type):
    return data_type in (
        0x08,
        0x09,
        0x0A,
        0x0B,
        0x0C,
        0x0D,
        0x0E,
        0x0F,
        0x10,
        0x18,
        0x19,
        0x1A,
        0x1B,
        0x1C,
        0x1D,
        0x1E,
        0x1F,
        0x30,
        0x31,
        0xE8,
        0xE9,
        0xEA,
        0xF0,
        0xF1,
    )

def analog_value(data_type):
    return data_type in (
        0x20,
        0x21,
        0x22,
        0x23,
        0x24,
        0x25,
        0x26,
        0x27,
        0x28,
        0x29,
        0x2A,
        0x2B,
        0x2C,
        0x2D,
        0x2E,
        0x2F,
        0x38,
        0x39,
        0x3A,
        0xE0,
        0xE1,
        0xE2,
    )
    
def composite_value( data_type ):
    return data_type in (
        0x41,
        0x42,
        0x43,
        0x44,
        0x48,
        0x4c,
        0x50,
        0x51,
    )
