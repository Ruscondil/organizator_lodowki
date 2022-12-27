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

MID_PIN = 23
LFT_PIN = 27
RHT_PIN = 17
UP_PIN = 24
DWN_PIN = 25

GPIO.setmode(GPIO.BCM)

GPIO.setup(MID_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(LFT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(RHT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(UP_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DWN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

RESET_PIN = digitalio.DigitalInOut(board.D4)
i2c = board.I2C()  
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C, reset=RESET_PIN)

cam = cv2.VideoCapture(0)
cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
#cam.set(3, 640)
#cam.set(4, 480)

 
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
    draw.text((0, 50), "tak <-           -> nie", font=font, fill=255)

    # Display image
    oled.image(image)
    oled.show()
    while True:
        time.sleep(0.01)
        if GPIO.input(LFT_PIN) == GPIO.LOW:
            print("L")
            return True
        if GPIO.input(RHT_PIN) == GPIO.LOW:
            print("R")
            return False

def outputAmount(product):
    count = 1
    
    while True:
        time.sleep(0.01)
        image = Image.new("1", (oled.width, oled.height))
        draw = ImageDraw.Draw(image)

        # Load a font in 2 different sizes.
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        draw.text((0, 0), product, font=font, fill=255)
        draw.text((0, 15), "Ilość "+str(count), font=font, fill=255)
        draw.text((0, 50), "up^  mid ok  vdwn", font=font, fill=255)

        # Display image
        oled.image(image)
        oled.show()
        if GPIO.input(UP_PIN) == GPIO.LOW:
            count = count +1
            time.sleep(0.05)
        if GPIO.input(DWN_PIN) == GPIO.LOW:
            count = count - 1
            time.sleep(0.05)
            if count<1:
                count = 1
        if GPIO.input(MID_PIN) == GPIO.LOW:
            return count





class Messages:
    settime = time.time()
    message = "test"
    def setMessage(self, mes):
        self.message = mes
        self.settime = time.time()+1

    def outputMessage(self):
        if self.settime > time.time():
            draw.rectangle((0, 50, 128, 64), outline=0, fill=0)
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
            draw.text((0, 50), self.message, font=font, fill=255)


mode = 0
productCode = 0
# Open, resize, and convert image to Black and White
oled.fill(0)
oled.show()
msg = Messages()
while True:

    suc, image = cam.read()
    #gray = get_grayscale(image)
    #thresh = thresholding(gray)
    #opening = opening(gray)
    #canny = canny(gray)
    
    cv2.imwrite('./testimage.jpg', image)

    image_screen = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB)).resize((oled.width, oled.height), Image.BICUBIC).convert("1")
    draw = ImageDraw.Draw(image_screen)
    
    msg.outputMessage()

    oled.image(image_screen)
    oled.show()

    outputAmount(str("ELOO"))
    if GPIO.input(MID_PIN) == GPIO.LOW:
        #searchForDate(image)
        print("ELO")
        if mode == 0:
            kody = searchForCode(image)
            if len(kody) > 0:
                for kod in kody:
                    if outputQuestion("Zgadza się?", kod["data"]):
                        print("A")
                        mode = 1
                        productCode = kod["data"]
                        break 
            else:
                msg.setMessage("Nie znaleziono")
                
    elif mode == 1:
        mode = 2
    elif mode == 2:
        outputAmount(productCode)
        msg.setMessage("Dodano")
        mode = 0
        
    
    

cam.release()
cv2.destroyAllWindows()
GPIO.cleanup()