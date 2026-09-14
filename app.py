from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

import sqlite3
import os
import uuid
from functools import wraps

from werkzeug.utils import secure_filename
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from students_data import STUDENTS_DATA


# =========================================================
# APP CONFIGURATION
# =========================================================

app = Flask(__name__)

app.secret_key = "smart_students_secret_key_2026"

DATABASE = "students.db"

UPLOAD_FOLDER = os.path.join(
    "static",
    "uploads",
    "achievements"
)

ALLOWED_IMAGE_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "gif",
    "webp"
}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# =========================================================
# CLASS INFORMATION
# =========================================================

CLASS_INFO = {
    "I BCA": {
        "department": "BCA",
        "year": "I Year",
        "section": ""
    },

    "II BCA": {
        "department": "BCA",
        "year": "II Year",
        "section": ""
    },

    "III BCA": {
        "department": "BCA",
        "year": "III Year",
        "section": ""
    },

    "I IT": {
        "department": "IT",
        "year": "I Year",
        "section": ""
    },

    "II IT": {
        "department": "IT",
        "year": "II Year",
        "section": ""
    },

    "III IT": {
        "department": "IT",
        "year": "III Year",
        "section": ""
    },

    "I CS": {
        "department": "CS",
        "year": "I Year",
        "section": ""
    },

    "II CS": {
        "department": "CS",
        "year": "II Year",
        "section": ""
    },

    "III CS A": {
        "department": "CS",
        "year": "III Year",
        "section": "A"
    },

    "III CS B": {
        "department": "CS",
        "year": "III Year",
        "section": "B"
    },

    "I MCA": {
        "department": "MCA",
        "year": "I Year",
        "section": ""
    },

    "II MSC CS": {
        "department": "MSc CS",
        "year": "II Year",
        "section": ""
    }
}


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():

    conn = sqlite3.connect(
        DATABASE,
        timeout=60
    )

    conn.row_factory = sqlite3.Row

    conn.execute(
        "PRAGMA busy_timeout = 60000"
    )

    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    return conn


# =========================================================
# DATABASE COLUMN HELPER
# =========================================================

def ensure_column(
    conn,
    table_name,
    column_name,
    column_type="TEXT"
):

    columns = conn.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    existing_columns = {
        column["name"]
        for column in columns
    }

    if column_name not in existing_columns:

        conn.execute(
            f"""
            ALTER TABLE {table_name}
            ADD COLUMN {column_name} {column_type}
            """
        )


# =========================================================
# GET TABLE COLUMNS
# =========================================================

def get_table_columns(conn, table_name):

    rows = conn.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    return {
        row["name"]: row
        for row in rows
    }


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def init_db():

    conn = get_db_connection()

    cursor = conn.cursor()

    # -----------------------------------------------------
    # USERS
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'admin'
        )
    """)

    # -----------------------------------------------------
    # STUDENTS
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            register_number TEXT UNIQUE,
            name TEXT NOT NULL,
            department TEXT,
            year TEXT,
            section TEXT,
            class_name TEXT
        )
    """)

    # -----------------------------------------------------
    # ACHIEVEMENTS
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            register_number TEXT,
            student_name TEXT,
            class_name TEXT,
            title TEXT,
            achievement_type TEXT,
            description TEXT,
            certificate TEXT,
            photo TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # -----------------------------------------------------
    # ATTENDANCE
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            register_number TEXT,
            student_name TEXT,
            name TEXT,
            department TEXT,
            year TEXT,
            section TEXT,
            class_name TEXT,
            attendance_date TEXT,
            status TEXT
        )
    """)

    # -----------------------------------------------------
    # ASSIGNMENTS
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            register_number TEXT,
            student_name TEXT,
            class_name TEXT,
            subject TEXT,
            title TEXT,
            status TEXT,
            marks TEXT
        )
    """)

    # -----------------------------------------------------
    # MARKS
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS marks (
            register_number TEXT,
            student_name TEXT,
            class_name TEXT,
            subject TEXT,
            mark TEXT,
            exam_type TEXT
        )
    """)

    # -----------------------------------------------------
    # EXAMS
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_name TEXT,
            subject TEXT,
            exam_name TEXT,
            exam_date TEXT,
            max_marks TEXT
        )
    """)

    # -----------------------------------------------------
    # SAVED REPORTS
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS saved_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            register_number TEXT,
            student_name TEXT,
            class_name TEXT,
            academic_notes TEXT,
            overall_performance TEXT,
            teacher_remarks TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # -----------------------------------------------------
    # OLD DATABASE MIGRATION
    # -----------------------------------------------------

    table_columns = {

        "students": [
            ("register_number", "TEXT"),
            ("name", "TEXT"),
            ("department", "TEXT"),
            ("year", "TEXT"),
            ("section", "TEXT"),
            ("class_name", "TEXT")
        ],

        "achievements": [
            ("register_number", "TEXT"),
            ("student_name", "TEXT"),
            ("class_name", "TEXT"),
            ("title", "TEXT"),
            ("achievement_type", "TEXT"),
            ("description", "TEXT"),
            ("certificate", "TEXT"),
            ("photo", "TEXT"),
            ("created_at", "TIMESTAMP")
        ],

        "attendance": [
            ("register_number", "TEXT"),
            ("student_name", "TEXT"),
            ("name", "TEXT"),
            ("department", "TEXT"),
            ("year", "TEXT"),
            ("section", "TEXT"),
            ("class_name", "TEXT"),
            ("attendance_date", "TEXT"),
            ("status", "TEXT")
        ],

        "assignments": [
            ("register_number", "TEXT"),
            ("student_name", "TEXT"),
            ("class_name", "TEXT"),
            ("subject", "TEXT"),
            ("title", "TEXT"),
            ("status", "TEXT"),
            ("marks", "TEXT")
        ],

        "marks": [
            ("register_number", "TEXT"),
            ("student_name", "TEXT"),
            ("class_name", "TEXT"),
            ("subject", "TEXT"),
            ("mark", "TEXT"),
            ("exam_type", "TEXT")
        ],

        "exams": [
            ("class_name", "TEXT"),
            ("subject", "TEXT"),
            ("exam_name", "TEXT"),
            ("exam_date", "TEXT"),
            ("max_marks", "TEXT")
        ],

        "saved_reports": [
            ("register_number", "TEXT"),
            ("student_name", "TEXT"),
            ("class_name", "TEXT"),
            ("academic_notes", "TEXT"),
            ("overall_performance", "TEXT"),
            ("teacher_remarks", "TEXT"),
            ("created_at", "TIMESTAMP")
        ]
    }

    for table_name, columns in table_columns.items():

        for column_name, column_type in columns:

            ensure_column(
                conn,
                table_name,
                column_name,
                column_type
            )

    # -----------------------------------------------------
    # FIX OLD ATTENDANCE DATA
    # -----------------------------------------------------

    attendance_columns = get_table_columns(
        conn,
        "attendance"
    )

    if "name" in attendance_columns:

        conn.execute("""
            UPDATE attendance
            SET name = COALESCE(student_name, '')
            WHERE name IS NULL
        """)

    if "department" in attendance_columns:

        conn.execute("""
            UPDATE attendance
            SET department = COALESCE(department, '')
            WHERE department IS NULL
        """)

    if "year" in attendance_columns:

        conn.execute("""
            UPDATE attendance
            SET year = COALESCE(year, '')
            WHERE year IS NULL
        """)

    if "section" in attendance_columns:

        conn.execute("""
            UPDATE attendance
            SET section = COALESCE(section, '')
            WHERE section IS NULL
        """)

    if "class_name" in attendance_columns:

        conn.execute("""
            UPDATE attendance
            SET class_name = COALESCE(class_name, '')
            WHERE class_name IS NULL
        """)

    if "attendance_date" in attendance_columns:

        conn.execute("""
            UPDATE attendance
            SET attendance_date = COALESCE(attendance_date, '')
            WHERE attendance_date IS NULL
        """)

    if "status" in attendance_columns:

        conn.execute("""
            UPDATE attendance
            SET status = COALESCE(status, 'Absent')
            WHERE status IS NULL
        """)

    # -----------------------------------------------------
    # DEFAULT ADMIN
    # -----------------------------------------------------

    existing_user = cursor.execute(
        """
        SELECT id
        FROM users
        WHERE username = ?
        """,
        ("admin",)
    ).fetchone()

    if existing_user is None:

        hashed_password = generate_password_hash(
            "admin123"
        )

        cursor.execute(
            """
            INSERT INTO users (
                username,
                password,
                role
            )
            VALUES (?, ?, ?)
            """,
            (
                "admin",
                hashed_password,
                "admin"
            )
        )

    conn.commit()

    conn.close()


