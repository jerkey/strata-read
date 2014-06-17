
#####################################################################
# This is the main project module
# Created on: 27 March 2013
# Author: kellen
# Company: Stratasense --> all rights reserved
# Description:
#####################################################################


from socket import * 
#from array import *
import array
import time
import struct
import threading
import sys
#import digicli
from ftplib import FTP
import cStringIO
import os
import termios
from xbee import XBee
import serial


module_names = {}


#enter in modules names per address here
module_names[ 0 ] = "module a"
module_names[ 1 ] = "module b"
module_names[ 2 ] = "module c"
module_names[ 3 ] = "module d"
module_names[ 4 ] = "module e"
module_names[ 5 ] = "module f"
module_names[ 6 ] = "module g"
module_names[ 7 ] = "module h"





total = len(sys.argv)
cmdargs = str(sys.argv)
print ("The total numbers of args passed to the script: %d " % total)
print ("Args list: %s " % cmdargs)
print ("Script name: %s" % str(sys.argv[0]))

UseFlash = 0
UseFTP = 0
UseWeather = 0
Broadcast_Summary = 0

VERSION = "1.04"

Run = 1

Print_Out = 0

BROADCAST_UDP_PORT = 9999
BROADCAST_IP = ''

ftpServer = "remanza.com"
ftpUser = "u39644038-loop"
ftpPwd = "bad"
ftpDir = ""
ivDir =""
statDir  = ""

for i in range(total):
    if 'use_flash' == str(sys.argv[i]):
        UseFlash = 1
    if  'use_ftp' ==  str(sys.argv[i]):
        UseFTP = 1 
    if 'debug' == str( sys.argv[i]):
        Print_Out = 1    
    if '-ftp' == str( sys.argv[i]):
        UseFTP = 1
        ftpServer = str( sys.argv[ i + 1 ])
        print('using ftp server %s'%ftpServer)
    if '-user' == str( sys.argv[i]):
        ftpUser = str( sys.argv[i + 1 ])
        print('using ftp user %s'%ftpUser)
    if '-pass' == str( sys.argv[i]):
        ftpPwd = str( sys.argv[i + 1 ]) 
        print( 'password set' )
    if '-iv' == str( sys.argv[ i ]):
        ivDir = str( sys.argv[ i + 1 ]) 
        print(' iv dir %s' % ivDir )
    if '-stat' == str( sys.argv[ i ]):
        statDir = str( sys.argv[ i + 1 ]) 
        print(' status dir %s' % statDir )
    if '-weather' == str( sys.argv[ i ] ):
        UseWeather = 1
    if '-broadcast' == str( sys.argv[ i ]):
        BROADCAST_IP = str( sys.argv[ i + 1 ])
        Broadcast_Summary = 1
        print( "broadcasting pmax data to %s"% BROADCAST_IP )
        
        
if UseFTP == 1:
    print( 'using ftp' )
else:
    print('NOT using ftp')     

    
if UseFlash == 1:
    print('writing to flash drive')
else:
    print('NOT writing to flash drive')
               





#Incoming data
MSG_TYPE_TEMPLATE = '<B'
IV_CURVE_MESSAGE_ID = 0x12
TRACER_STATE_MESSAGE_ID = 0x33

HARDWARE_VERSION = 165
sweep_time_scaler_per_point = 2
TOTAL_POINTS = 4
DAC_STEP = 1
info_byte = 128
           # loc += 1
vbat = 33 #BitConverter.ToUInt16(raw_data, loc) * 3.3f / 1023f
                                    #loc += 2
board_temp = 25 #100f * (BitConverter.ToUInt16(raw_data, loc) * 3.3f / 1023f - .5f)
                                    #loc += 2 //(get_voltage(raw_data, 5) - 0.5f) * 100f
accel_x = 1 #BitConverter.ToInt16(raw_data, loc)
                                    #loc += 2
accel_y = 2 #BitConverter.ToInt16(raw_data, loc)
                                    #loc += 2
accel_z = 3 #BitConverter.ToInt16(raw_data, loc)
                                    #loc += 2
v_thresh = 2000 #BitConverter.ToUInt16(raw_data, loc)
                                    #loc += 2
