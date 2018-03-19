#!/usr/bin/env python

import subprocess,time,platform,threading,re,Queue

class ConfigThread(threading.Thread):
    def __init__(self,ip,mac):
         super(ConfigThread, self).__init__()
         self.ip=ip
         self.mac=mac
         self.result= None
         #self.daemon = True
    def run(self):
         self.config_encoder()
    def send_arp(self):
        print "configuring arp for %s at %s" % (self.mac,self.ip)
        if platform.uname()[0] == 'Windows':
            cmd = 'arp -s %s %s' % (self.ip,self.mac)
            subprocess.call(cmd.split())
        elif platform.uname()[0] == 'Linux':
            cmd = "arp -s %s %s temp" % (self.ip,self.mac)
            subprocess.call(cmd.split())
        else:
            print 'Something went wrong.'
    def win_ping(self):
        done = 'no'
        timeout = 30
        cmd = 'ping -n 1 -l 408 %s' % self.ip
        packet_loss = re.compile(r'\((\d*)%\s*loss\)')
        start_time = time.time()
        while done == 'no':
            proc = subprocess.Popen(cmd.split(),stdout=subprocess.PIPE)
            stdout = proc.communicate()
            etime = time.time() - start_time
            loss = packet_loss.search(stdout[0]).group(1)
            if loss == '0':
                done = 'yes'
                success = 'yes'
                return True
            elif etime >= timeout:
                done = 'yes'
                success = 'no'
                return False
            else:
                done = 'no'

    def linux_ping(self):
        timeout = 30
        cmd = 'ping -c 1 -s 408 %s' % self.ip
        packet_loss = re.compile(r'(\d*)%\s*packet loss')
        start_time = time.time()
        done = 'no'
        while done == 'no':
            proc = subprocess.Popen(cmd.split(),stdout=subprocess.PIPE)
            stdout = proc.communicate()
            etime = time.time() - start_time
            loss = packet_loss.search(stdout[0]).group(1)
            if loss == '0':
                done = 'yes'
                success = 'yes'
                return True
            elif etime >= timeout:
                done = 'yes'
                success = 'no'
                return False
            else:
                done = 'no'

    def send_ping(self):
        print "Pinging %s" % self.ip
        timeout = 30
        if platform.uname()[0] == 'Windows':
            success = self.win_ping()
        else:
            success = self.linux_ping()
        if success == True:
            print "Ping succeeded for %s" % self.ip
        else:
            print "Ping failed for %s" % self.ip
        return success

    def config_encoder(self):
        print 'Configure Encoder'
        self.send_arp()
        self.send_ping()

def serial_to_mac(serial):
    if platform.uname()[0] == 'Windows':
        n = 2
        return "-".join([serial[i:i+n] for i in range(0,len(serial),n)])
    else:
        n = 2
        return ":".join([serial[i:i+n] for i in range(0,len(serial),n)])
def get_serials(self):
    print """Please type the serial number (s/n) of the video encoder.
This can be found on the back of the devices.  When you are done entering
serial numbers, just hit enter with no serial number to move on to the next
step.

Pro tip: serials can be entered on the command line separated by spaces and skip this step."""
    macs = []
    i = 1
    go = 'no'
    while go == 'no':
        _serial = raw_input('serial #%d ' % i)
        i = i + 1
        if _serial == '':
            go = 'yes'
        else:
            go = 'no'
            macs.append(serial_to_mac(_serial))
    return macs

def get_switch_ip(self):
    print """IP address will be configured sequetially starting at the .201
address of the configured network. ex. 192.168.1.201 or 10.1.10.201.
The router providing DHCP addresses but be configured to exclude these IP addresses
to avoid having them used by DHCP clients.

Pro tip: The switch ip can be specified on the command line with the -i option.
Then you can skip this step."""
    switchip = raw_input('What is the ip address of the switch? ')
    return switchip

def thread_config(macs,iprange):
    print 'configuring camera devices'
    q = Queue.Queue()
    macs.sort()
    threads = {}
    ips = ['%s.%s' % (iprange,str(x)) for x in range(210,(len(macs)+210))]
    macs_to_ip = dict(zip(ips,macs))
    for ip,mac in macs_to_ip.items():
        print "configuring %s as %s" % (mac,ip)
        threads[ip] = ConfigThread(ip,mac)
        threads[ip].start()

def get_options():
    import optparse
    usage = 'script -i <switch ip> serial1 serial2 serial3'
    optparser = optparse.OptionParser(usage)
    optparser.add_option('-i','--switchip',action='store',type='string',dest='switchip',help='IP address of POE switch.')
    return optparser.parse_args()

def main():
    options,args = get_options()
    if options.switchip:
        switchip = options.switchip
    else:
        switchip = get_switchip
    ip_range = ".".join(switchip.split('.')[:3])

    if args:
        macs = [ serial_to_mac(x) for x in args ]
    else:
        macs = get_serials()
    print macs,ip_range
    thread_config(macs,ip_range)

if __name__ == '__main__':
    main()
