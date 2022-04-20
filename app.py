from flask import Flask, render_template, redirect, session, url_for, request
from flaskext.mysql import MySQL
import yaml
import uuid
import qrcode
from flask_selfdoc import Autodoc
import os
from datetime import datetime, timedelta
import cv2



app = Flask(__name__)
app.secret_key = os.urandom(16)
app.permanent_session_lifetime = timedelta(days=30)


#mysql configuration
db = yaml.safe_load(open('db.yaml'))
app.config['MYSQL_DATABASE_HOST'] = db['mysql_host']
app.config['MYSQL_DATABASE_USER'] = db['mysql_user']
app.config['MYSQL_DATABASE_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DATABASE_DB'] = db['mysql_db']

# init app
mysql = MySQL()
mysql.init_app(app)
auto = Autodoc(app)

# function to que mysql cursor
def get_cursor():
    cursor = mysql.get_db().cursor()
    return cursor


#image folder
imageFolder = os.path.join('static', 'img')
app.config['UPLOAD_FOLDER'] = imageFolder

#homepage render 
@app.route('/')
@auto.doc()
def index():
    backdrop_picture = os.path.join(app.config['UPLOAD_FOLDER'], 'backdrop.jpg')
    return render_template('index.html', pic1 = backdrop_picture)

# visitor registration page
@app.route('/visitor-registration', methods=['POST','GET'])
@auto.doc()
def visitorRegister():
    """Landing page, registration page for visitors.
    Form Data: 
        name: name of visitor
        password: password of visitor
        address: address of visitor
        city: city of visitor
    All fields are required.
    """
    # check if the visitor already has a saved session
    if "visitor_device_id" in session:
        return redirect(url_for('visitorHomepage'))

    cur = get_cursor()

    if request.method == 'GET':
        return render_template('visitor_registration.html'), 200

    # check that all fields are filled
    if request.method == 'POST' and 'fname' in request.form and 'lname' in request.form and 'address' in request.form \
        and 'city' in request.form and 'email' in request.form and 'phone' in request.form:

        session.permanent = True

        # get data from form and put it in database
        first_name_visitor =  request.form['fname']
        name = request.form['fname'] + " " + request.form['lname']
        address = request.form['address'] + ", " + request.form['city']
        email = request.form['email']
        phone = request.form['phone']
        device_id = uuid.uuid4()    # generate a unique string
        session["visitor_device_id"] = device_id

        cur.execute('INSERT INTO Visitor (visitor_name,address,email,phone_number, device_id) \
                VALUES (%s,%s,%s,%s,%s)' , (name, address, email, phone, device_id))
        mysql.get_db().commit()

        # putting the citizen id into the session, needed for QR code scanning
        cur.execute(f"SELECT citizen_id FROM Visitor WHERE device_id = '{device_id}'")
        session["citizen_id"] = cur.fetchone()[0]

        cur.close()
        
        return redirect(url_for('visitorHomepage', first_name = first_name_visitor)), 200
    else:
        return render_template('visitor_registration.html'), 400

# place registration page
@app.route('/place-registration', methods=['POST','GET'])
@auto.doc()
def placeRegister():
    """Landing page, registration page for visitors.
    Form Data: 
        name: name of visitor
        password: password of visitor
        address: address of visitor
        city: city of visitor
    All fields are required.
    """

    # check if the place already has a saved session
    if "place_device_id" in session:
        return redirect(url_for('placeHomepage')), 200

    if request.method == "GET":
        return render_template('place_registration.html'), 200
    cur = get_cursor()
    # check that all fields are filled
    if request.method == 'POST' and 'name' in request.form and 'address' in request.form \
    and 'city' in request.form and 'email' in request.form and 'phone' in request.form:

        session.permanent = True

        # get data from form and put it in database
        name = request.form['name']
        address = request.form['address'] + ", " + request.form['city']
        email = request.form['email']
        phone = request.form['phone']
        unique_QR = uuid.uuid4()        # generate a unique string
        session["place_device_id"] = unique_QR

        cur.execute('INSERT INTO Places (place_name,address,email,phone_number,QRcode) \
                VALUES (%s,%s,%s,%s,%s)' , (name, address, email, phone, unique_QR))
        mysql.get_db().commit()
        cur.close()
        return redirect(url_for('placeHomepage')), 200
    else:
        return render_template('place_registration.html'), 400


