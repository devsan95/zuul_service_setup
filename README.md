# Automation Script for Zuul service setup on Linsee servers.

## Prerequisties:
1. Install following packages before execting this script(by disconnecting VPN)
    - paramiko : pip install paramiko
    - scp : pip install scp
    - api4jenkins: pip install api4jenkins

2. Must be Connected to NOKIA VPN from start of script run to end of execution
3. Provide your Linsee machine, gerrit, database details in config.yaml file
4. Run Script after "cd mn_scripts/tools/zuul_service_setup"
5. Run command for script: Python script.py

## Need:
- Its Very difficult for a new joiner for setting up zuul service in one or two attempts, since there are lot of checkpoints in between apart from sequential installation of containers. 
- Also, This script handles re-run environment very effectively by cleaning old images/containers, files created, etc.
- Approximately, It takes around 3-4 days to set this service for a first time user and around 30 min for a practioner. This script does this in 5 minutes for both kind of users.

## Approach:
- Automates Steps described for zuul service setup in https://confluence.ext.net.nokia.com/pages/viewpage.action?pageId=1027891609

- Every time, It cleans all previous containers/images and starts from fresh.
- Installs 6 containers sequentially.
- Handles configuring containers 
- Detailed Execution log at Log_file.log can be used for debugging.

## Benefits:
- Fresh installation every-time takes around 3 to 5 minutes.
- No missing steps or incorrect configuration done.
- Installation as per the confluence page.-
- Well tested for reliability for quick installation and demo to/by any user
- Logs provide detailed installation procedure and we can point out errors if any.

## Limitations:
- User must add script generated "SSH keys" of Zuul-server, merger and Linsee host (3 SSH Keys) to their  gerrit server displayed on Terminal at the end of execution.
- It only Setsup Environment, not a demo of Zuul working.
- Works only on Windows local machines, Linux support will be added later.
