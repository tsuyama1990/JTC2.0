from enum import StrEnum

class Phase(StrEnum):
    IDEATION = "ideation"
    VERIFICATION = "verification"
    SOLUTION = "solution"
    PMF = "pmf"

class Role(StrEnum):
    NEW_EMPLOYEE = "New Employee"
    FINANCE = "Finance Manager"
    SALES = "Sales Manager"
    CPO = "CPO"