# agent sign in page
@app.route('/agent-signin', methods=['POST', 'GET'])
@auto.doc()
def agentSignin():
    """login page for agents.
    Form Data: 
        username: username of agent
        password: password of agent
    All fields are required.
    Must be a correct combination in the database
    """

    # check if agent has a saved session
    if "agent_device_id" in session:
        return redirect(url_for('agent_tools'))

    error = None
    cur = get_cursor()
    # check that all form fields are filled
    if request.method == 'POST' and 'username' in request.form  and 'password' in request.form:
        
        session.permanent = True
        unique_agent = uuid.uuid4()     # generate a unique string
        session["agent_device_id"] = unique_agent

        # get data from form and put it in database
        username = request.form['username']
        password = request.form['password']
        cur.execute("SELECT * FROM Agent A WHERE A.username = %s AND A.password = %s", (username, password))
        account = cur.fetchone()
        if account:
            session['loggedin'] = True
            session['username'] = username
            session['agent_id'] = account[0]
            cur.close()
            return redirect(url_for('agent_tools'))
        else:
            error = 'Error occured'
            return render_template('agent_signin.html', error=error)

    else:
        return render_template('agent_signin.html')

#hospital sign in page
@app.route('/hospital-signin', methods=['POST', 'GET'])
@auto.doc()
def hospitalSignin():
    """login page for hospital.
    Form Data: 
        username: username of hospital
        password: password of hospital
    All fields are required.
    Must be a correct combination in the database
    """

    # check if hospital has a session
    if "hospital_device_id" in session:
        return redirect(url_for('hospital_tools'))

    error = None
    cur = get_cursor()
    # check that all fields are filled
    if request.method == 'POST' and 'username' in request.form  and 'password' in request.form:

        session.permanent = True
        unique_hospital = uuid.uuid4()      # generate a unique string
        session["hospital_device_id"] = unique_hospital

        # get data from form and put it in database
        username = request.form['username']
        password = request.form['password']
        cur.execute("SELECT * FROM Hospital A WHERE A.username = %s AND A.password = %s", (username, password))
        account = cur.fetchone()
        if account:
            session['loggedin'] = True
            session['username'] = username
            session['hospital_id'] = account[0]
            cur.close()
            return redirect(url_for('hospital_tools'))
        else:
            error = 'Error occured'
            return render_template('hospital_signin.html', error=error)

    else:
        return render_template('hospital_signin.html')

# visitor homepage
@app.route('/visitor-homepage/<first_name>')
@auto.doc()
def visitorHomepage(first_name):
    # if the visitor is not in session return to home
    if "visitor_device_id" not in session:
        return redirect('/')
    return render_template('visitor_homepage.html', first_name = first_name)

# place homepage
@app.route('/place-homepage')
@auto.doc()
def placeHomepage():
    # if the place is not in session return to home
    if "place_device_id" not in session:
        return redirect('/')

    return render_template('place_homepage.html')


#QR PICture folder
QRimageFolder = os.path.join('static', 'QR')
app.config['UPLOAD_FOLDER'] = QRimageFolder

# downloads QR to device
@app.route('/download-QR')
@auto.doc()
def downloadQR():
    # generate unique QR code that carries the place session as data
    qr = qrcode.QRCode(
        version=1,
        box_size=15,
        border=15
    )
    data = session["place_device_id"]
    qr.add_data(data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill = 'black', back_color='white')
    # saves image to file
    qr_img.save("static/QR/PlaceQR.png")
    qr_picture = os.path.join(app.config['UPLOAD_FOLDER'], 'PlaceQR.png')
    return render_template('place_homepage.html', qr = qr_picture)

