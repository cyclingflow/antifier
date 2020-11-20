import binascii, re, os, usb.core, glob, time, platform
#if os.name == 'posix':
if platform.system() == 'Linux':
  import serial

def calc_checksum(message):#calulate message checksum
  pattern = re.compile('[\W_]+')
  message=pattern.sub('', message)
  byte = 0
  xor_value = int(message[byte*2:byte*2+2], 16)
  data_length = int(message[byte*2+2:byte*2+4], 16)
  data_length += 3#account for sync byte, length byte and message type byte
  while (byte < data_length):#iterate through message progressively xor'ing
    if byte > 0: 
      xor_value = xor_value ^ int(message[byte*2:byte*2+2], 16)
    byte += 1
  return hex(xor_value)[2:].zfill(2)

def send_ant(stringl, dev_ant, debug):#send message string to dongle
  rtn = []
  for string in stringl:
    i=0
    send=""
    while i<len(string):
      send = send + binascii.unhexlify(string[i:i+2])
      i=i+3
    if debug == True: print int(time.time()*1000),'>>',binascii.hexlify(send)#log data to console
    #if os.name == 'posix':
    if platform.system() == 'Linux':
      dev_ant.write(send)
    else:
      try:
        dev_ant.write(0x01,send)
      except Exception, e:
        print "USB WRITE ERROR", str(e)
    tr = read_ant(dev_ant, debug)
    for v in tr: rtn.append(v)

  if debug == True: print rtn
  return rtn


def read_ant(dev_ant, debug):
  read_val = ""
  trv = True #temp rtn value from ANT stick
  #if os.name == 'posix':
  if platform.system() == 'Linux':
    dev_ant.timeout = 0.1
    try:
      read_val += binascii.hexlify(dev_ant.read(size=256))
    except Exception, e:
      read_val = ""
      print str(e)
  #elif os.name == 'nt': 
  else:
    try:
      while trv:
        trv = binascii.hexlify(dev_ant.read(0x81,64,20))
        read_val += trv
    except Exception, e:
      if "timeout error" in str(e):
        pass
      else:
        print "USB READ ERROR", str(e)
      
  read_val_list = read_val.split("a4")#break reply into list of messsages
  rtn = []
  for rv in read_val_list:
    if rv: 
      if len(rv)>6:
        if (int(rv[:2],16)+3)*2 == len(rv):
          if calc_checksum("a4"+rv) == rv[-2:]: 
            rtn.append("a4"+rv)
    
  if debug: print "<<",rtn
  return rtn
  
  
  
def calibrate(dev_ant, debug):
  stringl=[
  "a4 02 4d 00 54 bf 00 00",#request max channels
  "a4 01 4a 00 ef 00 00",#reset system
  "a4 02 4d 00 3e d5 00 00",#request ant version
  "a4 09 46 00 b9 a5 21 fb bd 72 c3 45 64 00 00",#set network key b9 a5 21 fb bd 72 c3 45
  ]
  send_ant(stringl,dev_ant, debug)
  
def master_channel_config(dev_ant, debug):
  stringl=[
  "a4 03 42 00 10 00 f5 00 00",#[42] assign channel, [00] 0, [10] type 10 bidirectional transmit, [00] network number 0, [f5] extended assignment
  "a4 05 51 00 cf 00 11 05 2b 00 00",#[51] set channel ID, [00] number 0 (wildcard search) , [cf] device number 207, [00] pairing request (off), [11] device type fec, [05] transmission type  (page 18 and 66 Protocols) 00000101 - 01= independent channel, 1=global data pages used
  "a4 02 45 00 39 da 00 00",#[45] set channel freq, [00] transmit channel on network #0, [39] freq 2400 + 57 x 1 Mhz= 2457 Mhz
  "a4 03 43 00 00 20 c4 00 00",#[43] set messaging period, [00] channel #0, [f61f] = 32768/8182(f61f) = 4Hz (The channel messaging period in seconds * 32768. Maximum messaging period is ~2 seconds. )
  "a4 02 60 00 03 c5 00 00",#[60] set transmit power, [00] channel #0, [03] 0 dBm
  "a4 01 4b 00 ee 00 00",#open channel #0
  "a4 09 4e 00 50 ff ff 01 59 00 85 83 ed 00 00",#broadcast manufacturer's data #FitSDKRelease_20.50.00.zip profile.xlsx D00001198_-_ANT+_Common_Data_Pages_Rev_3.1%20.pdf page 28 byte 4,5,6,7- 15=dynastream, 89=tacx
  ]
  send_ant(stringl, dev_ant, debug)

def second_channel_config(dev_ant, debug):
  #stringl=[
  #"a4 03 42 01 10 00 f4 00 00",#[42] assign channel, [01] channel #1, [10] type 10 bidirectional transmit, [00] network number 0, [f4] normal assignment
  #"a4 05 51 01 02 00 78 01 8a 00 00",#[51] set channel ID, [01] channel 1 , [02] device number 2, [00] pairing request (off), [78] device type HR sensor, [01] transmission type  (page 18 and 66 Protocols) 00000101 - 01= independent channel, 1=global data pages used
  #"a4 02 45 01 39 db 00 00",#[45] set channel freq, [01] set channel #1, [39] freq 2400 + 57 x 1 Mhz= 2457 Mhz
  #"a4 03 43 01 86 1f c5 00 00",#[43] set messaging period, [01] channel #1, [861f] = 32768/8070(861f) = 4Hz (The channel messaging period in seconds * 32768. Maximum messaging period is ~2 seconds. )
  #"a4 02 60 01 03 c4 00 00",#[60] set transmit power, [01] channel #1, [03] 0 dBm
  #"a4 01 4b 01 ef 00 00",#open channel #1
  #]
  stringl=[
    "a4 03 42 01 10 00 f4 00 00",
    "a4 05 51 01 65 00 78 01 ed 00 00",
    "a4 02 45 01 39 db 00 00",
    "a4 03 43 01 86 1f 7c 00 00",
    "a4 02 60 01 03 c4 00 00",
    "a4 01 4b 01 ef 00 00"
    ]
  send_ant(stringl, dev_ant, debug)

