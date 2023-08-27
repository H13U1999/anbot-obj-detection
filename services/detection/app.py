
import requests
from flask import Flask, request, jsonify
from obj_dect import DiscordBotObjectDetection
import pyrebase
from dotenv import load_dotenv
import os
load_dotenv()




firebaseConfig = {
  "apiKey": os.getenv('API_KEY'),
  "authDomain":os.getenv('AUTH_DOMAIN'),
  "projectId": os.getenv('PROJECT_ID'),
  "storageBucket": os.getenv('STORAGE_BUCKET'),
  "messagingSenderId": os.getenv('MESSAGING_SENDER_ID'),
  "appId": os.getenv('APP_ID'),
  "measurementId": os.getenv('MEASUREMENT_ID'),
      "databaseURL": ""

}
predictor =  DiscordBotObjectDetection()
firebase = pyrebase.initialize_app(firebaseConfig)
storage = firebase.storage()

auth = firebase.auth()


app = Flask(__name__)

@app.route("/obj-dect",methods=["POST"])
def return_detection():
    img_url = str(request.json['img']) 
    name = predictor.get_detection(img_url)
    storage.child(name).put(name)
    os.remove(name)
    return {"url":storage.child(name).get_url(None)}

@app.route("/health",methods=["GET"])
def health_check():
    return "ok"


app.run(host="0.0.0.0", port=os.getenv('PORT'))