# page to scan a QR code
@app.route('/scan-QR')
@auto.doc()
def scanQR():
    ''' Handles QR code scanning and visitor check-in into a place
    '''
    if "visitor_device_id" not in session:
        return redirect('/')
    # initalize the cam
    cap = cv2.VideoCapture(0)
    # initialize the cv2 QRCode detector
    detector = cv2.QRCodeDetector()
    while True:
        _, img = cap.read()
        # detect and decode
        data, bbox, _ = detector.detectAndDecode(img)
        # check if there is a QRCode in the image
        if data:
            a=data
            break
        # display the result
        cv2.imshow("QRCODEscanner", img)    
        if cv2.waitKey(1) == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    # scanning the QR code using javascript

    # fetching the place mentioned in the QR code
    qr_code = str(a)
    cur = get_cursor()
    cur.execute(f"""SELECT place_id, place_name FROM Places WHERE QRcode = '{qr_code}';""")
    place = cur.fetchone()
    if(place is not None): # checking if there is a hit
        # get all info needed to make an entry in VisitorToPlaces
        # get info about the place 
        place_id = place[0]
        place_name = place[1]
        # info about visitor (citizen_id, device_id)
        device_id = session["visitor_device_id"]
        citizen_id = session["citizen_id"]
        # get current timestamp
        dt = datetime.now()
        entry_timestamp = dt.strftime("%Y-%m-%d %H:%M:%S") # converting to sql supported format
        # add entry in VisitorToPlaces
        cur = get_cursor()
        #exit time stamp will be NULL until the user checks out of the place
        cur.execute(f"""INSERT INTO VisitorToPlaces  (QRcode, device_id, entry_timestamp, exit_timestamp, citizen_id, place_id)
                        VALUES ('{qr_code}','{device_id}','{entry_timestamp}',NULL,{citizen_id},{place_id})""")
        mysql.get_db().commit()
        cur.close()

        # creating additionnal session elements (used for timer and log-out)
        session['current_place_id'] = place_id # to update exit timestamp later on
        session['entry_timestamp'] = entry_timestamp # to configure timer relative to it

        # user feedback
        message = f"Connected to: {place_name}"
        logout = 1 # wether or not to show the log-out button and timer

    else:
        message = "Invalid QR Code, no place is linked to it."
        logout = 0

    return render_template('visitor_QR_scan.html', message=message, logout=logout) , 200

# visitor check-out route
@app.route('/visitor_check_out',methods=['POST','GET'])
@auto.doc()
def visitor_check_out():
    '''checks out visitor from place by updating entry with exit_timestamp
       ends visitor session
    '''
    if "visitor_device_id" not in session:
        return redirect('/')

    # get current timestamp
    dt = datetime.now()
    exit_timestamp = dt.strftime("%Y-%m-%d %H:%M:%S") # converting to sql supported format
    # updating the entry in VisitorToPlaces in order to reflect exit_timestamp
    cur = get_cursor()
    cur.execute(f"""
                    UPDATE VisitorToPlaces
                    SET exit_timestamp = '{exit_timestamp}'
                    WHERE device_id = '{session["visitor_device_id"]}' AND
                          entry_timestamp = '{session["entry_timestamp"]}' AND
                          place_id = {session["current_place_id"]};  
                """)
    mysql.get_db().commit()
    cur.close()

    # deleting current visitor session
    session.pop("entry_timestamp", None)
    session.pop("current_place_id", None)
    session.pop("visitor_device_id", None)
    return redirect('/')

# impressum page
@app.route('/impressum',methods=['POST','GET'])
@auto.doc()
def impressum():
    return render_template('imprint.html')

# agent tools page
@app.route('/agent_tools', methods=['POST','GET'])
@auto.doc()
def agent_tools():
    """agent tools page.
    Implementation pending
    """
    # if the agent is not in session return to home
    if "agent_device_id" not in session:
        return redirect('/')

    cur = get_cursor()
    cur.execute('SELECT citizen_id, visitor_name FROM Visitor WHERE infected')
    infected_people = cur.fetchall()
    # Struggling to figure out the query for places with infected visitors
    # TO DO
    cur.execute('SELECT place_id, place_name FROM Places')
    infected_places = cur.fetchall()
    return render_template('agent_tools.html',
        infected_people = infected_people, infected_places = infected_places) , 200

