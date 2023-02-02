#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Copyright 2023 Nokia
# Copyright 2023 Santoshkumar Vagga
# Copyright 2023 BGL 5G SCM Team

"""
Setup Zuul Service on a LinSEE maxhine
"""

import logging
import re
import time

import paramiko
from api4jenkins import Jenkins
from scp import SCPClient

from gerrit_rest import GerritRestClient
from utilites import (SSH_KEYS, Input, clean, create_db, filter_ssh_key,
                      format_result, gearman, gerrit, jenkins, merger,
                      merger_conf, mysql, show_progress, total_cmd, zuul,
                      zuul_conf, zuuL_conf_all)

logging.basicConfig(filename="Log_file.log",
                    format="%(asctime)s:%(levelname)s: %(message)s",
                    filemode="w")
logger = logging.getLogger()
logger.setLevel(logging.INFO)

inp = Input().get_val()

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname=inp.linux_ip, port=inp.linux_port,
            username=inp.linux_user,
            password=inp.linux_password, timeout=5)
scp = SCPClient(transport=ssh.get_transport())  # type:ignore


def clean_all():
    """Clean all images and containers in linsee host"""
    logger.info("Cleaning existing containers and images..")
    (stdin, stdout, stderr) = ssh.exec_command(clean)
    exit_code = stdout.channel.recv_exit_status()
    if not exit_code:
        logger.info("Successfully cleaned all images & containers.")
    elif exit_code == 1:
        logger.info("No containers and images found to clean.\n")
    else:
        logger.error("Issue in cleaning containers or images.")


def check_docker():
    """check existing docker in linsee host, install if not found"""
    logger.info("Checking docker setup now..")
    check_docker_command = "docker --version"
    (stdin, stdout, stderr) = ssh.exec_command(check_docker_command)
    exit_code = stdout.channel.recv_exit_status()
    if exit_code:
        logger.info("Docker not found, Installing docker..")
        (stdin, stdout, stderr) = ssh.exec_command(total_cmd)
        if "Hello" in str(stdout.read()):
            logger.info("Successfully installed docker on linux host.")
        else:
            logger.error(f"Docker installation error: {stderr.read()}")
    else:
        logger.info("Found existing docker. Skipping docker installation.")
        (stdin, stdout, stderr) = ssh.exec_command(
            "sudo systemctl start docker")


def docker_registry_login():
    """Log in to Nokia"s image registry for pulling various images"""
    logger.info("Logging in image registries esisoj70 & artifactory-espoo1.")
    registry_1 = "docker login zuul-local.esisoj70.emea.nsn-net.net"
    registry_2 = "docker login zuul-local.artifactory-espoo1.int.net.nokia.com"
    (stdin, stdout, stderr) = ssh.exec_command(registry_1)
    exit_code = stdout.channel.recv_exit_status()
    if not exit_code:
        logger.info("Log in Ok for esisoj70 registry")
    else:
        logger.error("Log in failure for esisoj70 registry")
    (stdin, stdout, stderr) = ssh.exec_command(registry_2)
    if not exit_code:
        logger.info("Log in Ok for artifactory-espoo1 registry")
    else:
        logger.error("Log in failure for artifactory-espoo1 registry")


def upload_files():
    dest_path = "/root/folder"
    scp.put(r"zuul.conf", f"{dest_path}/zuul.conf")
    merger_conf_file = "zuul_conf_merger.conf"
    scp.put(merger_conf_file, f"{dest_path}/zuul_conf_merger.conf")
    scp.put(r"layout.yaml", f"{dest_path}/layout.yaml")
    gearman_file = "hudson.plugins.gearman.GearmanPluginConfig.xml"
    gearman_path = f"{dest_path}/{gearman_file}"
    scp.put(gearman_file, gearman_path)
    scp.put(r"query.sql", f"{dest_path}/query.sql")
    (stdin, stdout, stderr) = ssh.exec_command("chmod -r /root/folder")
    (stdin, stdout, stderr) = ssh.exec_command(f"cat {gearman_path}")
    exit_code = stdout.channel.recv_exit_status()
    if not exit_code:
        logger.info("Successfully uploaded config files to host.")
    else:
        logger.info("Error copying config file to host")