v_gs_end = 1000 #BitConverter.ToUInt16(raw_data, loc)
                                    #loc += 2
sweep_time_ms = 270 #BitConverter.ToUInt16(raw_data, loc)
                                    #loc += 2
energy_dissipation = 1000 #BitConverter.ToUInt32(raw_data, loc)
                                    #loc += 4

#frame zero with 4 iv points
firstframe = '<BBBBBHBBHHHHHHHHLHHHHHHHH'
#other frame with 10 points
otherframes = '<BHBBHHHHHHHHHHHHHHHHHHHH'
#INCOMING_IV_CURVE_HEADER_LENGTH = struct.calcsize( INCOMING_IV_CURVE_HEADER_TEMPLATE )

zero = struct.pack( firstframe , IV_CURVE_MESSAGE_ID , 0 , TOTAL_POINTS , HARDWARE_VERSION ,sweep_time_scaler_per_point ,  TOTAL_POINTS , DAC_STEP,
                    info_byte , vbat , board_temp, accel_x , accel_y,
                   accel_z , v_thresh , v_gs_end , sweep_time_ms , energy_dissipation ,  0,0,1,1,2,2,3,3)
#two = struct.pack( otherframes ,  IV_CURVE_MESSAGE_ID , 1000 , 1 , 10  , 4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13 )

zero = map( ord , zero )
#two = map( ord, two )

text_streams = []

root_curves = {}

weather_data = 'no valid weather data\r\n'
hmp155_string = "no hmp155 data\r\n"

py_poa = -1
py_hor = -1

py_1 = -1
py_1_temp = -1
py_1_std = -1

        
py_2 = -1
py_2_temp = -1
py_2_std = -1
      
battery_voltage = -1
        



def get_module_name( address ):
      if address in module_names:
            return module_names[ address ]
      else:
            return "undefined"





rx_max_seconds_dead_time = int(600)

def set_multipliers( sense_r , v_gain ):
      user_adjust_scaler = 1.0
      vref = 2.5550   #user_adjust_scaler * 2.5 * 1.022
      dI = (vref / (3.0 * 32768.0 * sense_r))
      dV = (vref * v_gain / (3.0 * 32768.0))
      
      return ( dV, dI )


def get_short(raw_data , pos ):
    #print( '%d' % pos )
   # print( raw_data )
   # val = struct.unpack_from('<h' , raw_data , pos )
    val = raw_data[pos] + ( raw_data[pos + 1] << 8 )
    return val

def get_short_iv(raw_data , pos ):
    #print( '%d' % pos )
   # print( raw_data )
    #line = raw_data[pos:pos+2]
   # line = line.encode('hex')
   # the_two_byte_hex_string = "%02x%02x"%(raw_data[pos] , raw_data[pos + 1 ])
    #print(the_two_byte_hex_string)
    #val = int(line.encode('hex'),16)
   # val = struct.unpack('<h' , the_two_byte_hex_string )
    
    val =  raw_data[pos] + ( raw_data[pos + 1] << 8 )
    
    if val >= 32768:
        val = val - 65536
    return val


def get_multipliers( hardware_version ):
    if hardware_version == 255:
          dV, dI = set_multipliers( 0.2, 101.0 )
    elif hardware_version == 238:
          dV, dI = set_multipliers( 0.05, 101.0 )
    elif hardware_version == 139:
          dV, dI = set_multipliers( 0.02, 1001.0 )
    elif hardware_version == 175:
          dV, dI = set_multipliers( 0.02, 201.0 )            
    elif hardware_version == 174:
          dV, dI = set_multipliers( 0.02, 301.0 )
    elif hardware_version == 165:
          dV, dI = set_multipliers( 0.02, 301.0 )  # // changed from 201.0
    elif hardware_version == 145:
          dV, dI = set_multipliers( 0.02, 201.0 )   
    elif hardware_version == 143:  #            //pv evo 4/22
      dV, dI = set_multipliers( 0.02, 484.87096 )  
    elif hardware_version == 142:  #            //pv evo 4/22
      dV, dI = set_multipliers( 0.02, 250.250 )   
    elif hardware_version == 135:  #            //for sun sync
      dV, dI = set_multipliers( 0.02, 201.0 )
    else:
        print('could not find lookup val for hardware')
        dV, dI = set_multipliers( 0.02, 1001.0 )  
    return ( dV, dI )


