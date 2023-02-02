#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Copyright 2023 Nokia
# Copyright 2023 Santoshkumar Vagga
# Copyright 2023 BGL 5G SCM Team

"""
Utility file contianing utility methods required for zuul_setup.py
"""

import logging
import re
import time

import yaml

logging.basicConfig(filename="Log_file.log",
                    format="%(asctime)s:%(levelname)s: %(message)s",
                    filemode="w")

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SSH_KEYS = dict()

zuul = "docker run -itd --restart always --log-opt max-size=2g --log-opt max-file=1 --privileged --name zuul-server -v /ephemeral/etc/:/etc/zuul/ -v /ephemeral/git/:/ephemeral/zuul/git/ -v /ephemeral/log/:/ephemeral/log/zuul/ -v /ephemeral/tmp/:/tmp/ --net host zuul-local.artifactory-espoo1.int.net.nokia.com/zuul-images/zuul-server:v2.7.7.1"  # nopep8
mysql = "docker run --restart always --name mysql -v /var/fpwork/zuul/mysql:/var/lib/mysql -p 3306:3306 -e MYSQL_ALLOW_EMPTY_PASSWORD=true -d zuul-local.artifactory-espoo1.int.net.nokia.com/zuul-images/mysql:v1.0 --character-set-server=utf8 --collation-server=utf8_general_ci"  # nopep8
gerrit = "docker run -d --restart always --name gerrit -p 8180:8080 -p 29418:29418 -v /ephemeral/gerrit:/var/gerrit/review_site -e GERRIT_INIT_ARGS='--install-all-plugins' -e GITWEB_TYPE=gitiles -e http_proxy=http://10.158.100.1:8080 -e https_proxy=http://10.158.100.1:8080 -e AUTH_TYPE=DEVELOPMENT_BECOME_ANY_ACCOUNT -e SMTP_SERVER='webmail-emea.nsn-intra.net' -e HTTPD_LISTENURL='proxy-http://*:8080' -e WEBURL='http://gerrit.zuul.5g.dynamic.nsn-net.net' zuul-local.esisoj70.emea.nsn-net.net/zuul-images/gerrit"  # nopep8
gearman = "docker run -d --restart always --log-opt max-size=2g --log-opt max-file=1 -p 4731:4730 --name gearman -v /ephemeral/zuul_t/gearman:/root/mn_scripts/gearman -v /ephemeral/zuul_t/log/gearman:/ephemeral/log/zuul zuul-local.artifactory-espoo1.int.net.nokia.com/zuul-images/gearman:v1.0"  # nopep8
jenkins = "docker pull jenkins/jenkins:lts;docker run -itd --restart always -p 8080:8080 -p 50000:50000 --name jenkins -v /ephemeral/jenkins/:/var/jenkins_home jenkins/jenkins:lts"  # nopep8
merger = "docker run -itd --restart always --privileged -p 9191:9091 -p 8081:80 -p 8122:22 -v /ephemeral/zuul_mergers/merger_1/log/:/ephemeral/log/zuul/ -v /ephemeral/zuul_mergers/merger_1/git/:/ephemeral/zuul/git/ --name merger zuul-local.artifactory-espoo1.int.net.nokia.com/zuul-images/zuul-merger:v1.13"  # nopep8
merger_conf = "docker cp /root/folder/layout.yaml merger:/etc/zuul/layout.yaml; docker cp /root/folder/zuul_conf_merger.conf merger:/etc/zuul/zuul.conf"  # nopep8
zuul_conf = "docker cp /root/folder/layout.yaml zuul-server:/etc/zuul/layout.yaml; docker cp /root/folder/zuul.conf zuul-server:/etc/zuul/zuul.conf"  # nopep8
zuuL_conf_all = ["gearman-logging.conf", "launcher-logging.conf", "layout.yaml", "merger-logging.conf", "server-logging.conf", "zuul.conf", "zuul_layout_jenkins_paras.py"]  # nopep8
create_db = 'docker exec mysql bash -c "mysql -uroot --database=mysql < /var/lib/mysql/query.sql"'  # nopep8
clean = "docker stop $(docker ps -aq);docker rm $(docker ps -aq);docker rmi $(docker image ls -aq)"  # nopep8
command = "sudo yum remove docker docker-client docker-client-latest docker-common docker-latest docker-latest-logrotate docker-logrotate docker-engine"  # nopep8
repository_setup_command = "sudo yum install -y yum-utils sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo"    # nopep8
docker_engine_command = "sudo yum install docker-ce docker-ce-cli containerd.io docker-compose-plugin"    # nopep8
start_docker_command = "sudo systemctl start docker"
hello_world_container_command = "sudo docker run hello-world"
total_cmd = f"{command}&&{repository_setup_command}&&{docker_engine_command}&&{start_docker_command}&&{hello_world_container_command}"  # nopep8


def printProgressBar(
        iteration,
        total,
        prefix='',
        suffix='',
        decimals=1,
        length=100,
        fill='█',
        printEnd="\r"):
    """  # nopep8
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))  # nopep8
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + "-" * (length - filledLength)
    print(f"\r{prefix} |{bar}| {percent}% {suffix}", end=printEnd)
    if iteration == total:
        print()


def show_progress(Processes):
    # Initial call to print 0% progress
    printProgressBar(0, len(Processes), prefix='Progress:', suffix='Complete', length=50)  # nopep8
    for i, item in enumerate(Processes):
        item()
        time.sleep(0.1)
        printProgressBar(
            i + 1,
            len(Processes),
            prefix="Progress:",
            suffix="Complete",
            length=50)


def filter_ssh_key(machine, output):
    output = str(output)
    result = re.search(r"ssh-rsa.+", output)
    if result and result.group():
        key = str(result.group()).split("\\n")[0]
        SSH_KEYS[machine] = key
    else:
        logger.error(f"error in filtering ssh key for {machine}")


def format_result(output):
    output = str(output)
    result = None
    if output:
        result = "\n".join(output.split("\\n"))
    return "\n" + str(result)


class Input():
    def get_val(self):
        read_data = None
        with open("config.yaml", encoding="utf-8") as fh:
            read_data = yaml.load(fh, Loader=yaml.FullLoader)

            self.linux_ip = read_data["linux_host"][0]["ip"]
            self.linux_user = read_data["linux_host"][1]["user"]
            self.linux_password = read_data["linux_host"][2]["password"]
            self.linux_port = read_data["linux_host"][3]["port"]
            self.linux_type = read_data["linux_host"][4]["type"]

            self.database_name = read_data["database"][0]["name"]
            self.database_user = read_data["database"][1]["user"]
            self.database_password = read_data["database"][2]["password"]
            self.database_port = read_data["database"][3]["port"]

            self.gerrit_user = read_data["gerrit"][0]["user"]
            self.gerrit_password = read_data["gerrit"][1]["password"]
            self.gerrit_url = read_data["gerrit"][2]["url"]
            self.gerrit_repo = read_data["gerrit"][3]["project"]
            self.gerrit_reviewer = read_data["gerrit"][4]["reviewer"]

            self.zuul_img_version_tag = read_data["zuul"][0]["img_version_tag"]

            return self
