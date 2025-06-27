# save this as server.py oder app.py
from flask import Flask
from threading import Thread

app = Flask(__name__)


@app.route("/")
def home():
    return "Stay alive"


def run():
    app.run(host='0.0.0.0', port=8080)


def stay_alive():
    t = Thread(target=run)
    t.start()