class curve:
      def cleanUp( self ):
            print('deleting dictionary entry: %d id: %d' % ( self.tracer_address , self.id ))
            #root_curves[ self.tracer_address ] = curve( self.tracer_address )
            key = ( self.id << 8 ) + self.tracer_address
            del root_curves[ key ]

            
      def __init__( self , tracer_address ):
            global Print_Out
            self.tracer_address = tracer_address
            self.module_name = get_module_name( tracer_address )
            self.current = []
            self.voltage = []
            self.hardware_version = 0
            self.curve_complete = 0
            self.points_added = 0
            self.clean_it = threading.Timer( 2.5 , self.cleanUp )
  #          self.sweep_time = 0
            self.dI = -1
            self.dV = -1
            self.last_frame_added = -1
            self.filename = "none"
            self.total_points = 0
            self.id = -1
            self.last_peak = -1
            self.pp_index = 0
            self.max_power = -1
            self.adc_l = -1
            self.adc_h = -1
            self.sweep_error = 0
            self.reverse_point = 0
            self.v_gs_end_2 = 0
            self.reverse_ms = 0
            self.hmp155 = "no hmp155 data" 
            self.py_poa = -1
            self.py_hor = -1
            self.battery_voltage = -1
            
    
                  
            
      def add_frame ( self , raw_data ):
            #frame type, then 2 id bytes
            loc = 1
            self.id = raw_data[ loc ] +   ( raw_data[ loc + 1 ]  << 8 )
            loc = 3
           
            
            
            frame_number =  raw_data[ loc ] 
            loc = loc + 1
            
            print('add:%d  id:%d  frame:%d' % (self.tracer_address, self.id , frame_number ))
            
            if frame_number == self.last_frame_added:
                  print('duplicate frame\r\n')
                  return
            if frame_number != self.last_frame_added + 1:
                  print('skipped a frame\r\n')
                  

            self.last_frame_added = frame_number        
            points_in_frame =  raw_data[ loc ] 
            loc = loc + 1

            if frame_number == 0:
                  loc = self.frame_zero( raw_data , loc )
                  if points_in_frame == 0:
                      seconds = str( int(self.sweep_timestamp_digi) )
                      self.filename = '%s_%d_%s.csv' % ( seconds , self.tracer_address , self.module_name   )
                      self.clean_it.cancel() 
                      text_streams.append( self.upload_error_file( "no points in curve") )
                      self.cleanUp()
                      return
                      
                  if self.sweep_error == 2:
                      seconds = str( int(self.sweep_timestamp_digi) )
                      self.filename = '%s_%d_%s.csv' % ( seconds , self.tracer_address , self.module_name   )
                      self.clean_it.cancel() 
                      text_streams.append( self.upload_error_file( "no points in curve") )
                      self.cleanUp()
                      return
            
            self.add_points(  raw_data , loc , points_in_frame )
            self.points_added = self.points_added + points_in_frame
            if Print_Out == 1:
                print( 'points in frame %d'%points_in_frame)
            
            if self.points_added == self.total_points:
                  
                  self.curve_complete = 1
                  self.weather_data_string = weather_data
                  self.hmp155 = hmp155_string 
                  self.py_poa = py_2
                  self.py_hor = py_1
                  self.battery_voltage = battery_voltage
                  seconds = str( int(self.sweep_timestamp_digi) )
                  self.filename = '%s_%d_%s.csv' % ( seconds , self.tracer_address , self.module_name   )
                  print('curve id:%d complete:name: %s' % ( self.id, self.filename ) )
                  #consider locking text_streams here
                  text_streams.append( self.serialize_to_text() )
                  #self.clean_it.cancel() 
                  #root_curves[ self.tracer_address ] = curve( self.tracer_address )
                  #wait for timer to clean things up
                  

                  
      def add_points( self , raw_data , loc , points_in_frame ):
            
            while points_in_frame > 0:
                  #v = raw_data[ loc ] +  ( raw_data[ loc + 1 ]  << 8 )
                  v = get_short_iv( raw_data , loc )
                  loc = loc + 2
                  
                 # c = raw_data[ loc ] + ( raw_data[ loc + 1 ] << 8 )
                  c = get_short_iv( raw_data , loc )
                  loc = loc + 2
                  
                  
                  self.current.append( c )
                  self.voltage.append( v )
                  this_power_int = c*v
                  
                  if this_power_int > self.last_peak:
                      self.mppt_index = self.pp_index
                      self.last_peak = this_power_int
                  
                  points_in_frame = points_in_frame - 1
                  self.pp_index = self.pp_index + 1
                  


      def frame_zero( self , raw_data , loc ):
            global Print_Out
            self.sweep_timestamp_digi = float( time.time() )
            self.clean_it.start() 

            self.hardware_version = raw_data[ loc ]
            loc = loc + 1
            
            self.dV, self.dI = get_multipliers( self.hardware_version )
            
                  
            self.sweep_time_scaler_per_point = raw_data[ loc ]
            loc = loc + 1
            #struct.unpack('<H', raw_data[loc : loc + 2])[0]
            self.total_points = raw_data[ loc ] + ( raw_data[ loc + 1 ] << 8 )
            if Print_Out == 1:
                print('total points: %d' % self.total_points )
            #self.total_points = struct.unpack('<H', raw_data[loc : loc + 2])[0]
            #print( 'total points: %d'%self.total_points )
            loc = loc + 2

            self.step = raw_data[ loc ]
            loc = loc + 1

            self.info_byte = raw_data[ loc ]
            loc = loc + 1



            self.isCharging = 0
            if self.info_byte & 0x80 == 0x80:
                self.isCharging = 1


            self.vbat = raw_data[ loc ] + ( raw_data[ loc + 1 ] << 8 )
            self.vbat = 0.00322*self.vbat
            loc = loc + 2

            self.board_temp = 100.0*( (raw_data[ loc ] + ( raw_data[ loc + 1 ] << 8 )) * 0.00322580 - 0.5 )
            loc = loc + 2 

            self.accel_x = raw_data[ loc ] + ( raw_data[ loc + 1 ] << 8 )
            loc = loc + 2

            self.accel_y = raw_data[ loc ] + ( raw_data[ loc + 1 ] << 8 )
            loc = loc + 2

            self.accel_z = raw_data[ loc ] + ( raw_data[ loc + 1 ] << 8 )
            loc = loc + 2

            self.v_thresh = raw_data[ loc ] + ( raw_data[ loc + 1 ] << 8 )
            loc = loc + 2

            self.v_gs_end = raw_data[ loc ] + ( raw_data[ loc + 1 ] << 8 )
            loc = loc + 2
            

            self.sweep_time_ms = raw_data[ loc ] + ( raw_data[ loc + 1 ] << 8 )
            loc = loc + 2

            self.energy_dissipation = raw_data[ loc ] + ( raw_data[ loc + 1 ] << 8 ) + ( raw_data[ loc + 2 ] << 16 ) + ( raw_data[ loc + 3 ] << 24 )
            self.energy_dissipation = (256.0*self.dI) * (256.0*self.dV) * self.energy_dissipation*0.001
            loc = loc + 4

            self.sweep_direction = "Voc_TO_Isc"
            if self.info_byte & 0x01 == 0x01:
                    self.sweep_direction = "Voc_TO_Isc"

                    
                    
            return loc            
    
      def print_info( self ):
            print( "tracer address:,%d " % self.tracer_address )
            print( "module name:,%s  " % self.module_name )
            print( "sweep id:,%d  " % self.id )
            print( "epoch_time:,%07d  " % self.sweep_timestamp_digi )
            print( "\r\n")
            print( "params:  ")
            print( "iv points:,%d  " % self.total_points )
           
            print( "mppt power:,%4.3f  " % ( self.max_power ) )
            print( "mppt index:,%d  " % ( self.mppt_index ) )
            print( "mppt current:,%4.3f" % (self.dI*self.current[ self.mppt_index ]) )
            print( "mppt voltage:,%4.3f\r\n" % (self.dV*self.voltage[ self.mppt_index ]) )
            print( "weather station:,%s\r\n" % self.weather_data_string )
            print( "sweep time (ms):,%04d  " % self.sweep_time_ms )
         #   print( "trace dir:,%s\r\n" % self.sweep_direction )
         #   print( "acc_x:,%04d\r\n" % self.accel_x )
         #   print( "acc_y:,%04d\r\n" % self.accel_y )
         #   print( "acc_z:,%04d\r\n" % self.accel_z )
            print( "thermal energy (J):, %4.1f \r\n" %self.energy_dissipation)
            print( "\r\n")
            print( "debug info:\r\n")
            print( "vgs1:,%04d  " % self.v_thresh )
            print( "vgs2:,%04d  " % self.v_gs_end )
            print( "step:,%04d  " % self.step )
            print( "hardware version:,%d  " % self.hardware_version )
            print( "delay val:,%d\r\n" % self.sweep_time_scaler_per_point )
            print( "board temp:,%4.3f  " % self.board_temp )
            print( "vbat:,%4.3f  " % self.vbat )
            print( "charging:,%d  " % self.isCharging )
            print( "sweep error:,%d  " % self.sweep_error )


      def upload_error_file(self, error_string ):
            global ivDir
            string_buffer = cStringIO.StringIO()
            string_buffer.write( "Stratasense iv version:,%s\r\n" , VERSION )
            string_buffer.write( "tracer address:,%d\r\n" % self.tracer_address )
            string_buffer.write( "module name:,%s\r\n" % self.module_name )
            string_buffer.write( "sweep id:,%d\r\n" % self.id )
            string_buffer.write( "epoch_time:,%07d\r\n" % self.sweep_timestamp_digi )
            string_buffer.write( "\r\n")
            string_buffer.write( "error:%s\r\n"%error_string )
            string_buffer.write( "sweep error:,%d\r\n" % self.sweep_error )
            
            string_buffer.seek( 0 )
            
            return( self.filename , string_buffer , ivDir , 0 )

      def serialize_to_text( self ):
            global Print_Out
            global VERSION
            global ivDir
            string_buffer = cStringIO.StringIO()
            string_buffer.write( "Stratasense iv version:,%s\r\n" % VERSION )
            string_buffer.write( "address:,%d\r\n" % self.tracer_address )
            string_buffer.write( "module:,%s\r\n" % self.module_name )
            string_buffer.write( "id:,%d\r\n" % self.id )
            string_buffer.write( "seconds(epoch):,%07d\r\n" % self.sweep_timestamp_digi )
            string_buffer.write( "\r\n")
            
            string_buffer.write( "params:\r\n")
            string_buffer.write( "total points:,%d\r\n" % self.total_points )
            self.max_power  = ((self.dV*self.dI)*self.voltage[ self.mppt_index ]*self.current[ self.mppt_index ]) 
            pp = "mppt power:,%4.3f\r\n" % ( self.max_power )
            i_max = "mppt current:,%4.3f\r\n" % (self.dI*self.current[ self.mppt_index ])
            v_max = "mppt voltage:,%4.3f\r\n" % (self.dV*self.voltage[ self.mppt_index ])
            string_buffer.write( pp )
            string_buffer.write( "mppt index:,%d\r\n" % ( self.mppt_index ) )
            string_buffer.write( i_max  )
            string_buffer.write( v_max )
            
            if Broadcast_Summary == 1:
                broad = socket( AF_INET , SOCK_DGRAM ) # UDP
                #broad.settimeout( 1.2 )
                #broad.bind(('', HUMIDITY_UDP_PORT ))
                try:
                    broad.sendto( "address:,%d,module name:,%s,%s,%s,%s\r\n" %( self.tracer_address , self.module_name , pp, i_max, v_max ) , ( BROADCAST_IP , BROADCAST_UDP_PORT ) )
                    broad.close()
                except e:
                    print('failed to send broadcast summary')
                    print(e)
                
            string_buffer.write( "weather station:,%s" % self.weather_data_string )
            string_buffer.write( "hmp155:,%s" % self.hmp155 )
            string_buffer.write( "py poa (W/m*m):,%d\r\n" % self.py_poa )
            string_buffer.write( "py hor (W/m*m):,%d\r\n" % self.py_hor )
            string_buffer.write( "battery (V):,%4.3f\r\n" %  self.battery_voltage )
            string_buffer.write( "sweep time (ms):,%04d\r\n" % self.sweep_time_ms )
            string_buffer.write( "trace dir:,%s\r\n" % self.sweep_direction )
            string_buffer.write( "acc_x:,%04d\r\n" % self.accel_x )
            string_buffer.write( "acc_y:,%04d\r\n" % self.accel_y )
            string_buffer.write( "acc_z:,%04d\r\n" % self.accel_z )
            string_buffer.write( "Thermal ( J ):, %4.1f\r\n" % self.energy_dissipation)
            string_buffer.write( "\r\n")
            string_buffer.write( "debug:\r\n")
            string_buffer.write( "v1:,%04d\r\n" % self.v_thresh )
            string_buffer.write( "v2:,%04d\r\n" % self.v_gs_end )
            string_buffer.write( "step:,%04d\r\n" % self.step )
            string_buffer.write( "hardware ver:,%d\r\n" % self.hardware_version )
            string_buffer.write( "delay:,%d\r\n" % self.sweep_time_scaler_per_point )
            string_buffer.write( "board temp(C):,%4.3f\r\n" % self.board_temp )
            string_buffer.write( "vbat:,%4.3f\r\n" % self.vbat )
            string_buffer.write( "charging:,%d\r\n" % self.isCharging )
            string_buffer.write( "adc_l:,%d\r\n" % self.adc_l )
            string_buffer.write( "adc_l:,%d\r\n" % self.adc_h )
            string_buffer.write( "def end:,%d\r\n" % self.sweep_error )
            string_buffer.write( "reverse point:,%d\r\n" % self.reverse_point )
            string_buffer.write( "v3:,%d\r\n" % self.v_gs_end_2 )
            string_buffer.write( "reverse ms:,%d\r\n" % self.reverse_ms )
            string_buffer.write( "\r\n")     
            string_buffer.write( "curve data: (Volts),(Amps)\r\n" )
            for i in range( self.total_points ):
                  string_buffer.write( "%4.2f,%4.3f\r\n" % ( (self.dV*self.voltage[ i ])  ,  (self.dI*self.current[ i ]) ))
            
            
            string_buffer.seek( 0 )
            if Print_Out == 1:
                self.print_info()
            return( self.filename , string_buffer , ivDir , 0 )
        
        
        
            