def make_workspace():
    """Remove and create workspace, copy files to linsee host"""
    logger.info("Removing existing /ephermal directory if present..")
    (stdin, stdout, stderr) = ssh.exec_command("rm -rf /ephemeral/")
    exit_code = stdout.channel.recv_exit_status()
    if not exit_code:
        logger.info("Successfully removed existing workspace /ephermal.")

    logger.info("Creating new workspace /ephermal ...")
    (stdin, stdout, stderr) = ssh.exec_command("mkdir /ephemeral/git -p")
    (stdin, stdout, stderr) = ssh.exec_command("mkdir /ephemeral/tmp")
    (stdin, stdout, stderr) = ssh.exec_command("mkdir /ephemeral/etc")
    (stdin, stdout, stderr) = ssh.exec_command("mkdir /ephemeral/log")
    (stdin, stdout, stderr) = ssh.exec_command("mkdir /ephemeral/zuul_mergers")
    (stdin, stdout, stderr) = ssh.exec_command("mkdir /ephemeral/jenkins")
    (stdin, stdout, stderr) = ssh.exec_command("mkdir /ephemeral/gerrit")
    (stdin, stdout, stderr) = ssh.exec_command("mkdir /ephemeral/gearman")
    (stdin, stdout, stderr) = ssh.exec_command("chmod 777 /ephemeral/jenkins")
    (stdin, stdout, stderr) = ssh.exec_command("chmod 777 /ephemeral/gerrit")
    (stdin, stdout, stderr) = ssh.exec_command("chmod 777 /ephemeral/git")
    (stdin, stdout, stderr) = ssh.exec_command("chmod 777 /ephemeral/tmp")
    (stdin, stdout, stderr) = ssh.exec_command("chmod 777 /ephemeral/etc")
    (stdin, stdout, stderr) = ssh.exec_command("chmod 777 /ephemeral/log")
    (stdin, stdout, stderr) = ssh.exec_command("chmod 777 /ephemeral/gearman")
    (stdin, stdout, stderr) = ssh.exec_command(
        "chmod 777 /ephemeral/zuul_mergers")

    (stdin, stdout, stderr) = ssh.exec_command("ls /ephemeral/zuul_mergers")
    exit_code = stdout.channel.recv_exit_status()
    if not exit_code:
        filter_ssh_key("host", generate_ssh_keys())
        git_cache_credentials = "git config --global credential.helper store"
        (stdin, stdout, stderr) = ssh.exec_command(git_cache_credentials)
        (stdin, stdout, stderr) = ssh.exec_command("rm -rf /root/folder")
        (stdin, stdout, stderr) = ssh.exec_command("mkdir /root/folder")
        (stdin, stdout, stderr) = ssh.exec_command("chmod 777 /root/folder")
        upload_files()
    else:
        msg = f"Error creating workspace in linsee host, {stderr.read()}"
        logger.error(msg)


def install_mysql():
    """Run, install & configure mysql services."""
    logger.info("Installing Mysql container..")
    try:
        (stdin, stdout, stderr) = ssh.exec_command(mysql)
        exit_code = stdout.channel.recv_exit_status()
        if not exit_code:
            logger.info("Successfully installed Mysql.")
            time.sleep(3)
            stdin, stdout, stderr = ssh.exec_command(
                "docker cp folder/query.sql mysql:/var/lib/mysql/query.sql")
            if not exit_code:
                logger.info("Successfully copied query.sql to mysql.")
            else:
                logger.info("Error in copying query.sql to mysql container.")
            stdin, stdout, stderr = ssh.exec_command(create_db)
            if not exit_code:
                logger.info("Successfully created database in mysql server.")
            else:
                logger.error("Error in creating database:{stderr.read()}")
        else:
            logger.error(
                "Error in installing mysql container, check command again.")
    except Exception as e:
        logger.error(f"Error in installing mysql: {e}")


