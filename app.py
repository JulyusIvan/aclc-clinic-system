from flask import Flask, render_template,url_for,request,session,flash,redirect
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column,Relationship
import os
from werkzeug.utils import secure_filename
from datetime import date


app = Flask (__name__)
bootstrap = Bootstrap5 (app)

app.config ['SECRET_KEY'] = 'Julyus'
app.config ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///aclcclinic.db'
app.config ['SQLALCHEMY_TRACK_MODICATIONS'] = True

class Base (DeclarativeBase):
    pass

db = SQLAlchemy (model_class=Base)
db.init_app(app)

#==========================================================================================================================================
class User(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    username: Mapped[str] 
    password: Mapped[str] 
    role: Mapped[str] 
    profile_photo: Mapped[str]
    


class StudentInfo(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    first_name: Mapped[str]
    last_name: Mapped[str]
    gender: Mapped[str]
    bod: Mapped[str]
    contact_info: Mapped[str]

    examinations = Relationship("StudentExamine", back_populates="student", cascade="all, delete-orphan")
    medical_records = Relationship("StudentMedicalRecord", back_populates="student", cascade="all, delete-orphan")
    logs = Relationship("StudentLog", back_populates="student", cascade="all, delete-orphan")


class Doctor(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    first_name: Mapped[str]
    last_name: Mapped[str]
    specialization: Mapped[str]
    contact_info: Mapped[str]

    examinations = Relationship("StudentExamine", back_populates="doctor", cascade="all, delete-orphan")


class Nurse(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    first_name: Mapped[str]
    last_name: Mapped[str]
    shift: Mapped[str]
    contact_info: Mapped[str]

    examinations = Relationship("StudentExamine", back_populates="nurse", cascade="all, delete-orphan")


class StudentExamine(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student_info.id"), nullable=False)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctor.id"), nullable=True)
    nurse_id: Mapped[int] = mapped_column(ForeignKey("nurse.id"), nullable=False)
    examine_date: Mapped[str]
    symptoms: Mapped[str]

    student = Relationship("StudentInfo", back_populates="examinations")
    doctor = Relationship("Doctor", back_populates="examinations")
    nurse = Relationship("Nurse", back_populates="examinations")
    diagnosis = Relationship("Diagnosis", back_populates="examine", uselist=False, cascade="all, delete-orphan")
    medical_record = Relationship("StudentMedicalRecord", back_populates="examination", uselist=False, cascade="all, delete-orphan")


class Diagnosis(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    examine_id: Mapped[int] = mapped_column(ForeignKey("student_examine.id"), nullable=False)
    diagnose_details: Mapped[str] = mapped_column(Text)
    treatment_plan: Mapped[str] = mapped_column(Text)
    date_diagnose: Mapped[str]

    examine = Relationship("StudentExamine", back_populates="diagnosis")
    medical_record = Relationship("StudentMedicalRecord", back_populates="diagnosis", uselist=False)


class StudentMedicalRecord(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student_info.id"), nullable=False)
    examine_id: Mapped[int] = mapped_column(ForeignKey("student_examine.id"), nullable=False)
    diagnosis_id: Mapped[int] = mapped_column(ForeignKey("diagnosis.id"), nullable=True)
    date_recorded: Mapped[str]

    student = Relationship("StudentInfo", back_populates="medical_records")
    examination = Relationship("StudentExamine", back_populates="medical_record")
    diagnosis = Relationship("Diagnosis", back_populates="medical_record")


class StudentLog(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student_info.id"), nullable=False)
    log_date: Mapped[str]
    activity: Mapped[str]

    student = Relationship("StudentInfo", back_populates="logs")

#===========================================================================================================================================
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload_profile', methods=['POST'])
def upload_profile():
    if 'profile_photo' not in request.files or 'username' not in session:
        flash('No file selected or user session missing.', 'danger')
        return redirect(request.referrer)

    file = request.files['profile_photo']
    if file.filename == '':
        flash('No selected file.', 'danger')
        return redirect(request.referrer)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        user = User.query.filter_by(username=session['username']).first()
        user.profile_photo = filename
        db.session.commit()

        flash('Profile photo updated successfully.', 'success')
        return redirect(request.referrer)
    else:
        flash('File type not allowed.', 'danger')
        return redirect(request.referrer)


@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password: 
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash('Login successful!', 'success')
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'nurse':
                return redirect(url_for('nurse_dashboard'))
            elif user.role == 'doctor':
                return redirect(url_for('doctor_dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('User/login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.context_processor
def inject_user():
    if 'username' in session:
        user = User.query.filter_by(username=session['username']).first()
        return dict(user=user)
    return dict(user=None)

#=========================ADMIN==============================================
@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))

    student_count = StudentInfo.query.count()
    user_count = User.query.count()
    log_count = StudentLog.query.count()
    users = {u.username: u for u in User.query.all()}
    
    recent_logs = db.session.query(
        StudentLog.log_date,
        StudentLog.activity,
        StudentInfo.first_name,
        StudentInfo.last_name
    ).join(StudentInfo, StudentLog.student_id == StudentInfo.id).order_by(StudentLog.log_date.desc()).limit(5).all()  

    return render_template('User/dashboard_admin.html',
                           student_count=student_count,
                           user_count=user_count,
                           log_count=log_count,
                           users=users,
                           recent_logs=recent_logs)


@app.route('/admin/register', methods=['GET', 'POST'])
def register_user():
    if session.get('role') != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'warning')
            return redirect(url_for('register_user'))

        new_user = User(username=username, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()
        flash('User registered successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('User/register_user.html')

@app.route('/admin/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if session.get('role') != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))

    user = User.query.get(user_id)

    if request.method == 'POST':
        user.username = request.form['username']
        if request.form['password']:
             user.password = request.form['password']
        user.role = request.form['role']

        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('view_users'))

    return render_template('User/view_users.html', user=user)

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if session.get('role') != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))

    user = User.query.get(user_id)

    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('view_users'))


@app.route('/admin/users')
def view_users():
    if session.get('role') != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    
    users = User.query.all()
    return render_template('User/view_users.html', users=users)

@app.route('/admin/students')
def admin_students():
    if session.get('role') != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))

    students = StudentInfo.query.all()
    return render_template('User/view_students.html', students=students)

@app.route('/nurse/student/add', methods=['GET', 'POST'])
def add_student():
    if session.get('role') != 'nurse':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_student = StudentInfo(
            first_name=request.form['first_name'],
            last_name=request.form['last_name'],
            gender=request.form['gender'],
            bod=request.form['bod'],
            contact_info=request.form['contact_info']
        )
        db.session.add(new_student)
        db.session.commit()
        flash('Student added successfully!', 'success')
        return redirect(url_for('nurse_view_students'))

    return render_template('User/nurse_students_view.html')

@app.route('/admin/student/edit/<int:student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    student = StudentInfo.query.get(student_id)
    
    if request.method == 'POST':
        student.first_name = request.form['first_name']
        student.last_name = request.form['last_name']
        student.gender = request.form['gender']
        student.bod = request.form['bod']
        student.contact_info = request.form['contact_info']
        db.session.commit()
        flash('Student updated successfully!', 'success')
        return redirect(url_for('admin_students'))

    return render_template('User/view_students.html', student=student)

@app.route('/admin/student/delete/<int:student_id>')
def delete_student(student_id):
    student = StudentInfo.query.get(student_id)
    db.session.delete(student)
    db.session.commit()
    flash('Student deleted successfully!', 'success')
    return redirect(url_for('admin_students'))

@app.route('/admin/logs')
def view_logs():
    if session.get('role') != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))

    logs = StudentLog.query.join(StudentInfo).all()
    return render_template('User/view_logs.html', logs=logs)

#======================================================================================================================================
@app.route('/nurse/dashboard')
def nurse_dashboard():
    if session.get('role') != 'nurse':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    student_count = StudentInfo.query.count()
    examine_count = StudentExamine.query.count()
    log_count = StudentLog.query.count()
    recent_examinations = StudentExamine.query.order_by(StudentExamine.examine_date.desc()).limit(5).all()
    users = {u.username: u for u in User.query.all()}
    user = User.query.filter_by(username=session['username']).first()

    return render_template('User/dashboard_nurse.html', 
                           username=session.get('username'), 
                           student_count=student_count, 
                           examine_count=examine_count, 
                           log_count=log_count,
                           recent_examinations=recent_examinations,
                           users=users,
                           user=user)

@app.route('/nurse/students')
def nurse_view_students():
    if session.get('role') != 'nurse':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    students = StudentInfo.query.all()
    return render_template('User/nurse_students_view.html', students=students)

@app.route('/nurse/examinations')
def nurse_view_examinations():
    if session.get('role') != 'nurse':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    examinations = StudentExamine.query.all()
    students = StudentInfo.query.all()

    grouped_students = []
    for student in students:
        student_exams = [exam for exam in examinations if exam.student_id == student.id]
        if student_exams:
            student.examinations = sorted(student_exams, key=lambda e: e.examine_date, reverse=True)
            grouped_students.append(student)

    return render_template('User/nurse_view_examination.html', examinations=examinations, grouped_students=grouped_students)

@app.route('/nurse/examination/add/<int:student_id>', methods=['GET', 'POST'])
def nurse_add_examination(student_id):
    if session.get('role') != 'nurse':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))

    student = StudentInfo.query.get(student_id)
    doctors = Doctor.query.all()
    nurses = Nurse.query.all()

    if request.method == 'POST':
        doctor_id = request.form.get('doctor_id') or None 
        if doctor_id == '':
            doctor_id = None  
        nurse_id = request.form['nurse_id']
        examine_date = request.form['examine_date']
        symptoms = request.form['symptoms']

        new_exam = StudentExamine(
            student_id=student.id,
            doctor_id=doctor_id,
            nurse_id=nurse_id,
            examine_date=examine_date,
            symptoms=symptoms
        )
        db.session.add(new_exam)
        db.session.commit()
        flash('Examination recorded successfully!', 'success')
        return redirect(url_for('nurse_view_examinations'))

    return render_template('User/nurse_add_examination.html', student=student, doctors=doctors, nurses=nurses)