class wait_for_input( threading.Thread ):           
     def run(self): 
         global Run
         global Print_Out
         while Run == 1:
            try:
                line = sys.stdin.readline()
                #print(line)
                if line == "0\n":
                    Print_Out = 0
                    print('disabling debug output')
                elif line == "1\n":   
                    Print_Out = 1
                    print('setting debug output')
                else:    
                    Run = 0
            except KeyboardInterrupt:
                Run = 0       
      


              

                        

def get_adc( raw_data , pos ):
    counts = raw_data[ pos ] + ( raw_data[ pos + 1 ] << 8)
    return counts


    
def get_voltage( raw_data , pos ):
    v = ( 3.3 / 1024.0 ) * ( get_adc( raw_data , pos ) )    
    return v


def write_stat_to_file( address , raw_data ):
    global VERSION
    global statDir
    pos = 3
    
    buf = cStringIO.StringIO()
    
    seconds = int( time.time() )
    filename = 'stat_%d_%d.csv' % ( seconds , address   )
    print(filename)
    hardware_version = raw_data[1]
    ibat = ( get_voltage( raw_data, 2) - 2.05) / (0.05*50.0)
    vbat = get_voltage(raw_data, 4)
    board_temp = (get_voltage(raw_data, 6) - 0.5) * 100.0
    
    
    #100.0*( (raw_data[ loc ] + ( raw_data[ loc + 1 ] << 8 )) * 0.00322580 - 0.5 )
    vof = get_adc( raw_data , 8 )
    cof = get_adc( raw_data , 10 )

    total_sweeps = get_adc(raw_data, 12)
    tx_fails = get_adc(raw_data, 14)
    is_charging = raw_data[16]
    dip_switch_state = raw_data[17]
    
    dV, dI = get_multipliers( hardware_version )

    
    panel_v = get_short_iv(raw_data, 18) * dV
    panel_c = get_short_iv(raw_data, 20) * dI
    
    print( 'stat msg @address: %d , vbat:%3.2f , V: %4.2f, C: %4.3f' % ( address , vbat , panel_v , panel_c))
    
    adc_config_l = raw_data[22]
    adc_config_h = raw_data[23]
    accel_x = get_adc( raw_data , 24 )
    accel_y = get_adc( raw_data , 26 )
    accel_z = get_adc( raw_data , 28 )
    
    dip_4 = raw_data[30]
    dip_4 = raw_data[31]
    

    buf.write( "Stratasense ver.:,%s\r\n" % VERSION )
    buf.write('add:, %d\r\n' % address )
    buf.write('secs:,%d\r\n' % seconds )
    buf.write('total sweeps:,%d\r\n' % total_sweeps )
    buf.write('tx fails:,%d\r\n' % tx_fails )
    buf.write('dip switch state:,%d\r\n' % is_charging )
    buf.write('is charging:,%d\r\n' % is_charging )
    buf.write('cof:,%d\r\n' % cof )
    buf.write('vof:,%d\r\n' % vof )
    buf.write('ibat:,%f\r\n' % ibat )
    buf.write('vbat:,%f\r\n' % vbat )
    buf.write('board temp:,%f\r\n' % board_temp )
    buf.write('Panel V:,%4.2f\r\n' % panel_v )
    buf.write('Panel I:,%4.3f\r\n' % panel_c )
    buf.write('adc low:,%d\r\n' % adc_config_l )
    buf.write('adc high:,%d\r\n' % adc_config_h )
    
    #the below code will throw for panama
