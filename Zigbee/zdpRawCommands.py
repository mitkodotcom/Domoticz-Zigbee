#!/usr/bin/env python3
# coding: utf-8 -*-
#
# Author: pipiche38
#
"""
    Module: zdpRawCommands

    Description: ZDP commands via raw mode

"""
import struct
from Modules.zigateConsts import ZIGATE_EP
from Modules.sendZigateCommand import (raw_APS_request)
from Modules.tools import get_and_inc_ZDP_SQM

# ZDP Commands

def zdp_raw_NWK_address_request(self, router, ieee, u8RequestType , u8StartIndex):
    Cluster = "0000"
    payload = "%016x" %struct.unpack("Q", struct.pack(">Q", int(ieee, 16)))[0] + u8RequestType + u8StartIndex
    return raw_APS_request( self, router, "00", Cluster, "0000", payload, zigate_ep="00", groupaddrmode=False, ackIsDisabled=False, )  
    
def zdp_raw_IEEE_address_request(self, nwkid, u8RequestType , u8StartIndex):
    Cluster = "0001"
    payload = get_and_inc_ZDP_SQM(self, nwkid) + "%04x" % struct.unpack(">H", struct.pack("H", int(nwkid, 16)))[0] + u8RequestType + u8StartIndex
    return raw_APS_request( self, nwkid, "00", Cluster, "0000", payload, zigate_ep="00", groupaddrmode=False, ackIsDisabled=False, )   
    
    
def zdp_raw_node_descriptor_request(self, nwkid):
    self.log.logging( "zdpCommand", "Log","zdp_raw_node_descriptor_request %s" %(nwkid, ))
    Cluster = "0002"
    payload = get_and_inc_ZDP_SQM(self, nwkid) + "%04x" % struct.unpack(">H", struct.pack("H", int(nwkid, 16)))[0]
    return raw_APS_request( self, nwkid, "00", Cluster, "0000", payload, zigate_ep="00", groupaddrmode=False, ackIsDisabled=False, )   

def zdp_power_descriptor_request(self, nwkid):
    self.log.logging( "zdpCommand", "Log","zdp_power_descriptor_request %s" %(nwkid, ))
    Cluster = "0003"
    payload = get_and_inc_ZDP_SQM(self, nwkid) + "%04x" % struct.unpack(">H", struct.pack("H", int(nwkid, 16)))[0]
    return raw_APS_request( self, nwkid, "00", Cluster, "0000", payload, zigate_ep="00", groupaddrmode=False, ackIsDisabled=False, )   
    
def zdp_raw_simple_descriptor_request(self, nwkid, endpoint):
    self.log.logging( "zdpCommand", "Log","zdp_raw_simple_descriptor_request %s %s" %(nwkid, endpoint))
    Cluster = "0004" 
    payload = get_and_inc_ZDP_SQM(self, nwkid) + "%04x" % struct.unpack(">H", struct.pack("H", int(nwkid, 16)))[0] + endpoint
    return raw_APS_request( self, nwkid, "00", Cluster, "0000", payload, zigate_ep="00", groupaddrmode=False, ackIsDisabled=False, )   

def zdp_raw_active_endpoint_request(self, nwkid,):
    self.log.logging( "zdpCommand", "Log","zdp_raw_active_endpoint_request %s" %(nwkid, ))
    Cluster = "0005"
    payload = get_and_inc_ZDP_SQM(self, nwkid) + "%04x" % struct.unpack(">H", struct.pack("H", int(nwkid, 16)))[0]
    return raw_APS_request( self, nwkid, "00", Cluster, "0000", payload, zigate_ep="00", groupaddrmode=False, ackIsDisabled=False, )   
  
def zdp_raw_match_desc_req(self):
    self.log.logging( "zdpCommand", "Log","zdp_raw_match_desc_req %s" %("NOT IMPLEMENTED", ))
    cluster = "0006"


def zdp_raw_complex_descriptor_request(self, nwkid,):
    self.log.logging( "zdpCommand", "Log","zdp_raw_active_endpoint_request %s" %(nwkid, ))
    Cluster = "0010"
    payload = get_and_inc_ZDP_SQM(self, nwkid) + "%04x" % struct.unpack(">H", struct.pack("H", int(nwkid, 16)))[0]
    return raw_APS_request( self, nwkid, "00", Cluster, "0000", payload, zigate_ep="00", groupaddrmode=False, ackIsDisabled=False, )   

def zdp_raw_user_descriptor_request(self, nwkid,):
    self.log.logging( "zdpCommand", "Log","zdp_raw_active_endpoint_request %s" %(nwkid, ))
    Cluster = "0011"
    payload = get_and_inc_ZDP_SQM(self, nwkid) + "%04x" % struct.unpack(">H", struct.pack("H", int(nwkid, 16)))[0] 
    return raw_APS_request( self, nwkid, "00", Cluster, "0000", payload, zigate_ep=ZIGATE_EP, groupaddrmode=False, ackIsDisabled=False, )   

def zdp_raw_discovery_cache_req(self):
    self.log.logging( "zdpCommand", "Log","zdp_raw_discovery_cache_req %s" %("NOT IMPLEMENTED", ))
    cluster = "0012"
    







# Bindings primitive

