# slack-ansible-plugin

Slack integration with ansible callback plugin.

Every time you run your ansible playbook/runner, it will notify to slack.

### Usage
Set environment variable:
- export SLACK_TOKEN=[YOUR SLACK TOKEN]
- export SLACK_CHANNEL=[YOUR SLACK CHANNEL]

Move `slack-logger.py` to ansible callback plugins folder (default: `/usr/share/ansible_plugins/callback_plugins`)

Make sure your `ansible.cfg` callback plugins path refer to the correct one.