#    if hardware_version < 143 || hardware_version != 135:
#        try:
#            buf.write('dac:,%d\r\n' % dac )
#            buf.write('switch and ps:,%d\r\n' % Power_and_Switch )
#            buf.write('max thermal:,%4.3f\r\n' % max_joules )
#        except:    
#            do_nothing = 1
    do_nothing = 1
    buf.seek( 0 )
    return ( filename, buf , statDir , 0)
    
SendPos = 0


halt_on_keyboard = wait_for_input()
halt_on_keyboard.start()



sequential_timeouts = 0

current_mask = -1

last_radio_rx_time = int(time.time())



current_error = 0

last_radio_rx_time = 0


ser = serial.Serial('/dev/tty.usbserial-FTE4XS76', 115200)

xbee = XBee(ser)



print('booted')
print( 'digi time %s' % time.time() )


poof = 0

loop_counts = 0 
while Run == 1:        

            loop_counts = loop_counts + 1
            #jake, here is the old call===> payload, src_addr = xbee_socket.recvfrom(255)
	    #consider adding try catch around this 
	    response = xbee.wait_read_frame()
	    payload = response['rf_data']

	    src_addr = struct.unpack("!h", response['source_addr'])[0]
	    
            #map hex to numbers
            payload = map( ord , payload )
	    
            last_radio_rx_time = float(time.time())
            sequential_timeouts = 0
            
	     #jake you may have to mess with the hex conversion from the xbee api to get to an int
            address = src_addr

            id = payload[ 1 ] +   ( payload[ 2 ]  << 8 )
            key = ( id << 8 ) + address
            
            
            if  payload[0]  == IV_CURVE_MESSAGE_ID:
                if Print_Out == 1:
                    print('iv frame address: %d' % address )
                if key in root_curves:
                    root_curves[ key ].add_frame( payload ) 
                else:
                    root_curves[ key ] = curve( address )
                    root_curves[ key ].add_frame( payload )
                    
            elif payload[0] == TRACER_STATE_MESSAGE_ID:
                if Print_Out == 1:
                    print('status frame address: %d' % address )
                result = write_stat_to_file( address, payload)
                text_streams.append( result )
            else:
                print('unrecognized frame')      