def install_zuul():
    """Run, install & configure zuul-server services."""
    logger.info("Installing Zuul container now..")
    (stdin, stdout, stderr) = ssh.exec_command(zuul)
    exit_code = stdout.channel.recv_exit_status()
    if exit_code:
        logger.error(
            f"Issue in installing zuul, check command again. {stderr.read()}")
    else:
        logger.info(
            "Installed zuul container.")
        logger.info("Configuring zuul container..")
        filter_ssh_key("zuul", generate_ssh_keys("zuul-server"))

        (stdin, stdout, stderr) = ssh.exec_command(
            "docker exec -w /root/zuul zuul-server git pull")
        logger.info(stdout.read())
        (stdin, stdout, stderr) = ssh.exec_command(
            "docker exec -w /root/zuul zuul-server pip uninstall -y zuul")
        logger.info(stdout.read())
        (stdin, stdout, stderr) = ssh.exec_command(
            "docker exec -w /root/zuul zuul-server pip install .")
        logger.info(stdout.read())
        (stdin, stdout, stderr) = ssh.exec_command(
            'docker exec -w /root/zuul zuul-server  bash -c "\\cp -uv /root/zuul/etc/status/public_html/* /ephemeral/zuul/www/"')  # nopep8
        logger.info(stdout.read())
        (stdin, stdout, stderr) = ssh.exec_command(
            'docker exec -w /root zuul-server bash -c "git clone https://gerrit.ext.net.nokia.com/gerrit/MN/SCMTA/zuul/zuul-dockers"')  # nopep8
        (stdin, stdout, stderr) = ssh.exec_command(
            'docker exec -w /etc zuul-server bash -c "cd zuul"')
        if not exit_code:
            logger.info("Skipping zuul folder creation in /etc as it exists.")
        else:
            logger.info("Creating zuul folder at /etc in zuul.")
            (stdin, stdout, stderr) = ssh.exec_command(
                'docker exec -w /etc zuul-server bash -c "mkdir zuul"')
        cnt = 0
        for conf_file in zuuL_conf_all:
            command = f'docker exec zuul-server bash -c "cp ~/zuul-dockers/rootfs/etc/zuul/{conf_file} /etc/zuul"'  # nopep8
            (stdin, stdout, stderr) = ssh.exec_command(command)
            if exit_code:
                logger.error(F"Error copying config files to /etc/zuul: {stderr.read()}")  # nopep8
            else:
                cnt = cnt + 1
        if cnt != 7:
            logger.error(f"Copied {cnt} files of 7 config files at /etc/zuul")
        exit_code = stdout.channel.recv_exit_status()
        if not exit_code and configure_zuul_conf_layout() == -1:
            server_config_path = "zuul-server -c /etc/zuul/zuul.conf -l /etc/zuul/layout.yaml"  # nopep8
            (stdin, stdout, stderr) = ssh.exec_command(
                f"docker exec -w /root zuul-server {server_config_path}")
            launcher_config_path = "zuul-launcher -c /etc/zuul/zuul.conf"
            (stdin, stdout, stderr) = ssh.exec_command(
                f"docker exec -w /root zuul-server {launcher_config_path}")
            zuul_upgrade()
            logger.info("Successfully configured zuul container.")
        else:
            logger.error(
                f"Issue in configuring zuul container: \n {stderr.read()}")


def zuul_upgrade():
    """Upgrade Zuul version to latest one."""
    logger.info("Chekcing for Zuul upgrade..")
    (stdin, stdout, stderr) = ssh.exec_command(
        "docker exec -w /root zuul-server pip list | grep zuul")
    exit_code = stdout.channel.recv_exit_status()
    if not exit_code:
        res = re.findall(r"((\d\.){2}\d)", str(stdout.read()))
        zuul_version = None
        if res:
            zuul_version = res[0][0]
        else:
            logger.error("Error in fetching current zuul version.")
            return
        logger.info(f"Current Zuul Version is {zuul_version}")
        if str(zuul_version) == str(inp.zuul_img_version_tag):
            logger.info("Zuul version is up to date.")
            return
        else:
            logger.info(f"Upgrading Zuul to latest verison-{inp.zuul_img_version_tag}..")  # nopep8
            cmd1 = "docker exec -w /root/zuul/zuul zuul-server git pull --rebase"  # nopep8
            cmd2 = f"docker exec -w /root/zuul/zuul zuul-server git checkout tags/{inp.zuul_img_version_tag}"  # nopep8
            cmd3 = "docker exec -w /root/zuul/ zuul-server pip install ."
            (stdin, stdout, stderr) = ssh.exec_command(cmd1)
            (stdin, stdout, stderr) = ssh.exec_command(cmd2)
            (stdin, stdout, stderr) = ssh.exec_command(cmd3)
            zuul_upgrade()
    else:
        logger.info("Zuul not found, Installing now..")
        zuul_upgrade()


