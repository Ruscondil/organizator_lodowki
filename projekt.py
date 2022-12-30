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
import sqlite3

con = sqlite3.connect("base.db")
cur = con.cursor()

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

def createBase():
    cur.execute("CREATE TABLE IF NOT EXISTS storage (ean NUMERIC NOT NULL, date DATE, amount NUMERIC NOT NULL)")
    cur.execute("CREATE TABLE IF NOT EXISTS products (ean NUMERIC PRIMARY KEY,name VARCHAR NOT NULL)")
    con.commit()

def addToDatabase(ean, date, amount):
    cur.execute("INSERT INTO storage (ean, date, amount) VALUES(?,?,?)", (ean,date,amount))
    con.commit()

def searchProductBase(code):
    cur.execute("SELECT name FROM products WHERE ean=?", (int(code),))
    rows = cur.fetchall()
    if len(rows)>0:
        return rows[0][0]
    return code
 
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

def outputAmount(product, date):
    count = 1
    
    while True:
        time.sleep(0.01)
        image = Image.new("1", (oled.width, oled.height))
        draw = ImageDraw.Draw(image)
    
        # Load a font in 2 different sizes.
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        draw.text((0, 0), product, font=font, fill=255)
        draw.text((0, 15), "Ilość "+str(count), font=font, fill=255)
        draw.text((0, 30), "Data "+str(date), font=font, fill=255)
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


def showExpiring():
    cur.execute("SELECT p.name,s.date FROM products p, storage s WHERE p.ean = s.ean ORDER BY s.date")
    rows = cur.fetchall()
    selected = 0
    shift = 0
    while True:
        image = Image.new("1", (oled.width, oled.height))
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        print(len(rows))
        row_len = 4
        if len(rows)<4:
            row_len=len(rows)
        print(row_len, "aa",len(rows)<4 and len(rows))
        for i in range(shift,shift+row_len):
           
            if i == selected:
                print(i)
                draw.rectangle((0, (i-shift)*15, 128, (i+1-shift)*15), outline=0, fill=1)
                draw.text((0, (i-shift)*15), str(rows[i][0][:9])+" "+str(rows[i][1]), font=font, fill=0)
            else:
                draw.text((0, (i-shift)*15), str(rows[i][0][:9])+" "+str(rows[i][1]), font=font, fill=1)
        oled.image(image)
        oled.show()
        time.sleep(0.01)
        if GPIO.input(MID_PIN) == GPIO.LOW:
            return 
        if GPIO.input(UP_PIN) == GPIO.LOW:
            selected = selected - 1
            if selected < 0:
                selected = 0
            if selected < shift:
                shift = shift -1
        if GPIO.input(DWN_PIN) == GPIO.LOW:
            selected = selected + 1
            if selected >= len(rows):
                selected = len(rows)-1 
            if selected > shift + 3 and shift+row_len<len(rows):
                shift = shift + 1



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
createBase()
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

    #outputAmount(str("ELOO"),  "12.12.22")
    if GPIO.input(MID_PIN) == GPIO.LOW:
        #searchForDate(image)
        print("ELO")
        if mode == 0:
            kody = searchForCode(image)
            if len(kody) > 0:
                for kod in kody:
                    if outputQuestion("Zgadza się?", searchProductBase(kod["data"])):
                        mode = 1
                        productCode = kod["data"]
                        break 
            else:
                msg.setMessage("Nie znaleziono")       
        elif mode == 1:
            mode = 2
    elif mode == 2:
        amount = outputAmount(searchProductBase(productCode), "12.12.22")
        addToDatabase(productCode,"12.12.21", amount)
        msg.setMessage("Dodano")
        mode = 0
    elif GPIO.input(DWN_PIN) == GPIO.LOW:
        showExpiring()
        
    

cam.release()
cv2.destroyAllWindows()
GPIO.cleanup()