@app.route('/nurse/examination/edit/<int:exam_id>', methods=['GET', 'POST'])
def edit_examination(exam_id):
    if session.get('role') != 'nurse':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))

    exam = StudentExamine.query.get(exam_id)
    student = exam.student
    doctors = Doctor.query.all()
    nurses = Nurse.query.all()

    if request.method == 'POST':
        exam.examine_date = request.form['examine_date']
        exam.symptoms = request.form['symptoms']
        exam.nurse_id = request.form['nurse_id']
        doctor_id = request.form.get('doctor_id')
        exam.doctor_id = doctor_id if doctor_id else None

        db.session.commit()
        flash('Examination updated successfully!', 'success')
        return redirect(url_for('nurse_view_examinations'))

    return render_template('User/nurse_edit_examination.html', exam=exam, student=student, doctors=doctors, nurses=nurses)


@app.route('/nurse/examination/delete/<int:exam_id>', methods=['POST'])
def delete_examination(exam_id):
    if session.get('role') != 'nurse':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))

    exam = StudentExamine.query.get(exam_id)

    try:
        db.session.delete(exam)
        db.session.commit()
        flash('Examination deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting examination: ' + str(e), 'danger')

    return redirect(url_for('nurse_view_examinations'))

@app.route('/nurse/logs')
def nurse_view_logs():
    if session.get('role') != 'nurse':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    logs = db.session.query(StudentLog, StudentInfo).join(StudentInfo).all()
    students = StudentInfo.query.all()  
    
    return render_template('User/nurse_view_logs.html',logs=logs, students=students)

