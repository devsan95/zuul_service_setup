import logging
import re
import subprocess
import time

import paramiko
from scp import SCPClient

logging.basicConfig(filename="Log_file.log",
                    format='%(asctime)s:%(levelname)s:%(message)s',
                    filemode='w')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

ssh.connect('10.157.3.252', port=22, username='root',  # put your remote machine IP address, username and password.
            password='Santosh@123', timeout=3)

SSH_KEYS = dict()


def check_docker():
    # check existing docker
    logger.info("Checking docker setup now..")
    check_docker_command = "docker --version"
    (stdin, stdout, stderr) = ssh.exec_command(check_docker_command)
    if stdout.channel.recv_exit_status():
        logger.info("Docker not found, Installing docker..")
        command = """
                  sudo yum remove docker \
                  docker-client \
                  docker-client-latest \
                  docker-common \
                  docker-latest \
                  docker-latest-logrotate \
                  docker-logrotate \
                  docker-engine"""

        repository_setup_command = """
        sudo yum install -y yum-utils \
        sudo yum-config-manager \
        --add-repo \
        https://download.docker.com/linux/centos/docker-ce.repo"""

        docker_engine_command = """sudo yum install docker-ce docker-ce-cli containerd.io docker-compose-plugin"""

        start_docker_command = "sudo systemctl start docker"

        hello_world_container_command = "sudo docker run hello-world"

        total_command = f"""{command}&&{repository_setup_command}&&{docker_engine_command}&&{start_docker_command}&&{hello_world_container_command}"""

        (stdin, stdout, stderr) = ssh.exec_command(total_command)
        logger.info(f"stdout is {stdout.read()}")
        logger.info(
            f"Docker check exited with exit code {stdout.channel.recv_exit_status()}")
    else:
        logger.info("Found existing docker. Skipping docker installation.")
        (stdin, stdout, stderr) = ssh.exec_command(
            "sudo systemctl start docker")


def docker_registry_login():
    logger.info("Logging in Docker registries esisoj70 and artifactory-espoo1..")
    registry_1 = "docker login zuul-local.esisoj70.emea.nsn-net.net"
    registry_2 = "docker login zuul-local.artifactory-espoo1.int.net.nokia.com"

    (stdin, stdout, stderr) = ssh.exec_command(registry_1)
    logger.info(f"Log in status: {stdout.read()}")
    (stdin, stdout, stderr) = ssh.exec_command(registry_2)
    logger.info(f"Log in status: {stdout.read()}")


def make_workspace():
    logger.info("Removing existing /ephermal directory if present..")
    (stdin, stdout, stderr) = ssh.exec_command('rm -rf /ephemeral/')
    if not stdout.channel.recv_exit_status():
        logger.info("Successfully removed existing workspace.")

    logger.info('Creating new workspace..')
    (stdin, stdout, stderr) = ssh.exec_command('mkdir /ephemeral/git -p')
    (stdin, stdout, stderr) = ssh.exec_command('mkdir /ephemeral/tmp')
    (stdin, stdout, stderr) = ssh.exec_command('mkdir /ephemeral/etc')
    (stdin, stdout, stderr) = ssh.exec_command('mkdir /ephemeral/log')
    (stdin, stdout, stderr) = ssh.exec_command('mkdir /ephemeral/zuul_mergers')
    (stdin, stdout, stderr) = ssh.exec_command('mkdir /ephemeral/jenkins')
    (stdin, stdout, stderr) = ssh.exec_command('mkdir /ephemeral/gerrit')
    (stdin, stdout, stderr) = ssh.exec_command('mkdir /ephemeral/git -p')
    (stdin, stdout, stderr) = ssh.exec_command('mkdir /ephemeral/git -p')
    (stdin, stdout, stderr) = ssh.exec_command('mkdir /ephemeral/git -p')
    (stdin, stdout, stderr) = ssh.exec_command('mkdir /ephemeral/git -p')
    # make directories executable
    (stdin, stdout, stderr) = ssh.exec_command('chmod 777 /ephemeral/jenkins')
    (stdin, stdout, stderr) = ssh.exec_command('chmod 777 /ephemeral/gerrit')
    (stdin, stdout, stderr) = ssh.exec_command('chmod 777 /ephemeral/git')
    (stdin, stdout, stderr) = ssh.exec_command('chmod 777 /ephemeral/tmp')
    (stdin, stdout, stderr) = ssh.exec_command('chmod 777 /ephemeral/etc')
    (stdin, stdout, stderr) = ssh.exec_command('chmod 777 /ephemeral/log')
    (stdin, stdout, stderr) = ssh.exec_command('chmod 777 /ephemeral/gearman')
    (stdin, stdout, stderr) = ssh.exec_command(
        'chmod 777 /ephemeral/zuul_mergers')

    (stdin, stdout, stderr) = ssh.exec_command('ls /ephemeral/zuul_mergers')
    if not stdout.channel.recv_exit_status():
        add_ssh_keys_host_machine()
        logger.info("Successfully created new workspace.")


