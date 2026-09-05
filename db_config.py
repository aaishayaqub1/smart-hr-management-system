import os
from flask import Flask, render_template, request, redirect, url_for, session
import oracledb
load_dotenv()
# -------------------- Flask setup --------------------
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# -------------------- Oracle setup --------------------
oracledb.init_oracle_client(
    lib_dir=os.getenv("ORACLE_CLIENT_PATH")
)

def get_connection():
    return oracledb.connect(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        dsn=os.getenv("DB_DSN")
    )

# -------------------- LOGIN PAGE --------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role = request.form["role"]
        username = request.form["username"]
        password = request.form["password"]

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT username, role FROM users 
            WHERE username=:1 AND password=:2 AND role=:3
        """, (username, password, role))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            session["username"] = user[0]
            session["role"] = user[1]
            if role == "student":
                return redirect(url_for("student_dashboard"))
            elif role == "hr":
                return redirect(url_for("hr_dashboard"))
            elif role == "recruiter":
                return redirect(url_for("recruiter_dashboard"))
        else:
            return render_template("index.html", error="Invalid credentials")

    return render_template("index.html")

# -------------------- LOGOUT --------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# -------------------- STUDENT DASHBOARD --------------------
@app.route("/student")
def student_dashboard():
    if session.get("role") != "student":
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()

    # Each student only sees their own resume by email
    # We'll use session email after adding
    student_email = session.get("student_email")

    student = None
    if student_email:
        cur.execute("""
            SELECT student_id, name, email, branch, gpa, skills
            FROM students
            WHERE email = :1
        """, [student_email])
        student = cur.fetchone()

    cur.close()
    conn.close()

    return render_template("student.html", user="Student", student=student)

# -------------------- ADD OR UPDATE STUDENT INFO --------------------
@app.route("/student/add", methods=["GET", "POST"])
def add_student_info():
    if session.get("role") != "student":
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        branch = request.form["branch"]
        gpa = float(request.form["gpa"])
        skills = request.form["skills"]

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT student_id FROM students WHERE email=:1", [email])
        existing = cur.fetchone()

        if existing:
            cur.execute("""
                UPDATE students
                SET name=:1, branch=:2, gpa=:3, skills=:4
                WHERE email=:5
            """, (name, branch, gpa, skills, email))
        else:
            cur.execute("""
                INSERT INTO students (name, email, branch, gpa, skills)
                VALUES (:1, :2, :3, :4, :5)
            """, (name, email, branch, gpa, skills))

        conn.commit()
        cur.close()
        conn.close()

        # Save this student's email in session
        session["student_email"] = email

        return redirect(url_for("student_dashboard"))

    return render_template("add_student_info.html", user="Student")

# -------------------- DELETE STUDENT INFO --------------------
@app.route("/student/delete/<int:student_id>")
def delete_student(student_id):
    if session.get("role") != "student":
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM students WHERE student_id=:1", [student_id])
    conn.commit()
    cur.close()
    conn.close()

    session.pop("student_email", None)
    return redirect(url_for("student_dashboard"))

# -------------------- HR DASHBOARD --------------------
@app.route("/hr")
def hr_dashboard():
    if session.get("role") != "hr":
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT student_id, name, email, branch, gpa, skills FROM students")
    all_students = cur.fetchall()
    total = len(all_students)
    cur.close()
    conn.close()

    return render_template("hr.html", user="HR", students=all_students, total=total)

# -------------------- RECRUITER DASHBOARD --------------------
@app.route("/recruiter")
def recruiter_dashboard():
    if session.get("role") != "recruiter":
        return redirect(url_for("login"))
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT j.job_id, r.company_name, j.position, j.min_gpa, j.required_skills
        FROM job_requests j
        JOIN recruiters r ON j.recruiter_id = r.recruiter_id
    """)
    jobs = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("recruiter.html", user="Recruiter", jobs=jobs)

# -------------------- ADD JOB --------------------
@app.route("/add_job", methods=["GET", "POST"])
def add_job():
    if session.get("role") != "recruiter":
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT recruiter_id, company_name FROM recruiters")
    recruiters = cur.fetchall()

    if request.method == "POST":
        recruiter_id = int(request.form["recruiter_id"])
        position = request.form["position"]
        min_gpa = float(request.form["min_gpa"])
        required_skills = request.form["required_skills"]

        cur.execute("""
            INSERT INTO job_requests (recruiter_id, position, min_gpa, required_skills)
            VALUES (:1, :2, :3, :4)
        """, (recruiter_id, position, min_gpa, required_skills))
        conn.commit()

        cur.close()
        conn.close()
        return redirect(url_for("recruiter_dashboard"))

    cur.close()
    conn.close()
    return render_template("add_job.html", recruiters=recruiters, user="Recruiter")

# -------------------- SHORTLISTED STUDENTS --------------------
@app.route("/shortlists/<int:job_id>")
def shortlists(job_id):
    if session.get("role") != "recruiter":
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT position, min_gpa, required_skills
        FROM job_requests
        WHERE job_id = :job_id
    """, {"job_id": job_id})
    job = cur.fetchone()

    if not job:
        cur.close()
        conn.close()
        return render_template("shortlists.html", job=None, candidates=[])

    position, min_gpa, required_skills = job

    cur.execute("""
        SELECT student_id, name, email, branch, gpa, skills
        FROM students
        WHERE gpa >= :min_gpa
        AND LOWER(skills) LIKE '%' || LOWER(:required_skills) || '%'
    """, {"min_gpa": min_gpa, "required_skills": required_skills})

    candidates = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("shortlists.html", job=job, candidates=candidates)

# -------------------- MAIN --------------------
if __name__ == "__main__":
    app.run(debug=True)
