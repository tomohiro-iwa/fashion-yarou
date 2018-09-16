# -*- coding: utf-8 -*-

import os
import json
import pykintone

import logging

import boto3
from boto3.dynamodb.conditions import Key, Attr

from flask import (
    Flask, request, jsonify, abort
)
from cek import (
    Clova, SpeechBuilder, ResponseBuilder
)

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

# flask
app = Flask(__name__)

# logger
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# messagingapi

line_bot_api = LineBotApi('HqkmwVBgEnJn9Zvcefg649KXloFCVvz66opiP6M3ofiAkdyChR/6TPNVUCNO4tC3bprqlP7FsFqGDmP2umCoaBMip4x0HWzyKWur7yNujiszpVYlnrr81GNQGqA3DJGbjTQNtkAMNRHU+3xMI5PWsQdB04t89/1O/w1cDnyilFU=') # accesstoken
handler = WebhookHandler('18cb0127496d12942a5c83fb9b7566c2') #secrettoken

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=event.message.text))


# Clova
clova = Clova( application_id='com.fashion.clova', default_language='ja', debug_mode=False)
speech_builder = SpeechBuilder(default_language='ja')
response_builder = ResponseBuilder(default_language='ja')

@app.route('/', methods=['GET', 'POST'])
def lambda_handler(event=None, context=None):
    r = pykintone.app(
        "yarou", "5",
        "BAHSTXI4IJozgIShRbpZiEB16ERrg7AMPDuJ8nsf").select()

    if r.ok:
        records = r.records
        logger.info(json.dumps(records, ensure_ascii=False, indent=2))

    to = 'Ub89ae62d2101dcf736e4bd4bc33aac0e'
    line_bot_api.push_message(to, TextSendMessage(text='hello from Flask!'))

    return 'hello from Flask!'

@app.route('/clova', methods=['POST'])
def clova_service():
    resp = clova.route(request.data, request.headers)
    resp = jsonify(resp)
    # make sure we have correct Content-Type that CEK expects
    resp.headers['Content-Type'] = 'application/json;charset-UTF-8'
    return resp


'''
===================================
Clova RequestHandler 用メソッド
===================================
'''


@clova.handle.launch
def launch_request_handler(clova_request):
    # user_id = clova_request.user_id()
    user_id = 'Ub89ae62d2101dcf736e4bd4bc33aac0e'
    text = 'やっほー！今日のおすすめコーデを送信したぜ！'
    line_bot_api.push_message(user_id, TextSendMessage(text='秋　雨　長袖'))
    response = response_builder.simple_speech_text(text)
    response_builder.add_reprompt(response, text)
    return response


@clova.handle.default
def default_handler(clova_request):
    return clova.response('もう一度お願いします')


@clova.handle.intent('recommendIntent')
def find_gourmet_by_prefecture_intent_handler(clova_request):
    # user_id = clova_request.user_id()
    user_id = 'Ub89ae62d2101dcf736e4bd4bc33aac0e'
    logger.info('recommend method called!!')
    prefecture = clova_request.slot_value('prefecture')
    logger.info('Prefecture: %s', prefecture)
    response = None
    if prefecture is not None:
        try:
            # 都道府県名を判別できた場合
            response = makeRecommend(prefecture, user_id)
        except Exception as e:
            # 処理中に例外が発生した場合は、最初からやり直してもらう
            logger.error('Exception at make_gourmet_info_message_for: %s', e)
            text = '処理中にエラーが発生しました。もう一度はじめからお願いします。'
            response = response_builder.simple_speech_text(text)
    else:
        # 都道府県名を判別できなかった場合
        text = 'もう一度都道府県名を教えてください。'
        response = response_builder.simple_speech_text(text)
        response_builder.add_reprompt(response, text)
    # retrun
    return response

'''
===================================
Clova に返すResponse 生成用メソッド
===================================
'''


def makeRecommend(prefecture, user_id):
    logger.info('make_gourmet_info_message_by_prefecture method called!!')
    try:
        weather_info_list = []
        message = ''
        reprompt = None
        end_session = False
        if weather_info_list is None:
            # 天気情報が登録されていない場合
            message = '{}には天気情報が登録されていませんでした。他の都道府県で試してください。'.format(prefecture)
            reprompt = '今日滞在する都道府県名を教えてください。'
        else:
            message += 'やっほー！今日の{}のおすすめコーデを送信したぜ！'.format(prefecture)
            line_bot_api.push_message(user_id, TextSendMessage(text='都道府県　秋　雨　長袖'))
        # build response
        response = response_builder.simple_speech_text(message, end_session=end_session)
        if reprompt is not None:
            response = response_builder.add_reprompt(response, reprompt)
        return response
    except Exception as e:
        logger.error('Exception at make_gourmet_info_message_by_prefecture: %s', e)
        raise e

if __name__ == '__main__':
    app.run(debug=True)
