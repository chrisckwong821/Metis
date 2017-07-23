import cv2
import numpy as np
import sys

def main():
    imagepath = sys.argv[1] # image
    cascpath = sys.argv[2] #xml classifier
    faceCascade = cv2.CascadeClassifier(cascpath) #turn into Casc object
    image = cv2.imread(imagepath) #read in the xml
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) #turn img into gray
    faces = faceCascade.detectMultiScale(gray,scaleFactor=1.1,minNeighbors=5,minSize=(30, 30))#,)
        #flags = cv2.CASCADE_SCALE_IMAGE
    for (x, y, w, h) in faces: #draw rectangle
        cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(image,"text",(x+6,y+6),cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,0),2)

    cv2.imshow("Faces found" ,image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