def zdp_raw_binding_device(self, source , src_ep , cluster , addrmode , destination , dst_ep):
    self.log.logging( "zdpCommand", "Log","zdp_raw_binding_device %s %s %s %s %s %s" %(source , src_ep , cluster , addrmode , destination , dst_ep))
     
    if source in self.IEEE2NWK:
        nwkid = self.IEEE2NWK[ source ]
    else:
        self.log.logging( "zdpCommand", "Log","zdp_raw_unbinding_device %s not found in IEEE2NWK" %(source ))
        return
    Cluster = "0021"
    payload = get_and_inc_ZDP_SQM(self, nwkid) 
    payload += "%016x" %struct.unpack("Q", struct.pack(">Q", int(source, 16)))[0]
    payload += src_ep
    payload += "%04x" % struct.unpack(">H", struct.pack("H", int(cluster, 16)))[0]
    payload += "03" # Unicast
    payload += "%016x" %struct.unpack("Q", struct.pack(">Q", int(destination, 16)))[0]
    payload += dst_ep
    
    return raw_APS_request( self, nwkid, "00", Cluster, "0000", payload, zigate_ep="00", groupaddrmode=False, ackIsDisabled=False, )   

def zdp_raw_unbinding_device(self, source , src_ep , cluster , addrmode , destination , dst_ep):
    self.log.logging( "zdpCommand", "Log","zdp_raw_unbinding_device %s %s %s %s %s %s" %(source , src_ep , cluster , addrmode , destination , dst_ep))
     
    if source in self.IEEE2NWK:
        nwkid = self.IEEE2NWK[ source ]
    else:
        self.log.logging( "zdpCommand", "Log","zdp_raw_unbinding_device %s not found in IEEE2NWK" %(source ))
        return
    Cluster = "0022"
    payload = get_and_inc_ZDP_SQM(self, nwkid) 
    payload += "%016x" %struct.unpack("Q", struct.pack(">Q", int(source, 16)))[0]
    payload += src_ep
    payload += "%04x" % struct.unpack(">H", struct.pack("H", int(cluster, 16)))[0]
    payload += "03" # Unicast
    payload += "%016x" %struct.unpack("Q", struct.pack(">Q", int(destination, 16)))[0]
    payload += dst_ep
    
    return raw_APS_request( self, nwkid, "00", Cluster, "0000", payload, zigate_ep="00", groupaddrmode=False, ackIsDisabled=False, )   


# Network Management Client Services



def zdp_raw_nwk_lqi_request( self, nwkid, start_index):
    self.log.logging( "zdpCommand", "Log","zdp_raw_nwk_lqi_request %s" %(start_index, ))
    Cluster = "0031"
    payload = get_and_inc_ZDP_SQM(self, nwkid) + start_index
    return raw_APS_request( self, nwkid, "00", Cluster, "0000", payload, zigate_ep="00", highpriority=False, ackIsDisabled=False,) 
    
def zdp_management_routing_table_request(self, nwkid, payload):
    self.log.logging( "zdpCommand", "Log","zdp_management_routing_table_request %s" %(payload, ))
    Cluster = "0032"
    return raw_APS_request( self, nwkid, "00", Cluster, "0000", payload, zigate_ep="00", highpriority=False, ackIsDisabled=False,)

def zdp_management_binding_table_request(self, nwkid, payload):
    self.log.logging( "zdpCommand", "Log","zdp_management_binding_table_request %s" %(payload, ))
    Cluster = "0033"
    return raw_APS_request( self, nwkid, "00", Cluster, "0000", payload, zigate_ep="00", highpriority=False, ackIsDisabled=False,)

def zdp_raw_permit_joining_request(self, tgtnwkid , duration , significance):
    self.log.logging( "zdpCommand", "Log","zdp_raw_permit_joining_request %s %s %s" %(tgtnwkid , duration , significance, ))
    if self.zigbee_communitation == "zigpy":
        data = {'Duration': int(duration, 16), 'targetRouter': int(tgtnwkid, 16)}
        return self.ZigateComm.sendData( "PERMIT-TO-JOIN", data)
    
def zdp_raw_management_permit_joining_req(self, nwkid, duration, significance):
    self.log.logging( "zdpCommand", "Log","zdp_raw_management_permit_joining_req %s %s %s" %(nwkid, duration, significance, ))
    

def zdp_raw_leave_request(self, nwkid, ieee, rejoin="01", remove_children="00"):
    self.log.logging( "zdpCommand", "Log","zdp_raw_leave_request %s %s" %(nwkid, ieee))
    Cluster = "0034" 
    
    if rejoin == "00" and remove_children == "00":
        flag = "00"
    elif rejoin == "00" and remove_children == "01":
        flag = "01"
    elif rejoin == "01" and remove_children == "00":
        flag = "02"
    if rejoin == "01" and remove_children == "01":
        flag = '03'
    payload = get_and_inc_ZDP_SQM(self, nwkid) +  "%016x" %struct.unpack("Q", struct.pack(">Q", int(ieee, 16)))[0] + flag
    
    return raw_APS_request( self, nwkid, "00", Cluster, "0000", payload, zigate_ep="00", groupaddrmode=False, ackIsDisabled=False, )   


def zdp_raw_nwk_update_request(self, nwkid , scanchannel, scanduration, scancount="", nwkupdateid="", nwkmanageraddr=""):
    self.log.logging( "zdpCommand", "Log","zdp_raw_nwk_update_request %s %s %s %s %s %s" %(nwkid , scanchannel, scanduration, scancount, nwkupdateid, nwkmanageraddr ))
    Cluster = "0038"
    payload = get_and_inc_ZDP_SQM(self, nwkid) + scanchannel + scanduration + scancount + nwkupdateid +  nwkmanageraddr
    return raw_APS_request( self, nwkid, "00", Cluster, "0000", payload, zigate_ep="00", highpriority=False, ackIsDisabled=False,)