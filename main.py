import datetime
import logging
import os

import flask
import pytz
import requests

import secrets


logging.root.setLevel(logging.DEBUG)


app = flask.Flask(__name__)
app.config.update(
    DEBUG=os.environ.get('SERVER_SOFTWARE', '').startswith('Development'))


_TZ = pytz.timezone('US/Eastern')
_HUNT_DATES = [
    (_TZ.localize(datetime.datetime(2019, 1, 18, 12, 0, 0)),
     _TZ.localize(datetime.datetime(2019, 1, 20, 17, 0, 0))),
    (_TZ.localize(datetime.datetime(2019, 1, 17, 12, 0, 0)),
     _TZ.localize(datetime.datetime(2019, 1, 19, 17, 0, 0)))
]


def _format_timedelta(td):
    days = td.days
    hours = td.seconds // 3600
    minutes = (td.seconds % 3600) // 60
    seconds = td.seconds % 60
    return '{} days, {} hours, {} minutes, {} seconds'.format(
        days, hours, minutes, seconds)


def message_for_now():
    now = datetime.datetime.now().astimezone(_TZ)
    for start, end in _HUNT_DATES:
        if now < start:
            return "No.  You'll have to wait another {}.".format(
                _format_timedelta(start - now))
        elif now < end:
            return 'Yes!  HUNT HUNT HUNT!'
    else:
        return "Gosh, I'm not sure!  Ping @benkraft to update the bot."


@app.route('/slash', methods=['POST'])
def slash():
    try:
        return flask.jsonify({
            'response_type': 'in_channel',
            'text': message_for_now(),
        })
    except BaseException as e:
        logging.exception(e)
        return flask.jsonify({
            'text': ('Encountered an error: "%s"!  '
                     'Shout at @benkraft for help.' % e),
        })


@app.route('/auth', methods=['GET'])
def auth():
    res = requests.post('https://slack.com/api/oauth.access', {
        'code': flask.request.args.get('code'),
        'client_id': secrets.CLIENT_ID,
        'client_secret': secrets.CLIENT_SECRET,
    })
    try:
        logging.info(res.json())
        if res.json().get('ok'):
            return 'ok', 200
        else:
            return 'something went wrong :(', 500
    except Exception as e:
        logging.exception(e)
        return 'something went very wrong :((', 500
