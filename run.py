# -*- coding: utf-8 -*-

import os
import json
import pykintone
import requests

import logging

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
from pykintone import model


class PrefWeather(model.kintoneModel):

    def __init__(self):
        super(PrefWeather, self).__init__()
        self.prefecture = ""
        self.max_temp = 0.0
        self.min_temp = 0.0
        self.humidity = ""
        self.weather = ""
        self.url1 = ""
        self.url2 = ""

# flask
app = Flask(__name__)

# logger
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# messagingapi

line_bot_api = LineBotApi('HqkmwVBgEnJn9Zvcefg649KXloFCVvz66opiP6M3ofiAkdyChR/6TPNVUCNO4tC3bprqlP7FsFqGDmP2umCoaBMip4x0HWzyKWur7yNujiszpVYlnrr81GNQGqA3DJGbjTQNtkAMNRHU+3xMI5PWsQdB04t89/1O/w1cDnyilFU=') # accesstoken
handler = WebhookHandler('18cb0127496d12942a5c83fb9b7566c2') #secrettoken

# 取り合えずlineメッセージにはオウム返し
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
    # --- kintoneにuser_idが登録されているか確認する ---
    kint_data = 1
    if kint_data :
        text = 'やっほー！今日のおすすめコーデを送信したぜ！'
        line_bot_api.push_message(user_id, TextSendMessage(text='秋　雨　長袖'))
    else :
        text = '普段の活動場所を教えてください。どこどこに設定してと話しかけてください。'
    response = response_builder.simple_speech_text(text)
    response_builder.add_reprompt(response, text)
    return response


@clova.handle.default
def default_handler(clova_request):
    return clova.response('もう一度お願いします。わからないことがあれば使い方教えてと聞いてくださいな。')


@clova.handle.intent('recommendIntent')
def find_gourmet_by_prefecture_intent_handler(clova_request):
    #user_id = clova_request.user_id()
    user_id = 'Ub89ae62d2101dcf736e4bd4bc33aac0e'
    prefecture = clova_request.slot_value('prefecture')
    print(prefecture)

    r = pykintone.app(
        "yarou", "9",
        "wCOL14ThfaTvEUTBWKa7aQFmTFtU4qtToU7ZCRcV").select('prefecture = "{}"'.format(prefecture)).models(PrefWeather)[0]

    weather='{} humid:{}'.format(r.weather,r.humidity)
    temp='Max:{} min:{}'.format(r.max_temp,r.min_temp)
    sendFlexmessage(user_id,r.url1,r.url2,weather,temp)

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

    return response

@clova.handle.intent('settingIntent')
def setting_handler(clova_request):
    # user_id = clova_request.user_id()
    user_id = 'Ub89ae62d2101dcf736e4bd4bc33aac0e'
    user_local = clova_request.slot_value('user_local')

    # --- kintoneにidとユーザの地名を登録する処理 ---
    
    line_bot_api.push_message(user_id, TextSendMessage(text="banana"))
    text = '●●に設定されました。コーディネートを送信しました。次回からはスキルの起動時に●●の天気予報をもとにコーディネートいたします。また、遠出の際はどこどこ行くでとお伝えください。'
    response = response_builder.simple_speech_text(text)

    return response

@clova.handle.intent('weatherIntent')
def weather_handler(clova_request):
    # user_id = clova_request.user_id()
    user_id = 'Ub89ae62d2101dcf736e4bd4bc33aac0e'
    user_local = clova_request.slot_value('user_local')

    # --- kintoneからとユーザの地名をよむ処理 ---
    
    text = '快晴です'
    response = response_builder.simple_speech_text(text)

    return response

@clova.handle.intent('tempIntent')
def temp_handler(clova_request):
    # user_id = clova_request.user_id()
    user_id = 'Ub89ae62d2101dcf736e4bd4bc33aac0e'
    user_local = clova_request.slot_value('user_local')

    # --- kintonからユーザの地名を読む処理 ---
    
    text = '40どです'
    response = response_builder.simple_speech_text(text)

    return response


@clova.handle.intent("Clova.GuideIntent")
def guide_intent(clova_request):
    attributes = clova_request.session_attributes
    # The session_attributes in the current response will become session_attributes in the next request
    message = "今日何着てく？どこに行くか教えてな。"
    if 'HasExplainedService' in attributes:
        message = "大阪行くで、ゆうてみてな"

    response = response_builder.simple_speech_text(message)
    response.session_attributes = {'HasExplainedService': True}

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

