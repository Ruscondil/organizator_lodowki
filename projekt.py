import cv2
import pytesseract
from pytesseract import Output
from pyzbar.pyzbar import decode
import adafruit_ssd1306
import digitalio
import board
from PIL import Image
import RPi.GPIO as GPIO

BUTTON_PIN = 23
GPIO.setmode(GPIO.BCM)

GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)


RESET_PIN = digitalio.DigitalInOut(board.D4)
i2c = board.I2C()  # uses board.SCL and board.SDA
# i2c = board.STEMMA_I2C()  # For using the built-in STEMMA QT connector on a microcontroller
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C, reset=RESET_PIN)

cam = cv2.VideoCapture(0)
cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
#cam.set(3, 640)
#cam.set(4, 480)

lastScan = []

def onlyCode(rawcode):
    return rawcode.decode("utf-8") 

def searchForCode():
    while True:
        success, image = cam.read()
        decoded_list = decode(image)
        code_list = []
        for code in decoded_list:
            #print(code.data, type(code.data))
            #print(code.type)
            code_list.append({ "data": onlyCode(code.data), "type": code.type})
           
        #cv2.imwrite('/home/pi/projekt/testimage.jpg', image)
    return code_list

def searchForDate():
    while True:
        print("------------------------------------------")
        ret, image = cam.read()
        #custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_data(image)
        """   n_boxes = len(d['text'])
        text = ""
        for i in range(n_boxes):
            if int(d['conf'][i]) > 60:
                (text, x, y, w, h) = (d['text'][i], d['left'][i], d['top'][i], d['width'][i], d['height'][i])
                # don't show empty text """
        cv2.imwrite('./testimage.jpg', image)
        return text
oled.fill(0)
oled.show()

# Open, resize, and convert image to Black and White

while True:
    """  codes = searchForCode()
    for code in codes:
        print("Git?", code["data"])
        if input() == 'y':
            print("gitara")
            exit() """
    #print(searchForDate())
    ret, image = cam.read()
    cv2.imwrite('./testimage.jpg', image)
    image = (
    Image.open('./testimage.jpg')
    .resize((oled.width, oled.height), Image.BICUBIC)
    .convert("1")
    )
    

    # Display the converted image
    oled.image(image)
    oled.show()
    if GPIO.input(BUTTON_PIN) == GPIO.LOW:
        print("ELO")
        quit()
    #cv2.imshow('Imagetest',image)
    #k = cv2.waitKey(1)
    #if k != -1:
    #   break """

cam.release()
cv2.destroyAllWindows()
GPIO.cleanup()