# =========================================================
# LOGIN REQUIRED
# =========================================================

def login_required():

    def decorator(function):

        @wraps(function)
        def wrapper(*args, **kwargs):

            if "user_id" not in session:

                return redirect(
                    url_for("login")
                )

            return function(
                *args,
                **kwargs
            )

        return wrapper

    return decorator


# =========================================================
# GET STUDENTS FOR CLASS
# =========================================================

def get_students_for_class(class_name):

    students = []

    if not class_name:
        return students

    data = STUDENTS_DATA.get(
        class_name,
        []
    )

    for item in data:

        if isinstance(item, dict):

            register_number = (
                item.get("register_number")
                or item.get("regno")
                or item.get("register")
                or ""
            )

            name = item.get(
                "name",
                ""
            )

        else:

            try:

                register_number = item[0]
                name = item[1]

            except (
                IndexError,
                TypeError
            ):

                continue

        if register_number:

            students.append({
                "register_number": str(
                    register_number
                ),
                "name": str(
                    name
                )
            })

    return students


# =========================================================
# FIND CLASS FROM SELECTION
# =========================================================

def find_class_from_selection(
    department,
    year,
    section
):

    department = (
        department or ""
    ).strip()

    year = (
        year or ""
    ).strip()

    section = (
        section or ""
    ).strip()

    for class_name, info in CLASS_INFO.items():

        if info["department"] != department:
            continue

        if info["year"] != year:
            continue

        if info["section"] != section:
            continue

        return class_name

    return ""


# =========================================================
# GET STUDENT DETAILS
# =========================================================

def get_student_details(register_number):

    if not register_number:
        return None

    for class_name, students_list in STUDENTS_DATA.items():

        for item in students_list:

            if isinstance(item, dict):

                regno = (
                    item.get("register_number")
                    or item.get("regno")
                    or item.get("register")
                    or ""
                )

                name = item.get(
                    "name",
                    ""
                )

            else:

                try:

                    regno = item[0]
                    name = item[1]

                except (
                    IndexError,
                    TypeError
                ):

                    continue

            if str(regno) == str(register_number):

                class_details = CLASS_INFO.get(
                    class_name,
                    {
                        "department": "",
                        "year": "",
                        "section": ""
                    }
                )

                return {
                    "register_number": str(regno),
                    "name": str(name),
                    "class_name": class_name,
                    "department": class_details.get(
                        "department",
                        ""
                    ),
                    "year": class_details.get(
                        "year",
                        ""
                    ),
                    "section": class_details.get(
                        "section",
                        ""
                    )
                }

    return None


# =========================================================
# ALLOWED IMAGE
# =========================================================

def allowed_image(filename):

    if not filename:
        return False

    if "." not in filename:
        return False

    extension = filename.rsplit(
        ".",
        1
    )[1].lower()

    return extension in ALLOWED_IMAGE_EXTENSIONS


# =========================================================
# SAVE UPLOADED FILE
# =========================================================

def save_uploaded_file(file):

    if file is None:
        return None

    if not file.filename:
        return None

    if not allowed_image(file.filename):
        return None

    original_name = secure_filename(
        file.filename
    )

    if "." not in original_name:
        return None

    extension = original_name.rsplit(
        ".",
        1
    )[1].lower()

    new_name = (
        f"{uuid.uuid4()}.{extension}"
    )

    file_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        new_name
    )

    file.save(file_path)

    return new_name


# =========================================================
# HOME / INDEX
# =========================================================

@app.route("/")
def index():

    return render_template(
        "index.html"
    )


