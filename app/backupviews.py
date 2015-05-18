from app import app
from flask import render_template, flash, redirect, session, request
from .forms import JoinForm, ValidateForm, SprocketForm, CreateEvent, Notify
from models import db, generateLongID, adminLoginCheck, generateShortID, sanitary, getSQLList, getSQLDict, loginCheck, uploadFile
from sqlalchemy.sql import text
from twilio.rest import TwilioRestClient
import datetime, calendar

app.secret_key = "MisOKjjkeD0L1j48GuDN"

@app.route('/')
@app.route('/index')
@app.route('/home')
@app.route('/index.html')
def index():
    return render_template('index.html')
	
@app.route('/about')
@app.route('/about.html')
def about():
    return redirect('/index.html')
	
@app.route('/join', methods=['GET', 'POST'])
@app.route('/join.html', methods=['GET', 'POST'])
def join():
	form = JoinForm()
	if form.validate_on_submit():	
		#Obtain Data from form after Validation
		fname = form.fname.data
		lname = form.lname.data
		
		year = form.year.data
		major = form.major.data
		focus = form.focus.data
		
		phone = form.phone.data
		email = form.email.data
		canText = form.cantext.data
		
		about = form.about.data

		password = form.password.data
		
		#Fix Phone Input
		temp = ""
		for each in phone:
			if each != "(" and each != ")" and each != "-":
				temp += each
		phone = temp
		del temp
		
		#Fix canText Input
		if canText == "No":
			canText = 0;
		else:
			canText = 1;

		#Commit to Database and Route User to Phone Validation	
		sql = """INSERT INTO `Users`(`password`, `level`, `status`, `fname`, `lname`, `year`, `major`, `focus`, `phone`, `email`, 
			`cantext`, `about`) VALUES (:password,0,0,:fname,:lname,:year,:major,:focus,:phone,:email,:cantext,:about)"""
		connection = db.engine.connect()		
		connection.execute(text(sql), password = password, fname = fname, lname = lname, year = year, major = major, focus = focus, phone = phone, email = email, cantext = canText, about = about)
		#Create Login Validation Number
		sql = """UPDATE Users SET loginValidation = :randomValidation WHERE phone = :phone"""
		connection.execute(text(sql), randomValidation = generateShortID(), phone = phone)

		#Login User
		currentKey = generateLongID()
		session['id'] = currentKey

		if session['id'] == currentKey:
			connection.execute(text('UPDATE Users SET loginid = :currentKey WHERE phone = :phone'), currentKey = currentKey, phone = phone)
		else:
			return redirect('/error')
		return redirect('/validate')
	return render_template('join.html', form=form)
	
@app.route('/events')
@app.route('/events.html')
def events():
	now = datetime.datetime.now()
	#Check to see if month requested
	if sanitary(request.args.get('month')):
		if request.args.get('month') is not None:
			month = request.args.get('month')
		else:
			month = str(now.month)
			#Zero Padding
			month = month if int(month) > 10 else '0'+month
	else:
		return redirect('/error')

        #Check to see if Year requested
        if sanitary(request.args.get('year')):
                if request.args.get('year') is not None:
                        year = request.args.get('year')
                else:
                        year = str(now.year)
        else:
                return redirect('/error')

	#Find the first and second day of the week in requested Month
	boxIndex = datetime.datetime.strptime(month + ' 01 ' + year , '%m %d %Y').strftime('%w')
	secondStart = 8 - int(boxIndex)
	
	#Next Month
	endMonth = str(int(month) + 1) if int(month) != 12 else str(1)
	endYear = year if int(endMonth) != 1 else str(int(year) + 1)
	
	#Get all events for given month
	sqlDateStart = year + '-' + month + '-01'
	sqlDateEnd = datetime.date(int(endYear), int(endMonth), 1) - datetime.timedelta(days = 1)
	sql = "SELECT * FROM Events WHERE Date BETWEEN :sqlDateStart AND :sqlDateEnd"
        connection = db.engine.connect()
        rows = connection.execute(text(sql), sqlDateStart = sqlDateStart, sqlDateEnd = sqlDateEnd)
	rows = getSQLDict(rows)
	
	#Get Featured Event
	featuredList = []
	for each in rows:
		if each['Featured'] == 1 and each['Date'] <= now.date():
			featuredList.append(each)
	newlist = sorted(featuredList, key=lambda k: k['Date'])
	if not newlist and rows:
		featured = rows[0]
	elif newlist:
		featured = newlist[0]
	else:
		featured = None

	#Add list for each day	
	eventsByDay = []
	emptyList = []
	for block in range (0 , int(sqlDateEnd.strftime('%d'))+1):
		eventsByDay.append(list(emptyList)) 
	for each in rows:
		day = int(each['Date'].strftime('%d'))
		eventsByDay[day].append(each)

	nMonth = calendar.month_name[int(month)]
	previousMonth = int(month) - 1 if int(month) - 1 != 0 else 12
	nextMonth = int(month) + 1 if int(month) + 1 != 13 else 1

	return render_template('events.html', startingDay = int(boxIndex), events = eventsByDay, secondStart = secondStart, lastDay = int(sqlDateEnd.strftime('%d')), featured = featured, Month = nMonth, nextMonth = nextMonth, previousMonth = previousMonth)

