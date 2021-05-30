from flask  import Flask, render_template, send_from_directory, send_file, Response, request
import numpy as np
import cv2
import pathlib
from flask.helpers import make_response
import io
import requests
import imutils
import base64
import uuid

myapp = Flask(__name__)

def analyseImagebyColor(lower_mask, upper_mask, image, color_name):
    imageConverted = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    imageConverted = cv2.GaussianBlur(imageConverted, (5, 5), 0)
    
    mask = cv2.inRange(imageConverted, lower_mask, upper_mask)

    print("Buscando Contornos...")
    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
    	cv2.CHAIN_APPROX_SIMPLE)
    
    return cnts

def drawContour(cnts,image,color_contour):
    print("Desenhando Contornos...")
    cnts_imutils = imutils.grab_contours(cnts)
    for c in cnts_imutils:
        cv2.drawContours(image, [c], -1, color_contour, 2)
        
    return image

def uploadToS3(image,token):
    headers = {'x-access-token' : token}
    data = {"fileType": ".png"}
    r = requests.post("https://helptonic-api.azurewebsites.net/s3",data=data,headers=headers)
    if r.ok:
        response = r.json()
        if response['success']:
            responseUplodad = requests.put(response['uploadUrl'], data=image)
            if responseUplodad.ok:
                return True, response['downloadUrl']
            else:
                return False, 'Erro enviar dados ao servidor S3.'
        else:
            return False, response['message']
    else:
        return False, 'Erro enviar dados ao servidor de dados.'
    
    print(r)

@myapp.route("/")
def hello():
    return "Hello Flask, on Azure App Service for Linux";

@myapp.route("/analyser", methods=['POST'])
def analyserTestImage():
    base64Image = request.json['image']
    tokenUser = request.json['token']
    
    image_bytes = base64.b64decode(base64Image)
    im_arr = np.frombuffer(image_bytes, dtype=np.uint8)
    imageOriginal = cv2.imdecode(im_arr, flags=cv2.IMREAD_COLOR)
    
    lower_orange = np.array([15, 38, 40], dtype="uint8") #Laranja
    upper_orange = np.array([24, 200, 200], dtype="uint8") #Laranja
    cnts_orange = analyseImagebyColor(lower_orange, upper_orange, imageOriginal, "Laranja")
    
    lower_yellow = np.array([25, 50, 40], dtype="uint8") #Amarelo
    upper_yellow = np.array([39, 255, 255], dtype="uint8") #Amarelo
    cnts_yellow = analyseImagebyColor(lower_yellow, upper_yellow, imageOriginal, "Amarelo")
    
    lower_green = np.array([40, 38, 40], dtype="uint8") #Verde
    upper_green = np.array([80, 200, 200], dtype="uint8") #verde
    cnts_green = analyseImagebyColor(lower_green, upper_green, imageOriginal, "Verde")
    
    lower_blue = np.array([81, 151, 121], dtype="uint8") #Azul
    upper_blue = np.array([127, 255, 255], dtype="uint8") #Azul
    cnts_blue = analyseImagebyColor(lower_blue, upper_blue, imageOriginal, "Azul")
    
    lower_purple = np.array([130, 38, 40], dtype="uint8") #Roxo
    upper_purple = np.array([144, 200, 200], dtype="uint8") #Roxo
    cnts_purple = analyseImagebyColor(lower_purple, upper_purple, imageOriginal, "Roxo")
    
    lower_pink = np.array([145, 38, 40], dtype="uint8") #Rosa
    upper_pink = np.array([160, 200, 200], dtype="uint8") #Rosa
    cnts_pink = analyseImagebyColor(lower_pink, upper_pink, imageOriginal, "Rosa")
    
    imageOriginal = drawContour(cnts_orange,imageOriginal,(255,0,0))
    imageOriginal = drawContour(cnts_yellow,imageOriginal,(0,255,0)) 
    imageOriginal = drawContour(cnts_green,imageOriginal,(0,0,255))
    imageOriginal = drawContour(cnts_blue,imageOriginal,(255,255,0))
    imageOriginal = drawContour(cnts_purple,imageOriginal,(0,255,255)) 
    imageOriginal = drawContour(cnts_pink,imageOriginal,(255,0,255))
    
    
    print("Codificando Imagem...")    
    data = cv2.imencode('.png', imageOriginal)[1].tobytes()
    success, returnString = uploadToS3(data,tokenUser)
    if success:
        return returnString
    else:
        return returnString, 500



@myapp.errorhandler(Exception)
def exception_handler(error):
    return repr(error), 500
