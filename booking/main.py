from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask import jsonify

app = Flask(__name__)
app.secret_key = 'super_slepena_atslega'

#datubaze
def get_db_connection():
    con = sqlite3.connect("booking_db.db")
    con.row_factory = sqlite3.Row
    return con

@app.route("/home")
def home():
    return render_template("home.html", epasts=session['epasts'])

@app.route("/")
def index():
    return render_template("index.html")


#ielogoties
@app.route("/index", methods=['GET', 'POST'])
def login():
    zina = ""
    if request.method == 'POST':
        epasts = request.form['epasts']
        parole = request.form['parole']
        
        con = get_db_connection()
        cur = con.cursor()
        cur.execute('SELECT * FROM login WHERE epasts=?', (epasts,))
        rekords = cur.fetchone()
        
        if rekords:
            stored_hash = rekords['parole']
            if check_password_hash(stored_hash, parole):
                session['ielogojas'] = True
                session['epasts'] = rekords['epasts']
                return redirect(url_for('home'))
            else:
                zina = 'Nepareizs epasts vai parole. Mēģiniet velreiz.'
        else:
            zina = 'Nepareizs epasts vai parole. Mēģiniet velreiz.'
    
    return render_template('index.html', zina=zina)

#reģistrācija
@app.route("/signup", methods=['GET', 'POST'])
def signup():
    zina = ""
    if request.method == 'POST':
        vards = request.form['vards']
        info = request.form['info']
        epasts = request.form['epasts']
        parole = request.form['parole']
    
        hashed_password = generate_password_hash(parole, method='pbkdf2:sha256')
        
        con = get_db_connection()
        cur = con.cursor()
        cur.execute('SELECT * FROM login WHERE epasts=?', (epasts,))
        existing_user = cur.fetchone()
        
        if existing_user:
            zina = "Šis e-pasts jau ir reģistrēts."
        else:
            cur.execute('INSERT INTO login (vards, info, epasts, parole) VALUES (?, ?, ?, ?)', 
                        (vards, info, epasts, hashed_password))
            con.commit()
            zina = "Jūs esat veiksmīgi reģistrēti!" 
            
    return render_template("signup.html", zina=zina)

#navigacijaa 
@app.route("/home")
def homee():
    if 'epasts' not in session:
        return redirect(url_for('login'))
    con = get_db_connection()
    cur = con.cursor()
    cur.execute('SELECT * FROM login WHERE epasts = ?', (session['epasts'],))
    user = cur.fetchone()
    return render_template("home.html", user=user)

@app.route("/profils")
def profils():
    if 'epasts' not in session:
        return redirect(url_for('login')) #parbauda 
    con = get_db_connection()
    cur = con.cursor()
    cur.execute('SELECT * FROM login WHERE epasts = ?', (session['epasts'],)) #no datubazes panem
    user = cur.fetchone()
    return render_template("profils.html", user=user)

@app.route("/pievienot_rezerv", methods=['POST'])
def pievienot_rezerv():
    if 'epasts' not in session:
        return jsonify({"zina": "Jums jābūt ielogotam!"}), 401

    dati = request.get_json()
    id = dati.get('id')
    datums = dati.get('datums')
    tituls = dati.get('tituls')
    sakumaLaiks = dati.get('sakumaLaiks')
    beiguLaiks = dati.get('beiguLaiks')

    con = get_db_connection()
    cur = con.cursor()

    if id:
        cur.execute("UPDATE rezervacijas SET tituls=?, datums=?, sakumaLaiks=?, beiguLaiks=? WHERE id=?", 
                    (tituls, datums, sakumaLaiks, beiguLaiks, id))
    else:
        cur.execute("INSERT INTO rezervacijas (epasts, tituls, datums, sakumaLaiks, beiguLaiks) VALUES (?, ?, ?, ?, ?)", 
                    (session['epasts'], tituls, datums, sakumaLaiks, beiguLaiks))

    con.commit()
    con.close()
    return jsonify({"zina": "Rezervācija saglabāta!"})



@app.route("/dabut_rezerv")
def dabut_rezervaciju():
    if 'epasts' not in session:
        return jsonify([]) #atdod neko ja nav ielogojis

    con = get_db_connection()
    cur = con.cursor()
    cur.execute("SELECT id, tituls, datums, sakumaLaiks, beiguLaiks FROM rezervacijas WHERE epasts = ?", (session['epasts'],))
    rezervacijas = cur.fetchall()

    events = [{"id": res["id"], "title": res["tituls"], "start": f"{res['datums']}T{res['sakumaLaiks']}", 
               "end": f"{res['datums']}T{res['beiguLaiks']}", "sakumaLaiks": res["sakumaLaiks"], "beiguLaiks": res["beiguLaiks"]} for res in rezervacijas]
    #res - ciklaa apstradaa katru ierakstu un partaisa par dictionary lai kalendaraa var rezdet
    return jsonify(events)

@app.route("/dzest_rezerv/<int:id>", methods=['DELETE'])
def dzest_rezerv(id):
    con = get_db_connection()
    cur = con.cursor()
    cur.execute("DELETE FROM rezervacijas WHERE id=?", (id,))
    con.commit()
    return jsonify({"zina": "Rezervācija dzēsta!"})

@app.route("/redzet_rezerv")
def redzet_rezerv():
    if 'epasts' not in session:
        return redirect(url_for('login'))  # Ensure user is logged in

    con = get_db_connection()
    cur = con.cursor()
    cur.execute("SELECT id, tituls, datums, sakumaLaiks, beiguLaiks FROM rezervacijas WHERE epasts = ?", (session['epasts'],))
    rezervacijas = cur.fetchall()

    return render_template("redzet_rezerv.html", rezervacijas=rezervacijas)


#iziet
@app.route("/logout", methods=['POST'])
def iziet():
    session.clear()
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=80)