def add_ssh_keys_host_machine():
    (stdin, stdout, stderr) = ssh.exec_command("rm -f  ~/.ssh/new_id_rsa*")
    (stdin, stdout, stderr) = ssh.exec_command(
        "ssh-keygen -t rsa -f ~/.ssh/new_id_rsa -N ''")
    (stdin, stdout, stderr) = ssh.exec_command("cat ~/.ssh/new_id_rsa.pub")
    filter_ssh_key("host", stdout.read())


def install_zuul():
    logger.info("Installing Zuul container now..")
    zuul_install_command = """docker run -itd --restart always --log-opt max-size=2g --log-opt max-file=1 --privileged --name zuul-server -v /ephemeral/etc/:/etc/zuul/ -v /ephemeral/git/:/ephemeral/zuul/git/ -v /ephemeral/log/:/ephemeral/log/zuul/ -v /ephemeral/tmp/:/tmp/ --net host zuul-local.artifactory-espoo1.int.net.nokia.com/zuul-images/zuul-server:v2.7.7.1"""
    (stdin, stdout, stderr) = ssh.exec_command(zuul_install_command)
    if stdout.channel.recv_exit_status():
        logger.info(
            "Issue in installing zuul, check name of zuul server if already exists in running containers.")
    else:
        logger.info(
            f"Installed zuul container, Container id : {stdout.read()}")
        logger.info("Configuring zuul container..")
        # generate ssh key using RSA
        logger.info("Removing existing ssh keys..")
        (stdin, stdout, stderr) = ssh.exec_command(
            "docker exec -w  ~/.ssh/ zuul-server rm -f  ~/.ssh/id_rsa*")
        (stdin, stdout, stderr) = ssh.exec_command(
            "docker exec -w  ~/.ssh/ zuul-server ssh-keygen -t rsa -f ~/.ssh/id_rsa -N ''")
        (stdin, stdout, stderr) = ssh.exec_command(
            "docker exec -w  ~/.ssh/ zuul-server cat id_rsa.pub")
        filter_ssh_key("zuul", stdout.read())

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
            "docker exec -w /root/zuul zuul-server  \\cp -uv /root/zuul/etc/status/public_html/* /ephemeral/zuul/www/")
        logger.info(stdout.read())
        (stdin, stdout, stderr) = ssh.exec_command(
            "docker exec -w ~ zuul-server  git clone 'https://gerrit.ext.net.nokia.com/gerrit/MN/SCMTA/zuul/zuul-dockers'")
        logger.info(stdout.read())
        (stdin, stdout, stderr) = ssh.exec_command("cd zuul-dockers")
        if not stdout.channel.recv_exit_status():
            logger.info("Successfully cloned zuul-dockers repository")
        else:
            logger.error(
                "zuul-dockers repository not cloned successfully to host machine")
        (stdin, stdout, stderr) = ssh.exec_command(
            "docker exec -w ~ zuul-server  \\cp -uv ./zuul-dockers/rootfs/etc/zuul/* /etc/zuul/")
        logger.info(stdout.read())
        if not stdout.channel.recv_exit_status() and configure_zuul_conf_layout() == -1:
            (stdin, stdout, stderr) = ssh.exec_command(
                                                    "docker exec -w /root zuul-server zuul-server -c /etc/zuul/zuul.conf -l /etc/zuul/layout.yaml")
            (stdin, stdout, stderr) = ssh.exec_command(
                                                    "docker exec -w /root zuul-server zuul-launcher -c /etc/zuul/zuul.conf")
            logger.info("Successfully configured zuul container.")
        else:
            logger.error(
                f"Issue in configuring zuul container: \n {stderr.read()}")


