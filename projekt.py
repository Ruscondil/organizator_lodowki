import cv2
import pytesseract
from pytesseract import Output
from pyzbar.pyzbar import decode
import adafruit_ssd1306
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import RPi.GPIO as GPIO
import numpy as np
import time

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
 
def get_grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
 
 
def thresholding(image):
    return cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
 
 
def opening(image):
    kernel = np.ones((5, 5), np.uint8)
    return cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
 
 
def canny(image):
    return cv2.Canny(image, 100, 200)

def onlyCode(rawcode):
    return rawcode.decode("utf-8") 

def searchForCode(image):
    decoded_list = decode(image)
    code_list = []
    for code in decoded_list:
        code_list.append({ "data": onlyCode(code.data), "type": code.type})
        
    return code_list

def searchForDate(image):
    custom_config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(image, config=custom_config, lang="pol")
    return text

def outputQuestion(question, text):
    image = Image.new("1", (oled.width, oled.height))
    draw = ImageDraw.Draw(image)

    # Load a font in 2 different sizes.
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    draw.text((0, 0), question, font=font, fill=255)
    draw.text((0, 15), text, font=font, fill=255)
    draw.text((0, 30), "tak <-    -> nie", font=font, fill=255)

    # Display image
    oled.image(image)
    oled.show()
    while GPIO.input(BUTTON_PIN) != GPIO.LOW:
        time.sleep(0.01)




# Open, resize, and convert image to Black and White
oled.fill(0)
oled.show()

while True:

    suc, image = cam.read()
    #gray = get_grayscale(image)
    #thresh = thresholding(gray)
    #opening = opening(gray)
    #canny = canny(gray)
    
    cv2.imwrite('./testimage.jpg', image)

    image_screen = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB)).resize((oled.width, oled.height), Image.BICUBIC).convert("1")
    draw = ImageDraw.Draw(image_screen)
  
    
    # Display the converted image
    
    if GPIO.input(BUTTON_PIN) == GPIO.LOW:
        kody = searchForCode(image)
        if len(kody) > 0:
            for kod in kody:
                outputQuestion("Zgadza się?", kod["data"])
        else:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
            draw.text((0, 50), "Nie znaleziono", font=font, fill=255)
        

        #searchForDate(image)
        print("ELO")
    oled.image(image_screen)
    oled.show()
    #cv2.imshow('Imagetest',image)
    #k = cv2.waitKey(1)
    #if k != -1:
    #   break """

cam.release()
cv2.destroyAllWindows()
GPIO.cleanup()