import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, make_response
import oracledb
from reportlab.pdfgen import canvas
from io import BytesIO

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

# -------------------- ADD NOTIFICATION --------------------
def add_notification(message):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO notifications (message) VALUES (:msg)", {"msg": message})
    conn.commit()
    cur.close()
    conn.close()


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


# =====================================================
#                STUDENT DASHBOARD
# =====================================================
@app.route("/student", methods=["GET", "POST"])
def student_dashboard():
    username = session.get("username")

    if request.method == "POST":
        email_entered = request.form["email"]
        session["student_email"] = email_entered

    student_email = session.get("student_email")

    conn = get_connection()
    cur = conn.cursor()

    if student_email:
        cur.execute("""
            SELECT name, email, desired_position, desired_company, branch, gpa, skills
            FROM students
            WHERE email = :1
        """, (student_email,))
        student = cur.fetchone()

        if student:
            gpa = student[5]
            student_skills = student[6].lower()

            cur.execute("""
                SELECT j.job_id, r.company_name, j.position, j.min_gpa, j.required_skills
                FROM job_requests j
                JOIN recruiters r ON j.recruiter_id = r.recruiter_id
                WHERE j.min_gpa <= :gpa
            """, (gpa,))
            jobs = [
                job for job in cur.fetchall()
                if any(skill.strip() in student_skills for skill in job[4].lower().split(","))
            ]
        else:
            jobs = []
    else:
        student = None
        jobs = []

    cur.close()
    conn.close()

    return render_template(
        "student.html",
        user=username,
        student=student,
        jobs=jobs,
        verified_email=student_email
    )


# -------------------- ADD / UPDATE STUDENT --------------------
@app.route("/student/add", methods=["GET", "POST"])
def add_student_info():
    username = session.get("username")

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        desired_position = request.form["desired_position"]
        desired_company = request.form["desired_company"]
        branch = request.form["branch"]
        gpa = float(request.form["gpa"])
        skills = request.form["skills"]

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM students WHERE email=:1", (email,))
        exists = cur.fetchone()

        if exists:
            cur.execute("""
                UPDATE students
                SET name=:1, desired_position=:2, desired_company=:3, branch=:4, gpa=:5, skills=:6
                WHERE email=:7
            """, (name, desired_position, desired_company, branch, gpa, skills, email))
            add_notification(f"Student {name} updated their resume.")
        else:
            cur.execute("""
                INSERT INTO students (name, email, desired_position, desired_company, branch, gpa, skills)
                VALUES (:1, :2, :3, :4, :5, :6, :7)
            """, (name, email, desired_position, desired_company, branch, gpa, skills))
            add_notification(f"New student resume added: {name}")

        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for("student_dashboard"))

    return render_template("add_student_info.html", user=username)


# -------------------- DELETE STUDENT --------------------
@app.route("/student/delete")
def delete_student_info():
    email = session.get("student_email")
    if not email:
        return redirect(url_for("student_dashboard"))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM students WHERE email=:1", (email,))
    conn.commit()
    cur.close()
    conn.close()

    add_notification(f"Student resume deleted for {email}")
    return redirect(url_for("student_dashboard"))


# =====================================================
#                   HR DASHBOARD
# =====================================================
@app.route("/hr")
def hr_dashboard():
    if session.get("role") != "hr":
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM students")
    students = cur.fetchall()

    cur.execute("SELECT * FROM recruiters")
    recruiters = cur.fetchall()

    cur.execute("""
        SELECT j.job_id, r.company_name, j.position, j.min_gpa, j.required_skills
        FROM job_requests j
        JOIN recruiters r ON j.recruiter_id = r.recruiter_id
    """)
    jobs = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("hr.html",
                           students=students,
                           recruiters=recruiters,
                           jobs=jobs,
                           user=session.get("username"))


# -------------------- HR: VIEW NOTIFICATIONS --------------------
@app.route("/hr/notifications")
def hr_notifications():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT notification_id, message, created_at FROM notifications ORDER BY created_at DESC")
    notes = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("notifications.html", notes=notes)


# -------------------- HR: STUDENTS --------------------
@app.route("/hr/students")
def hr_students():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM students")
    students = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("hr_students.html", students=students)


