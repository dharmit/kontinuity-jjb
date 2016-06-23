#!/usr/bin/python

import json
import os
import subprocess
import sys
import urllib

api_key = open("/home/kontinuity/duffy.key").read().strip()
req_url = \
    "http://admin.ci.centos.org:8080/Node/get?key=%s&ver=7&arch=x86_64&count=1"\
    % api_key

env_vars_path = "/home/kontinuity/env_vars"
# cwd = "/home/kontinuity/workspace/kontinuity-build-catapult/"

branch = os.environ["branch"]
tag = os.environ["ref"]

if tag == "master" and branch == "master":
    tag = "latest"


def return_node_to_duffy(ssid):
    done_nodes_url = "http://admin.ci.centos.org:8080/Node/done?" \
        "key=%s&ssid=%s" % (api_key, ssid)
    print urllib.urlopen(done_nodes_url).read()

try:
    jsondata = urllib.urlopen(req_url).read()
except:
    sys.exit("Failed to reserve node through Duffy")

data = json.loads(jsondata)

with open(env_vars_path) as f:
    for line in f:
        split = line.split("=")
        os.environ[split[0]] = split[1].strip()


for host in data['hosts']:
    h = data['hosts'][0]

    try:
        # Using full path to gh repo instead of env var since bug in git-plugin
        # prevents clone: https://issues.jenkins-ci.org/browse/JENKINS-30405
        subprocess.check_call(['git', 'clone',
                               'http://github.com/dharmit/adb-ci-ansible'])
        subprocess.check_call(['git', 'checkout', 'parameterized-build'],
                              cwd='adb-ci-ansible/')
    except:
        return_node_to_duffy(data["ssid"])
        sys.exit("Failed to setup fresh environment")

    with open("adb-ci-ansible/hosts", "a") as f:
        f.write(h)

    try:
        subprocess.check_call(
            ['ansible-playbook',
             'install-adb.yml',
             '--extra-vars',
             '%s' % "start-openshift=true"],
            cwd='adb-ci-ansible'
        )
    except:
        return_node_to_duffy(data["ssid"])
        sys.exit("Failed to setup ADB with OpenShift")

    catapult_extra_args = \
        "base_image=redhatdistortion/wildfly-100-centos7 "
    catapult_extra_args += \
        "oc_binary=%s " % os.environ["OC_BINARY"]
    catapult_extra_args += \
        "docker_user=%s " % os.environ["DOCKER_USERNAME"]
    catapult_extra_args += \
        "docker_password=%s " % os.environ["DOCKER_PASSWORD"]
    catapult_extra_args += \
        "docker_email=%s " % os.environ["DOCKER_EMAIL"]
    catapult_extra_args += \
        "github_client_id=%s " % os.environ[
            "KONTINUITY_CATAPULT_GITHUB_APP_CLIENT_ID"
        ]
    catapult_extra_args += \
        "github_client_secret=%s " % os.environ[
            "KONTINUITY_CATAPULT_GITHUB_APP_CLIENT_SECRET"
        ]
    catapult_extra_args += "ose_host=%s " % host
    catapult_extra_args += "destination_tag=%s" % tag

    try:
        subprocess.check_call(
            ['ansible-playbook',
             'catapult.yml',
             '--extra-vars',
             '%s' % catapult_extra_args],
            cwd='adb-ci-ansible'
        )
    except:
        return_node_to_duffy(data["ssid"])
        sys.exit("Failed to deploy and validate app")
    return_node_to_duffy(data["ssid"])