# =========================================================
# LOGIN
# =========================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if not username or not password:

            flash(
                "Please enter username and password.",
                "error"
            )

            return redirect(
                url_for("login")
            )

        conn = get_db_connection()

        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE username = ?
            """,
            (username,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session.clear()

            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Invalid username or password.",
            "error"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "login.html"
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("index")
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
@login_required()
def dashboard():

    conn = get_db_connection()

    student_count = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM students
        """
    ).fetchone()["count"]

    achievement_count = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM achievements
        """
    ).fetchone()["count"]

    attendance_count = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM attendance
        """
    ).fetchone()["count"]

    assignment_count = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM assignments
        """
    ).fetchone()["count"]

    conn.close()

    if student_count == 0:

        student_count = sum(
            len(
                get_students_for_class(
                    class_name
                )
            )
            for class_name in CLASS_INFO
        )

    return render_template(
        "dashboard.html",
        student_count=student_count,
        achievement_count=achievement_count,
        attendance_count=attendance_count,
        assignment_count=assignment_count
    )


# =========================================================
# STUDENTS DETAILS
# =========================================================

@app.route("/students")
@login_required()
def students():

    selected_class = request.args.get(
        "class_name",
        ""
    ).strip()

    selected_department = request.args.get(
        "department",
        ""
    ).strip()

    selected_year = request.args.get(
        "year",
        ""
    ).strip()

    selected_section = request.args.get(
        "section",
        ""
    ).strip()

    if not selected_class:

        selected_class = find_class_from_selection(
            selected_department,
            selected_year,
            selected_section
        )

    student_list = []

    if selected_class:

        student_list = get_students_for_class(
            selected_class
        )

        for student in student_list:

            student["class_name"] = (
                selected_class
            )

    available_classes = list(
        CLASS_INFO.keys()
    )

    departments = sorted({
        info["department"]
        for info in CLASS_INFO.values()
    })

    years = [
        "I Year",
        "II Year",
        "III Year"
    ]

    sections = [
        "A",
        "B"
    ]

    return render_template(
        "students.html",
        students=student_list,
        available_classes=available_classes,
        departments=departments,
        years=years,
        sections=sections,
        selected_class=selected_class,
        selected_department=selected_department,
        selected_year=selected_year,
        selected_section=selected_section,
        class_info=CLASS_INFO
    )


# =========================================================
# STUDENT PROFILE
# =========================================================

@app.route(
    "/student/<register_number>"
)
@login_required()
def student_profile(
    register_number
):

    selected_student = get_student_details(
        register_number
    )

    if selected_student is None:

        flash(
            "Student not found.",
            "error"
        )

        return redirect(
            url_for("students")
        )

    conn = get_db_connection()

    achievements = conn.execute(
        """
        SELECT *
        FROM achievements
        WHERE register_number = ?
        ORDER BY id DESC
        """,
        (register_number,)
    ).fetchall()

    attendance_data = conn.execute(
        """
        SELECT *
        FROM attendance
        WHERE register_number = ?
        ORDER BY id DESC
        """,
        (register_number,)
    ).fetchall()

    marks_data = conn.execute(
        """
        SELECT *
        FROM marks
        WHERE register_number = ?
        ORDER BY rowid DESC
        """,
        (register_number,)
    ).fetchall()

    assignments_data = conn.execute(
        """
        SELECT *
        FROM assignments
        WHERE register_number = ?
        ORDER BY id DESC
        """,
        (register_number,)
    ).fetchall()

    conn.close()

    return render_template(
        "student_profile.html",
        student=selected_student,
        class_name=selected_student["class_name"],
        achievements=achievements,
        attendance=attendance_data,
        marks=marks_data,
        assignments=assignments_data
    )


# =========================================================
# ACHIEVEMENT PAGE
# =========================================================

@app.route("/achievement")
@login_required()
def achievement():

    selected_department = request.args.get(
        "department",
        ""
    ).strip()

    selected_year = request.args.get(
        "year",
        ""
    ).strip()

    selected_section = request.args.get(
        "section",
        ""
    ).strip()

    selected_class = request.args.get(
        "class_name",
        ""
    ).strip()

    selected_register = request.args.get(
        "register_number",
        ""
    ).strip()

    departments = sorted({
        info["department"]
        for info in CLASS_INFO.values()
    })

    years = [
        "I Year",
        "II Year",
        "III Year"
    ]

    classes = []

    for class_name, info in CLASS_INFO.items():

        if selected_department:
            if info["department"] != selected_department:
                continue

        if selected_year:
            if info["year"] != selected_year:
                continue

        if selected_section:
            if info["section"] != selected_section:
                continue

        classes.append(class_name)

    if selected_class:

        selected_info = CLASS_INFO.get(
            selected_class
        )

        if selected_info:

            selected_department = selected_info["department"]
            selected_year = selected_info["year"]
            selected_section = selected_info["section"]

            if selected_class not in classes:
                classes.append(selected_class)

    students = []

    if selected_class:

        students = get_students_for_class(
            selected_class
        )

        info = CLASS_INFO.get(
            selected_class,
            {}
        )

        for student in students:

            student["class_name"] = selected_class
            student["department"] = info.get(
                "department",
                ""
            )
            student["year"] = info.get(
                "year",
                ""
            )
            student["section"] = info.get(
                "section",
                ""
            )

    selected_student = None

    if selected_register:

        for student in students:

            if str(
                student["register_number"]
            ) == str(selected_register):

                selected_student = student
                break

        if selected_student is None:

            selected_student = get_student_details(
                selected_register
            )

            if selected_student:

                selected_class = selected_student["class_name"]
                selected_department = selected_student["department"]
                selected_year = selected_student["year"]
                selected_section = selected_student["section"]

                students = get_students_for_class(
                    selected_class
                )

    achievements = []

    if selected_register:

        conn = get_db_connection()

        achievements = conn.execute(
            """
            SELECT *
            FROM achievements
            WHERE register_number = ?
            ORDER BY id DESC
            """,
            (selected_register,)
        ).fetchall()

        conn.close()

    return render_template(
        "achievement.html",
        departments=departments,
        years=years,
        classes=classes,
        available_classes=list(
            CLASS_INFO.keys()
        ),
        students=students,
        achievements=achievements,
        selected_department=selected_department,
        selected_year=selected_year,
        selected_section=selected_section,
        selected_class=selected_class,
        selected_register=selected_register,
        selected_student=selected_student,
        class_info=CLASS_INFO
    )


# =========================================================
# ADD ACHIEVEMENT
# =========================================================

@app.route(
    "/add_achievement",
    methods=["POST"]
)
@login_required()
def add_achievement():

    register_number = request.form.get(
        "register_number",
        ""
    ).strip()

    class_name = request.form.get(
        "class_name",
        ""
    ).strip()

    title = request.form.get(
        "title",
        ""
    ).strip()

    achievement_type = request.form.get(
        "achievement_type",
        ""
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()

    certificate_file = request.files.get(
        "certificate"
    )

    photo_file = request.files.get(
        "photo"
    )

    if not register_number:

        flash(
            "Please select a student.",
            "error"
        )

        return redirect(
            url_for(
                "achievement",
                class_name=class_name
            )
        )

    student = get_student_details(
        register_number
    )

    if student is None:

        flash(
            "Student not found.",
            "error"
        )

        return redirect(
            url_for(
                "achievement",
                class_name=class_name
            )
        )

    if not class_name:

        class_name = student["class_name"]

    if not title:

        flash(
            "Please enter achievement title.",
            "error"
        )

        return redirect(
            url_for(
                "achievement",
                department=student["department"],
                year=student["year"],
                section=student["section"],
                class_name=class_name,
                register_number=register_number
            )
        )

    certificate_name = save_uploaded_file(
        certificate_file
    )

    photo_name = save_uploaded_file(
        photo_file
    )

    conn = get_db_connection()

    conn.execute(
        """
        INSERT INTO achievements (
            register_number,
            student_name,
            class_name,
            title,
            achievement_type,
            description,
            certificate,
            photo
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            register_number,
            student["name"],
            class_name,
            title,
            achievement_type,
            description,
            certificate_name,
            photo_name
        )
    )

    conn.commit()
    conn.close()

    flash(
        "Achievement added successfully.",
        "success"
    )

    return redirect(
        url_for(
            "achievement",
            department=student["department"],
            year=student["year"],
            section=student["section"],
            class_name=class_name,
            register_number=register_number
        )
    )