def generate_ssh_keys(container=None):
    """Generate public ssh keys for gerrit server"""
    if container:
        logger.info(f"Generating gerrit SSH keys for {container}..")
        remove_keys = f"docker exec -w ~/.ssh {container} "
        generate_keys = f"docker exec -w ~/.ssh {container} "
        show_keys = f"docker exec -w ~/.ssh {container} "
    else:
        container = "host"
        logger.info(f"Generating gerrit SSH keys for {container}..")
        remove_keys = ""
        generate_keys = ""
        show_keys = ""

    command = f"{remove_keys}rm -rf ~/.ssh/gerrit_rsa*"
    (stdin, stdout, stder) = ssh.exec_command(command)

    command = f"{generate_keys}ssh-keygen -t rsa -f ~/.ssh/gerrit_rsa -N ''"
    (stdin, stdout, stderr) = ssh.exec_command(command)

    command = f"{show_keys}cat ~/.ssh/gerrit_rsa.pub"
    (stdin, stdout, stderr) = ssh.exec_command(command)

    exit_code = stdout.channel.recv_exit_status()
    if not exit_code:
        ssh_key = stdout.read()
        logger.info(f"Successfully generated gerrit SSH keys for {container}.")
        return ssh_key
    else:
        msg = f"Error creating gerrit ssh keys for {container},{stderr.read()}"
        logger.error(msg)


def install_gearman():
    """Run, install & configure gearmang services."""
    logger.info("Installing gearman container now..")
    (stdin, stdout, stderr) = ssh.exec_command(gearman)
    exit_code = stdout.channel.recv_exit_status()
    if not exit_code:
        logger.info("Successfully installed gearman.")
    else:
        logger.error(stderr.read())


def show_services(container):
    """Show current status of all services in a container."""
    command = f"docker exec {container} supervisorctl restart all"
    (stdin, stdout, stderr) = ssh.exec_command(command)
    time.sleep(15)
    command = f"docker exec {container} supervisorctl status"
    (stdin, stdout, stderr) = ssh.exec_command(command)
    logger.info(f"Status of {container} Services:{format_result(stdout.read())}")  # nopep8


def install_merger():
    """Run, install & configure merger services."""
    logger.info("Installing Merger container now.. ")
    (stdin, stdout, stderr) = ssh.exec_command(merger)
    exit_code = stdout.channel.recv_exit_status()
    if not exit_code:
        logger.info("Successfully installed merger.")
    else:
        logger.error(stderr.read())
    filter_ssh_key("merger", generate_ssh_keys("merger"))
    if configure_merger_conf_layout() == -1:
        (stdin, stdout, stderr) = ssh.exec_command(
            "docker exec -w  /root merger zuul-merger -c /etc/zuul/zuul.conf")
        logger.info("Successfully configured Merger container.")
    else:
        logger.error("Issue in configuring Merger container.")


def install_jenkins():
    """Run, install & configure jenkins services."""
    logger.info("Installing Jenkins container now..")
    (stdin, stdout, stderr) = ssh.exec_command(jenkins)
    exit_code = stdout.channel.recv_exit_status()
    if not exit_code:
        logger.info("Successfully installed jenkins.")
    else:
        logger.error(stderr.read())


def install_gerrit():
    """Run, install & configure gerrit services."""
    logger.info("Installing gerrit container now..")
    (stdin, stdout, stderr) = ssh.exec_command(gerrit)
    exit_code = stdout.channel.recv_exit_status()
    if not exit_code:
        logger.info("Successfully installed gerrit.")
    else:
        logger.error(stderr.read())


def configure_zuul_conf_layout():
    """Configures zuul-server container"""
    logger.info("Working on Copying basic Zuul.conf and basic layout to zuul container.")  # nopep8
    (stdin, stdout, stderr) = ssh.exec_command(zuul_conf)
    exit_code = stdout.channel.recv_exit_status()
    if not exit_code:
        logger.info(
            "Successfully copied zuul.conf and layout.yaml to zuul container.")
        return -1
    else:
        logger.error(stderr.read())


def configure_merger_conf_layout():
    """Configures merger container"""
    logger.info("Copying zuul.conf and layout.yaml for merger container.")
    (stdin, stdout, stderr) = ssh.exec_command(merger_conf)
    exit_code = stdout.channel.recv_exit_status()
    if not exit_code:
        logger.info(
            "Successfully copied zuul.conf and layout.yaml to merger")
        return -1
    else:
        logger.error(stderr.read())


def check_status():
    """Gives current status of installed containers"""
    time.sleep(3)
    command = "docker ps --format '{{.Names}}  {{.Status}}'"
    (stdin, stdout, stderr) = ssh.exec_command(command)
    exit_code = stdout.channel.recv_exit_status()
    if not exit_code:
        logger.info(
            f"Displaying all containers {format_result(stdout.read())}")
    else:
        logger.error(stderr.read())


