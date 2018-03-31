from flask import g, Flask, request, abort, jsonify
import requests
import os
import re

ZAMMAD_TOKEN = os.environ.get('ZAMMAD_TOKEN', '')
MATTERMOST_TOKENS = os.environ.get('MATTERMOST_TOKENS', '').split(',')
COMPANY_DOMAIN = os.environ.get('COMPANY_DOMAIN', '')
ZAMMAD_DOMAIN = os.environ.get('ZAMMAD_DOMAIN', '')
ZAMMAD_DEFAULT_GROUP = os.environ.get('ZAMMAD_DEFAULT_GROUP', 'Users')

app = Flask(__name__)

def extract_option(_re, text):
    """Extracts and removes options"""
    match = re.search(_re,
                     text)
    match = match.groups()[0]
    text = re.sub(_re, '', text)
    return match, text


def extract_options_from_text(information_text):
    """Set of options to search for in text"""
    output = {}
    
    if '--customer=' in information_text:
        _re = r'--customer=(?P<text>[a-zA-Z]+)'
        customer, information_text = extract_option(_re, information_text)
        customer = '{}@{}'.format(customer, COMPANY_DOMAIN)
        output['customer'] = customer
    elif '--customer-email=' in information_text:
        _re = r"--customer-email=(?P<text>[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)"
        customer, information_text = extract_option(_re, information_text)
        output['customer'] = customer

    if '--assignee=' in information_text:
        _re = '--assignee=(?P<text>[a-zA-Z]+)'
        assignee, information_text = extract_option(_re, information_text)
        assignee = '{}@{}'.format(assignee, COMPANY_DOMAIN)
        output['assignee'] = assignee
    elif '--assignee-email=' in information_text:
        _re = r"--assignee-email=(?P<text>[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)"
        assignee, information_text = extract_option(_re, information_text)
        output['assignee'] = assignee

    if '--group=' in information_text:
        _re = '--group=(?P<text>[\S]+)'
        group, information_text = extract_option(_re, information_text)
        output['group'] = assignee

    output['information_text'] = information_text

    return output

@app.route('/zammad/ticket', methods=['POST'])
def mm_zammad_create_ticket():
    """Creates a ticket from slack/mm slash command"""
    if request.method == 'POST':

        # verify mattermost is sender
        token = request.form.get('token')
        if token not in MATTERMOST_TOKENS:
            return jsonify({'status':'bad token'}), 401

        # get arguments from mattermost request
        text = request.form.get('text')
        user_name = request.form.get('user_name')
        user_name = '{}@{}'.format(user_name, COMPANY_DOMAIN)
        command = request.form.get('command')

        # default group for ticket
        group = ZAMMAD_DEFAULT_GROUP if ZAMMAD_DEFAULT_GROUP is not None else 'Users'

        # get opt args
        info = extract_options_from_text(text)
        assignee = info['assignee'] if 'assignee' in info.keys() else None
        customer = info['customer'] if 'customer' in info.keys() else user_name
        group = info['group'] if 'group' in info.keys() else group
        information_text = info['information_text']
        
        # post to Zammad
        post_body = {
            "title": information_text,
            "group": group,
            "customer": customer,
            "article": {
                "subject": information_text,
                "body": "{}".format(text),
                "type": "note",
                "internal": "false"
            },
            "note": "{}".format(text)
        }
        if assignee is not None:
            post_body['owner'] = assignee
        
        r = requests.post('{}/api/v1/tickets'.format(ZAMMAD_DOMAIN),
                          headers = {
                              'Authorization': 'Bearer {}'.format(ZAMMAD_TOKEN),
                              'Content-Type': 'application/json'},
                          json = post_body)

        response = {
            "text":"""### {} 
* Submitted: {} 
* Assigned Group: {}
* Owner: {}
* Customer: {}""".format(information_text,
                       user_name,
                       group,
                       str(assignee),
                       customer)}
        
        if (r.status_code < 200) | (r.status_code >= 300):
            return jsonify({
                "response_type": "ephemeral",
                "text": "```NRRRRGGGG``` Ticket not created successfully. Response from Zammad server: {}. Make sure you've correctly spelled your options.".format(str(r.status_code)),
                "attachments":[response]
            }), 200
        else:
            data = response.json()
            ticket_number = data.get('id','0')
            ticket_url = '{}/#tickets/zoom/{}'.format(ZAMMAD_DOMAIN,str(ticket_number))

        # success message
        return jsonify( {
            "response_type": "in_channel",
            "text": "```BLEEP BOOP``` Ticket Created Successfully ({})".format(ticket_url),
            "attachments": [response]
        }), 200
    else:
        abort(400)

if __name__ == '__main__':
    app.run(debug=True)
