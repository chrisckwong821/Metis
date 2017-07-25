import cv2
import httplib, urllib, base64,requests
import ast
import os
import sys
from multiprocessing.dummy import Pool as ThreadPool

def Emotion_API(image):
    # image as binary
    api_url ='https://westus.api.cognitive.microsoft.com/emotion/v1.0/recognize'
    header = {'Content-Type': 'application/octet-stream',
    'Ocp-Apim-Subscription-Key': '6b360cc90f064ddcac8af790289a641e'}
        # Request headers. Replace the placeholder key below with your subscription key.
    params = urllib.urlencode({})
    #with open(image, 'rb') as f:
    #    img_data = f.read()
    try:
        #  You must use the same region in your REST call as you used to obtain your subscription keys.
        r = requests.post(api_url,params=params,headers=header,data=image)
        response = ast.literal_eval(r.text)
        score = response[0]['scores']
        emotion = sorted(score,key=score.get)[-1]
        #print emotion
        return emotion
    except Exception as e:
        #print "Exception"
        return ""

def Track_face():
    cwd = os.getcwd()
    cascPath = sys.argv[1]
    faceCascade = cv2.CascadeClassifier(cascPath)
    video_capture = cv2.VideoCapture(0)
    while True:
        # Capture frame-by-frame
        ret, frame = video_capture.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = faceCascade.detectMultiScale(
            gray,
            scaleFactor=1.2,
            minNeighbors=5,
            minSize=(40, 40)
        )
        # Draw a rectangle around the faces
        for (x, y, w, h) in faces:
            a,b,c,d = x,y,w,h
            face = frame[y-4:y+h+4,x-4:x+w+4]
            r = cv2.imencode('.jpg',face)[1].tobytes()
            #cv2.imwrite("1.jpg",face)
            #with open(cwd +"/1.jpg",'rb') as f:
            #    image = f.read()
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            #emotion = Emotion_API(r)
        cv2.imshow('Video', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    # When everything is done, release the capture
    video_capture.release()
    cv2.destroyAllWindows()

def Print_emotion():
    global face,frame,a,b
    r = cv2.imencode('.jpg',face)[1].tobytes()
    emotion = Emotion_API(r)
    cv2.putText(frame,emotion,(a+6,b+6),cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,0),2)

def Test():
    global a
    while True:
        print a

if __name__ == "__main__":
    a=b=face=frame=0
    pool = ThreadPool(4)
    pool(Track_face(),Test())
    pool.close()
    pool.join()