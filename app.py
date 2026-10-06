from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import string
from functools import wraps

app = Flask(__name__)

# Secret key for Flask sessions
app.secret_key = "vaultnest-secret-key-change-this-later"

DATABASE = "vaultnest.db"


# ---------------------------------------------------------
# DATABASE CONNECTION
# ---------------------------------------------------------

def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


# ---------------------------------------------------------
# CREATE DATABASE TABLES
# ---------------------------------------------------------

def init_db():

    connection = get_db()

    # Users table
    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Saved passwords table
    connection.execute("""
        CREATE TABLE IF NOT EXISTS passwords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            website TEXT NOT NULL,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    connection.commit()
    connection.close()


# ---------------------------------------------------------
# LOGIN REQUIRED DECORATOR
# ---------------------------------------------------------

def login_required(function):

    @wraps(function)
    def decorated_function(*args, **kwargs):

        if "user_id" not in session:
            flash("Please login first.", "error")
            return redirect(url_for("login"))

        return function(*args, **kwargs)

    return decorated_function


# ---------------------------------------------------------
# HOME PAGE
# ---------------------------------------------------------

@app.route("/")
def home():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


# ---------------------------------------------------------
# REGISTER
# ---------------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"]

        if not username or not password:
            flash("All fields are required.", "error")
            return redirect(url_for("register"))

        if len(password) < 6:
            flash("Password must contain at least 6 characters.", "error")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        connection = get_db()

        try:

            connection.execute(
                """
                INSERT INTO users (username, password)
                VALUES (?, ?)
                """,
                (username, hashed_password)
            )

            connection.commit()

            flash("Registration successful. Please login.", "success")
            return redirect(url_for("login"))

        except sqlite3.IntegrityError:

            flash("Username already exists.", "error")
            return redirect(url_for("register"))

        finally:

            connection.close()

    return render_template("register.html")


# ---------------------------------------------------------
# LOGIN
# ---------------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"]

        connection = get_db()

        user = connection.execute(
            """
            SELECT * FROM users
            WHERE username = ?
            """,
            (username,)
        ).fetchone()

        connection.close()

        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["id"]
            session["username"] = user["username"]

            flash("Login successful.", "success")

            return redirect(url_for("dashboard"))

        flash("Invalid username or password.", "error")

    return render_template("login.html")


# ---------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------

@app.route("/logout")
def logout():

    session.clear()

    flash("You have been logged out.", "success")

    return redirect(url_for("login"))


# ---------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------

@app.route("/dashboard")
@login_required
def dashboard():

    connection = get_db()

    passwords = connection.execute(
        """
        SELECT * FROM passwords
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (session["user_id"],)
    ).fetchall()

    connection.close()

    return render_template(
        "dashboard.html",
        passwords=passwords
    )


# ---------------------------------------------------------
# ADD PASSWORD
# ---------------------------------------------------------

@app.route("/add", methods=["GET", "POST"])
@login_required
def add_password():

    if request.method == "POST":

        website = request.form["website"].strip()
        username = request.form["username"].strip()
        password = request.form["password"]
        notes = request.form["notes"].strip()

        if not website or not username or not password:

            flash("Website, username and password are required.", "error")

            return redirect(url_for("add_password"))

        connection = get_db()

        connection.execute(
            """
            INSERT INTO passwords
            (user_id, website, username, password, notes)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                session["user_id"],
                website,
                username,
                password,
                notes
            )
        )

        connection.commit()
        connection.close()

        flash("Password saved successfully.", "success")

        return redirect(url_for("dashboard"))

    return render_template("add_password.html")


# ---------------------------------------------------------
# EDIT PASSWORD
# ---------------------------------------------------------

@app.route("/edit/<int:password_id>", methods=["GET", "POST"])
@login_required
def edit_password(password_id):

    connection = get_db()

    saved_password = connection.execute(
        """
        SELECT * FROM passwords
        WHERE id = ? AND user_id = ?
        """,
        (password_id, session["user_id"])
    ).fetchone()

    if saved_password is None:

        connection.close()

        flash("Password entry not found.", "error")

        return redirect(url_for("dashboard"))

    if request.method == "POST":

        website = request.form["website"].strip()
        username = request.form["username"].strip()
        password = request.form["password"]
        notes = request.form["notes"].strip()

        connection.execute(
            """
            UPDATE passwords
            SET website = ?,
                username = ?,
                password = ?,
                notes = ?
            WHERE id = ? AND user_id = ?
            """,
            (
                website,
                username,
                password,
                notes,
                password_id,
                session["user_id"]
            )
        )

        connection.commit()
        connection.close()

        flash("Password updated successfully.", "success")

        return redirect(url_for("dashboard"))

    connection.close()

    return render_template(
        "edit_password.html",
        password=saved_password
    )


# ---------------------------------------------------------
# DELETE PASSWORD
# ---------------------------------------------------------

@app.route("/delete/<int:password_id>", methods=["POST"])
@login_required
def delete_password(password_id):

    connection = get_db()

    connection.execute(
        """
        DELETE FROM passwords
        WHERE id = ? AND user_id = ?
        """,
        (password_id, session["user_id"])
    )

    connection.commit()
    connection.close()

    flash("Password deleted successfully.", "success")

    return redirect(url_for("dashboard"))


# ---------------------------------------------------------
# PASSWORD GENERATOR
# ---------------------------------------------------------

@app.route("/generate-password")
@login_required
def generate_password():

    characters = (
        string.ascii_letters
        + string.digits
        + "!@#$%^&*"
    )

    generated_password = "".join(
        secrets.choice(characters)
        for _ in range(14)
    )

    return {
        "password": generated_password
    }


# ---------------------------------------------------------
# RUN APPLICATION
# ---------------------------------------------------------

if __name__ == "__main__":

    init_db()

    app.run(debug=True)