# =========================================================
# DELETE ACHIEVEMENT
# =========================================================

@app.route(
    "/delete_achievement/<int:achievement_id>",
    methods=["GET", "POST"]
)
@login_required()
def delete_achievement(
    achievement_id
):

    conn = get_db_connection()

    achievement_data = conn.execute(
        """
        SELECT *
        FROM achievements
        WHERE id = ?
        """,
        (achievement_id,)
    ).fetchone()

    redirect_data = {}

    if achievement_data:

        redirect_data["class_name"] = (
            achievement_data["class_name"] or ""
        )

        redirect_data["register_number"] = (
            achievement_data["register_number"] or ""
        )

        student = get_student_details(
            achievement_data["register_number"]
        )

        if student:

            redirect_data["department"] = student["department"]
            redirect_data["year"] = student["year"]
            redirect_data["section"] = student["section"]

        certificate = achievement_data["certificate"]
        photo = achievement_data["photo"]

        if certificate:

            certificate_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                certificate
            )

            if os.path.exists(certificate_path):
                os.remove(certificate_path)

        if photo:

            photo_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                photo
            )

            if os.path.exists(photo_path):
                os.remove(photo_path)

        conn.execute(
            """
            DELETE FROM achievements
            WHERE id = ?
            """,
            (achievement_id,)
        )

        conn.commit()

        flash(
            "Achievement deleted successfully.",
            "success"
        )

    else:

        flash(
            "Achievement not found.",
            "error"
        )

    conn.close()

    return redirect(
        url_for(
            "achievement",
            **redirect_data
        )
    )


# =========================================================
# ATTENDANCE
# =========================================================

@app.route(
    "/attendance",
    methods=["GET", "POST"]
)
@login_required()
def attendance():

    # =====================================================
    # SAVE ATTENDANCE
    # =====================================================

    if request.method == "POST":

        class_name = request.form.get(
            "class_name",
            ""
        ).strip()

        attendance_date = request.form.get(
            "attendance_date",
            ""
        ).strip()

        if not class_name or not attendance_date:

            flash(
                "Please select class and date.",
                "error"
            )

            return redirect(
                url_for("attendance")
            )

        students_data = STUDENTS_DATA.get(
            class_name,
            []
        )

        class_details = CLASS_INFO.get(
            class_name,
            {}
        )

        department = class_details.get(
            "department",
            ""
        )

        year = class_details.get(
            "year",
            ""
        )

        section = class_details.get(
            "section",
            ""
        )

        conn = get_db_connection()

        # -------------------------------------------------
        # GET REAL DATABASE SCHEMA
        # -------------------------------------------------

        schema = get_table_columns(
            conn,
            "attendance"
        )

        # -------------------------------------------------
        # SAVE EACH STUDENT
        # -------------------------------------------------

        for item in students_data:

            if isinstance(item, dict):

                register_number = (
                    item.get("register_number")
                    or item.get("regno")
                    or item.get("register")
                    or ""
                )

                student_name = item.get(
                    "name",
                    ""
                )

            else:

                try:

                    register_number = item[0]
                    student_name = item[1]

                except (
                    IndexError,
                    TypeError
                ):

                    continue

            if not register_number:
                continue

            register_number = str(
                register_number
            )

            student_name = str(
                student_name
            )

            status = request.form.get(
                "status_" + register_number,
                "Absent"
            )

            # -------------------------------------------------
            # VALUES FOR OLD / NEW COLUMN NAMES
            # -------------------------------------------------

            values_map = {

                "register_number":
                    register_number,

                "regno":
                    register_number,

                "register":
                    register_number,

                "student_name":
                    student_name,

                "name":
                    student_name,

                "department":
                    department,

                "year":
                    year,

                "section":
                    section,

                "class_name":
                    class_name,

                "attendance_date":
                    attendance_date,

                "date":
                    attendance_date,

                "status":
                    status
            }

            # -------------------------------------------------
            # FIND EXISTING RECORD
            # -------------------------------------------------

            existing = None

            if (
                "register_number" in schema
                and "class_name" in schema
                and "attendance_date" in schema
            ):

                existing = conn.execute(
                    """
                    SELECT id
                    FROM attendance
                    WHERE register_number = ?
                    AND class_name = ?
                    AND attendance_date = ?
                    """,
                    (
                        register_number,
                        class_name,
                        attendance_date
                    )
                ).fetchone()

            # -------------------------------------------------
            # UPDATE EXISTING RECORD
            # -------------------------------------------------

            if existing:

                update_columns = []

                update_values = []

                for column_name, column_info in schema.items():

                    if column_name == "id":
                        continue

                    if column_name in values_map:

                        update_columns.append(
                            f'"{column_name}" = ?'
                        )

                        update_values.append(
                            values_map[column_name]
                        )

                if update_columns:

                    update_values.append(
                        existing["id"]
                    )

                    update_sql = f"""
                        UPDATE attendance
                        SET {", ".join(update_columns)}
                        WHERE id = ?
                    """

                    conn.execute(
                        update_sql,
                        update_values
                    )

            # -------------------------------------------------
            # INSERT NEW RECORD
            # -------------------------------------------------

            else:

                insert_columns = []

                insert_values = []

                # -------------------------------------------------
                # ADD ALL REQUIRED / KNOWN COLUMNS
                # -------------------------------------------------

                for column_name, column_info in schema.items():

                    if column_name == "id":
                        continue

                    # Known column
                    if column_name in values_map:

                        insert_columns.append(
                            f'"{column_name}"'
                        )

                        insert_values.append(
                            values_map[column_name]
                        )

                    # -------------------------------------------------
                    # ANY OTHER LEGACY NOT NULL COLUMN
                    # -------------------------------------------------

                    elif column_info["notnull"]:

                        default_value = ""

                        # Try sensible values for old schemas
                        lower_name = column_name.lower()

                        if (
                            "reg" in lower_name
                            or "roll" in lower_name
                        ):

                            default_value = register_number

                        elif (
                            "name" in lower_name
                        ):

                            default_value = student_name

                        elif (
                            "dept" in lower_name
                        ):

                            default_value = department

                        elif (
                            "year" in lower_name
                        ):

                            default_value = year

                        elif (
                            "section" in lower_name
                        ):

                            default_value = section

                        elif (
                            "class" in lower_name
                        ):

                            default_value = class_name

                        elif (
                            "date" in lower_name
                        ):

                            default_value = attendance_date

                        elif (
                            "status" in lower_name
                        ):

                            default_value = status

                        insert_columns.append(
                            f'"{column_name}"'
                        )

                        insert_values.append(
                            default_value
                        )

                if insert_columns:

                    placeholders = ", ".join(
                        ["?"] * len(insert_columns)
                    )

                    insert_sql = f"""
                        INSERT INTO attendance (
                            {", ".join(insert_columns)}
                        )
                        VALUES (
                            {placeholders}
                        )
                    """

                    conn.execute(
                        insert_sql,
                        insert_values
                    )

        conn.commit()
        conn.close()

        flash(
            "Attendance saved successfully.",
            "success"
        )

        return redirect(
            url_for(
                "attendance",
                class_name=class_name,
                date=attendance_date
            )
        )

    # =====================================================
    # GET ATTENDANCE PAGE
    # =====================================================

    selected_department = request.args.get(
        "department",
        ""
    ).strip()

    selected_year = request.args.get(
        "year",
        ""
    ).strip()

    selected_section = request.args.get(
        "section",
        ""
    ).strip()

    selected_class = request.args.get(
        "class_name",
        ""
    ).strip()

    attendance_date = request.args.get(
        "date",
        ""
    ).strip()

    if not selected_class:

        selected_class = find_class_from_selection(
            selected_department,
            selected_year,
            selected_section
        )

    students = []

    if selected_class:

        students = get_students_for_class(
            selected_class
        )

    attendance_records = {}

    if selected_class and attendance_date:

        conn = get_db_connection()

        records = conn.execute(
            """
            SELECT
                register_number,
                status
            FROM attendance
            WHERE class_name = ?
            AND attendance_date = ?
            """,
            (
                selected_class,
                attendance_date
            )
        ).fetchall()

        conn.close()

        for record in records:

            attendance_records[
                record["register_number"]
            ] = record["status"]

    present_count = sum(
        1
        for status in attendance_records.values()
        if str(status).lower() == "present"
    )

    absent_count = sum(
        1
        for status in attendance_records.values()
        if str(status).lower() == "absent"
    )

    return render_template(
        "attendance.html",
        available_classes=list(
            CLASS_INFO.keys()
        ),
        students=students,
        attendance_records=attendance_records,
        present_count=present_count,
        absent_count=absent_count,
        selected_department=selected_department,
        selected_year=selected_year,
        selected_section=selected_section,
        selected_class=selected_class,
        attendance_date=attendance_date
    )