@app.route("/hr/delete_student/<int:id>")
def hr_delete_student(id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM students WHERE student_id=:1", (id,))
    conn.commit()

    cur.close()
    conn.close()

    add_notification(f"HR deleted student record ID {id}")

    return redirect(url_for("hr_students"))


# -------------------- HR: RECRUITERS --------------------
@app.route("/hr/recruiters")
def hr_recruiters():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM recruiters")
    recruiters = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("hr_recruiters.html", recruiters=recruiters)


@app.route("/hr/delete_recruiter/<int:id>")
def hr_delete_recruiter(id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM recruiters WHERE recruiter_id=:1", (id,))
    conn.commit()

    cur.close()
    conn.close()

    add_notification(f"HR deleted recruiter ID {id}")

    return redirect(url_for("hr_recruiters"))


# -------------------- HR: JOB POSTINGS --------------------
@app.route("/hr/jobs")
def hr_jobs():
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
    return render_template("hr_jobs.html", jobs=jobs)


@app.route("/hr/delete_job/<int:id>")
def hr_delete_job(id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM job_requests WHERE job_id=:1", (id,))
    conn.commit()

    cur.close()
    conn.close()

    add_notification(f"HR deleted job posting ID {id}")

    return redirect(url_for("hr_jobs"))


# =====================================================
#               RESUME PDF DOWNLOAD
# =====================================================
@app.route("/hr/download_resume/<int:student_id>")
def download_resume(student_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT name, email, desired_position, desired_company, branch, gpa, skills FROM students WHERE student_id=:1", (student_id,))
    s = cur.fetchone()

    cur.close()
    conn.close()

    # PDF creation
    pdf_buffer = BytesIO()
    pdf = canvas.Canvas(pdf_buffer)

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(50, 800, "Student Resume")

    pdf.setFont("Helvetica", 12)
    y = 760

    labels = ["Name", "Email", "Desired Position", "Desired Company", "Branch", "GPA", "Skills"]
    for i, label in enumerate(labels):
        pdf.drawString(50, y, f"{label}: {s[i]}")
        y -= 20

    pdf.save()
    pdf_buffer.seek(0)

    response = make_response(pdf_buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=resume.pdf'
    return response

@app.route("/hr/reports")
def hr_reports():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM students")
    total_students = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM recruiters")
    total_recruiters = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM job_requests")
    total_jobs = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM students WHERE gpa >= 7.0")
    eligible_candidates = cur.fetchone()[0]

    cur.close()
    conn.close()

    return render_template("hr_reports.html",
        total_students=total_students,
        total_recruiters=total_recruiters,
        total_jobs=total_jobs,
        eligible_candidates=eligible_candidates
    )

# =====================================================
#                   RECRUITER DASHBOARD
# =====================================================
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

    return render_template("recruiter.html", jobs=jobs, user=session.get("username"))


# =====================================================
#                        ADD JOB
# =====================================================
@app.route("/add_job", methods=["GET", "POST"])
def add_job():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT recruiter_id, company_name FROM recruiters")
    recruiters = cur.fetchall()

    if request.method == "POST":
        recruiter_id = request.form["recruiter_id"]
        position = request.form["position"]
        min_gpa = float(request.form["min_gpa"])
        skills = request.form["required_skills"]

        cur.execute("""
            INSERT INTO job_requests (recruiter_id, position, min_gpa, required_skills)
            VALUES (:1, :2, :3, :4)
        """, (recruiter_id, position, min_gpa, skills))

        conn.commit()
        cur.close()
        conn.close()

        add_notification(f"Recruiter posted new job: {position}")

        return redirect(url_for("recruiter_dashboard"))

    cur.close()
    conn.close()
    return render_template("add_job.html", recruiters=recruiters)


# =====================================================
#                  ADD RECRUITER BY HR
# =====================================================
@app.route("/add_recruiter", methods=["GET", "POST"])
def add_recruiter():
    if request.method == "POST":
        company = request.form["company_name"]
        email = request.form["email"]

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO recruiters (company_name, email)
            VALUES (:1, :2)
        """, (company, email))

        conn.commit()
        cur.close()
        conn.close()

        add_notification(f"New recruiter added: {company}")

        return redirect(url_for("hr_dashboard"))

    return render_template("add_recruiter.html")


# =====================================================
#                     SHORTLISTS
# =====================================================
@app.route("/shortlists/<int:job_id>")
def shortlists(job_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT position, min_gpa, required_skills
        FROM job_requests
        WHERE job_id = :1
    """, (job_id,))
    job = cur.fetchone()

    cur.execute("""
        SELECT name, email, branch, gpa, skills
        FROM students
        WHERE gpa >= :1
    """, (job[1],))
    candidates = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("shortlists.html", job=job, candidates=candidates)



# -------------------- MAIN --------------------
if __name__ == "__main__":
    app.run(debug=True)
