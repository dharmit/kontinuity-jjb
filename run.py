#!/usr/bin/python

import json
import subprocess
import urllib

api_key = open("/home/atomic-sig/duffy.key").read().strip()
req_url = "http://admin.ci.centos.org:8080/Node/get?key=%s&ver=7&arch=x86_64&count=1" % api_key
ansible_repo = "https://github.com/dharmit/adb-ci-ansible"
ansible_branch = "kontinuity"

jsondata = urllib.urlopen(req_url).read()
data = json.loads(jsondata)
# below print statement is kept to manually return node back to duffy
# TODO - remove print statement and automate node return process
print data

for host in data['hosts']:
    h = data['hosts'][0]

    subprocess.check_call(['rm', '-rf', 'adb-ci-ansible'])

    subprocess.check_call(['git', 'clone', "%s" % ansible_repo])
    subprocess.check_call(['git', 'checkout', '%s' % ansible_branch],
                          cwd='adb-ci-ansible/')

    with open("adb-ci-ansible/hosts", "a") as f:
        f.write(h)

    subprocess.check_call(
        ['ansible-playbook',
         'install-adb.yml',
         '--extra-vars',
         '%s' % "start-openshift=true"],
        cwd='adb-ci-ansible'
    )