def add_jobs(admin_passwd):
    """Adds jenkins jobs"""
    logger.info("Trying to connect jenkins running on linux host..")
    xml = """<?xml version="1.1" encoding="UTF-8"?>
        <project>
        <builders>
            <hudson.tasks.Shell>
            <command>Executing . .</command>
            <command>sleep 60</command>
            </hudson.tasks.Shell>
        </builders>
        </project>"""
    client = Jenkins(url=f"http://{inp.linux_ip}:8080/",
                         auth=("admin", str(admin_passwd)))
    logger.info("Successfully connected to Jenkins.")
    logger.info("Adding 3 Jenkins Jobs, each sleeping for 60 sec..")
    cnt = 0
    try:
        cnt = cnt + 1
        client.create_job("job1", xml)
        client.create_job("job2", xml)
        client.create_job("job3", xml)
        logger.info("Added Jenkins jobs.")
    except Exception as e:
        if "job already exists" in str(e):
            return
        else:
            if cnt == 4:
                logger.error(f"Tried 3 times, Error connecting jenkins {e}. Unable to add 3 jobs.")  # nopep8
                return
            time.sleep(5)
            add_jobs(admin_passwd)


def configure_jenkins():
    """Configures jenkins container"""
    logger.info("Configuring Jenkins now..")
    logger.info("Installing Gearman Plugin in jenkins..")
    command = "jenkins-plugin-cli --plugins gearman-plugin:0.6.0"
    (stdin, stdout, stderr) = ssh.exec_command(
        f"docker exec -w /var/jenkins_home/ jenkins {command}")
    exit_code = stdout.channel.recv_exit_status()
    if not exit_code:
        logger.info("Successfully installed plugin-gearman in jenkins.")
        file = "hudson.plugins.gearman.GearmanPluginConfig.xml"
        source = f"/root/folder/{file}"
        dest = f"/var/jenkins_home/{file}"
        command = f"docker cp {source} jenkins:{dest}"
        (stdin, stdout, stderr) = ssh.exec_command(command)
        if not exit_code:
            logger.info(
                "Successfully copied GearmanPluginConfig to jenkins")
            logger.info(f"Restarting Jenkins..")
            (stdin, stdout, stderr) = ssh.exec_command("docker restart jenkins")
            if not exit_code:
                time.sleep(15)
                logger.info("Restarted Jenkins, Gearman plugin enabled.")
            else:
                logger.error(stderr.read())
        else:
            logger.error("Error in copying GearmanPluginConfig file")
    else:
        logger.error(stderr.read())
    logger.info("Getting jenkins initial admin password for reference..")
    password_path = "/ephemeral/jenkins/secrets/initialAdminPassword"
    (stdin, stdout, stderr) = ssh.exec_command(f"cat {password_path}")
    jenkins_admin_password = str(stdout.read()).split("\\n")[0].split("'")[1]
    logger.info(f"Jenkins Admin Password is :{jenkins_admin_password}")
    add_jobs(jenkins_admin_password)
    logger.info("Jenkins configuration done.")


def add_gerrit_ssh():
    """Adds generated public ssh keys to gerrit server"""
    rest_client = GerritRestClient(url=inp.gerrit_url,
                                   user=inp.gerrit_user,
                                   pwd=inp.gerrit_password, auth='basic')
    for key, value in SSH_KEYS.items():
        rest_client.add_ssh_key(account=inp.gerrit_user, pub_key=value)
        logger.info(f"Successfully added gerrit public ssh key for {key}.")

    logger.info("Now, After adding ssh keys, Restarting services of zuul & merger.")  # nopep8
    show_services("zuul-server")
    show_services("merger")
    logger.info("FINISHED: Zuul setup process")


logger.info("Performing fresh installation of all containers from scratch..")
Processes = [clean_all, check_docker, docker_registry_login, upload_files, make_workspace,
             install_mysql, install_zuul, install_merger, install_gearman,
             install_jenkins, install_gerrit, check_status, configure_jenkins,
             add_gerrit_ssh]
st = time.time()
show_progress(Processes)
et = time.time()
elapsed_time = round((et - st) / 60, 2)
logger.info(f"Zuul Setup automation has taken : {elapsed_time} minutes")
