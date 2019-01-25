import json
import requests
import io
MESSAGE_MAX_LENGTH = 4096


def get_response(*args, **kwargs):
    resp = requests.get(*args, **kwargs)
    if resp.ok:
        return json.loads(resp.content).get('result')


class Bot:
    def __init__(self, token, offset):
        self.token = token
        self.offset = offset
        self.first_name = ''
        self.last_name = ''
        self.username = ''

    @property
    def base_url(self):
        return 'https://api.telegram.org/bot{}/'.format(self.token)

    def update(self, *, timeout=60):
        url = self.base_url + "getUpdates"
        payload = {'offset': self.offset or "", 'timeout': timeout}
        updates = get_response(url, params=payload)
        self.offset = updates[-1]['update_id'] + 1
        return updates

    def update_information(self):
        url = self.base_url + 'getMe'
        resp = requests.get(url)
        if resp:
            self.username = resp.get('username')
            self.first_name = resp.get('first_name')
            self.last_name = resp.get('last_name')
            self.save()

    def get_group_member(self, participant_group, participant):
        url = self.base_url + 'getChatMember'
        payload = {'chat_id': participant_group, 'user_id': participant}
        return requests.get(url, params=payload)

    def send_message(self,
                     group: str or int,
                     text,
                     *,
                     parse_mode='HTML',
                     reply_to_message_id=None):
        if not (isinstance(group, str) or isinstance(group, int)):
            group = group.telegram_id

        if parse_mode == 'Markdown':
            text = text.replace('_', '\_')
        blocks = []
        if len(text) > MESSAGE_MAX_LENGTH:
            current = text
            while len(current) > MESSAGE_MAX_LENGTH:
                f = current.rfind('. ', 0, MESSAGE_MAX_LENGTH)
                blocks.append(current[:f + 1])
                current = current[f + 2:]
            blocks.append(current)
        else:
            blocks.append(text)
        resp = []
        for message in blocks:
            url = self.base_url + 'sendMessage'
            payload = {
                'chat_id':
                group,
                'text':
                message.replace('<', '&lt;').replace('\\&lt;', '<'),
                'reply_to_message_id':
                reply_to_message_id if not resp else resp[-1].get('message_id')
            }
            if parse_mode:
                payload['parse_mode'] = parse_mode
            resp_c = requests.get(url, params=payload)
            resp.append(resp_c)
        return resp

    def send_image(self,
                   participant_group: 'text/id or group',
                   image_file: io.BufferedReader,
                   *,
                   caption='',
                   reply_to_message_id=None):
        if not (isinstance(participant_group, str)
                or isinstance(participant_group, int)):
            participant_group = participant_group.telegram_id
        url = self.base_url + 'sendPhoto'
        payload = {
            'chat_id': participant_group,
            'caption': caption,
            'reply_to_message_id': reply_to_message_id,
        }
        files = {'photo': image_file}
        resp = requests.get(
            url,
            params=payload,
            files=files,
            headers={"Content-Type": "application/json"})
        return resp

    def delete_message(self, participant_group: str, message_id: int or str):
        if not (isinstance(participant_group, str)
                or isinstance(participant_group, int)):
            participant_group = participant_group.telegram_id
        url = self.base_url + 'deleteMessage'
        payload = {'chat_id': participant_group, 'message_id': message_id}
        resp = requests.get(url, params=payload)
        return resp

    def __str__(self):
        return '[BOT] {}'.format(self.first_name or self.username
                                 or self.last_name)

    class Meta:
        verbose_name = 'Bot'
        db_table = 'db_bot'