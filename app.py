from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_sqlalchemy import SQLAlchemy

from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

import numpy as np
import joblib

# ===================================
# CREATE FLASK APP
# ===================================

app = Flask(__name__)

# ===================================
# SECRET KEY
# ===================================

app.config['SECRET_KEY'] = 'supersecretkey'

# ===================================
# DATABASE CONFIG
# ===================================

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ===================================
# INITIALIZE DATABASE
# ===================================

db = SQLAlchemy(app)

# ===================================
# LOGIN MANAGER
# ===================================

login_manager = LoginManager()

login_manager.init_app(app)

login_manager.login_view = 'student_login'

# ===================================
# USER MODEL
# ===================================

class User(UserMixin, db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    email = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(200),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        default='student'
    )

# ===================================
# PREDICTION MODEL
# ===================================

class Prediction(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id')
    )

    performance = db.Column(
        db.String(50)
    )

    confidence = db.Column(
        db.Float
    )

    risk_level = db.Column(
        db.String(50)
    )

    user = db.relationship(
        'User',
        backref='predictions'
    )

# ===================================
# LOAD USER
# ===================================

@login_manager.user_loader
def load_user(user_id):

    return User.query.get(
        int(user_id)
    )

# ===================================
# LOAD ML MODEL
# ===================================

model = joblib.load(
    'model/student_performance_model.pkl'
)

scaler = joblib.load(
    'model/scaler.pkl'
)

# ===================================
# RECOMMENDATION SYSTEM
# ===================================

def give_recommendations(

    study_hours,
    attendance,
    social_media,
    sleep_hours,
    mental_health,
    exercise_frequency,
    diet_quality

):

    recommendations = []

    if study_hours < 3:

        recommendations.append(
            "Increase daily study hours."
        )

    else:

        recommendations.append(
            "Maintain consistent study schedule."
        )

    if attendance < 75:

        recommendations.append(
            "Improve attendance consistency."
        )

    else:

        recommendations.append(
            "Attendance performance is good."
        )

    if social_media > 5:

        recommendations.append(
            "Reduce social media usage."
        )

    else:

        recommendations.append(
            "Balanced screen time detected."
        )

    if sleep_hours < 6:

        recommendations.append(
            "Improve sleep quality."
        )

    else:

        recommendations.append(
            "Healthy sleep schedule detected."
        )

    if mental_health < 5:

        recommendations.append(
            "Focus on stress management."
        )

    if exercise_frequency < 3:

        recommendations.append(
            "Regular exercise improves focus."
        )

    if diet_quality < 5:

        recommendations.append(
            "Improve nutritional habits."
        )

    return recommendations

# ===================================
# ROLE SELECTION PAGE
# ===================================

@app.route('/')

def select_role():

    return render_template(
        'select_role.html'
    )

# ===================================
# REGISTER ROUTE
# ===================================

@app.route(
    '/register',
    methods=['GET', 'POST']
)

def register():

    if request.method == 'POST':

        username = request.form['username']

        email = request.form['email']

        password = request.form['password']

        role = request.form['role']

        hashed_password = generate_password_hash(
            password
        )

        new_user = User(

            username=username,

            email=email,

            password=hashed_password,

            role=role
        )

        db.session.add(new_user)

        db.session.commit()

        flash(
            'Registration Successful!'
        )

        return redirect(
            url_for('select_role')
        )

    return render_template(
        'register.html'
    )

# ===================================
# STUDENT LOGIN
# ===================================

@app.route(
    '/student-login',
    methods=['GET', 'POST']
)

def student_login():

    if request.method == 'POST':

        email = request.form['email']

        password = request.form['password']

        user = User.query.filter_by(

            email=email,

            role='student'

        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):

            login_user(user)

            return redirect(
                url_for('dashboard')
            )

        else:

            flash(
                'Invalid Student Credentials'
            )

    return render_template(

        'login.html',

        role='Student'
    )

# ===================================
# TEACHER LOGIN
# ===================================

@app.route(
    '/teacher-login',
    methods=['GET', 'POST']
)

def teacher_login():

    if request.method == 'POST':

        email = request.form['email']

        password = request.form['password']

        user = User.query.filter_by(

            email=email,

            role='teacher'

        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):

            login_user(user)

            return redirect(
                url_for('teacher_dashboard')
            )

        else:

            flash(
                'Invalid Teacher Credentials'
            )

    return render_template(

        'login.html',

        role='Teacher'
    )



# ===================================
# LOGOUT
# ===================================

@app.route('/logout')

@login_required
def logout():

    logout_user()

    return redirect(
        url_for('select_role')
    )

# ===================================
# STUDENT DASHBOARD
# ===================================

@app.route('/dashboard')

@login_required
def dashboard():

    predictions = Prediction.query.filter_by(
        user_id=current_user.id
    ).all()

    high_count = 0
    moderate_count = 0
    low_count = 0

    for p in predictions:

        if p.performance == "Excellent":

            high_count += 1

        elif p.performance == "Moderate":

            moderate_count += 1

        else:

            low_count += 1

    return render_template(

        'dashboard.html',

        predictions=predictions,

        high_count=high_count,

        moderate_count=moderate_count,

        low_count=low_count
    )

# ===================================
# TEACHER DASHBOARD
# ===================================

@app.route('/teacher-dashboard')

