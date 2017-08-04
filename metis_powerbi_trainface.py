import cv2
import httplib, urllib, base64,requests
import urllib2
import ast
import os
import sys
import json
import re

from threading import Thread 

from datetime import datetime
import urllib2, time
#video_capture = cv2.VideoCapture(1)

'''
def face_similarity(image):
    #def all the parameters
    personGroup = 'chrisid'
    key = "8c1358b1918b459898750ff689cce6b0"
    content = "application/octem"
    persistedFaceId = "2f6a595c-1145-4ea5-ac91-e8cf257d0c3a"
    person = "chris_p"
    personId = "9a6bd70b-deae-4e34-a14f-b7f2e65ab565"
'''

def powerBI(emotion,age,gender):#,anger,comtempt,disgust,fear,happiness,surprise,neutral,sadness):
    REST_API_url = "https://api.powerbi.com/beta/84c31ca0-ac3b-4eae-ad11-519d80233e6f/datasets/5c0abbce-e8ac-4114-b4f2-18e01e5b0aea/rows?key=iUn4OscyhdGQfZEg9LO%2BofsRj2eqLwOuPRuVdNYG2WqUl9HyLN%2FJJceZxXaHmh0GzoqYyklPS4L1Jcotl7zkjw%3D%3D"
    now = datetime.strftime(datetime.now(), "%Y-%m-%dT%H:%M:%S%Z")
    #data = '[{{"Time":"{0}","Emotion":"{1}","Age":"{2}","Gender":"{3}"#,"anger":"{4},"comtempt":"{5}","disgust":"{6}","fear":"{7}","happiness":"{8}","surprise":"{9}","neutral":"{10}","sadness":"{11}"}}]'.format(now,emotion,age,gender,anger,comtempt,disgust,fear,happiness,surprise,neutral,sadness)
    data = '[{{"Time":"{0}","Emotion":"{1}","Age":"{2}","Gender":"{3}"}}]'.format(now,emotion,age,gender)
    try:
        req = urllib2.Request(REST_API_url,data)
        #response = urllib2.urlopen(req)
        print "powerBI pass"
        time.sleep(1)
    except:
        pass
    
def faceapi(image):
    headers = {
        # Request headers
        'Content-Type': 'application/octet-stream',
        'Ocp-Apim-Subscription-Key': '8c1358b1918b459898750ff689cce6b0',
    }

    params = urllib.urlencode({
    # Request parameters
    'returnFaceId': 'true',
    'returnFaceRectangle':'true',
    'returnFaceAttributes': 'age,gender,emotion',
})

    try:
        conn = httplib.HTTPSConnection('southeastasia.api.cognitive.microsoft.com')
        conn.request("POST", "/face/v1.0/detect?%s" % params, image, headers)
        response = conn.getresponse()
        data = json.loads(response.read())
        conn.close()
        print data
        return data
    except Exception as e:
        conn.close()

def faceapi_train(image):
    headers = {
        # Request headers
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': '8c1358b1918b459898750ff689cce6b0',
    }

    params = urllib.urlencode({
    # Request parameters
    # groupid for waqas : 'waqas'
    # personid : '998bc890-c82f-4f3c-a4d5-04c4447a102f'
    'personGroupId': 'chrisid',
    'personId':'9a6bd70b-deae-4e34-a14f-b7f2e65ab565',

})
    try:
        conn = httplib.HTTPSConnection('southeastasia.api.cognitive.microsoft.com')
        conn.request("POST", "/face/v1.0/persongroups/{personGroupId}/persons/{personId}/persistedFaces?%s" % params, image, headers)
        response = conn.getresponse()
        data = response.read()
        print(data)
        conn.close()
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))

def faceapi_findsimilar(faceid):
    headers = {
        # Request headers
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': '8c1358b1918b459898750ff689cce6b0',
    }

    params = urllib.urlencode({})
    faceid = str(faceid)
    body = {'faceId':faceid,
    'personId':'9a6bd70b-deae-4e34-a14f-b7f2e65ab565',
    'personGroupId':'chrisid'}
    body = str(body)
    print "ok"
    try:
        conn = httplib.HTTPSConnection('southeastasia.api.cognitive.microsoft.com')
        conn.request("POST", "https://southeastasia.api.cognitive.microsoft.com/face/v1.0/verify%s" % params, body, headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        print data
        data = re.sub(r'true', 'True', data)
        data = re.sub(r'false','False',data)
        return ast.literal_eval(data)
    except Exception as e:
        print "SOME ERROR SHIT"
        #print("[Errno {0}] {1}".format(e.errno, e.strerror))
    
def face_analyse():
     global faceData
     control = 0
     #conn = http.HTTPSConnection("https://southeastasia.api.cognitive.microsoft.com")
     #conn.request("POST", "/face/v1.0/persongroups/chrisid/persons/9a6bd70b-deae-4e34-a14f-b7f2e65ab565/persistedFaces")
     while True:
        response = faceapi(cv2.imencode('.jpg', frame)[1].tobytes())
        #faceapi_train(cv2.imencode('.jpg', frame)[1].tobytes())
        faceData = []
        if response != None:
            for face in response:
                compare = faceapi_findsimilar(face['faceId'])
                if compare['isIdentical'] == True and compare['confidence'] > 0.5 and control==0:
                    urllib2.urlopen("http://metischatbot.azurewebsites.net/api/listener?customerid=123112")
                    control+=1
                    print "ALL SET"
                emotion = sorted(face["faceAttributes"]["emotion"],key=face["faceAttributes"]["emotion"].get)[-1]
                age = face["faceAttributes"]["age"]
                gender = ((face["faceAttributes"]["gender"]=="male")*1)
                faceData.append([face["faceRectangle"]["left"],face["faceRectangle"]["top"],emotion,age,gender])
def getFrame():
    global frame
    while True:
        frame = video_capture.read()[1]

def realtime():
    faceCascade = cv2.CascadeClassifier("Models/haarcascade_frontalface_default.xml")
    alreadysent = False
    while True:
        # Capture frame-by-frame
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = faceCascade.detectMultiScale(
            gray,
            scaleFactor=1.2,
            minNeighbors=5,
            minSize=(40, 40)
        )
        
        for (x, y, w, h) in faces:
            face = frame[y-4:y+h+4,x-4:x+w+4]
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            emotion = checkMapping(x,y,w,h)
            if emotion != "NULL":
                if emotion == "happiness" and alreadysent == False:
                    urllib2.urlopen("http://localhost:3978/api/listener?customerid=123112")
                    alreadysent = True

                textX = x + int(round(1.05*w))
                textY = y + int(round(0.1*h))
                cv2.putText(frame,emotion,(textX,textY),cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,0),2)
        
        cv2.imshow('Video', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            video_capture.release()
            cv2.destroyAllWindows()
            break

def checkMapping(x,y,w,h):
    global faceData
    for face in faceData:
        if abs(face[0] - x) <= 0.2*w:
            if abs(face[1] - y) <= 0.2*h:
                return face[2]
    return "NULL"
    
if __name__ =="__main__":
    global video_capture
    global frame
    global faceData
    faceData = []
    video_capture = cv2.VideoCapture(1)
    frame = video_capture.read()[1]

    gfthread = Thread(target=getFrame, args='')
    gfthread.start()

    rtthread = Thread(target=realtime, args='')
    rtthread.start()

    fathread = Thread(target=face_analyse, args='')
    fathread.start()
    