@app.route('/eventhandler')
@app.route('/eventhandler.html')
def eventhandler():
	sql = "SELECT * FROM Events WHERE EventId = :query"
	connection = db.engine.connect()
        
	#Check to see if ID requested
        if sanitary(request.args.get('e')):
                if request.args.get('e') is not None:
                        query = request.args.get('e')
                else:
                        return redirect('/events')
        else:
                return redirect('/error')

	rows = connection.execute(text(sql), query = query)
	rows = getSQLDict(rows)[0]
	
	return render_template('eventhandler.html', Title = rows['Title'], Description = rows['Description'], ImgDirectory = rows['ImgDirectory'])

@app.route('/validate', methods=['GET', 'POST'])
@app.route('/validate.html', methods=['GET', 'POST'])
def validate():
    vform = ValidateForm()
    #Check the current ID with logged in IDs
    sql = "SELECT loginValidation,canText,phone,status FROM Users WHERE loginid = :loginCookie"

    #Send Text
    ACCOUNT_SID = "AC3eb2aaedda1d2decf032a0b4956c2d02" 
    AUTH_TOKEN = "ae4199cac8c0e75c0f97f3c812895043" 
 
    client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN) 
 
    if not sanitary(session['id']):
               return redirect('/sprocket')
    else:
               inputLoginCookie = session['id']

    #Connect to db and see if there's a loginVal with given loginID
    connection = db.engine.connect()
    rows = connection.execute(text(sql), loginCookie = inputLoginCookie)
    #Validate cookie with inputLogin
    result = getSQLDict(rows)

    if len(result) > 1:
            return redirect('/error')
    elif len(result) == 0:
            return redirect('/error')
    #Check if user already validated
    if result[0]['status'] != 0:
        return redirect('/sprocket')

    if vform.validate_on_submit():
        inputLoginValidation = vform.validationCode.data
        if str(result[0]['loginValidation']) == str(inputLoginValidation):
            sql = "UPDATE Users SET status = 1, loginValidation = NULL  WHERE loginid = :inputLogin"
            connection.execute(text(sql), inputLogin = inputLoginCookie)
            return redirect('/sprocket')
        else:
            return redirect('/error')

    #Notify User via text or email
    if result[0]['canText'] == True:
        textMessage = "Welcome to ASME! Your validation code is " + str(result[0]['loginValidation']) + ". See you around campus!"

        client.messages.create(
            to=result[0]['phone'],
            from_="+19254758577",
            body=textMessage
        )
        messageType = "text message"
    else:
        #Send Email
        messageType = "email"
    return render_template('validate.html', validationType = messageType, form = vform)
	
