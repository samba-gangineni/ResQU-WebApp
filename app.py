import requests
import geocoder
from config import API
from pymongo import MongoClient
from passlib.hash import pbkdf2_sha256
from flask import (
	Flask, render_template, request, session, flash, url_for, redirect, make_response
	)
# twilio for sending msg alert
from twilio.rest import Client

# Flask app connection
app = Flask(__name__)
app.secret_key = 'ResQU'
app.config['SESSION_TYPE'] = 'filesystem'


# Mongo Connection 
client = MongoClient()
db = client['ResQU']


@app.route('/')
@app.route('/api/v1/')
def home():
	return render_template('index.html')


@app.route('/api/v1/dashboard', methods=["GET","POST"])
def dashboard():
	results = get_precausions()
	return render_template('dashboard.html', precausions = results)


@app.route('/api/v1/login', methods=["GET","POST"])
def login():
	if request.method == 'POST':
		unique_user = db['Users'].find({ 'username': { '$exists': True, '$in': [ str(request.form['username']) ]}})
		if unique_user.count() != 0:
			for user in unique_user:
				password = user.get('password')
				username = user.get('username')
				break
			if not pbkdf2_sha256.verify(request.form.get('password'), password):
				err = 'Password or Username is incorrect.'
				return render_template('login.html', error=err)
			else:
				session['username'] = username
				session['logged_in'] = True
				return redirect(url_for('dashboard'))
		else:
			err = 'Users not exists try again!'
			return render_template('login.html', error=err)
	return render_template('login.html')


@app.route('/api/v1/signup', methods=["GET","POST"])
def signup():
	err = request.args('error',)
	if request.method == 'POST':
		unique_user = db['Users'].find({ 'username': { '$exists': True, '$in': [ str(request.form['username']) ]}})
		if unique_user.count() == 0:
			if request.form['password'] == request.form['password2']:
				user = {}
				for key,val in request.form.items():
					if 'password' == key:
						user['password'] = pbkdf2_sha256.hash(val)
					elif 'password2'== key:
						pass
					else:
						user[key] = val

				session['username'] = str(request.form['username'])
				session['logged_in'] = False
				try:
					db['Users'].insert_one(user)
				except Exception as e:
					err = 'Users cant be signed up.' + e
					return render_template('signup.html', error=err)    

				return redirect(url_for('home'))
			else:
				err = 'Passwords do not match.'
				return render_template('signup.html', error=err)
		else:
			err = 'Users not exists try again!'
			return render_template('signup.html', error=err)
	return render_template('signup.html')


@app.route('/api/v1/logout')
def logout():
    session.pop('username', None)
    session.pop('logged_in', None)
    return render_template('home', msg='Succesfully logout!')

@app.route('/api/v1/sos', methods=['GET','POST'])
def sos():
	if request.method == 'POST':
		disaster = request.form.get('disaster','Disaster')
		msg = ''
		unique_user = db['Users'].find({ 'username': { '$exists': True, '$in': [ str(session['username']) ]}})
		full_name, contact = '', ''
		for user in unique_user:
			full_name = user.get('last_name') + ', '+ user.get('first_name')
			username = user.get('username')
			contact = user.get('contact')
			break
		msg += 'Disaster SOS Alerts\n {} has been stuck in {}.\n Help Urgently Needed!!\n Contact Info: {}\n '.format(full_name, disaster, contact)
		latlng = get_latlng()
		if latlng:
			address = get_location(latlng)
			if address:
				for k,v in address.items():
					msg += '{}: {}\n '.format(k,v)
		msg += 'Please Send Help Soon!'
		if send_alert(msg):
			return render_template('home', msg='Succesfully SOS Help Request Sent!')
	return render_template('home', msg='SOS Request Unable to Sent!') 

def get_precausions(lang="English"):
	precausions = []
	results = db['Precausions'].find({"language":lang})
	for result in results:
		feature = {}
		feature['title'] = result['title']
		feature['body'] = result['body'].replace('\\','')
		feature['label'] = result['title'].split(' ')[0]
		feature['hazard_type'] = result['hazard_type']
		precausions.append(feature)
	return precausions

def get_location(latlng):
	geolocation_api = 'https://maps.googleapis.com/maps/api/geocode/json?latlng={}&key={}'.format(latlng, API().API_KEY)
	response = requests.get(geolocation_api)
	if response.json().get('results'):
		return {
			'Address': response.json().get('results')[0].get('formatted_address'),
			'Location': response.json().get('results')[0]['geometry']['location'],
			'Location_type': response.json().get('results')[0].get('location_type')
			}
	return {}

def get_latlng():
	g = geocoder.ip('me')
	print(g.latlng)
	return ''.join(list(map(str, g.latlng)))

def send_alert(body):
	client = Client(API().account_sid, API().auth_token)
	try:
		message = client.messages.create(
		                              from_= API().from_,
		                              body='body',
		                              to= API().to
		                          )

		return message.sid
	except:
		return False


if __name__ == '__main__':
	app.run(host='0.0.0.0',port=5000)