# =========================================================
# ASSIGNMENTS
# =========================================================

@app.route("/assignments")
@login_required()
def assignments():

    selected_class = request.args.get(
        "class_name",
        ""
    ).strip()

    conn = get_db_connection()

    if selected_class:

        assignments_data = conn.execute(
            """
            SELECT *
            FROM assignments
            WHERE class_name = ?
            ORDER BY id DESC
            """,
            (selected_class,)
        ).fetchall()

    else:

        assignments_data = conn.execute(
            """
            SELECT *
            FROM assignments
            ORDER BY id DESC
            """
        ).fetchall()

    conn.close()

    return render_template(
        "assignments.html",
        assignments=assignments_data,
        available_classes=list(
            CLASS_INFO.keys()
        ),
        selected_class=selected_class
    )


# =========================================================
# ADD ASSIGNMENT
# =========================================================

@app.route(
    "/add_assignment",
    methods=["POST"]
)
@login_required()
def add_assignment():

    register_number = request.form.get(
        "register_number",
        ""
    ).strip()

    student_name = request.form.get(
        "student_name",
        ""
    ).strip()

    class_name = request.form.get(
        "class_name",
        ""
    ).strip()

    subject = request.form.get(
        "subject",
        ""
    ).strip()

    title = request.form.get(
        "title",
        ""
    ).strip()

    status = request.form.get(
        "status",
        ""
    ).strip()

    marks = request.form.get(
        "marks",
        ""
    ).strip()

    conn = get_db_connection()

    conn.execute(
        """
        INSERT INTO assignments (
            register_number,
            student_name,
            class_name,
            subject,
            title,
            status,
            marks
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            register_number,
            student_name,
            class_name,
            subject,
            title,
            status,
            marks
        )
    )

    conn.commit()
    conn.close()

    flash(
        "Assignment added successfully.",
        "success"
    )

    return redirect(
        url_for(
            "assignments",
            class_name=class_name
        )
    )


# =========================================================
# BUILD REPORT DATA
# =========================================================

def build_report_data(
    register_number,
    class_name=""
):

    student = get_student_details(
        register_number
    )

    if student is None:
        return None

    if not class_name:
        class_name = student["class_name"]

    conn = get_db_connection()

    # -----------------------------------------------------
    # ATTENDANCE
    # -----------------------------------------------------

    attendance_rows = conn.execute(
        """
        SELECT *
        FROM attendance
        WHERE register_number = ?
        AND class_name = ?
        ORDER BY id DESC
        """,
        (
            register_number,
            class_name
        )
    ).fetchall()

    total_days = len(
        attendance_rows
    )

    present_days = sum(
        1
        for row in attendance_rows
        if str(
            row["status"] or ""
        ).lower() == "present"
    )

    absent_days = sum(
        1
        for row in attendance_rows
        if str(
            row["status"] or ""
        ).lower() == "absent"
    )

    attendance_percentage = 0

    if total_days > 0:

        attendance_percentage = round(
            (
                present_days
                / total_days
            ) * 100,
            2
        )

    attendance_data = {
        "total_days": total_days,
        "present_days": present_days,
        "absent_days": absent_days,
        "percentage": attendance_percentage
    }

    # -----------------------------------------------------
    # MARKS
    # -----------------------------------------------------

    mark_rows = conn.execute(
        """
        SELECT
            subject,
            mark,
            exam_type
        FROM marks
        WHERE register_number = ?
        AND class_name = ?
        ORDER BY rowid DESC
        """,
        (
            register_number,
            class_name
        )
    ).fetchall()

    marks = []

    total_marks = 0
    total_max_marks = 0

    for row in mark_rows:

        try:
            mark_value = float(
                row["mark"]
            )
        except (
            TypeError,
            ValueError
        ):
            mark_value = 0

        max_mark = 100

        total_marks += mark_value
        total_max_marks += max_mark

        marks.append({
            "subject": row["subject"] or "",
            "mark": mark_value,
            "max_mark": max_mark,
            "exam_type": row["exam_type"] or ""
        })

    marks_percentage = 0

    if total_max_marks > 0:

        marks_percentage = round(
            (
                total_marks
                / total_max_marks
            ) * 100,
            2
        )

    if marks_percentage >= 90:
        grade = "A+"
    elif marks_percentage >= 80:
        grade = "A"
    elif marks_percentage >= 70:
        grade = "B+"
    elif marks_percentage >= 60:
        grade = "B"
    elif marks_percentage >= 50:
        grade = "C"
    elif marks_percentage >= 40:
        grade = "D"
    else:
        grade = "F"

    if marks and marks_percentage >= 40:
        result = "PASS"
    elif marks:
        result = "FAIL"
    else:
        result = "NO MARKS"

    marks_summary = {
        "total": round(
            total_marks,
            2
        ),
        "percentage": marks_percentage,
        "grade": grade,
        "result": result
    }

    # -----------------------------------------------------
    # ACHIEVEMENTS
    # -----------------------------------------------------

    achievement_rows = conn.execute(
        """
        SELECT *
        FROM achievements
        WHERE register_number = ?
        AND class_name = ?
        ORDER BY id DESC
        """,
        (
            register_number,
            class_name
        )
    ).fetchall()

    achievements = []

    for row in achievement_rows:

        achievements.append({
            "achievement_title":
                row["title"] or "",

            "achievement_type":
                row["achievement_type"] or "",

            "achievement_date":
                row["created_at"] or "",

            "description":
                row["description"] or "",

            "photo":
                row["photo"] or "",

            "certificate":
                row["certificate"] or ""
        })

    # -----------------------------------------------------
    # ASSIGNMENTS
    # -----------------------------------------------------

    assignment_rows = conn.execute(
        """
        SELECT *
        FROM assignments
        WHERE register_number = ?
        AND class_name = ?
        ORDER BY id DESC
        """,
        (
            register_number,
            class_name
        )
    ).fetchall()

    assignments_data = []

    for row in assignment_rows:

        assignments_data.append({
            "title":
                row["title"] or "",

            "subject":
                row["subject"] or "",

            "status":
                row["status"] or "",

            "marks":
                row["marks"] or ""
        })

    # -----------------------------------------------------
    # EXAMS
    # -----------------------------------------------------

    exam_rows = conn.execute(
        """
        SELECT *
        FROM exams
        WHERE class_name = ?
        ORDER BY id DESC
        """,
        (class_name,)
    ).fetchall()

    exams_data = []

    for row in exam_rows:

        exams_data.append({
            "exam_name":
                row["exam_name"] or "",

            "subject":
                row["subject"] or "",

            "exam_date":
                row["exam_date"] or "",

            "max_marks":
                row["max_marks"] or ""
        })

    # -----------------------------------------------------
    # SAVED REPORT
    # -----------------------------------------------------

    saved_report = conn.execute(
        """
        SELECT *
        FROM saved_reports
        WHERE register_number = ?
        AND class_name = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (
            register_number,
            class_name
        )
    ).fetchone()

    conn.close()

    return {

        "student": {

            "name":
                student["name"],

            "register_number":
                student["register_number"],

            "class_name":
                class_name,

            "department":
                student["department"],

            "year":
                student["year"],

            "section":
                student["section"]
        },

        "attendance":
            attendance_data,

        "marks":
            marks,

        "marks_summary":
            marks_summary,

        "achievements":
            achievements,

        "assignments":
            assignments_data,

        "exams":
            exams_data,

        "saved_report":
            saved_report
    }