def makeMessage(max_temp,min_temp,sunny):
    seasonstatus=0
    if(seasonstatus==0):
        if(max_temp<6):
            message="かなり寒い日です、カイロを持って行きましょう"
        elif(max_temp<11):
            message="かなり寒い日です、防寒具で対策しましょう"
        elif(max_temp<16):
            message="だいぶ寒くなりましたね、セーターやニットを着ても良いでしょう"
        elif(max_temp<21):
            if(seasonstatus==0):
                message="重ね着に最適な気温です、少し暖かい恰好をするといいでしょう"
            else:
                message="重ね着に最適な気温です。何かアウターを羽織るといいでしょう"
        elif(max_temp<26):
            if(seasonstatus==0 and sunny):
                message="今日は良い天気ですね、半袖でもいいでしょう"
            elif(seasonstatus==0):
                message="今日はあいにくの天気ですので、少し寒くなりそうです"
            elif(seasonstatus==1 and sunny):
                message="今日は良い天気ですね、秋のファッションを楽しみましょう"
            else:
                message="寒くなってきましたね、上着を用意しておくと安心ですよ"
        elif(max_temp<31):
            if(seasonstatus==0 and min_temp>=25):
                message="だんだん暑くなってきましたね、もうすぐ夏本番です"
            elif(seasonstatus==0 and min_temp<25):
                message="夜は肌寒くなる可能性があります、羽織り物があるといいかもしれません"
            elif(seasonstatus==1 and min_temp>=25):
                message="少し過ごし易くなりましたね、もうすぐ秋ですね"
            else:
                message="夜は肌寒くなる可能性があります、長袖でも良いかもしれません"
        elif(max_temp<36):
            message="今日は真夏日です、涼しい恰好で出かけましょう。"      
        else:
             message="今日は猛暑日です、熱中症に気をつけて下さいね。"
    return message

def sendFlexmessage(user_id,image,weather_image,weather,temp):
    url = 'https://api.line.me/v2/bot/message/push'
    dict={"a":user_id,"b":image,"c":weather_image,"d":weather,"e":temp}
    payload = '''
{
  "to": "a",
  "messages": [
    {
      "type":"flex",
      "altText":"this is FLEX",
      "contents":{
        "type": "bubble",
        "header": {
          "type": "box",
          "layout": "horizontal",
          "contents": [
            {
              "type": "text",
              "text": "chao",
              "weight": "bold",
              "color": "#aaaaaa",
              "size": "sm"
            }
          ]
        },
        "hero": {
          "type": "image",
          "url": "b",
          "size": "full",
          "aspectRatio": "20:13",
          "aspectMode": "cover"
        },
        "body": {
          "type": "box",
          "layout": "horizontal",
          "spacing": "md",
          "contents": [
            {
              "type": "box",
              "layout": "vertical",
              "flex": 1,
              "contents": [
                {
                  "type": "image",
                  "url": "c",
                  "aspectMode": "cover",
                  "aspectRatio": "4:3",
                  "size": "lg",
                  "gravity": "bottom"
                }
              ]
            },
            {
              "type": "box",
              "layout": "vertical",
              "flex": 2,
              "contents": [
                {
                  "type": "text",
                  "text": "d",
                  "gravity": "top",
                  "size": "md",
                  "flex": 1
                },
                {
                  "type": "separator"
                },
                {
                  "type": "text",
                  "text": "e",
                  "gravity": "center",
                  "size": "md",
                  "flex": 1
                },
                {
                  "type": "separator"
                }
              ]
            }
          ]
        }
      }
    }
  ]
}
'''#.format(**dict)
    jisyo = json.loads(payload)
    jisyo["to"]=user_id
    jisyo["messages"][0]["contents"]["hero"]["url"]=image
    jisyo["messages"][0]["contents"]["body"]["contents"][0]["contents"][0]["url"]=weather_image
    jisyo["messages"][0]["contents"]["body"]["contents"][1]["contents"][0]["text"]=weather
    jisyo["messages"][0]["contents"]["body"]["contents"][1]["contents"][2]["text"]=temp

    headers = {
        'content-type': 'application/json',
        'Authorization': 'Bearer HqkmwVBgEnJn9Zvcefg649KXloFCVvz66opiP6M3ofiAkdyChR/6TPNVUCNO4tC3bprqlP7FsFqGDmP2umCoaBMip4x0HWzyKWur7yNujiszpVYlnrr81GNQGqA3DJGbjTQNtkAMNRHU+3xMI5PWsQdB04t89/1O/w1cDnyilFU='
    }
    requests.post(url, data=json.dumps(jisyo), headers=headers)

def check_user(prefecture):
        r = pykintone.app(
        "yarou", "9",
        "wCOL14ThfaTvEUTBWKa7aQFmTFtU4qtToU7ZCRcV").select(('prefecture = "{}"').format(prefecture)).models(PrefWeather)

if __name__ == '__main__':
    app.run(debug=True)
