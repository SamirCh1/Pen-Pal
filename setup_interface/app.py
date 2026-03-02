from flask import Flask, render_template, request
import subprocess

app = Flask(__name__)

@app.route("/")
def home():
    output = subprocess.check_output(["nmcli", "-t", "-f", "SSID", "dev", "wifi"])
    ssid_list = output.decode().split("\n")
    return render_template("index.html", networks=list(set(ssid_list)))

@app.route("/connect", methods=["POST"])
def connect():
    network_name = request.form["network"]
    password = request.form["password"]

    # TODO: make this nicer
    return f"Connected to {network_name}"

if __name__ == "__main__":
    app.run(debug=True)