# searching page for visitors, allows searching using 
# visitor name, address, phone number and so on, all in one field
# only accessible by agents and hospitals
@app.route('/search_visitors', methods=['POST','GET'])
@auto.doc()
def search_visitors():
    """Page for searching / displaying visitors  
    """
    # accessible by both agents and hospitals
    if ("agent_device_id" not in session) and ("hospital_device_id" not in session):  
        return redirect('/')


    if request.method == "GET":
        cur = get_cursor()
        cur.execute(f"""SELECT citizen_id, visitor_name, address, email, 
                               phone_number, device_id, infected FROM Visitor;""")
        people = cur.fetchall()    
        return render_template('search_visitors.html',data=people), 200
    # POST request for searching
    if request.method == "POST":
        entry = request.form['entry']
        cur = get_cursor()
        cur.execute(f"""SELECT citizen_id, visitor_name, address, email, 
                               phone_number, device_id, infected FROM Visitor
                        WHERE citizen_id LIKE '%{entry}%' OR visitor_name LIKE '%{entry}%' OR
                              address LIKE '%{entry}%' OR email LIKE '%{entry}%' OR 
                              phone_number LIKE '%{entry}%';""")
        people = cur.fetchall()
        return render_template('search_visitors.html',data=people), 200

# route to display info of infected people and places visited by that person
@app.route('/agent_visitor_info', methods=['POST','GET'])
@auto.doc()
def agent_visitor_info():
    """display visitor info and places the visitor has been to
    """
    # if the agent is not in session return to home
    if "agent_device_id" not in session:
        return redirect('/')

    # handling post request
    if request.method == "POST":

        citizen_id = request.form["visitors"]
        # running a query to get the info of the selected visitor
        cur = get_cursor()
        cur.execute(f"""SELECT citizen_id, visitor_name, address, email, 
                               phone_number, device_id, infected 
                        FROM Visitor
                        WHERE citizen_id = {citizen_id};""")
        visitor_info = cur.fetchone()

        # running a query to get the places the visitor visited along with entry and exit timestamps

        cur = get_cursor()
        cur.execute(f""" SELECT P.place_id, P.place_name, VP.entry_timestamp, VP.exit_timestamp, P.address, P.email, P.phone_number
                         FROM Places P 
                         INNER JOIN VisitorToPlaces VP ON P.place_id = VP.place_id
                         WHERE VP.citizen_id = {citizen_id}; 
                    """)
        places_visited = cur.fetchall()
    
    return render_template('agent_visitor_info.html', visitor_info = visitor_info , places_visited=places_visited), 200



# searching page for visitors, allows searching using 
# visitor name, address, phone number and so on, all in one field
# only accessible by agents
@app.route('/agent_search_hospitals', methods=['POST','GET'])
@auto.doc()
def agent_search_hospitals():
    """Page for searching / displaying hospitals  
    """
    if "agent_device_id" not in session:
        return redirect('/')
    # At first, all the data is displayed
    if request.method == "GET":
        cur = get_cursor()
        cur.execute(f"""SELECT hospital_id, username FROM Hospital;""")
        hospitals = cur.fetchall()    
        return render_template('agent_search_hospitals.html',data=hospitals), 200
    # POST request for searching
    if request.method == "POST":
        entry = request.form['entry']
        cur = get_cursor()
        cur.execute(f"""SELECT hospital_id, username FROM Hospital
                        WHERE hospital_id LIKE '%{entry}%' OR username LIKE '%{entry}%';""")
        hospitals = cur.fetchall()
        return render_template('agent_search_hospitals.html',data=hospitals), 200

# agent route for search places
@app.route('/agent_search_places', methods=['POST', 'GET'])
def agent_search_places():
    if "agent_device_id" not in session:
        return redirect('/')
    # At first, all the data is displayed
    if request.method == "GET":
        cur = get_cursor()
        cur.execute(f"""SELECT place_id, place_name, address, email, phone_number, QRcode FROM Places;""")
        places = cur.fetchall()    
        return render_template('agent_search_places.html',data=places), 200
    # POST request for searching
    if request.method == "POST":
        entry = request.form['entry']
        cur = get_cursor()
        cur.execute(f"""SELECT place_id, place_name, address, email, phone_number, QRcode FROM Places
                        WHERE place_id LIKE '%{entry}%' OR place_name LIKE '%{entry}%' OR
                              address LIKE '%{entry}%' OR email LIKE '%{entry}%' OR
                              phone_number LIKE '%{entry}%';""")
        places = cur.fetchall()
        return render_template('agent_search_places.html',data=places), 200

