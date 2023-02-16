from flask import Flask, request, Response
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from viberbot.api.messages.text_message import TextMessage
from viberbot.api.viber_requests import ViberMessageRequest
from viberbot.api.viber_requests import ViberSubscribedRequest
from viberbot.api.viber_requests import ViberUnsubscribedRequest
from sqlalchemy import create_engine
from datetime import datetime
from sqlalchemy.pool import NullPool

app = Flask(__name__)
viber = Api(BotConfiguration(
    name='PBS IT Club Bot',
    avatar='https://media-direct.cdn.viber.com/pg_download?pgtp=icons&dlid=0-04-01' +
           '-0fee2b0cdd17d907661f5cb2cf09640a787d74b4219e4872d0d5b4693c1d3224&fltp=jpg&imsz=0000',
    auth_token='token-id'
))


@app.route('/', methods=['POST'])
def incoming():
    if not viber.verify_signature(request.get_data(), request.headers.get('X-Viber-Content-Signature')):
        return Response(status=403)
    # this library supplies a simple way to receive a request object
    viber_request = viber.parse_request(request.get_data())
    if isinstance(viber_request, ViberMessageRequest):
        if viber_request.sender.id == '6cklxu1AVThdq/D+5m0==':
            admin_request(viber_request)
        else:
            handle_message(viber_request)
    if isinstance(viber_request, ViberSubscribedRequest):
        handle_sub(viber_request)
    if isinstance(viber_request, ViberUnsubscribedRequest):
        handle_remove(viber_request)
    return Response(status=200)


def send_admin_message(msg):
    viber.send_messages('6cklxu1AVThdq/D+5mmQ==', messages=[TextMessage(text=msg)])


def send_user_message(u_id, msg, name):
    full_msg = '''Hi {f_name}, {body}
    '''.format(f_name=name, body=msg)
    viber.send_messages(to=u_id, messages=[TextMessage(text=full_msg)])


def get_member_id():
    try:
        engine = create_engine(
            "mysql+pymysql://your_database"
            "/Table", poolclass=NullPool)
        conn = engine.connect()
        res = conn.execute('Select name,id from member_list').fetchall()
        conn.close()
        return list(res)
    except:
        pass


def admin_request(viber_request):
    try:
        day = datetime.today().date().day
        mess = str(viber_request.message.text)
        if mess.find(str(day + 99999)) != -1:
            if mess.find('-m') != -1:
                group_mes = mess[mess.find('=') + 1:]
                mem_list = get_member_id()
                if mem_list is not None:
                    for user_id in mem_list:
                        f_name = user_id[0]
                        temp = user_id[1]
                        send_user_message(temp, group_mes, f_name)
                        send_admin_message('Message sent to ' + str(temp)+str(f_name))
        else:
            send_admin_message('Auth Fail')
            return
        send_admin_message('Query Success')
    except Exception as e:
        send_admin_message(str(e))


def handle_sub(viber_request):
    try:
        engine = create_engine(
            "mysql+pymysql://"
            "/Table", poolclass=NullPool)
        conn = engine.connect()
        conn.execute("Insert into member_list values('{name}','{id}')".format(id=str(viber_request.user.id),
                                                                              name=viber_request.user.name))
        send_admin_message(str(viber_request.user.name + " has subscribed"))
        conn.close()
    except:
        pass
    viber.send_messages(viber_request.user.id, messages=[
        TextMessage(
            text='Thank you for subscribing to PBS IT Club Bot. ' + str(viber_request.user.name) + '. You will now '
                                                                                                   'receive alerts '
                                                                                                   'about events '
                                                                                                   'organized by '
                                                                                                   'IT Club.')])


def handle_remove(viber_request):
    user_id = viber_request.user_id
    try:
        engine = create_engine(
            "mysql+pymysql://database"
            "/Table", poolclass=NullPool)
        conn = engine.connect()
        conn.execute("Delete from member_list where id='{}'".format(user_id))
        conn.close()
        send_admin_message(str(viber_request.user_id) + " has been removed from DB")
    except Exception as e:
        send_admin_message("Remove Failed")


def handle_message(viber_request):
    try:
        engine = create_engine(
            "mysql+pymysql://database"
            "/Table", poolclass=NullPool)
        conn = engine.connect()
        res = conn.execute("Select * from member_list where id='{}'".format(viber_request.sender.id))
        id_arr = res.fetchall()
        if len(id_arr) == 0:
            conn.execute("Insert into member_list values('{name}','{id}')".format(id=str(viber_request.sender.id),
                                                                                  name=viber_request.sender.name))
            send_admin_message(
                str(viber_request.sender.name) + ' has been added to DB message= ' + str(viber_request.message.text))
            conn.close()
        elif len(id_arr) == 1:
            send_admin_message(
                'User ' + str(viber_request.sender.name) + " is sending message= " + str(viber_request.message.text))
            conn.close()
            return
    except Exception as e:
        send_admin_message(str(e))
    mes = '''
    Thank you for subscribing to PBS IT Club Bot.
    You will now receive alerts about events organized by IT Club.
    To unsubscribe:
    1. Open the bot.
    2. Tap on the 3-dots button in the top right and then on “Chat Info”
    3. Tap on "Stop messages"

    Regards,
    PBS IT Club
    '''

    viber.send_messages(viber_request.sender.id,
                        messages=[TextMessage(text="Hi " + str(viber_request.sender.name) + "," + mes
                                              )])