@app.route('/add-log', methods=['POST'])
def add_log():
    student_id = request.form['student_id']
    log_date = request.form['log_date']
    activity = request.form['activity']

    new_log = StudentLog(student_id=student_id, log_date=log_date, activity=activity)
    db.session.add(new_log)
    db.session.commit()

    return redirect(url_for('nurse_view_logs'))

@app.route('/edit-log/<int:log_id>', methods=['POST'])
def edit_log(log_id):
    log = StudentLog.query.get(log_id)
    log.student_id = request.form['student_id']
    log.log_date = request.form['log_date']
    log.activity = request.form['activity']
    db.session.commit()
    flash('Log updated successfully.', 'success')
    return redirect(url_for('nurse_view_logs'))

@app.route('/delete-log/<int:log_id>')
def delete_log(log_id):
    log = StudentLog.query.get(log_id)
    db.session.delete(log)
    db.session.commit()
    flash('Log deleted successfully.', 'success')
    return redirect(url_for('nurse_view_logs'))

@app.route('/nurse/profile')
def nurse_profile():
    if session.get('role') != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))

    nurse = Nurse.query.all()
    return render_template('User/nurse_profile.html', nurse=nurse)

@app.route('/add_nurse', methods=['POST'])
def add_nurse():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        shift = request.form['shift']
        contact_info = request.form['contact_info']

        new_nurse = Nurse(
            first_name=first_name,
            last_name=last_name,
            shift=shift,
            contact_info=contact_info
        )

        try:
            db.session.add(new_nurse)
            db.session.commit()
            flash('Nurse added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error adding nurse: ' + str(e), 'danger')

        return redirect(url_for('nurse_profile')) 
    
