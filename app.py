import requests
import urllib.parse

from datetime import datetime, timedelta
from flask import Flask, redirect, request, jsonify, session, render_template
from PIL import Image, ImageFont, ImageDraw

app = Flask(__name__)
app.secret_key = '38jfknkdls-93fjkj-3920jfkldsjfkdk993'

CLIENT_ID = '5c33963460a1403ba93c2add750bde6d'
CLIENT_SECRET = '37a8cce6c8a04b29a2b8049326947726'
REDIRECT_URI = 'http://localhost:5000/callback'

AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1/'

@app.route('/')
def index():
    return render_template('front_page.html', href='/login')

@app.route('/login')
def login():
    scope = 'user-top-read'

    params = {
        'client_id' : CLIENT_ID,
        'response_type' : 'code',
        'scope' : scope,
        'redirect_uri' : REDIRECT_URI,
        'show_dialog' : True    #set to true for debug purposes, omit when finished
    }

    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    return redirect(auth_url)

@app.route('/callback')
def callback():
    if 'error' in request.args:
        return jsonify({"error" : request.args['error']})
    
    if 'code' in request.args:
        req_body = {
            'code' : request.args['code'],
            'grant_type' : 'authorization_code',
            'redirect_uri' : REDIRECT_URI,
            'client_id' : CLIENT_ID,
            'client_secret' : CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)

        token_info = response.json()

        session['access_token'] = token_info['access_token']
        session['refresh_token'] = token_info['refresh_token']
        session['expires_at'] = datetime.now().timestamp() + token_info['expires_in']

        return redirect('/artists')

def create_row(idx, len, artists):
    row = ''
    for i in range(len):
        row += artists[idx]
        row += '   '
        idx += 3
    return(row)

@app.route('/artists')
def get_artists():
    if 'access_token' not in session:

        return redirect('/login')
    
    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh_token')
    
    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    response = requests.get(API_BASE_URL + "me/top/artists?limit=36", headers=headers)

    data = response.json()['items']
    jsonify(data)

#now that the data is retrieved, its time to create the image and pass it to the html file
    
    artists = []
    for deta in data:
        artists.append(deta['name'])
    
    img = Image.open('sunset.png')
    draw = ImageDraw.Draw(img)

#header
    font = ImageFont.truetype("title.otf", 90)
    draw.text((330, 60), 'MEFEST', (255,255,255), font=font)

#headliners
    font = ImageFont.truetype("Bebas-Regular.otf", 60)
    fheadl = 200 #height of first headliner
    for i in range(3):
        draw.text((50, fheadl), artists[i], (255,255,255), font=font)
        fheadl += 260

#subheadliners
    font = ImageFont.truetype("Bebas-Regular.otf", 35)
    fsubheadl = 280
    for i in range(3):
        draw.text((50,fsubheadl), create_row(3+i,3,artists), (255,255,255), font=font)
        fsubheadl += 260

#third row
    font = ImageFont.truetype("Bebas-Regular.otf", 25)
    ftrow = 330
    for i in range(3):
        draw.text((50,ftrow), create_row(12+i,4,artists), (255,255,255), font=font)
        ftrow += 260

#last row
    ftrow = 370
    for i in range(3):
        draw.text((50,ftrow), create_row(24+i,4,artists), (255,255,255), font=font)
        ftrow += 260

#headliners
    img.save('static/lineup.png')

    return render_template('main.html', artists=artists)
    
    
    

@app.route('/refresh_token')
def refresh_token():
    if 'refresh_token' not in session:
        return redirect('/login')
    
    if datetime.now().timestamp() > session['expires_at']:
        req_body = {
            'grant_type': 'refresh_token',
            'refresh_token': session['refresh_token'],
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)
        new_token_info = response.json()

        session['access_token'] = new_token_info['access_token']
        session['expires_at'] = datetime.now().timestamp() + new_token_info['expires_in']

        return redirect('/artists')
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)