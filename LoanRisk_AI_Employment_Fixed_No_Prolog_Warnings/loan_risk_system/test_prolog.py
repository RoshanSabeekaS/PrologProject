from pyswip import Prolog

prolog = Prolog()
prolog.consult("loan_rules.pl")

# Test the current 15-argument loan_eligible/15 predicate.
result = list(prolog.query(
    "loan_eligible('agriculture', 21, 60000.0, 'salaried', 650, 10000.0, 500000.0, 0, 0, '', 0, 0, '', 5.0, 'owned')"
))

print("Loan Eligibility:", result)

risk_result = list(
    prolog.query(
        "risk_level('agriculture', 650, 10000.0, 60000.0, Risk)"
    )
)

print("Risk Result:", risk_result)