@app.route('/edit-nurse/<int:nurse_id>', methods=['POST'])
def edit_nurse(nurse_id):
    nurse = Nurse.query.get(nurse_id)
    nurse.first_name = request.form['first_name']
    nurse.last_name = request.form['last_name']
    nurse.shift = request.form['shift']
    nurse.contact_info = request.form['contact_info']
    db.session.commit()
    flash('Nurse updated successfully!', 'success')
    return redirect(url_for('nurse_profile'))

@app.route('/delete-nurse/<int:nurse_id>')
def delete_nurse(nurse_id):
    nurse = Nurse.query.get(nurse_id)
    db.session.delete(nurse)
    db.session.commit()
    flash('Nurse deleted successfully!', 'danger')
    return redirect(url_for('nurse_profile'))

@app.route('/nurse/medical_records', methods=['GET', 'POST'])
def view_student_medical_records():
    if session.get('role') != 'nurse':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))

    selected_student_id = request.args.get('student_id', type=int)
    students = StudentInfo.query.all()

    records = []
    all_examinations = StudentExamine.query.all()

    for exam in all_examinations:
        existing_record = StudentMedicalRecord.query.filter_by(examine_id=exam.id).first()
        if not existing_record:
            new_record = StudentMedicalRecord(
                student_id=exam.student_id,
                examine_id=exam.id,
                diagnosis_id=exam.diagnosis.id if exam.diagnosis else None,
                date_recorded=date.today()
            )
            db.session.add(new_record)
            db.session.commit()
            records.append(new_record)
        else:
            records.append(existing_record)

    if selected_student_id:
        records = [record for record in records if record.student_id == selected_student_id]
        selected_student = StudentInfo.query.get(selected_student_id)
    else:
        selected_student = None

    return render_template(
        'User/nurse_medical_records.html',
        records=records,
        students=students,
        selected_student=selected_student
    )
@app.route('/edit_medical_record/<int:record_id>', methods=['GET', 'POST'])
def edit_medical_record(record_id):
    record = StudentMedicalRecord.query.get(record_id)

    if request.method == 'POST':
       
        record.date_recorded = request.form['date_recorded']

    
        if record.diagnosis:
            record.diagnosis.diagnose_details = request.form['diagnose_details']
            record.diagnosis.treatment_plan = request.form['treatment_plan']
            record.diagnosis.date_diagnose = request.form['date_diagnose']

        db.session.commit()
        flash('Medical record updated successfully!', 'success')
        return redirect(url_for('view_student_medical_records')) 

    return render_template('User/nurse_medical_records.html', record=record)

@app.route('/delete_medical_record/<int:record_id>', methods=['POST'])
def delete_medical_record(record_id):
    record = StudentMedicalRecord.query.get(record_id)
    
    
    if record.diagnosis:
        db.session.delete(record.diagnosis)
    
   
    db.session.delete(record)
    db.session.commit()  
    
    flash('Medical record deleted successfully!', 'danger')
    return redirect(url_for('view_student_medical_records')) 
#=================================================================================================================================

@app.route('/doctor/dashboard')
def doctor_dashboard():
    if session.get('role') != 'doctor':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))

    doctor_id = session.get('user_id')
    examine_count = StudentExamine.query.count()
    diagnosis_count = Diagnosis.query.count()
    recent_diagnoses = Diagnosis.query.all()
    users = {u.username: u for u in User.query.all()}

    return render_template('User/dashboard_doctor.html',
                           username=session.get('username'),
                           examine_count=examine_count,
                           diagnosis_count=diagnosis_count,
                           recent_diagnoses=recent_diagnoses,
                           users = users)