def clean_all():
    logger.info("Cleaning existing contianers and images..")
    command = "docker stop $(docker ps -aq);docker rm $(docker ps -aq);docker rmi $(docker image ls -aq)"

    (stdin, stdout, stderr) = ssh.exec_command(command)
    if not stdout.channel.recv_exit_status():
        logger.info("Successfully cleaned all images & containers.")
    elif stdout.channel.recv_exit_status() == 1:
        logger.info("No containers and images found to clean.\n")
    else:
        logger.error("Issue in cleaning containers or images.")


def install_mysql():
    logger.info("Installing Mysql container..")
    command = """docker run --restart always --name mysql -v /ephemeral/mysql:/var/lib/mysql -p 3306:3306 -e MYSQL_ROOT_PASSWORD=5gzuul_pwd -d zuul-local.artifactory-espoo1.int.net.nokia.com/zuul-images/mysql:v1.0 --character-set-server=utf8 --collation-server=utf8_general_ci"""
    (stdin, stdout, stderr) = ssh.exec_command(command)
    if not stdout.channel.recv_exit_status():
        logger.info("Successfully installed Mysql.")
        print(
            "IN Heidisql client application, connect to linux host machine, use Network type Mariadb or Mysql(TCP/Ip), \
                            Library libmariadb.dll, port 3306, username and password of linux host machine.")
        subprocess.Popen(r"C:\\Program Files\\HeidiSQL\\heidisql.exe")
        timer("Create database 'test_zuul' in HeidiSql application")
    else:
        logger.error(stderr.read())


def install_gearman():
    logger.info("Installing gearman container now..")
    command = "docker run -d --restart always --log-opt max-size=2g --log-opt max-file=1 -p 4731:4730 --name gearman -v /ephemeral/zuul_t/gearman:/root/mn_scripts/gearman -v /ephemeral/zuul_t/log/gearman:/ephemeral/log/zuul zuul-local.artifactory-espoo1.int.net.nokia.com/zuul-images/gearman:v1.0"
    (stdin, stdout, stderr) = ssh.exec_command(command)
    if not stdout.channel.recv_exit_status():
        logger.info("Successfully installed gearman.")
    else:
        logger.error(stderr.read())


def filter_ssh_key(machine, output):
    output = str(output)
    result = re.search(r'ssh-rsa.+', output)
    if result.group():
        key = str(result).split('\\n')[0]
        SSH_KEYS[machine] = key
    else:
        logger.info(f"error in filtering ssh key for {machine}")


def format_result(output):
    output = str(output)
    result = '\n'.join(output.split("\\n"))
    logger.info('\n'+result)


def install_merger():
    logger.info("Installing Merger container now.. ")
    command = """docker run -itd --restart always --privileged -p 9191:9091 -p 8081:80 -p 8122:22 -v /ephemeral/zuul_mergers/merger_1/log/:/ephemeral/log/zuul/ -v /ephemeral/zuul_mergers/merger_1/git/:/ephemeral/zuul/git/ --name merger zuul-local.artifactory-espoo1.int.net.nokia.com/zuul-images/zuul-merger:v1.13"""
    (stdin, stdout, stderr) = ssh.exec_command(command)
    if not stdout.channel.recv_exit_status():
        logger.info("Successfully installed merger.")
    else:
        logger.error(stderr.read())
    # generate ssh key using RSA
    logger.info("Removing existing ssh keys..")
    (stdin, stdout, stderr) = ssh.exec_command(
        "docker exec -w  ~/.ssh/ merger rm -f  ~/.ssh/id_rsa*")
    (stdin, stdout, stderr) = ssh.exec_command(
        "docker exec -w  ~/.ssh/ merger ssh-keygen -t rsa -f ~/.ssh/id_rsa -N ''")
    (stdin, stdout, stderr) = ssh.exec_command(
        "docker exec -w  ~/.ssh/ merger cat id_rsa.pub")
    filter_ssh_key("merger", stdout.read())
    if configure_merger_conf_layout() == -1:
        (stdin, stdout, stderr) = ssh.exec_command(
            "docker exec -w  /root merger zuul-merger -c /etc/zuul/zuul.conf")
        logger.info("Successfully configured Merger container.")
    else:
        logger.info("Issue in configuring Merger container.")


