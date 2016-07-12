# deploy.py

This package will clone git repository and constantly poll it for new tags.
When new tag is detected then it's checked out, have custom script run over it's directory, packaged into .zip and then
send via scp to remote server.

## Requirements


* Python 3.4+
* git 2.0+
* scp

It was tested only on OS X and Linux, but it should work on Windows if scp and git provided.

## Instructions

**Security tip: Create additional underprivileged user for that and chroot him in SSH config.**


First you have to create SSH key for your user and then add it to your git repository and upload host.
Then you need to save fingerprints of your servers locally:
```shell
ssh-keyscan REPOSITORY_HOST >> ~/.ssh/known_hosts
ssh-keyscan UPLOAD_HOST >> ~/.ssh/known_hosts
```

Now you are ready to start using *deploy.py*. Rename `config.ini.example` to `config.ini` and put there your
configuration.

* `sleep_seconds` - time in seconds to wait between checking repo for updates
* `repository_type` - here only git is supported
* `repository_url` - URL to repository
* `data_dir` - path where `deploy.py` will store it's files
* `name` - name of your project, will be used in .zip packages
* `scp_url` - URL for scp
* `script` - absolute path to your script ( more info below )
* `scp_settings` - command line options for scp

To simply run, go to deploy.py directory and run:
```
nohup python3 deploy.py &
```
, but it is strongly advised to run it as service job or in some tmux/screen.

### script

Supplied script will be run with temporary repository dir checked out to tag as CWD.
It's first argument will be tag and it's second argument will be CWD path.
