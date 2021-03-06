#!/usr/bin/env python2.7

import json
import random
import urllib

import requests

from flask import Flask, session, redirect, jsonify, request, abort
app = Flask(__name__)


OAUTH_URI = "https://oauth-latest.dev.lcip.org/v1"
PROFILE_URI = "https://latest.dev.lcip.org/profile/v1"
AUTH_URI = "https://oauth-latest.dev.lcip.org/v1/authorization"
REDIRECT_URI = "http://localhost"
SCOPES = "profile"

CLIENT_SECRET = "86d2d8f8324eb98880724dea718e408bfdb96d7499b4d8df47b34b379131fe56"
CLIENT_ID = "08c0eb0d8c85b964"


def random_nonce(length=32):
    return "".join([chr(random.randint(0,255)) for i in range(length)]).encode("hex")

def redirect_url(action, nonce, email=None, pre_verify_token=None):
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "state": nonce,
        "scope": SCOPES,
        "action": action
    }
    if email is not None:
        params["email"] = email
    if pre_verify_token is not None:
        params["preVerifyToken"] = pre_verify_token
    return AUTH_URI + "?" + urllib.urlencode(params)

def get_token(code):
    data = dict(code=code, client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
    headers = {"Content-type": "application/json"}
    r = requests.post(OAUTH_URI + "/token", data=json.dumps(data), headers=headers)
    r.raise_for_status()
    return r.json()

def get_profile(token):
    r = requests.get(PROFILE_URI + "/profile", headers={"Authorization": "Bearer " + token})
    r.raise_for_status()
    return r.json()

def verify(access_token):
    if access_token:
        data = dict(token=access_token)
        headers = {"Content-type": "application/json"}
        r = requests.post(OAUTH_URI + "/verify", data=json.dumps(data), headers=headers)
        r.raise_for_status()
        return r.json()

@app.route("/")
def index():
    return "There is nothing to see here. Try the <a href=\"https://github.com/st3fan/moz-androidfxa-client\"></a>Android Client instead."

@app.route("/login")
def login():
    state = random_nonce()
    res = redirect(redirect_url("/signin", state))
    res.set_cookie("state", state)
    return res

@app.route("/oauth")
def oauth():
    if "state" not in request.args or "code" not in request.args:
        abort(400)

    state = request.args.get("state")
    if not state or state != request.cookies.get("state"):
        abort(400)

    code = request.args.get("code")
    if not code:
        abort(400)

    token_response = get_token(code)
    profile = get_profile(token_response["access_token"])

    return jsonify(token=token_response, profile=profile)


@app.route("/api/hello")
def api_hello():
    if "Authorization" not in request.headers:
        abort(401)

    method, token = request.headers["authorization"].split(" ")
    if method != "Bearer":
        abort(401)

    r = verify(token)
    if r is None:
        abort(401)

    return "Hello, " + request.args.get("name")


if __name__ == "__main__":
    app.secret_key = "dnedie83j2oshs0829w2o2ojo2ijw02ndndwj92092"
    app.run(host="0.0.0.0", debug=True)
