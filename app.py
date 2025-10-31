from flask import Flask, render_template, redirect, request, url_for, session, flash
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
import os

if os.path.exists("env.py"):
    import env

app = Flask(__name__)
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)

# ===== ROUTES ===== #

@app.route("/")
def index():
    if "user" in session:
        inventory = list(mongo.db.items.find({"user": session["user"]}))
        return render_template("inventory.html", inventory=inventory)
    return render_template("index.html")


# --- Authentication --- #
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        existing_user = mongo.db.users.find_one({"username": request.form.get("username").lower()})
        if existing_user:
            flash("Username already exists", "error")
            return redirect(url_for("register"))
        hashpass = generate_password_hash(request.form.get("password"))
        mongo.db.users.insert_one({
            "username": request.form.get("username").lower(),
            "password": hashpass
        })
        session["user"] = request.form.get("username").lower()
        flash("Registration successful!", "success")
        return redirect(url_for("index"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = mongo.db.users.find_one({"username": request.form.get("username").lower()})
        if user and check_password_hash(user["password"], request.form.get("password")):
            session["user"] = request.form.get("username").lower()
            flash("Welcome back!", "success")
            return redirect(url_for("index"))
        flash("Invalid username or password", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    flash("You have logged out", "info")
    session.pop("user")
    return redirect(url_for("login"))


# --- CRUD Operations --- #
@app.route("/add_item", methods=["GET", "POST"])
def add_item():
    if request.method == "POST":
        item = {
            "name": request.form.get("name"),
            "sku": request.form.get("sku"),
            "category": request.form.get("category"),
            "quantity": int(request.form.get("quantity")),
            "price": float(request.form.get("price")),
            "supplier": request.form.get("supplier"),
            "location": request.form.get("location"),
            "user": session["user"]
        }
        mongo.db.items.insert_one(item)
        flash("Item added successfully!", "success")
        return redirect(url_for("index"))
    return render_template("add_item.html")


@app.route("/edit_item/<item_id>", methods=["GET", "POST"])
def edit_item(item_id):
    item = mongo.db.items.find_one({"_id": ObjectId(item_id)})
    if request.method == "POST":
        mongo.db.items.update_one(
            {"_id": ObjectId(item_id)},
            {"$set": {
                "name": request.form.get("name"),
                "sku": request.form.get("sku"),
                "category": request.form.get("category"),
                "quantity": int(request.form.get("quantity")),
                "price": float(request.form.get("price")),
                "supplier": request.form.get("supplier"),
                "location": request.form.get("location")
            }}
        )
        flash("Item updated successfully!", "success")
        return redirect(url_for("index"))
    return render_template("edit_item.html", item=item)


@app.route("/delete_item/<item_id>")
def delete_item(item_id):
    mongo.db.items.delete_one({"_id": ObjectId(item_id)})
    flash("Item deleted successfully!", "info")
    return redirect(url_for("index"))


# --- Run App --- #
if __name__ == "__main__":
    app.run(host=os.environ.get("IP"), port=int(os.environ.get("PORT", 5000)), debug=True)
    
