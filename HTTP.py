import httplib, urllib, base64,requests
import ast
import numpy as np
import cv2
import sys


# "/Users/chunkauwong/Desktop/WTH/1.jpg"
def Response(image):
    reload(sys)
    sys.setdefaultencoding('utf8')
    api_url ='https://westus.api.cognitive.microsoft.com/emotion/v1.0/recognize'
    header = {'Content-Type': 'application/octet-stream',
    'Ocp-Apim-Subscription-Key': '6b360cc90f064ddcac8af790289a641e'}
        # Request headers. Replace the placeholder key below with your subscription key.
    params = urllib.urlencode({})
    #img_data = cv2.imencode('.jpg', image)[1].tostring()
    #img_data = image.tostring()
    with open(image, 'rb') as f:
        img_data = f.read()
    try:
        #  You must use the same region in your REST call as you used to obtain your subscription keys.
        #   For example, if you obtained your subscription keys from westcentralus, replace "westus" in the
        #   URL below with "westcentralus".
        r = requests.post(api_url,params=params,headers=header,data=img_data)
        response = ast.literal_eval(r.text)
        score = response[0]['scores']
        emotion = sorted(score,key=score.get)[-1]
        #print emotion
        return emotion
    except Exception as e:
        #print "Exception"
        return ""

if __name__ == "__main__":
    Response()
