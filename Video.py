import cv2
import sys
import httplib, urllib, base64,requests
import ast
from http import Response

if __name__ == "__main__":
    cascPath = sys.argv[1]
    faceCascade = cv2.CascadeClassifier(cascPath)
    video_capture = cv2.VideoCapture(0)
    while True:
        # Capture frame-by-frame
        ret, frame = video_capture.read()

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = faceCascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)

        )
        # Draw a rectangle around the faces
        for (x, y, w, h) in faces:
            face = frame[y-4:y+h+4,x-4:x+w+4]
            cv2.imwrite("1.png",face)
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame,Response("/Users/chunkauwong/Desktop/WTH/1.png"),(x+6,y+6),cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,0),2)


        # Display the resulting frame
        cv2.imshow('Video', frame)



        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # When everything is done, release the capture
    video_capture.release()
    cv2.destroyAllWindows()