# =========================================================
# REPORTS
# =========================================================

@app.route("/reports")
@login_required()
def reports():

    selected_department = request.args.get(
        "department",
        ""
    ).strip()

    selected_year = request.args.get(
        "year",
        ""
    ).strip()

    selected_section = request.args.get(
        "section",
        ""
    ).strip()

    selected_class = request.args.get(
        "class_name",
        ""
    ).strip()

    selected_register = request.args.get(
        "register_number",
        ""
    ).strip()

    departments = sorted({
        info["department"]
        for info in CLASS_INFO.values()
    })

    year_order = {
        "I Year": 1,
        "II Year": 2,
        "III Year": 3
    }

    years = []

    for class_name, info in CLASS_INFO.items():

        if selected_department:
            if info["department"] != selected_department:
                continue

        if info["year"] not in years:
            years.append(info["year"])

    years.sort(
        key=lambda value:
        year_order.get(value, 99)
    )

    sections = []

    for class_name, info in CLASS_INFO.items():

        if selected_department:
            if info["department"] != selected_department:
                continue

        if selected_year:
            if info["year"] != selected_year:
                continue

        if info["section"]:

            if info["section"] not in sections:
                sections.append(info["section"])

    sections.sort()

    class_names = []

    for class_name, info in CLASS_INFO.items():

        if selected_department:
            if info["department"] != selected_department:
                continue

        if selected_year:
            if info["year"] != selected_year:
                continue

        if selected_section:
            if info["section"] != selected_section:
                continue

        class_names.append(class_name)

    report_students = []

    if selected_class:

        report_students = get_students_for_class(
            selected_class
        )

    report_data = None

    if selected_register:

        report_data = build_report_data(
            selected_register,
            selected_class
        )

        if report_data:

            student_info = report_data["student"]

            selected_class = student_info["class_name"]
            selected_department = student_info["department"]
            selected_year = student_info["year"]
            selected_section = student_info["section"]

            report_students = get_students_for_class(
                selected_class
            )

    conn = get_db_connection()

    db_student_count = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM students
        """
    ).fetchone()["count"]

    total_achievements = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM achievements
        """
    ).fetchone()["count"]

    total_attendance = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM attendance
        """
    ).fetchone()["count"]

    total_assignments = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM assignments
        """
    ).fetchone()["count"]

    total_reports = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM saved_reports
        """
    ).fetchone()["count"]

    conn.close()

    if db_student_count > 0:

        total_students = db_student_count

    else:

        total_students = sum(
            len(
                get_students_for_class(
                    class_name
                )
            )
            for class_name in CLASS_INFO
        )

    if not selected_register:

        return render_template(
            "reports.html",
            departments=departments,
            years=years,
            sections=sections,
            class_names=class_names,
            report_students=report_students,
            selected_department=selected_department,
            selected_year=selected_year,
            selected_section=selected_section,
            selected_class=selected_class,
            selected_register=selected_register,
            report_data=None,
            total_students=total_students,
            total_achievements=total_achievements,
            total_attendance=total_attendance,
            total_assignments=total_assignments,
            total_reports=total_reports,
            class_info=CLASS_INFO
        )

    if report_data:

        return render_template(
            "report.html",
            departments=departments,
            years=years,
            sections=sections,
            class_names=class_names,
            report_students=report_students,
            selected_department=selected_department,
            selected_year=selected_year,
            selected_section=selected_section,
            selected_class=selected_class,
            selected_register=selected_register,
            report_data=report_data,
            total_students=total_students,
            total_achievements=total_achievements,
            total_attendance=total_attendance,
            total_assignments=total_assignments,
            total_reports=total_reports,
            print_mode=False,
            class_info=CLASS_INFO
        )

    flash(
        "Student report not found.",
        "error"
    )

    return redirect(
        url_for(
            "reports",
            department=selected_department,
            year=selected_year,
            section=selected_section,
            class_name=selected_class
        )
    )


# =========================================================
# SAVE REPORT
# =========================================================

@app.route(
    "/save_report",
    methods=["POST"]
)
@login_required()
def save_report():

    register_number = request.form.get(
        "register_number",
        ""
    ).strip()

    class_name = request.form.get(
        "class_name",
        ""
    ).strip()

    academic_notes = request.form.get(
        "academic_notes",
        ""
    ).strip()

    overall_performance = request.form.get(
        "overall_performance",
        ""
    ).strip()

    teacher_remarks = request.form.get(
        "teacher_remarks",
        ""
    ).strip()

    if not register_number:

        flash(
            "Please select a student first.",
            "error"
        )

        return redirect(
            url_for("reports")
        )

    student = get_student_details(
        register_number
    )

    if student is None:

        flash(
            "Student not found.",
            "error"
        )

        return redirect(
            url_for("reports")
        )

    if not class_name:
        class_name = student["class_name"]

    conn = get_db_connection()

    conn.execute(
        """
        INSERT INTO saved_reports (
            register_number,
            student_name,
            class_name,
            academic_notes,
            overall_performance,
            teacher_remarks
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            register_number,
            student["name"],
            class_name,
            academic_notes,
            overall_performance,
            teacher_remarks
        )
    )

    conn.commit()
    conn.close()

    flash(
        "Report saved successfully.",
        "success"
    )

    return redirect(
        url_for(
            "reports",
            department=student["department"],
            year=student["year"],
            section=student["section"],
            class_name=class_name,
            register_number=register_number,
            saved="1"
        )
    )


