import ibm_db
conn = ibm_db.connect("DATABASE=bludb;HOSTNAME=ea286ace-86c7-4d5b-8580-3fbfa46b1c66.bs2io90l08kqb1od8lcg.databases.appdomain.cloud;PORT=31505;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=yqp88191;PWD=AuWG1YTPyE1OouIA;","","")
if(conn):
	print("connection successfully")



# Store this code in 'app.py' file

from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import requests
from sklearn.preprocessing import MinMaxScaler
import numpy as np
from flask import request, render_template,session,redirect,url_for
from ibm_db import exec_immediate
from ibm_db import tables
import joblib


app = Flask(__name__)


app.secret_key = 'london'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Lokesh@2005'
app.config['MYSQL_DB'] = 'userlogin'

API_KEY = "j3LQaUfy6rbDdziBTa_eKtLmkmVTk4UIluDVSEOpi0HL"
token_response = requests.post('https://iam.cloud.ibm.com/identity/token', data={"apikey": API_KEY, "grant_type": 'urn:ibm:params:oauth:grant-type:apikey'})
mltoken = token_response.json()["access_token"]
mysql = MySQL(app)

@app.route('/')
@app.route('/login', methods =['GET', 'POST'])
def login():
	msg = ''
	if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
		username = request.form['username']
		password = request.form['password']
		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		cursor.execute('SELECT * FROM accounts WHERE username = % s AND password = % s', (username, password, ))
		account = cursor.fetchone()
		if account:
			session['loggedin'] = True
			session['id'] = account['id']
			session['username'] = account['username']
			msg = 'Logged in successfully !'
			return render_template('index.html', msg = msg)
		else:
			msg = 'Incorrect username / password !'
	return render_template('login.html', msg = msg)

@app.route('/logout')
def logout():
	session.pop('loggedin', None)
	session.pop('id', None)
	session.pop('username', None)
	return redirect(url_for('login'))

@app.route('/register', methods =['GET', 'POST'])
def register():
	msg = ''
	if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form :
		username = request.form['username']
		password = request.form['password']
		email = request.form['email']
		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		cursor.execute('SELECT * FROM accounts WHERE username = % s', (username, ))
		account = cursor.fetchone()
		if account:
			msg = 'Account already exists !'
		elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
			msg = 'Invalid email address !'
		elif not re.match(r'[A-Za-z0-9]+', username):
			msg = 'Username must contain only characters and numbers !'
		elif not username or not password or not email:
			msg = 'Please fill out the form !'
		else:
			cursor.execute('INSERT INTO accounts VALUES (NULL, % s, % s, % s)', (username, password, email, ))
			mysql.connection.commit()
			msg = 'You have successfully registered !'
	elif request.method == 'POST':
		msg = 'Please fill out the form !'
	return render_template('register.html', msg = msg)	

@app.route('/')
@app.route('/mainpage', methods =['GET', 'POST'])
def mainpage():
	msg=''
	return render_template('mainpage.html', msg = msg)

@app.route('/mainpage', methods=['POST'])
def predictSpecies():
    if 'uid' in session:
        if request.method=="POST":
            email=session['uid']
            age = float(request.form['age'])
            gender = float(request.form['gender'])
            tb = float(request.form['tb'])
            db = float(request.form['db'])
            ap = float(request.form['ap'])
            aa1 = float(request.form['aa1'])
            aa2 = float(request.form['aa2'])
            tp = float(request.form['tp'])
            a = float(request.form['a'])
            agr = float(request.form['agr'])
            X = np.array([float(age),float(gender),float(tb),float(db),float(ap),float(aa1),float(aa2),float(tp),float(a),float(agr)]).reshape(1,-1);
            print(X)
            mc=joblib.load('mc1.pkl')
            scaled_x=mc.transform(X)
            X=scaled_x.tolist()
            print(X)
            payload_scoring = {"input_data": [{"field": [['age','gender','tb','db','ap','aa1','aa2','tp','a','agr']], "values": X}]}
            response_scoring = requests.post('https://us-south.ml.cloud.ibm.com/ml/v4/deployments/8216d53f-c157-4b9f-89af-174229f60e03/predictions?version=2022-11-11', json=payload_scoring,headers={'Authorization': 'Bearer ' + mltoken})
            print(response_scoring)
            predictions = response_scoring.json()
            predict = predictions['predictions'][0]['values'][0][0]
            print("Final prediction :",predict)
           
            if(predict==1):
                predict1='Liver Disease'
                msg="Predicted Result shows there is a possibility of Liver Disease"
            else:
                predict1='No Liver Disease'
                msg="Predicted Result Shows No Liver Disease"
            sql2="insert into history values('"+str(email)+"','"+str(age)+"','"+str(gender)+"','"+str(tb)+"','"+str(db)+"','"+str(ap)+"','"+str(aa1)+"','"+str(aa2)+"','"+str(tp)+"','"+str(a)+"','"+str(agr)+"','"+str(predict1)+"')"
           
            exec_immediate(conn,sql2)
            # showing the prediction results in a UI# showing the prediction results in a UI
            if(predict==1):
                return render_template('liverdisease.html')
            else:
                return render_template('noLiverDisease.html')
    else:	
        return render_template('login.html')




if __name__ == "__main__":
    app.run(debug = True)