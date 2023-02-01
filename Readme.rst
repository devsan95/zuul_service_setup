Automatic deployment of Zuul service on Linsee servers.
========================================================

Prerequisties:
--------------
1. Install project by cloning the repo and navigate to setup.py path[``cd mn_scripts\tools\zuul_service_setup``] and do ``pip install zuul_setup`` (disconnect vpn to install packages)
2. Must be Connected to NOKIA VPN from here on (after step 1 in Prerequisties) i,e. start of script run to end of its execution.
3. Provide following details:
    - your Linsee machine, gerrit, database details in config.yaml file
    - host and port values in GearmanPluginConfig.xml file
    - details in zuul.conf and zuul_conf_merger.conf
    - details in layout.yaml
4. Run Script after ``cd mn_scripts/tools/zuul_service_setup/src/zuul_setup``
5. Run command for script: ``python script.py``

Need:
-----
1. Its Very difficult for a new joiner for setting up zuul service in one or two attempts, since there are lot of checkpoints in between apart 
  from sequential installation of containers as per confluence page - https://confluence.ext.net.nokia.com/pages/viewpage.action?pageId=1027891609

2. Also, This script handles pre-re-run environment of LinSEE host very effectively by cleaning old images/containers, logs directory, etc.
3. Approximately, It takes around 3-4 days to set this service for a first time user and around 30 min for a practioner. 
  This script does this in 5 minutes for both kind of users.

Approach:
---------
1. Automates Steps described for zuul service setup in https://confluence.ext.net.nokia.com/pages/viewpage.action?pageId=1027891609

2. Installs 6 containers sequentially.
3. Apart from just installing containers, this script takes off the burden of manual activities like:
  - creation of database on mysql server container
  - adding jenkins jobs
  - uploading gerrit public keys of 3 peers(for LinSEE host, zuul and merger container)
  - installing gearman plugin in jenkins and configuring its port.
  - checking health of services inside container
  - upgrading zuul version to latest mentioned
  - displaying all containers status
  - cleans all images/container before running script
  - creates new log directory ephermal everytime for smooth installation
  - configures LinSEE machine git to cache gerrit credentials to avoid repetetive prompts of login credentials
4. Detailed Execution log at Log_file.log can be used for debugging.

Benefits:
---------
1. Fresh installation every-time takes around 5 minutes.
2. No missing steps or incorrect configuration done.
3. Installation as per the confluence page.
4. Well tested for reliability for quick installation by any user.
5. Logs provide detailed installation procedure and we can point out errors if any.

Limitations
-----------
1. Currently, Script runs well only on Windows machines, Linux support will be added later.
2. Script is developed using python 3.9 and needs python versions >=3.7; hence lacks support for python 2.x versions, which are officially deprecated by today.
