Automatic deployment of Zuul service on Linsee servers.
========================================================

Prerequisties:
--------------
1. Install project by cloning the repo and navigate to setup.py path[cd "mn_scripts\tools\zuul_service_setup"] and do "pip install zuul_setup"
2. Must be Connected to NOKIA VPN from start of script run to end of execution
3. Provide following details:
    - your Linsee machine, gerrit, database details in config.yaml file
    - host and port values in GearmanPluginConfig.xml file
    - details in zuul.conf and zuul_conf_merger.conf
    - details in layout.yaml
4. Run Script after "cd mn_scripts/tools/zuul_service_setup/src/zuul_setup"
5. Run command for script: Python script.py

Need:
-----
- Its Very difficult for a new joiner for setting up zuul service in one or two attempts, since there are lot of checkpoints in between apart 
  from sequential installation of containers as per confluence page - https://confluence.ext.net.nokia.com/pages/viewpage.action?pageId=1027891609

- Also, This script handles re-run environment very effectively by cleaning old images/containers, files created, etc.
- Approximately, It takes around 3-4 days to set this service for a first time user and around 30 min for a practioner. 
  This script does this in 5 minutes for both kind of users.

Approach:
---------
- Automates Steps described for zuul service setup in https://confluence.ext.net.nokia.com/pages/viewpage.action?pageId=1027891609

- Every time, It cleans all previous containers/images and starts from fresh.
- Installs 6 containers sequentially.
- Handles configuring containers 
- Detailed Execution log at Log_file.log can be used for debugging.

Benefits:
---------
- Fresh installation every-time takes around 5 minutes.
- No missing steps or incorrect configuration done.
- Installation as per the confluence page.
- Well tested for reliability for quick installation by any user.
- Logs provide detailed installation procedure and we can point out errors if any.

Limitations
-----------
- Currently, Script runs well only on Windows machines, Linux support will be added later.
- Script is developed using python 3.9 and needs python versions >=3.7, hence lacks support for python 2.x versions.