def install_jenkins():
    logger.info("Installing Jenkins container now..")
    command = """docker pull jenkins/jenkins:lts;docker run -itd --restart always -p 8080:8080 -p 50000:50000 --name jenkins -v /ephemeral/jenkins/:/var/jenkins_home jenkins/jenkins:lts"""
    (stdin, stdout, stderr) = ssh.exec_command(command)
    if not stdout.channel.recv_exit_status():
        logger.info("Successfully installed jenkins.")
    else:
        logger.error(stderr.read())


def install_gerrit():
    logger.info("Installing gearman container now..")
    command = """docker run -d --restart always --name gerrit -p 8180:8080 -p 29418:29418 -v /ephemeral/gerrit:/var/gerrit/review_site -e GERRIT_INIT_ARGS='--install-all-plugins' -e GITWEB_TYPE=gitiles -e http_proxy=http://10.158.100.1:8080 -e https_proxy=http://10.158.100.1:8080 -e AUTH_TYPE=DEVELOPMENT_BECOME_ANY_ACCOUNT -e SMTP_SERVER='webmail-emea.nsn-intra.net' -e HTTPD_LISTENURL='proxy-http://*:8080' -e WEBURL='http://gerrit.zuul.5g.dynamic.nsn-net.net' zuul-local.esisoj70.emea.nsn-net.net/zuul-images/gerrit"""
    (stdin, stdout, stderr) = ssh.exec_command(command)
    if not stdout.channel.recv_exit_status():
        logger.info("Successfully installed gerrit.")
    else:
        logger.error(stderr.read())


def configure_zuul_conf_layout():
    layout_file = "layout.yaml"
    config_file = "zuul.conf"

    command = "docker cp /root/layout.yaml zuul-server:/etc/zuul/layout.yaml; docker cp /root/zuul.conf zuul-server:/etc/zuul/zuul.conf"
    scp = SCPClient(ssh.get_transport())
    scp.put(layout_file, '/root/layout.yaml')
    scp.put(config_file, '/root/zuul.conf')
    (stdin, stdout, stderr) = ssh.exec_command("find /root -name zuul.conf")
    if stdout.channel.recv_exit_status():
        logger.error(
            "zuul.conf or layout.yaml file transfer not happened to host machine")
    else:
        logger.info(
            " Successfully transfered zuul.conf and layout.yaml to host machine.")
    (stdin, stdout, stderr) = ssh.exec_command(command)
    if not stdout.channel.recv_exit_status():
        logger.info(
            "Successfully copied zuul.conf and layout.yaml to zuul container.")
        return -1
    else:
        logger.error(stderr.read())


def configure_merger_conf_layout():
    config_file_merger = "zuul_conf_merger.conf"
    scp = SCPClient(ssh.get_transport())
    scp.put(config_file_merger, '/root/zuul_conf_merger.conf')
    (stdin, stdout, stderr) = ssh.exec_command(
        "find /root -name zuul_conf_merger.conf")
    if stdout.channel.recv_exit_status():
        logger.error("zuul_conf_merger file transfer not happened")
    else:
        logger.info(" Successfully transfered zuul_conf_merger file.")

    command = "docker cp /root/layout.yaml merger:/etc/zuul/layout.yaml; docker cp /root/zuul_conf_merger.conf merger:/etc/zuul/zuul.conf"
    (stdin, stdout, stderr) = ssh.exec_command(command)
    if not stdout.channel.recv_exit_status():
        logger.info(
            "Successfully copied config and layout.yaml to merger container.")
        return -1
    else:
        logger.error(stderr.read())