@app.route('/doctor/examinations')
def doctor_examinations():
    if session.get('role') != 'doctor':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    
    examinations = StudentExamine.query.all()

    return render_template('User/doc_view_examination.html', examinations=examinations)

@app.route('/doctor/diagnose/<int:examine_id>', methods=['GET', 'POST'])
def add_diagnosis(examine_id):
    if session.get('role') != 'doctor':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))

    exam = StudentExamine.query.get(examine_id)

    if exam.diagnosis:
        flash('Diagnosis already exists for this examination.', 'warning')
        return redirect(url_for('doctor_examinations'))

    if request.method == 'POST':
        diagnose_details = request.form['diagnose_details']
        treatment_plan = request.form['treatment_plan']
        date_diagnose = request.form['date_diagnose']

        new_diagnosis = Diagnosis(
            examine_id=exam.id,
            diagnose_details=diagnose_details,
            treatment_plan=treatment_plan,
            date_diagnose=date_diagnose
        )
        db.session.add(new_diagnosis)
        db.session.commit()
        flash('Diagnosis recorded successfully!', 'success')
        return redirect(url_for('doctor_examinations'))

    return render_template('User/doc_add_diagnosis.html', exam=exam)

@app.route('/doctor/diagnoses')
def view_all_diagnoses():
    if session.get('role') != 'doctor':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))

    diagnoses = Diagnosis.query.all()
    return render_template('User/doc_view_diagnosis.html', diagnoses=diagnoses)

@app.route('/doctor/diagnosis/edit/<int:diagnosis_id>', methods=['POST'])
def edit_diagnosis(diagnosis_id):
    if session.get('role') != 'doctor':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))

    diagnosis = Diagnosis.query.get(diagnosis_id)

    diagnosis.diagnose_details = request.form['diagnose_details']
    diagnosis.treatment_plan = request.form['treatment_plan']
    diagnosis.date_diagnose = request.form['date_diagnose']

    db.session.commit()
    flash('Diagnosis updated successfully!', 'success')
    return redirect(url_for('view_all_diagnoses'))

@app.route('/doctor/diagnosis/delete/<int:diagnosis_id>', methods=['POST'])
def delete_diagnosis(diagnosis_id):
    if session.get('role') != 'doctor':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))

    diagnosis = Diagnosis.query.get(diagnosis_id)
    db.session.delete(diagnosis)
    db.session.commit()
    flash('Diagnosis deleted successfully.', 'success')
    return redirect(url_for('view_all_diagnoses'))

@app.route('/admin/doctors')
def view_doctors():
    if session.get('role') != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    doctors = Doctor.query.all()
    return render_template('User/doctor_profile.html', doctors=doctors)

@app.route('/admin/doctors/add', methods=['POST'])
def add_doctor():
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    specialization = request.form['specialization']
    contact_info = request.form['contact_info']

    new_doc = Doctor(first_name=first_name, last_name=last_name, specialization=specialization, contact_info=contact_info)
    db.session.add(new_doc)
    db.session.commit()
    flash('Doctor added successfully!', 'success')
    return redirect(url_for('view_doctors'))

@app.route('/admin/doctors/edit/<int:doctor_id>', methods=['POST'])
def edit_doctor(doctor_id):
    doc = Doctor.query.get(doctor_id)
    doc.first_name = request.form['first_name']
    doc.last_name = request.form['last_name']
    doc.specialization = request.form['specialization']
    doc.contact_info = request.form['contact_info']
    db.session.commit()
    flash('Doctor updated successfully!', 'success')
    return redirect(url_for('view_doctors'))

@app.route('/admin/doctors/delete/<int:doctor_id>', methods=['POST'])
def delete_doctor(doctor_id):
    doc = Doctor.query.get(doctor_id)
    db.session.delete(doc)
    db.session.commit()
    flash('Doctor deleted successfully!', 'success')
    return redirect(url_for('view_doctors'))

if __name__ == '__main__':
    app.run(debug=True)


