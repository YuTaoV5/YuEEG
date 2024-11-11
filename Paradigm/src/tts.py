# coding=utf-8
import sys
import json

from urllib.request import urlopen
from urllib.request import Request
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.parse import quote_plus
import pyaudio
import wave

class DemoError(Exception):
    pass

# PER发音人选择, 基础音库：0为度小美，1为度小宇，3为度逍遥，4为度丫丫，
# 精品音库：5为度小娇，103为度米朵，106为度博文，110为度小童，111为度小萌，默认为度小美
# SPD语速，取值0-15，默认为5中语速
# PIT音调，取值0-15，默认为5中语调
# VOL音量，取值0-9，默认为5中音量
# AUE下载的文件格式, 3：mp3(default) 4： pcm-16k 5： pcm-8k 6. wav

def TTS(TEXT = "你好", PER=3, SPD=5, PIT = 5, VOL = 5, AUE = 6):
    API_KEY = ''
    SECRET_KEY = ''

    FORMATS = {3: "mp3", 4: "pcm", 5: "pcm", 6: "wav"}
    FORMAT = FORMATS[AUE]

    CUID = "123456PYTHON"

    TTS_URL = 'http://tsn.baidu.com/text2audio'

    """  TOKEN start """

    TOKEN_URL = 'http://aip.baidubce.com/oauth/2.0/token'
    SCOPE = 'audio_tts_post'  # 有此scope表示有tts能力，没有请在网页里勾选
    print("fetch token begin")
    params = {'grant_type': 'client_credentials',
              'client_id': API_KEY,
              'client_secret': SECRET_KEY}
    post_data = urlencode(params)
    post_data = post_data.encode('utf-8')
    req = Request(TOKEN_URL, post_data)
    try:
        f = urlopen(req, timeout=5)
        result_str = f.read()
    except URLError as err:
        print('token http response http code : ' + str(err.code))
        result_str = err.read()

    result_str = result_str.decode()

    print(result_str)
    result = json.loads(result_str)
    print(result)
    if ('access_token' in result.keys() and 'scope' in result.keys()):
        if not SCOPE in result['scope'].split(' '):
            raise DemoError('scope is not correct')
        print('SUCCESS WITH TOKEN: %s ; EXPIRES IN SECONDS: %s' % (result['access_token'], result['expires_in']))
        token =  result['access_token']


    tex = quote_plus(TEXT)  # 此处TEXT需要两次urlencode
    # print(tex)
    params = {'tok': token, 'tex': tex, 'per': PER, 'spd': SPD, 'pit': PIT, 'vol': VOL, 'aue': AUE, 'cuid': CUID,
              'lan': 'zh', 'ctp': 1}  # lan ctp 固定参数

    data = urlencode(params)
    # print('test on Web Browser' + TTS_URL + '?' + data)

    req = Request(TTS_URL, data.encode('utf-8'))
    has_error = False
    try:
        f = urlopen(req)
        result_str = f.read()

        headers = dict((name.lower(), value) for name, value in f.headers.items())

        has_error = ('content-type' not in headers.keys() or headers['content-type'].find('audio/') < 0)
    except  URLError as err:
        print('asr http response http code : ' + str(err.code))
        result_str = err.read()
        has_error = True

    save_file = "error.txt" if has_error else 'result.' + FORMAT
    with open(save_file, 'wb') as of:
        of.write(result_str)

    if has_error:

        result_str = str(result_str, 'utf-8')
        print("tts api  error:" + result_str)

    print("result saved as :" + save_file)

    chunk = 1024
    wf = wave.open('result.'+ FORMAT, 'rb')
    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    data = wf.readframes(chunk)

    while len(data) > 0:
        stream.write(data)
        data = wf.readframes(chunk)
    stream.stop_stream()
    stream.close()
    p.terminate()

if __name__ == '__main__':
    TTS(TEXT="你好")