def check_status():
    command = "docker ps --format '{{ .Names }} {{ .Status }}'"
    (stdin, stdout, stderr) = ssh.exec_command(command)
    if not stdout.channel.recv_exit_status():
        logger.info(
            f"Displaying overall containers.. please check.\n{format_result(stdout.read())}")
    else:
        logger.error(stderr.read())


def timer(s):
    logger.info("Refer Terminal.")
    key = int(input(f"{s}, press 0 key once after completion : "))
    if key == 0:
        print("Refer to Log file now.")
        return
    else:
        timer(s)


def configure_jenkins():
    jenkins_plugins_file = "plugins.txt"
    logger.info("Jenkins Setup now..")
    logger.info("find jenkins admin password in jenkins container at /ephemeral/jenkins/secrets/initialAdminPassword file in zuul-server container")
    (stdin, stdout, stderr) = ssh.exec_command(
        "cat /ephemeral/jenkins/secrets/initialAdminPassword")
    admin_password = stdout.read()
    logger.info(f"Jenkins Admin Password is :{admin_password}")
    scp = SCPClient(ssh.get_transport())
    scp.put(jenkins_plugins_file, '/root/plugins.txt')
    (stdin, stdout, stderr) = ssh.exec_command("find /root -name plugins.txt")
    if stdout.channel.recv_exit_status():
        logger.error("plugins.txt file transfer not happened to host machine")
    else:
        logger.info(" Successfully transfered plugins.txt to host machine.")
    command = "docker cp /root/plugins.txt jenkins:/var/jenkins_home/plugins.txt"
    (stdin, stdout, stderr) = ssh.exec_command(command)
    if not stdout.channel.recv_exit_status():
        logger.info("Successfully copied plugins.txt to jenkins container.")
    else:
        logger.error(stderr.read())
    (stdin, stdout, stderr) = ssh.exec_command(
        "docker exec -w /var/jenkins_home/ jenkins jenkins-plugin-cli --plugins gearman-plugin:0.6.0")
    if not stdout.channel.recv_exit_status():
        logger.info("Successfully installed gearman plugin.")
    else:
        logger.error(stderr.read())
    (stdin, stdout, stderr) = ssh.exec_command("docker restart jenkins")
    timer("configure linux host's ip address and gearman port(4731) for Gearman under Jenkins Configure System.")
    logger.info("Jenkins configuration done.")


def add_gerrit_ssh():
    logger.info(f"Now add following ssh keys to gerrit: ")
    for machine, key in SSH_KEYS.items():
        logger.info(f"{machine} {key}")
        logger.info(f"{machine} {key}")
        logger.info(f"{machine} {key}")
    timer("Create your gerrit account at http://gerrit-code.zuulqa.dynamic.nsn-net.net/ and add ssh keys of host, merger and zuul")


def restart_services_zuul_and_merger():
    (stdin, stdout, stderr) = ssh.exec_command(
        "docker exec zuul-server supervisorctl restart all")
    (stdin, stdout, stderr) = ssh.exec_command(
        "docker exec merger supervisorctl restart all")
    time.sleep(5)
    (stdin, stdout, stderr) = ssh.exec_command(
        "docker exec zuul-server supervisorctl status")
    logger.info(f"Zuul services status:\n {format_result(stdout.read())}")
    (stdin, stdout, stderr) = ssh.exec_command(
        "docker exec zuul-server supervisorctl status")
    logger.info(f"Merger services status:\n {format_result(stdout.read())}")


# Entry point of Script
clean_all()
check_docker()
docker_registry_login()
make_workspace()
install_mysql()
install_zuul()
install_merger()
install_gearman()
install_jenkins()
install_gerrit()
check_status()
configure_jenkins()
add_gerrit_ssh()
restart_services_zuul_and_merger()
logger.info("Finally, Check Zuul dashboard at 10.157.3.252 in URL")