@app.route('/sprocket', methods=['GET', 'POST'])
@app.route('/sprocket.html', methods=['GET', 'POST'])
def sprocketlogin():
	form = SprocketForm()
	connection = db.engine.connect()	

	if loginCheck():
                return redirect('/sprockethandle')
        else:
                pass
	
	if form.validate_on_submit():
		phoneInput = form.phoneInput.data
		password = form.password.data
		sql = "SELECT loginid FROM Users WHERE phone = :phoneInput AND password = :password"
		result = getSQLList(connection.execute(text(sql), phoneInput = phoneInput, password = password))
		if len(result) > 1:
                	return redirect('/error')
        	elif len(result) == 0:
			flash('Incorrect Phone Number or Password')
			return redirect('/sprocket.html')
        	else:
			session['id'] = result[0]
			print "Login Successful"
			return redirect('/sprockethandle')
	return render_template('sprocket.html', form = form)

@app.route('/sprockethandle')
@app.route('/sprockethandle.html')
def sprocketHandle():
	#List Standard Commands
	Commands = [
	{"name":"Print in ASME Clubroom", "link":"print"}
	]

	#List Admin Commands
	adminCommands = [
	{"name":"Schedule Event", "link":"schedule"},
	{"name":"Manual Notification", "link":"notify"}
	]

	if not loginCheck():
		return redirect('/sprocket')
	else:
		sessionid = session['id']

	connection = db.engine.connect()	
	#Is user admin?
	sql = "SELECT level FROM Users WHERE loginid = :sessionid"
	result = getSQLList(connection.execute(text(sql), sessionid = sessionid))
	#If so, add admin Commands
	if len(result) == 1 and result[0] == 1:
		for each in adminCommands:
			Commands.insert(0, each)
	
	return render_template('sprockethandle.html', commands = Commands)

@app.route('/schedule', methods=['GET', 'POST'])
@app.route('/schedule.html', methods=['GET', 'POST'])
def schedule():
	if adminLoginCheck() == False:
		return redirect('/error')
	form = CreateEvent()
	if form.validate_on_submit():
		title = form.title.data
		date = form.date.data
		time = form.time.data
		shortDescription = form.shortDescription.data
		description = form.description.data
		address = form.address.data
		featured = form.featured.data

		file = request.files['eventPicture']
		fileDir = uploadFile(file)
		
                if fileDir == None:
			return redirect('/error')
		fileDir = "static/events/" + fileDir

		connection = db.engine.connect()

		sql = "SELECT MAX(EventId) AS EventIdMax FROM Events"
		result = getSQLList(connection.execute(text(sql)))
		result = int(result[0]) + 1
		sql = """INSERT INTO `Events`(`EventId`,`Title`, `Time`, `Date`, `Description`, `ShortDescription`, `ImgDirectory`, `Address`, `Featured`)
		VALUES (:EventId,:title,:time,:date,:description,:shortDescription,:fileDir,:address,:featured)"""
                connection.execute(text(sql), EventId = result, title = title, time = time, date = date, description = description, shortDescription = shortDescription, fileDir = fileDir, address = address, featured = featured)
	        
	return render_template('schedule.html', form = form)

@app.route('/notify', methods=['GET', 'POST'])
@app.route('/notify.html', methods=['GET', 'POST'])
def notify():	
	if adminLoginCheck() == False:
		session["id"] = None
                return redirect('/error')
	form = Notify()
	if form.validate_on_submit():
    		ACCOUNT_SID = "AC3eb2aaedda1d2decf032a0b4956c2d02"
    		AUTH_TOKEN = "ae4199cac8c0e75c0f97f3c812895043"
    		client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN)

		numbers = form.manualList.data.split(",")
		message = form.message.data
		if numbers == "":
			sql = 'SELECT phone FROM Users'
			connection = db.engine.connect()
			result = getSQLList(connection.execute(text(sql)))
			numbers = result
		textMessage = message

		for each in numbers:
        		client.messages.create(
            			to=each,
            			from_="+19254758577",
            			body=textMessage
        		)

	return render_template('notify.html', form = form)

@app.route('/error')
@app.route('/error.html')
def error():
    return render_template('error.html')

@app.route('/logout')
@app.route('/logout.html')
def logout():
	print "Logout Successful of user " + str(session['id'])
	session['id'] = None
	return render_template('index.html')
