#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket

xbee_socket = socket(AF_XBEE, SOCK_DGRAM, XBS_PROT_TRANSPORT)
# Bind to endpoint 0x00 for 802.15.4
xbee_socket.bind( ("", 0x00, 0, 0 ) )
xbee_socket.settimeout(1.0)
root_curves = {}

#Block until a single frame is received, up to 255 byte or until timeout
while True:
            payload, src_addr = xbee_socket.recvfrom(255)
            payload = map( ord , payload )
            last_radio_rx_time = float(time.time())
            sequential_timeouts = 0

            address_string = src_addr[0][1:5]
            address = int( address_string , 16 )
            
            if  payload[0]  == IV_CURVE_MESSAGE_ID:
                print('iv frame address: %d' % address )
                if address in root_curves:
                    root_curves[ address ].add_frame( payload ) 
                else:
                    root_curves[ address ] = curve( address )
                    root_curves[ address ].add_frame( payload )
                    
            elif payload[0] == TRACER_STATE_MESSAGE_ID:
                print('status frame address: %d' % address )
                result = write_stat_to_file( address, payload)
                text_streams.append( result )
            else:
                print('bad frame')    
