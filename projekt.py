import cv2
import pytesseract 
from pyzbar.pyzbar import decode
import adafruit_ssd1306
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import RPi.GPIO as GPIO
import numpy as np
import time
import sqlite3
from threading import Thread
import dateutil.parser as dparser

#### Init
con = sqlite3.connect("base.db")
cur = con.cursor()

RESET_PIN = digitalio.DigitalInOut(board.D4)
i2c = board.I2C()  
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C, reset=RESET_PIN)

class ThreadedCamera(object):
    def __init__(self, src=0):
        self.capture = cv2.VideoCapture(src)
        self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 2)
       
        # FPS = 1/X
        # X = desired FPS
        self.FPS = 1/30
        self.FPS_MS = int(self.FPS * 1000)
        
        # Start frame retrieval thread
        self.thread = Thread(target=self.update, args=())
        self.thread.daemon = True
        self.thread.start()
        
    def update(self):
        while True:
            if self.capture.isOpened():
                (self.status, self.frame) = self.capture.read()
            time.sleep(self.FPS)
            
    def show_frame(self):
        return self.frame

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

#### Variables

MID_PIN = 23
LFT_PIN = 27
RHT_PIN = 17
UP_PIN = 24
DWN_PIN = 25

cam = ThreadedCamera(0)
time.sleep(0.4)
msg = Messages()
##start functions
GPIO.setmode(GPIO.BCM)

GPIO.setup(MID_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(LFT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(RHT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(UP_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DWN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

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

    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    draw.text((0, 0), question, font=font, fill=255)
    draw.text((0, 15), text, font=font, fill=255)
    draw.text((0, 50), "tak <-           -> nie", font=font, fill=255)

    oled.image(image)
    oled.show()
    while True:
        time.sleep(0.01)
        if GPIO.input(LFT_PIN) == GPIO.LOW:
            return True
        if GPIO.input(RHT_PIN) == GPIO.LOW:
            return False

def outputAmount(product, date):
    count = 1
    
    while True:
        time.sleep(0.01)
        image = Image.new("1", (oled.width, oled.height))
        draw = ImageDraw.Draw(image)
    
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        draw.text((0, 0), product, font=font, fill=255)
        draw.text((0, 15), "Ilość "+str(count), font=font, fill=255)
        draw.text((0, 30), "Data "+str(date), font=font, fill=255)
        draw.text((0, 50), "up^  mid ok  vdwn", font=font, fill=255)

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

        row_len = 4
        if len(rows)<4:
            row_len=len(rows)

        for i in range(shift,shift+row_len):
            if i == selected:
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




if __name__ == '__main__':
    oled.fill(0)
    oled.show()

    createBase()

    mode = 0
    productCode = 0
    productDate = ""

    while True:
        image = cam.show_frame()
        #cv2.imwrite('./testimage.jpg', image)

        image_screen = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB)).resize((oled.width, oled.height), Image.BICUBIC).convert("1")
        draw = ImageDraw.Draw(image_screen)
        
        msg.outputMessage()

        oled.image(image_screen)
        oled.show()
       
        if GPIO.input(DWN_PIN) == GPIO.LOW:
            showExpiring()
        elif mode == 0:
                
            height, width, channels = image.shape #todo usunąc albo dac na pasek
            kody = searchForCode(image)
            if len(kody) > 0:
                for kod in kody:
                    if outputQuestion("Zgadza się?", searchProductBase(kod["data"])):
                        mode = 1
                        productCode = kod["data"]
                        break 
                  
        elif GPIO.input(MID_PIN) == GPIO.LOW and mode == 1:
            result = searchForDate(image)
            try:
                result = dparser.parse(result,fuzzy=True,dayfirst = True).strftime("%d.%m.%Y")
                if not outputQuestion("Zgadza się data?", result):
                    result = False
            except ValueError:
                result = False
                msg.setMessage("Nie znaleziono") 

            if result: 
                productDate = result
                mode = 2
               
        elif mode == 2:
            amount = outputAmount(searchProductBase(productCode), productDate)
            addToDatabase(productCode, productDate , amount)
            msg.setMessage("Dodano")
            mode = 0
        
            
        

    cam.release()
    cv2.destroyAllWindows()
    GPIO.cleanup()