from flask import Flask, render_template, request
from pyswip import Prolog
import sqlite3
import json

app = Flask(__name__)

prolog = Prolog()
prolog.consult("loan_rules.pl")

LOAN_NAMES = {
    "home": "Home Loan",
    "education": "Education Loan",
    "personal": "Personal Loan",
    "agriculture": "Agriculture Loan"
}


def create_database():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            age INTEGER,
            income REAL,
            employment TEXT,
            credit_score INTEGER,
            debt REAL,
            loan_amount REAL,
            eligibility TEXT,
            risk TEXT
        )
    """)
    # Migrate an older database created by the previous version.
    columns = [row[1] for row in cursor.execute("PRAGMA table_info(applications)").fetchall()]
    if "loan_type" not in columns:
        cursor.execute("ALTER TABLE applications ADD COLUMN loan_type TEXT DEFAULT 'personal'")
    if "loan_details" not in columns:
        cursor.execute("ALTER TABLE applications ADD COLUMN loan_details TEXT DEFAULT '{}'")
    conn.commit()
    conn.close()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/applications")
def applications():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM applications ORDER BY id DESC")
    applications = cursor.fetchall()
    conn.close()
    return render_template("applications.html", applications=applications)


def as_float(name, default=0):
    value = request.form.get(name, "")
    try:
        return float(value) if value != "" else default
    except ValueError:
        return default


def as_int(name, default=0):
    value = request.form.get(name, "")
    try:
        return int(value) if value != "" else default
    except ValueError:
        return default


def prolog_atom(value):
    """Return a safely quoted Prolog atom for values coming from the HTML form."""
    value = str(value)
    value = value.replace('\\', '\\\\').replace("'", "\\'")
    return "'" + value + "'"


@app.route("/check", methods=["POST"])
def check_loan():
    loan_type = request.form.get("loan_type", "personal")
    if loan_type not in LOAN_NAMES:
        loan_type = "personal"

    name = request.form.get("name", "").strip()
    age = as_int("age")
    # Read only the inputs relevant to the selected loan type.
    income = as_float("income")
    employment = request.form.get("employment", "not_applicable") if loan_type == "personal" else "not_applicable"
    credit_score = as_int("credit_score")
    debt = as_float("debt")
    loan_amount = as_float("loan_amount")

    # Loan-specific values. They are optional in the database, but required by
    # the corresponding rule set when that loan type is selected.
    property_value = as_float("property_value")
    down_payment = as_float("down_payment")
    education_level = request.form.get("education_level", "")
    academic_score = as_float("academic_score")
    coapplicant_income = as_float("coapplicant_income")
    course_type = request.form.get("course_type", "")
    land_area = as_float("land_area")
    land_ownership = request.form.get("land_ownership", "")
    agricultural_income = as_float("agricultural_income")
    crop_type = request.form.get("crop_type", "")

    # Use the financially relevant income for risk calculation for each loan.
    if loan_type == "education":
        income = coapplicant_income
        debt = 0
        employment = "student"
    elif loan_type == "agriculture":
        income = agricultural_income
        debt = 0
        employment = "self_employed"

    details = {
        "property_value": property_value,
        "down_payment": down_payment,
        "education_level": education_level,
        "academic_score": academic_score,
        "coapplicant_income": coapplicant_income,
        "course_type": course_type,
        "land_area": land_area,
        "land_ownership": land_ownership,
        "agricultural_income": agricultural_income,
        "crop_type": crop_type
    }

    # Common fields are passed to every loan-specific Prolog rule.
    query = (
        "loan_eligible(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)" % (
            prolog_atom(loan_type), age, income, prolog_atom(employment),
            credit_score, debt, loan_amount, property_value, down_payment,
            prolog_atom(education_level), academic_score, coapplicant_income,
            prolog_atom(course_type), land_area, prolog_atom(land_ownership)
        )
    )

    eligible = list(prolog.query(query))
    eligibility = "Eligible" if eligible else "Not Eligible"

    risk_result = list(prolog.query(
        "risk_level(%s, %s, %s, %s, Risk)" %
        (prolog_atom(loan_type), credit_score, debt, income)
    ))
    risk = str(risk_result[0]["Risk"]) if risk_result else "high"

    reasons = []
    reason_result = prolog.query(
        "reason(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, Reason)" % (
            prolog_atom(loan_type), age, income, prolog_atom(employment),
            credit_score, debt, loan_amount, property_value, down_payment,
            prolog_atom(education_level), academic_score, coapplicant_income,
            prolog_atom(course_type), land_area, prolog_atom(land_ownership)
        )
    )
    for item in reason_result:
        reasons.append(str(item["Reason"]))
    reason_result.close()

    if not eligible:
        # Show ONLY failed criteria for rejected applications; do not mix in
        # successful criteria returned by the Prolog reason/16 rules.
        reasons = []
        # Python-side explanations make the result page easy to understand.
        if loan_type == "home":
            if age < 21 or age > 60: reasons.append("Home loan age range is 21 to 60")
            if income < 30000: reasons.append("Home loan monthly income should be at least ₹30,000")
            if credit_score < 700: reasons.append("Home loan credit score should be at least 700")
            if debt > income * 0.5: reasons.append("Existing debt is too high for the applicant's income")
            if property_value <= 0: reasons.append("Property value is required")
            if down_payment < property_value * 0.20: reasons.append("Down payment should be at least 20% of property value")
        elif loan_type == "education":
            if age < 18 or age > 60: reasons.append("Education loan applicant/co-applicant age should be between 18 and 60")
            if academic_score < 50: reasons.append("Academic score should be at least 50%")
            if coapplicant_income < 20000: reasons.append("Co-applicant monthly income should be at least ₹20,000")
            if credit_score < 650: reasons.append("Credit score should be at least 650")
        elif loan_type == "agriculture":
            if age < 21 or age > 65: reasons.append("Agriculture loan age range is 21 to 65")
            if land_area <= 0: reasons.append("Land area is required")
            if land_ownership != "owned": reasons.append("Applicant should have owned agricultural land for this demo rule")
            if agricultural_income <= 0: reasons.append("Agricultural income is required")
            if credit_score < 600: reasons.append("Credit score should be at least 600")
        else:
            if age < 21 or age > 60: reasons.append("Personal loan age range is 21 to 60")
            if income < 25000: reasons.append("Personal loan monthly income should be at least ₹25,000")
            if employment not in ["salaried", "self_employed"]: reasons.append("Personal loan requires salaried or self-employed employment")
            if credit_score < 650: reasons.append("Personal loan credit score should be at least 650")
            if debt > income * 0.5: reasons.append("Existing debt is too high compared to income")

        # Avoid a blank reason list if an invalid/missing input was submitted.
        if not reasons:
            reasons.append("One or more loan-specific conditions were not satisfied")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO applications
        (name, age, income, employment, credit_score, debt, loan_amount,
         eligibility, risk, loan_type, loan_details)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        name, age, income, employment, credit_score, debt, loan_amount,
        eligibility, risk, loan_type, json.dumps(details)
    ))
    conn.commit()
    conn.close()

    return render_template(
        "result.html", name=name, age=age, income=income,
        employment=employment, credit_score=credit_score, debt=debt,
        loan_amount=loan_amount, eligibility=eligibility, risk=risk,
        reasons=reasons, loan_type=loan_type, loan_type_name=LOAN_NAMES[loan_type],
        details=details
    )


if __name__ == "__main__":
    create_database()
    app.run(debug=False)