# =========================================================
# PRINT REPORT
# =========================================================

@app.route(
    "/print_report/<register_number>"
)
@login_required()
def print_report(
    register_number
):

    class_name = request.args.get(
        "class_name",
        ""
    ).strip()

    report_data = build_report_data(
        register_number,
        class_name
    )

    if report_data is None:

        flash(
            "Report student not found.",
            "error"
        )

        return redirect(
            url_for("reports")
        )

    return render_template(
        "report.html",
        departments=[],
        years=[],
        sections=[],
        class_names=[],
        report_students=[],
        selected_department=
            report_data["student"]["department"],
        selected_year=
            report_data["student"]["year"],
        selected_section=
            report_data["student"]["section"],
        selected_class=
            report_data["student"]["class_name"],
        selected_register=
            register_number,
        report_data=report_data,
        total_students=0,
        total_achievements=0,
        total_attendance=0,
        total_assignments=0,
        total_reports=0,
        print_mode=True
    )


# =========================================================
# DOWNLOAD REPORT PDF
# =========================================================

@app.route(
    "/download_report_pdf/<register_number>"
)
@login_required()
def download_report_pdf(
    register_number
):

    class_name = request.args.get(
        "class_name",
        ""
    ).strip()

    report_data = build_report_data(
        register_number,
        class_name
    )

    if report_data is None:

        flash(
            "Report student not found.",
            "error"
        )

        return redirect(
            url_for("reports")
        )

    return render_template(
        "report.html",
        departments=[],
        years=[],
        sections=[],
        class_names=[],
        report_students=[],
        selected_department=
            report_data["student"]["department"],
        selected_year=
            report_data["student"]["year"],
        selected_section=
            report_data["student"]["section"],
        selected_class=
            report_data["student"]["class_name"],
        selected_register=
            register_number,
        report_data=report_data,
        total_students=0,
        total_achievements=0,
        total_attendance=0,
        total_assignments=0,
        total_reports=0,
        print_mode=True,
        pdf_mode=True
    )


# =========================================================
# MARKS
# =========================================================

@app.route("/marks")
@login_required()
def marks():

    selected_class = request.args.get(
        "class_name",
        ""
    ).strip()

    selected_department = request.args.get(
        "department",
        ""
    ).strip()

    selected_year = request.args.get(
        "year",
        ""
    ).strip()

    selected_section = request.args.get(
        "section",
        ""
    ).strip()

    selected_register = request.args.get(
        "register_number",
        ""
    ).strip()

    if not selected_class:

        selected_class = find_class_from_selection(
            selected_department,
            selected_year,
            selected_section
        )

    students = []

    if selected_class:

        students = get_students_for_class(
            selected_class
        )

        info = CLASS_INFO.get(
            selected_class,
            {}
        )

        for student in students:

            student["class_name"] = selected_class

            student["department"] = info.get(
                "department",
                ""
            )

            student["year"] = info.get(
                "year",
                ""
            )

            student["section"] = info.get(
                "section",
                ""
            )

    marks_data = []

    if selected_register:

        conn = get_db_connection()

        marks_data = conn.execute(
            """
            SELECT
                register_number,
                student_name,
                class_name,
                subject,
                mark,
                exam_type
            FROM marks
            WHERE register_number = ?
            ORDER BY rowid DESC
            """,
            (selected_register,)
        ).fetchall()

        conn.close()

    return render_template(
        "marks.html",
        available_classes=list(
            CLASS_INFO.keys()
        ),
        students=students,
        marks=marks_data,
        selected_class=selected_class,
        selected_register=selected_register,
        selected_department=selected_department,
        selected_year=selected_year,
        selected_section=selected_section,
        class_info=CLASS_INFO
    )


# =========================================================
# STUDENT MARKS
# =========================================================

