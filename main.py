#!/bin/env python

from sys import argv
from paramiko import SSHClient, AutoAddPolicy
from scp import SCPClient
from tempfile import mkdtemp
from shutil import rmtree
from os import walk, listdir
import blacklist
import re

ssh = SSHClient()
ssh.load_system_host_keys()
ssh.set_missing_host_key_policy(AutoAddPolicy())

REGEXES = {
  'nginx-default': '(.*?)([0-9]{1,3}\.[0-9]{1,3}\.[0-9]'+ \
  '{1,3}\.[0-9]{1,3})\s+-\s-\s(\[.*\])\s+(\".*\")'
}

FORMATS = {
  'nginx-default': re.compile(REGEXES['nginx-default'])
}

def     usage():
  print('usage %s : host username directory (password) (port)' %argv[0])
  return 0

def     mktemp(dir=None):
  temp = mkdtemp(dir=dir)
  return temp

def     ssh_copy(temp, host, username, password, port=22):
  print('Connecting to %s:%s' %(host, port))
  ssh.connect(host, auth_timeout=5, timeout=5, username=username, password=password, port=port)
  print('Connected to %s\nCopying logs to %s' %(host, temp))
  with SCPClient(ssh.get_transport(), sanitize=lambda x: x) as scp:
    scp.get('/var/log/nginx/full_access*.log', temp)
    scp.close()
  return 0

def     rm_temp(temp):
  return

def     fetch(log_directory):
  logs = ""
  f = listdir(log_directory)
  for filename in f:
    with open('%s/%s' %(log_directory, filename)) as f:
      logs += f.read()
  return logs

def     parse(logs):
  parsed = []
  for line in logs.split('\n'):
    m = FORMATS['nginx-default'].search(line, re.IGNORECASE)
    if m:
      log = {
        "ip": m.group(2),
        "date": m.group(3),
        "request": m.group(4)
      }
      if len(m.groups()) == 4:
        log['vhost'] = m.group(1)
      parsed.append(log)
  return parsed

def analyze(logs):
  for log in logs:
    if log['ip'] in blacklist.ips:
      print('Warning : blacklisted IP', log)

def	    main():
  if len(argv) < 4:
    return usage()
  temp = mktemp()
  ssh_copy(temp, argv[1], argv[2], argv[3], argv[4] if len(argv) > 4 else None)
  logs = fetch(temp)
  parsed = parse(logs)
  print(parsed)
  analyze(parsed)
  return 0

if __name__ == '__main__':
  exit(main())
