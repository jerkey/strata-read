From kellen@pvtracer.com Tue Mar 25 11:54:02 2014
Date: Tue, 25 Mar 2014 11:53:54 -0700
From: Kellen Gillispie <kellen@pvtracer.com>
To: Jake <jake@spaz.org>
Subject: Re: Strata sense tracer

Jake,
Here is the link to digi x2 connectport.

Here is part of the application.  The 802.15.4 packet frames originate from the
iv tracers radio.  If you can write something that reads the serial port and
halts on a new packet in the xbee api mode we are good to go for using the linux
box you have. 

Regards,
Kellen

======================python code=============================
xbee_socket = socket(AF_XBEE, SOCK_DGRAM, XBS_PROT_TRANSPORT)
# Bind to endpoint 0x00 for 802.15.4
xbee_socket.bind( ("", 0x00, 0, 0 ) )
xbee_socket.settimeout(1.0)
root_curves = {}

while True:
      try:
         #Block until a single frame is received, up to 255 byte or until
timeout
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
        catch:            
             #catch a timeout and ensure a heartbeat



On Mon, Mar 24, 2014 at 6:00 PM, Kellen Gillispie <kellen@pvtracer.com> wrote:
      Jake,
Yeah G's party was great. Good to see social and business worlds collide. 

The IP address assigned by Laney is: 10.38.132.221.  
You should note that the X2's radio is monopolized with the Stratasense
application.  Sharing this resource is possible, but not within the scope
of the project since it adds a bit of software complexity.  If you want to
connect other xbee sensors aside from the tracers, I recommend you
parallel them on a separate gateway and RF channel.  Or we can restructure
our quote to customize access to that radio interface.  But as of now our
software has an exclusive lock on the radio.

I have not been in contact with anyone regarding the allegedly waterlogged
digi gatway other than Mark just to warn me of this situation.  

I'm open to continuing to help SS get data from your product, but I
haven't seen any evidence that we will ever get paid for the deliverables
we've already invoiced weeks ago, let alone future work.

Feel free to reach out by phone if you want discuss in more detail.  323
229 2755.

Regards,
-Kellen

 


On Sun, Mar 23, 2014 at 7:53 PM, Jake <jake@spaz.org> wrote:
      Hi Kellen,

      This is Jake, with SunSynchrony.  I saw you at G's birthday
      party recently, i hope you had a good time.

      I don't know if you've heard from us about the solar panel
      tracker equipment you helped put on the rooftop, but my
      understanding is that it's not working because the
      ethernet-xbee bridge got waterlogged.

      I never saw an email with any technical details about the
      setup so as far as I know, you're the only one who knows
      anything about this system.

      Of course to get the system up and running again, the
      equipment will have to be repaired or replaced, and
      reinstalled.  Have you been in contact with anyone about this?

      Also, can you relay the IP address and routing information
      that was given to our project by the school?  We want to put a
      router up there which will let us have a webcam and also allow
      us to login to the xbee device, using a VPN that our router
      will connect to.  (but first we need the connection from the
      university to reach the VPN)

      thank you
      -jake




