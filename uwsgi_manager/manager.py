#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Adam Strauch
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#     1. Redistributions of source code must retain the above copyright notice,
#        this list of conditions and the following disclaimer.
#   
#     2. Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


import os, shlex, time, errno, sys
from xml.etree.ElementTree import XMLParser
from subprocess import Popen, PIPE, call
from optparse import OptionParser

UWSGIs_PATH = "/usr/local/bin/uwsgi"

class manager:
    config_file = "/etc/uwsgi/config.xml"
    config_tree = None
    config = {}

    def __init__(self):
        f = open(self.config_file)
        xml_src = f.read()
        f.close()

        parser = XMLParser()
        parser.feed(xml_src)
        self.config_tree = parser.close()

        self.parse()

    def parse(self):
        for element in self.config_tree:
            web_id = int(element.get("id"))
            self.config[web_id] = {}
            for subelement in element:
                self.config[web_id][subelement.tag] = subelement.text

    ############################
    ## Process manipulation
    ############################

    def run_cmd(self, cmd):
        return_code = call(shlex.split(cmd))

        if not return_code:
            return True
        else:
            print "Error: '%s' return %d" % (cmd, return_code)
            return False

    def send_signal(self, id, signal):
        if not os.path.isfile(self.config[id]["pidfile"]):
            return False
        try:
            os.kill(self.get_pid(id), signal)
            return True
        except OSError, err:
            if err.errno == errno.ESRCH:
                return False
            elif err.errno == errno.EPERM:
                print pid
                print "No permission to signal this process!"
                sys.exit(1)
            else:
                print pid
                print "Unknown error"
                sys.exit(1)
        else:
            return True


    def running_check(self, id):
        return self.send_signal(id, 0)

    def get_pid(self, id):
        f = open(self.config[id]["pidfile"])
        try:
            pid = int(f.read().strip())
        except ValueError:
            print "Wrong PID format (int %s)" % self.config[id]["pidfile"]
            sys.exit(1)
        f.close()
        return pid

    def check_id(self, id):
        if not id in self.config:
            print "ID not found"
            sys.exit(1)

    #{'43': {'wsgi-file': '/home/cx/co/sexflirt/sexflirt.wsgi', 'processes': '1', 'uid': 'cx', 'pythonpath': '/home/cx/co/', 'limit-as': '48', 'chmod-socket': '660', 'gid': 'cx', 'master': None, 'home': '/home/cx/virtualenvs/default', 'optimize': '1', 'socket': '/home/cx/uwsgi/sexflirt.cz.sock'}}

    ## Actions it selfs

    def start(self, id):
        self.check_id(id)

        python_bin = self.config[id]["home"]+"/bin/python -V"
        p = Popen(shlex.split(python_bin), stdout=PIPE, stderr=PIPE)
        data_raw = p.communicate()
        version = ".".join(data_raw[1].split(" ")[1].split(".")[0:2])

        uwsgi_bin = "%s%s" % (UWSGIs_PATH, version.replace(".",""))
        if not os.path.isfile(uwsgi_bin):
            uwsgi_bin = "/usr/bin/uwsgi"

        if not self.running_check(id):
            cmd = "sudo su %s -c '%s -x %s:%d'" % (self.config[id]["uid"], uwsgi_bin, self.config_file, id)
            self.run_cmd(cmd)

    def startall(self):
        for web in self.config:
            self.start(web)

    def stop(self, id):
        self.check_id(id)
        if self.running_check(id):
            if not self.send_signal(id, 3): #QUIT signal
                print "Error QUIT"
            time.sleep(1)
            if self.running_check(id):
                if not self.send_signal(id, 9): #KILL signal
                    print "Error KILL"
            time.sleep(1)
        else:
            print "Error: app %d doesn't run" % id

    def stopall(self):
        for web in self.config:
            self.stop(web)
        
    def restart(self, id):
        self.check_id(id)
        if self.running_check(id):
            self.stop(id)
        if not self.running_check(id):
            self.start(id)

    def restartall(self):
        for web in self.config:
            self.restart(web)

    def reload(self, id):
        self.check_id(id)
        if self.running_check(id):
            return self.send_signal(id, 1)
        else:
            self.start(id)

    def brutal_reload(self, id):
        self.check_id(id)
        if self.running_check(id):
            return self.send_signal(id, 15)
        else:
            self.start(id)

    def brutal_reloadall(self):
        for web in self.config:
            self.brutal_reload(web)

    def check(self, id):
        self.check_id(id)
        if self.running_check(id):
            print "Aplikace běží"
        else:
            print "Aplikace neběží"

    def list(self):
        for app in self.config:
            if os.getuid() != 0 and os.getlogin() != self.config[app]["uid"]: continue
            prefix = "run"
            if not self.running_check(app):
                prefix = "not"
            print "%s %d: %s (%s)" % (prefix ,app, self.config[app]["wsgi-file"], self.config[app]["uid"])

def main():
    m = manager()

    parser = OptionParser()
    parser.add_option("-s", "--start", dest="start", help="Start app", metavar="ID", action="store")
    parser.add_option("-S", "--stop", dest="stop", help="Stop app (sig 9)", metavar="ID", action="store")
    parser.add_option("-r", "--reload", dest="reload", help="Reload app (sig 1)", metavar="ID", action="store")
    parser.add_option("-b", "--brutal-reload", dest="brutalreload", help="Brutal reload app (sig 15)", metavar="ID", action="store")
    parser.add_option("-R", "--restart", dest="restart", help="Restart app", metavar="ID", action="store")
    parser.add_option("-c", "--check", dest="check", help="Check state of app", metavar="ID", action="store")
    parser.add_option("-a", "--start-all", dest="startall", help="Start all apps", action="store_true")
    parser.add_option("-A", "--stop-all", dest="stopall", help="Stop all apps", action="store_true")
    parser.add_option("-w", "--reload-all", dest="reloadall", help="Reload all apps", action="store_true")
    parser.add_option("-W", "--restart-all", dest="restartall", help="Restart all apps", action="store_true")
    parser.add_option("-B", "--brutal-reload-all", dest="brutalreloadall", help="Brutal reload all apps", action="store_true")
    parser.add_option("-l", "--list", dest="list", help="Print state of all apps", action="store_true")
    

    (options, args) = parser.parse_args()
    
    if options.start: m.start(int(options.start))
    elif options.stop: m.stop(int(options.stop))
    elif options.restart: m.restart(int(options.restart))
    elif options.reload: m.reload(int(options.reload))
    elif options.brutalreload: m.brutal_reload(int(options.brutalreload))
    elif options.check: m.check(int(options.check))


    elif options.startall: m.startall()
    elif options.stopall: m.stopall()
    elif options.reloadall: m.reloadall()
    elif options.brutalreloadall: m.brutal_reloadall()
    elif options.restartall: m.restartall()
    elif options.list: m.list()

    else: parser.print_help()
    
if __name__ == "__main__":
    main()