def powerdisplay(dev_ant, debug):
  #calibrate as power display
  stringl=[
  "a4 03 42 00 00 00 e5 00 00", #42 assign channel
  "a4 05 51 00 00 00 0b 00 fb 00 00", #51 set channel id, 0b device=power sensor
  "a4 02 45 00 39 da 00 00", #45 channel freq
  "a4 03 43 00 f6 1f 0d 00 00", #43 msg period
  "a4 02 71 00 00 d7 00 00", #71 Set Proximity Search chann number 0 search threshold 0
  "a4 02 63 00 0a cf 00 00", #63 low priority search channel number 0 timeout 0
  "a4 02 44 00 02 e0 00 00", #44 Host Command/Response 
  "a4 01 4b 00 ee 00 00" #4b ANT_OpenChannel message ID channel = 0 D00001229_Fitness_Modules_ANT+_Application_Note_Rev_3.0.pdf
  ]
  send_ant(stringl, dev_ant, debug)
  
def antreset(dev_ant, debug):
  #for i in range (0,10):
  #  if os.name == 'posix': read_val = binascii.hexlify(dev_ant.read(size=256))#clear cached data
  #  elif os.name == 'nt': read_val = binascii.hexlify(dev_ant.read(0x81,64))#
  send_ant(["a4 01 4a 00 ef 00 00"],dev_ant, debug)

def get_ant(debug):
  msg=""
  dongles = {4104:"Suunto", 4105:"Garmin", 4100:"Older"}
  reset_string="a4 01 4a 00 ef 00 00"#reset string probe 
  i = 0
  send=""
  while i<len(reset_string):
    send = send + binascii.unhexlify(reset_string[i:i+2])
    i=i+3
  ###windows###
  #if os.name == 'nt':
  if platform.system() == 'Windows' or platform.system() == 'Darwin':
    found_available_ant_stick= False
    #CF Force uses of garmin over Suunto, because of problematic 4104 Anself/CYCLOPS dongles    
    ant_pids = [0x1009, 0x1008, 0x1004]#0x1008 4104 suunto, 0x1009 4105 garmin
    for ant_pid in ant_pids:#iterate through ant pids
      if not found_available_ant_stick:#if haven't found a working ANT dongle yet
        try:
          dev_ant = usb.core.find(idVendor=0x0fcf, idProduct=ant_pid) #get ANT+ stick 
          dev_ant.set_configuration() #set active configuration
          try:#check if in use
            if debug: print "Trying to write to %s dongle" % ant_pid
            dev_ant.write(0x01, send)#probe with reset command
            reply = read_ant(dev_ant, debug)
            matching = [s for s in reply if "a4016f" in s]#look for an ANT+ reply
            if matching:
              found_available_ant_stick = True
              msg = "Using %s dongle" % dongles[ant_pid]
              if debug: print msg
          except usb.core.USBError:#cannot write to ANT dongle
            if debug: print "ANT dongle in use"
            found_available_ant_stick = False
        #except AttributeError:#could not find dongle
        except Exception, e:
          if debug: print str(e)
          if "AttributeError" in str(e):
            if debug: print "Could not find %s dongle" % ant_pid
            msg = "Could not find dongle"
          elif "No backend" in str(e):
            if debug: print "No backend- check libusb"
            msg = str(e)+"- check libusb"
          else:
            msg = str(e)
          found_available_ant_stick = False

    if found_available_ant_stick == False:
      dev_ant = False 

  ###Linux###
  #elif os.name == 'posix':
  elif platform.system() == 'Linux':
    #Find ANT+ USB stick on serial (Linux)
    ant_stick_found = False
    for p in glob.glob('/dev/ttyUSB*'):
      dev_ant = serial.Serial(p, 19200, rtscts=True,dsrdtr=True)
      read_val = send_ant(["a4 01 4a 00 ef 00 00"], dev_ant, False) #probe with reset command
      if "a4016f20ea" in read_val or "a4016f00ca" in read_val:#found ANT+ stick
        serial_port=p
        ant_stick_found = True
        msg = "Found ANT Stick"
      else:
        if debug: print read_val 
        dev_ant.close()#not correct reply to reset
      if ant_stick_found == True  : break

    if ant_stick_found == False:
      #print 'Could not find ANT+ device. Check output of "lsusb | grep 0fcf" and "ls /dev/ttyUSB*"'
      #sys.exit()
      dev_ant = False
      
    
  else:
    #print "OS not Supported"
    #sys.exit()
    dev_ant = False
  
  
  if not dev_ant: 
    print "ANT Stick not found"
  return dev_ant, msg