@app.route(
    "/student_marks/<register_number>"
)
@login_required()
def student_marks(
    register_number
):

    department = request.args.get(
        "department",
        ""
    ).strip()

    year = request.args.get(
        "year",
        ""
    ).strip()

    section = request.args.get(
        "section",
        ""
    ).strip()

    class_name = request.args.get(
        "class_name",
        ""
    ).strip()

    if not class_name:

        class_name = find_class_from_selection(
            department,
            year,
            section
        )

    student = get_student_details(
        register_number
    )

    if student is None:

        flash(
            "Student not found.",
            "error"
        )

        return redirect(
            url_for(
                "marks",
                department=department,
                year=year,
                section=section,
                class_name=class_name
            )
        )

    if not class_name:
        class_name = student["class_name"]

    class_details = CLASS_INFO.get(
        class_name,
        {}
    )

    student["class_name"] = class_name

    student["department"] = class_details.get(
        "department",
        student.get("department", "")
    )

    student["year"] = class_details.get(
        "year",
        student.get("year", "")
    )

    student["section"] = class_details.get(
        "section",
        student.get("section", "")
    )

    conn = get_db_connection()

    marks_data = conn.execute(
        """
        SELECT
            register_number,
            student_name,
            class_name,
            subject,
            mark,
            exam_type
        FROM marks
        WHERE register_number = ?
        ORDER BY rowid DESC
        """,
        (register_number,)
    ).fetchall()

    conn.close()

    return render_template(
        "student_marks.html",
        student=student,
        class_name=class_name,
        marks=marks_data,
        saved_marks=marks_data,
        department=student["department"],
        year=student["year"],
        section=student["section"],
        selected_class=class_name,
        selected_department=student["department"],
        selected_year=student["year"],
        selected_section=student["section"]
    )


# =========================================================
# SAVE STUDENT MARKS
# =========================================================

@app.route(
    "/save_student_marks",
    methods=["POST"]
)
@login_required()
def save_student_marks():

    register_number = request.form.get(
        "register_number",
        ""
    ).strip()

    student_name = request.form.get(
        "student_name",
        ""
    ).strip()

    department = request.form.get(
        "department",
        ""
    ).strip()

    year = request.form.get(
        "year",
        ""
    ).strip()

    section = request.form.get(
        "section",
        ""
    ).strip()

    class_name = request.form.get(
        "class_name",
        ""
    ).strip()

    subjects = request.form.getlist(
        "subject[]"
    )

    marks_list = request.form.getlist(
        "mark[]"
    )

    if not register_number:

        flash(
            "Student register number is missing.",
            "error"
        )

        return redirect(
            url_for("marks")
        )

    if not class_name:

        class_name = find_class_from_selection(
            department,
            year,
            section
        )

    student = get_student_details(
        register_number
    )

    if student:

        if not student_name:
            student_name = student["name"]

        if not class_name:
            class_name = student["class_name"]

    conn = get_db_connection()

    conn.execute(
        """
        DELETE FROM marks
        WHERE register_number = ?
        AND class_name = ?
        AND exam_type = ?
        """,
        (
            register_number,
            class_name,
            "Mark Sheet"
        )
    )

    total_items = min(
        len(subjects),
        len(marks_list)
    )

    for i in range(total_items):

        subject = subjects[i].strip()
        mark_value = marks_list[i].strip()

        if not subject or not mark_value:
            continue

        conn.execute(
            """
            INSERT INTO marks (
                register_number,
                student_name,
                class_name,
                subject,
                mark,
                exam_type
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                register_number,
                student_name,
                class_name,
                subject,
                mark_value,
                "Mark Sheet"
            )
        )

    conn.commit()
    conn.close()

    flash(
        "Marks saved successfully.",
        "success"
    )

    return redirect(
        url_for(
            "student_marks",
            register_number=register_number,
            class_name=class_name
        )
    )


# =========================================================
# ADD MARK
# =========================================================

@app.route(
    "/add_mark",
    methods=["POST"]
)
@login_required()
def add_mark():

    register_number = request.form.get(
        "register_number",
        ""
    ).strip()

    student_name = request.form.get(
        "student_name",
        ""
    ).strip()

    class_name = request.form.get(
        "class_name",
        ""
    ).strip()

    subject = request.form.get(
        "subject",
        ""
    ).strip()

    mark = request.form.get(
        "mark",
        ""
    ).strip()

    exam_type = request.form.get(
        "exam_type",
        ""
    ).strip()

    conn = get_db_connection()

    conn.execute(
        """
        INSERT INTO marks (
            register_number,
            student_name,
            class_name,
            subject,
            mark,
            exam_type
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            register_number,
            student_name,
            class_name,
            subject,
            mark,
            exam_type
        )
    )

    conn.commit()
    conn.close()

    flash(
        "Mark added successfully.",
        "success"
    )

    return redirect(
        url_for(
            "student_marks",
            register_number=register_number,
            class_name=class_name
        )
    )


# =========================================================
# EXAMS
# =========================================================

@app.route("/exams")
@login_required()
def exams():

    conn = get_db_connection()

    exams_data = conn.execute(
        """
        SELECT *
        FROM exams
        ORDER BY id DESC
        """
    ).fetchall()

    conn.close()

    return render_template(
        "exams.html",
        exams=exams_data,
        available_classes=list(
            CLASS_INFO.keys()
        )
    )


# =========================================================
# ADD EXAM
# =========================================================

@app.route(
    "/add_exam",
    methods=["POST"]
)
@login_required()
def add_exam():

    class_name = request.form.get(
        "class_name",
        ""
    ).strip()

    subject = request.form.get(
        "subject",
        ""
    ).strip()

    exam_name = request.form.get(
        "exam_name",
        ""
    ).strip()

    exam_date = request.form.get(
        "exam_date",
        ""
    ).strip()

    max_marks = request.form.get(
        "max_marks",
        ""
    ).strip()

    conn = get_db_connection()

    conn.execute(
        """
        INSERT INTO exams (
            class_name,
            subject,
            exam_name,
            exam_date,
            max_marks
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            class_name,
            subject,
            exam_name,
            exam_date,
            max_marks
        )
    )

    conn.commit()
    conn.close()

    flash(
        "Exam added successfully.",
        "success"
    )

    return redirect(
        url_for("exams")
    )


# =========================================================
# SETTINGS
# =========================================================

@app.route("/settings")
@login_required()
def settings():

    return render_template(
        "settings.html"
    )


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/health")
def health():

    return {
        "status": "running",
        "application":
            "Smart Students Success Tracking System"
    }


# =========================================================
# 404 ERROR
# =========================================================

@app.errorhandler(404)
def page_not_found(error):

    return render_template(
        "404.html"
    ), 404


# =========================================================
# 413 ERROR
# =========================================================

@app.errorhandler(413)
def file_too_large(error):

    flash(
        "File is too large. Maximum size is 10 MB.",
        "error"
    )

    return redirect(
        request.referrer
        or url_for("dashboard")
    )


# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":

    init_db()

    print()
    print("=" * 60)
    print(
        "SMART STUDENTS SUCCESS TRACKING SYSTEM"
    )
    print("=" * 60)
    print(
        "Server running..."
    )
    print(
        "Open: http://127.0.0.1:5000"
    )
    print(
        "Default username: admin"
    )
    print(
        "Default password: admin123"
    )
    print("=" * 60)
    print()

    app.run(
        debug=True,
        use_reloader=False,
        host="127.0.0.1",
        port=5000
    )