# hospital registration route, only accessible by Agents
@app.route('/hospital_register', methods=['POST','GET'])
@auto.doc()
def hospital_register():
    """hospital registration route, will handle post requests coming
       from the registration form for agents  
    """
    # if the agent is not in session return to home
    if "agent_device_id" not in session:
        return redirect('/')

    cur = get_cursor()
    # handling post request
    if request.method == 'POST' and 'username' in request.form  and 'password' in request.form:
        username = request.form["username"]
        password = request.form["password"]

        cur.execute('INSERT INTO Hospital (username, password) \
                VALUES (%s,%s)' , (username, password))
        mysql.get_db().commit()
        cur.close()
        return render_template('agent_tools.html', message=f"successfully registered {username}"), 200

#hospital tools page
@app.route('/hospital_tools',methods=['POST','GET'])
@auto.doc()
def hospital_tools():
    """hospital tools page.
    Implementation pending
    """
    # if the hospital is not in session return to home
    if "hospital_device_id" not in session:
        return redirect('/')

    cur = get_cursor()
    cur.execute('SELECT citizen_id, visitor_name FROM Visitor WHERE infected = 1')
    infected_people = cur.fetchall()
    # Struggling to figure out the query for places with infected visitors
    cur.execute('SELECT place_id, place_name FROM Places')
    infected_places = cur.fetchall()
    return render_template('hospital_tools.html', infected_people = infected_people, infected_places = infected_places)

# route to mark people as infected
@app.route('/hospital_DB_status_change', methods=['GET', 'POST'])
@auto.doc()
def hospital_DB_status_change():
    if "hospital_device_id" not in session:
        return redirect('/')
    if request.method == "GET":
        return render_template('hospital_DB_status_change.html', message=""), 200

    if request.method == "POST":
        # Obtain data from request object
        name = request.form['fname'] + " " + request.form['lname']
        status = request.form['status']

        # check to see if the person exists in the database
        cur = get_cursor()
        command = f"SELECT * FROM Visitor WHERE visitor_name LIKE '{name}'"
        cur.execute(command)
        visitors = cur.fetchall()
        # if yes then update the status
        if len(visitors) > 0:
            command = f"UPDATE Visitor SET infected = {status} WHERE visitor_name LIKE '{name}'"
            cur.execute(command)
            mysql.get_db().commit()
            # display confirmation message
            message = f"{name.title()} was successfully set as " + ("infected." if int(status) else "not infected.")
        # if not an error message is displayed
        else:
            message = f"The is no user named {name.title()}"
        cur.close()

        return render_template('hospital_DB_status_change.html', message=message), 200

# Add /docs at the end of the standard link for the documentation
@app.route('/docs')
def docs():
    return auto.html(title='Corona Center API Docs')


@app.route('/visitor-logout')
def visitorLogout():
    """
        Deletes visitor session and returns to homepage
    """
    session.pop("visitor_device_id", None)
    return redirect('/')

@app.route('/place-logout')
def placeLogout():
    """
        Deletes place session and returns to homepage
    """
    session.pop("place_device_id", None)
    return redirect('/')

@app.route('/agent-logout')
def agentLogout():
    """
        Deletes agent session and returns to homepage
    """
    session.pop("agent_device_id", None)
    return redirect('/')

@app.route('/hospital-logout')
def hospitalLogout():
    """
        Deletes hospital session and returns to homepage
    """
    session.pop("hospital_device_id", None)
    return redirect('/')

@app.route('/user-search', methods=['POST', 'GET'])
def UserSearch():
    pass
    
    
    
    
if __name__ == "__main__":
    app.run(debug = True)
