import cv2
from pyzbar.pyzbar import decode
cam = cv2.VideoCapture(0)

lastScan = []

def onlyCode(rawcode):
    return rawcode.decode("utf-8") 

def searchForCode():
    while True:
        ret, image = cam.read()
        decoded_list = decode(image)
        code_list = []
        for code in decoded_list:
            #print(code.data, type(code.data))
            #print(code.type)
            code_list.append({ "data": onlyCode(code.data), "type": code.type})
           
        #cv2.imwrite('/home/pi/projekt/testimage.jpg', image)
        return code_list

while True:
    codes = searchForCode()
    for code in codes:
        print("Git?", code["data"])
        if input() == 'y':
            print("gitara")
            exit()
    #cv2.imshow('Imagetest',image)
    #k = cv2.waitKey(1)
    #if k != -1:
    #   break """

cam.release()
cv2.destroyAllWindows()