% ================================================================
% LOAN ELIGIBILITY & RISK ASSESSMENT SYSTEM
% Four loan types: home, education, personal, agriculture
% These are project/demo rules, not official bank lending criteria.
% ================================================================

% ---------- COMMON ELIGIBILITY HELPERS ----------
age_ok(Age) :- Age >= 21, Age =< 60.
edu_age_ok(Age) :- Age >= 18, Age =< 60.
agri_age_ok(Age) :- Age >= 21, Age =< 65.

% ---------- PERSONAL LOAN ----------
loan_eligible(personal, Age, Income, Employment, Score, Debt, _Loan,
              _, _, _, _, _, _, _, _) :-
    age_ok(Age), Income >= 25000,
    employment_eligible(Employment), Score >= 650,
    Debt =< Income * 0.5.

% ---------- HOME LOAN ----------
loan_eligible(home, Age, Income, _Employment, Score, Debt, _Loan,
              Property, Down, _, _, _, _, _, _) :-
    age_ok(Age), Income >= 30000, Score >= 700,
    Debt =< Income * 0.5, Property > 0,
    Down >= Property * 0.20.

% ---------- EDUCATION LOAN ----------
loan_eligible(education, Age, _Income, _Employment, Score, _Debt, _Loan,
              _, _, _, Academic, CoIncome, _, _, _) :-
    edu_age_ok(Age), Academic >= 50, CoIncome >= 20000,
    Score >= 650.

% ---------- AGRICULTURE LOAN ----------
loan_eligible(agriculture, Age, Income, _Employment, Score, _Debt, _Loan,
              _, _, _, _, _, _, LandArea, Ownership) :-
    agri_age_ok(Age), Score >= 600, Income > 0,
    LandArea > 0, Ownership = owned.

employment_eligible(salaried).
employment_eligible(self_employed).

% ---------- RISK: LOAN-TYPE AWARE ----------
risk_level(home, Score, Debt, Income, low) :- Score >= 750, Debt =< Income * 0.30.
risk_level(home, Score, Debt, Income, medium) :- Score >= 700, Score < 750, Debt =< Income * 0.50.
risk_level(home, Score, _, _, high) :- Score < 700.
risk_level(home, _, Debt, Income, high) :- Debt > Income * 0.50.

risk_level(education, Score, Debt, Income, low) :- Score >= 750, Debt =< Income * 0.40.
risk_level(education, Score, Debt, Income, medium) :- Score >= 650, Score < 750, Debt =< Income * 0.50.
risk_level(education, Score, _, _, high) :- Score < 650.
risk_level(education, _, Debt, Income, high) :- Debt > Income * 0.50.

risk_level(personal, Score, Debt, Income, low) :- Score >= 750, Debt =< Income * 0.30.
risk_level(personal, Score, Debt, Income, medium) :- Score >= 650, Score < 750, Debt =< Income * 0.50.
risk_level(personal, Score, _, _, high) :- Score < 650.
risk_level(personal, _, Debt, Income, high) :- Debt > Income * 0.50.

risk_level(agriculture, Score, Debt, Income, low) :- Score >= 750, Debt =< Income * 0.40.
risk_level(agriculture, Score, Debt, Income, medium) :- Score >= 600, Score < 750, Debt =< Income * 0.50.
risk_level(agriculture, Score, _, _, high) :- Score < 600.
risk_level(agriculture, _, Debt, Income, high) :- Debt > Income * 0.50.

% ---------- REASONS: COMMON + LOAN-SPECIFIC ----------
reason(personal, Age, _, _, _, _, _, _, _, _, _, _, _, _, _, 'Age is within the personal loan range') :- age_ok(Age).
reason(personal, _, Income, _, _, _, _, _, _, _, _, _, _, _, _, 'Income meets the personal loan minimum') :- Income >= 25000.
reason(personal, _, _, Employment, _, _, _, _, _, _, _, _, _, _, _, 'Employment type is acceptable for a personal loan') :- employment_eligible(Employment).
reason(personal, _, _, _, Score, _, _, _, _, _, _, _, _, _, _, 'Credit score meets the personal loan requirement') :- Score >= 650.
reason(personal, _, Income, _, _, Debt, _, _, _, _, _, _, _, _, _, 'Existing debt is within the personal loan limit') :- Debt =< Income * 0.5.

reason(home, Age, _, _, _, _, _, _, _, _, _, _, _, _, _, 'Age is within the home loan range') :- age_ok(Age).
reason(home, _, Income, _, _, _, _, _, _, _, _, _, _, _, _, 'Income meets the home loan minimum') :- Income >= 30000.
reason(home, _, _, _, Score, _, _, _, _, _, _, _, _, _, _, 'Credit score meets the home loan requirement') :- Score >= 700.
reason(home, _, Income, _, _, Debt, _, _, _, _, _, _, _, _, _, 'Existing debt is within the home loan limit') :- Debt =< Income * 0.5.
reason(home, _, _, _, _, _, _, Property, Down, _, _, _, _, _, _, 'Down payment meets the 20% property requirement') :- Property > 0, Down >= Property * 0.20.

reason(education, Age, _, _, _, _, _, _, _, _, _, _, _, _, _, 'Applicant age is within the education loan range') :- edu_age_ok(Age).
reason(education, _, _, _, _, _, _, _, _, _, Academic, _, _, _, _, 'Academic score meets the minimum requirement') :- Academic >= 50.
reason(education, _, _, _, _, _, _, _, _, _, _, CoIncome, _, _, _, 'Co-applicant income meets the minimum requirement') :- CoIncome >= 20000.
reason(education, _, _, _, Score, _, _, _, _, _, _, _, _, _, _, 'Credit score meets the education loan requirement') :- Score >= 650.

reason(agriculture, Age, _, _, _, _, _, _, _, _, _, _, _, _, _, 'Age is within the agriculture loan range') :- agri_age_ok(Age).
reason(agriculture, _, _, _, Score, _, _, _, _, _, _, _, _, _, _, 'Credit score meets the agriculture loan requirement') :- Score >= 600.
reason(agriculture, _, Income, _, _, _, _, _, _, _, _, _, _, _, _, 'Agricultural income is provided') :- Income > 0.
reason(agriculture, _, _, _, _, _, _, _, _, _, _, _, _, LandArea, _, 'Agricultural land area is provided') :- LandArea > 0.
reason(agriculture, _, _, _, _, _, _, _, _, _, _, _, _, _, Ownership, 'Land ownership requirement is satisfied') :- Ownership = owned.
