import json
import time
from os import environ as env
from slackclient import SlackClient
from ansible import utils
from ansible.module_utils import basic

'''
reference: https://serversforhackers.com/running-ansible-programmatically
'''

SLACK_TOKEN = 'SLACK_TOKEN' in env and env['SLACK_TOKEN']
SLACK_CHANNEL = 'SLACK_CHANNEL' in env and env['SLACK_CHANNEL']

slack_client = SlackClient(SLACK_TOKEN)
slack_message = None

# the message
log_message = ''

def banner(msg):
    # output trailing stars
    width = 78 - len(msg)
    if width < 3:
        width = 3
    filler = '*' * width
    return '\n%s %s ' % (msg, filler)

def append_to_log(msg):
    # append message to log_message
    global log_message
    log_message += msg + "\n"

def send_to_slack():
    global log_message
    global slack_message
    # send slack message
    try:
        slack_message = json.loads(slack_client.api_call('chat.postMessage', **{
            'text': '```{}```'.format(log_message),
            'channel': SLACK_CHANNEL,
            'as_user': True
        }))
    except:
        pass

def update_to_slack():
    global log_message
    global slack_message
    # update slack message
    try:
        slack_message = json.loads(slack_client.api_call('chat.update', **{
            'text': '```{}```'.format(log_message),
            'ts': slack_message['ts'],
            'channel': slack_message['channel']
        }))
    except:
        pass
        
class CallbackModule(object):
    """
    An ansible callback module for sending ansible output to slack
    """

    def runner_on_failed(self, host, res, ignore_errors=False):
        results2 = res.copy()
        results2.pop('invocation', None)
        item = results2.get('item', None)
        if item:
            msg = 'failed: [%s] => (item=%s) => %s' % (host, item, utils.jsonify(results2))
        else:
            msg = 'failed: [%s] => %s' % (host, utils.jsonify(results2))
        append_to_log(msg)
        update_to_slack()

    def runner_on_ok(self, host, res):
        results2 = res.copy()
        results2.pop('invocation', None)
        item = results2.get('item', None)
        changed = results2.get('changed', False)
        ok_or_changed = 'ok'
        if changed:
            ok_or_changed = 'changed'
        msg = '%s: [%s] => (item=%s)' % (ok_or_changed, host, item)
        append_to_log(msg)
        update_to_slack()

    def runner_on_skipped(self, host, item=None):
        if item:
            msg = 'skipping: [%s] => (item=%s)' % (host, item)
        else:
            msg = 'skipping: [%s]' % host
        append_to_log(msg)
        update_to_slack()

    def runner_on_unreachable(self, host, res):
        item = None
        if type(res) == dict:
            item = res.get('item', None)
            if isinstance(item, unicode):
                item = utils.unicode.to_bytes(item)
            results = basic.json_dict_unicode_to_bytes(res)
        else:
            results = utils.unicode.to_bytes(res)
        host = utils.unicode.to_bytes(host)
        if item:
            msg = 'fatal: [%s] => (item=%s) => %s' % (host, item, results)
        else:
            msg = 'fatal: [%s] => %s' % (host, results)
        append_to_log(msg)
        update_to_slack()

    def runner_on_no_hosts(self):
        append_to_log('FATAL: no hosts matched or all hosts have already failed -- aborting')
        update_to_slack()

    def playbook_on_task_start(self, name, is_conditional):
        name = utils.unicode.to_bytes(name)
        msg = 'TASK: [%s]' % name
        if is_conditional:
            msg = 'NOTIFIED: [%s]' % name
        append_to_log(banner(msg))
        update_to_slack()

    def playbook_on_setup(self):
        append_to_log(banner('GATHERING FACTS'))
        update_to_slack()

    def playbook_on_play_start(self, name):
        append_to_log(banner('PLAY [%s]' % name))
        send_to_slack()

    def playbook_on_stats(self, stats):
        """Complete: Flush log to database"""
        hosts = stats.processed.keys()
        append_to_log(banner('PLAY RECAP'))
        for h in hosts:
            t = stats.summarize(h)
            msg = "Host: %s, ok: %d, failures: %d, unreachable: %d, changed: %d, skipped: %d" % (h, t['ok'], t['failures'], t['unreachable'], t['changed'], t['skipped'])
            append_to_log(msg)
        update_to_slack()