@login_required
def teacher_dashboard():

    if current_user.role != 'teacher':

        return redirect(
            url_for('dashboard')
        )

    predictions = Prediction.query.all()

    total_predictions = len(predictions)

    high_risk = 0

    total_confidence = 0

    high_count = 0
    moderate_count = 0
    low_count = 0

    for p in predictions:

        total_confidence += p.confidence

        if p.risk_level == "High Risk":

            high_risk += 1

        if p.performance == "Excellent":

            high_count += 1

        elif p.performance == "Moderate":

            moderate_count += 1

        else:

            low_count += 1

    avg_confidence = 0

    if total_predictions > 0:

        avg_confidence = round(
            total_confidence / total_predictions,
            2
        )

    return render_template(

        'teacher_dashboard.html',

        predictions=predictions,

        total_predictions=total_predictions,

        high_risk=high_risk,

        avg_confidence=avg_confidence,

        high_count=high_count,

        moderate_count=moderate_count,

        low_count=low_count
    )


# ===================================
# ADMIN ROUTE
# ===================================


@app.route('/admin-dashboard')
@login_required
def admin_dashboard():

    if current_user.role != 'admin':
        return redirect('/')

    total_users = User.query.count()

    total_students = User.query.filter_by(role='student').count()

    total_teachers = User.query.filter_by(role='teacher').count()

    total_predictions = Prediction.query.count()

    high_risk = Prediction.query.filter_by(
        risk_level='High Risk'
    ).count()

    users = User.query.all()

    return render_template(

        'admin_dashboard.html',

        total_users=total_users,

        total_students=total_students,

        total_teachers=total_teachers,

        total_predictions=total_predictions,

        high_risk=high_risk,

        users=users
    )


# ===================================
# ADMIN LOGIN
# ===================================

@app.route(
    '/admin-login',
    methods=['GET', 'POST']
)

def admin_login():

    if request.method == 'POST':

        email = request.form['email']

        password = request.form['password']

        user = User.query.filter_by(

            email=email,

            role='admin'

        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):

            login_user(user)

            return redirect(
                url_for('admin_dashboard')
            )

        else:

            flash(
                'Invalid Admin Credentials'
            )

    return render_template(

        'login.html',

        role='Admin'
    )

# ===================================
# PREDICTION PAGE
# ===================================

@app.route('/predict')

@login_required
def predict():

    return render_template(
        'predict.html'
    )

# ===================================
# RESULT PAGE
# ===================================

@app.route(
    '/result',
    methods=['POST']
)

@login_required
def result():

    age = float(
        request.form['age']
    )

    gender = float(
        request.form['gender']
    )

    study_hours = float(
        request.form['study_hours']
    )

    social_media = float(
        request.form['social_media']
    )

    netflix_hours = float(
        request.form['netflix_hours']
    )

    part_time_job = float(
        request.form['part_time_job']
    )

    attendance = float(
        request.form['attendance']
    )

    sleep_hours = float(
        request.form['sleep_hours']
    )

    diet_quality = float(
        request.form['diet_quality']
    )

    exercise_frequency = float(
        request.form['exercise_frequency']
    )

    parental_education = float(
        request.form['parental_education']
    )

    internet_quality = float(
        request.form['internet_quality']
    )

    mental_health = float(
        request.form['mental_health']
    )

    extracurricular = float(
        request.form['extracurricular']
    )


    # ===================================
    # FEATURE ENGINEERING
    # ===================================

    entertainment_usage = (
        social_media +
        netflix_hours
    )

    lifestyle_score = (
        sleep_hours +
        exercise_frequency +
        diet_quality
    )

    discipline_score = (
        study_hours +
        attendance / 10
    )

    stress_indicator = (
        social_media -
        sleep_hours
    )

    study_efficiency = (
        study_hours /
        (social_media + 1)
    )

    # ===================================
    # FINAL FEATURES
    # ===================================

    features = np.array([[
        age,
        gender,
        study_hours,
        social_media,
        netflix_hours,
        part_time_job,
        attendance,
        sleep_hours,
        diet_quality,
        exercise_frequency,
        parental_education,
        internet_quality,
        mental_health,
        extracurricular,
        entertainment_usage,
        lifestyle_score,
        discipline_score,
        stress_indicator,
        study_efficiency
    ]])

    # ===================================
    # SCALE FEATURES
    # ===================================

    scaled_features = scaler.transform(
        features
    )


    # ===================================
    # PREDICTION
    # ===================================

    prediction = model.predict(
        scaled_features
    )[0]

    print("\n====================")
    print("Prediction Class:", prediction)
    print("Probabilities:", model.predict_proba(scaled_features))
    print("====================\n")

    probabilities = model.predict_proba(
        scaled_features
    )

    confidence = np.max(
        probabilities
    ) * 100

    # ===================================
    # LABELS
    # ===================================

    if prediction == 0:

        performance = "Moderate"
        risk_level = "Moderate Risk"

    elif prediction == 1:

        performance = "Excellent"
        risk_level = "Low Risk"

    elif prediction == 2:

        performance = "Poor"
        risk_level = "High Risk"

    # ===================================
    # RECOMMENDATIONS
    # ===================================

    recommendations = give_recommendations(

        study_hours,
        attendance,
        social_media,
        sleep_hours,
        mental_health,
        exercise_frequency,
        diet_quality
    )

    # ===================================
    # SAVE PREDICTION
    # ===================================

    new_prediction = Prediction(

        user_id=current_user.id,

        performance=performance,

        confidence=round(
            confidence,
            2
        ),

        risk_level=risk_level
    )

    db.session.add(
        new_prediction
    )

    db.session.commit()

    # ===================================
    # RESULT PAGE
    # ===================================

    return render_template(

        'result.html',

        performance=performance,

        confidence=round(
            confidence,
            2
        ),

        risk_level=risk_level,

        recommendations=recommendations
    )

# ===================================
# CREATE DATABASE
# ===================================

with app.app_context():

    db.create_all()

# ===================================
# RUN FLASK APP
# ===================================

if __name__ == '__main__':

    app.run(
        debug=True
    )