from flask import Flask, render_template, request, redirect
from flask_login import login_user, logout_user, login_required
from datetime import datetime

from config import Config
from models import db, User, Event, Resource, Allocation
from auth import login_manager

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = "login"

with app.app_context():
    db.create_all()
    if not User.query.first():
        db.session.add(User(username="admin", password="admin", role="admin"))
        db.session.commit()

# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(
            username=request.form["username"],
            password=request.form["password"]
        ).first()
        if user:
            login_user(user)
            return redirect("/")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

# ---------- DASHBOARD ----------
@app.route("/")
@login_required
def dashboard():
    resource_usage = {
        r.name: Allocation.query.filter_by(resource_id=r.id).count()
        for r in Resource.query.all()
    }

    upcoming_events = Event.query.filter(
        Event.start_time >= datetime.now()
    ).order_by(Event.start_time).limit(5).all()

    return render_template(
        "dashboard.html",
        resource_usage=resource_usage,
        upcoming_events=upcoming_events
    )

# ---------- EVENTS ----------
@app.route("/events", methods=["GET", "POST"])
@login_required
def events():
    if request.method == "POST":
        db.session.add(Event(
            title=request.form["title"],
            start_time=datetime.fromisoformat(request.form["start"]),
            end_time=datetime.fromisoformat(request.form["end"]),
            description=request.form["description"]
        ))
        db.session.commit()
    return render_template("events.html", events=Event.query.all())

@app.route("/events/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_event(id):
    event = Event.query.get_or_404(id)

    if request.method == "POST":
        event.title = request.form["title"]
        event.start_time = datetime.fromisoformat(request.form["start"])
        event.end_time = datetime.fromisoformat(request.form["end"])
        event.description = request.form["description"]
        db.session.commit()
        return redirect("/events")

    return render_template("edit_event.html", event=event)

@app.route("/events/delete/<int:id>")
@login_required
def delete_event(id):
    Event.query.filter_by(id=id).delete()
    db.session.commit()
    return redirect("/events")

# ---------- RESOURCES ----------
@app.route("/resources", methods=["GET", "POST"])
@login_required
def resources():
    if request.method == "POST":
        rtype = request.form["type"]
        if rtype == "Other":
            rtype = request.form["custom_type"]

        db.session.add(Resource(
            name=request.form["name"],
            type=rtype
        ))
        db.session.commit()

    return render_template("resources.html", resources=Resource.query.all())

@app.route("/resources/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_resource(id):
    resource = Resource.query.get_or_404(id)

    if request.method == "POST":
        resource.name = request.form["name"]
        resource.type = request.form["type"]
        db.session.commit()
        return redirect("/resources")

    return render_template("edit_resource.html", resource=resource)

@app.route("/resources/delete/<int:id>")
@login_required
def delete_resource(id):
    Resource.query.filter_by(id=id).delete()
    db.session.commit()
    return redirect("/resources")

# ---------- ALLOCATE ----------
@app.route("/allocate", methods=["GET", "POST"])
@login_required
def allocate():
    error = None

    if request.method == "POST":
        event_id = request.form["event"]
        resource_id = request.form["resource"]

        event = Event.query.get(event_id)
        conflict = db.session.query(Allocation, Event)\
            .join(Event)\
            .filter(
                Allocation.resource_id == resource_id,
                Event.start_time < event.end_time,
                Event.end_time > event.start_time
            ).first()

        if conflict:
            error = "⚠ Resource already allocated in this time"
        else:
            db.session.add(Allocation(
                event_id=event_id,
                resource_id=resource_id
            ))
            db.session.commit()

    return render_template(
        "allocate.html",
        events=Event.query.all(),
        resources=Resource.query.all(),
        allocations=Allocation.query.all(),
        error=error
    )

@app.route("/allocate/delete/<int:id>")
@login_required
def delete_allocation(id):
    Allocation.query.filter_by(id=id).delete()
    db.session.commit()
    return redirect("/allocate")

if __name__ == "__main__":
    app.run(debug=True)
