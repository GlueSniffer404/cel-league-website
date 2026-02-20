from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "CEL_SECRET_2026"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
db = SQLAlchemy(app)

ADMIN_USER = "CEL-Admin"
ADMIN_PASS = "CEL!Comp_EuroLeague@2026"

# ---------- MODELS ----------

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    manager = db.Column(db.String(100))
    player1 = db.Column(db.String(100))
    player2 = db.Column(db.String(100))
    player3 = db.Column(db.String(100))
    sub1 = db.Column(db.String(100))
    sub2 = db.Column(db.String(100))

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team1 = db.Column(db.String(100))
    team2 = db.Column(db.String(100))
    score1 = db.Column(db.Integer)
    score2 = db.Column(db.Integer)
    date = db.Column(db.String(50))
    played = db.Column(db.Boolean, default=False)
    match_type = db.Column(db.String(20)) # league / major / shield / friendly

with app.app_context():
    db.create_all()

# ---------- LOGIN ----------

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == ADMIN_USER and request.form["password"] == ADMIN_PASS:
            session["admin"] = True
            return redirect("/admin")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------- PUBLIC ----------

@app.route("/")
def index():
    tab = request.args.get("tab","standings")

    teams = Team.query.all()
    upcoming = Match.query.filter_by(played=False).order_by(Match.date).all()

    league_results = Match.query.filter_by(played=True, match_type="league").all()
    major_results = Match.query.filter_by(played=True, match_type="major").all()
    shield_results = Match.query.filter_by(played=True, match_type="shield").all()
    friendly_results = Match.query.filter_by(played=True, match_type="friendly").all()

    # standings (points only)
    table = {t.name:{"played":0,"wins":0,"draws":0,"losses":0,"points":0} for t in teams}

    for m in league_results:
        if m.team1 not in table or m.team2 not in table:
            continue

        table[m.team1]["played"]+=1
        table[m.team2]["played"]+=1

        if m.score1 > m.score2:
            table[m.team1]["wins"]+=1
            table[m.team1]["points"]+=3
            table[m.team2]["losses"]+=1
        elif m.score2 > m.score1:
            table[m.team2]["wins"]+=1
            table[m.team2]["points"]+=3
            table[m.team1]["losses"]+=1
        else:
            table[m.team1]["draws"]+=1
            table[m.team2]["draws"]+=1
            table[m.team1]["points"]+=1
            table[m.team2]["points"]+=1

    sorted_table = sorted(table.items(), key=lambda x:x[1]["points"], reverse=True)

    return render_template(
        "index.html",
        tab=tab,
        table=sorted_table,
        upcoming=upcoming,
        league_results=league_results,
        major_results=major_results,
        shield_results=shield_results,
        friendly_results=friendly_results
    )

# ---------- ADMIN ----------

@app.route("/admin")
def admin():
    if not session.get("admin"): return redirect("/login")
    teams = Team.query.all()
    matches = Match.query.filter_by(played=False).order_by(Match.date).all()
    return render_template("admin.html", teams=teams, matches=matches)

@app.route("/add_team", methods=["POST"])
def add_team():
    if not session.get("admin"): return redirect("/")
    t = Team(**request.form)
    db.session.add(t)
    db.session.commit()
    return redirect("/admin")

@app.route("/edit_team/<int:id>", methods=["GET","POST"])
def edit_team(id):
    if not session.get("admin"): return redirect("/")
    team = Team.query.get(id)

    if request.method=="POST":
        for field in request.form:
            setattr(team, field, request.form[field])
        db.session.commit()
        return redirect("/admin")

    return render_template("edit_team.html", team=team)

@app.route("/add_match", methods=["POST"])
def add_match():
    if not session.get("admin"): return redirect("/")

    match_type = request.form.get("type")

    m = Match(
        team1=request.form["team1"],
        team2=request.form["team2"],
        date=request.form["date"],
        match_type=match_type
    )
    db.session.add(m)
    db.session.commit()
    return redirect("/admin")

@app.route("/set_result/<int:id>", methods=["POST"])
def set_result(id):
    if not session.get("admin"): return redirect("/")
    m = Match.query.get(id)
    m.score1=int(request.form["score1"])
    m.score2=int(request.form["score2"])
    m.played=True
    db.session.commit()
    return redirect("/admin")

@app.route("/wipe")
def wipe():
    if not session.get("admin"): return redirect("/")
    db.drop_all()
    db.create_all()
    return redirect("/admin")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=25565, debug=True)