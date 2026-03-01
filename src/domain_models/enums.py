from enum import StrEnum


class Phase(StrEnum):
    IDEATION = "ideation"
    VERIFICATION = "verification"
    SOLUTION = "solution"
    PMF = "pmf"
    GOVERNANCE = "governance"


class Role(StrEnum):
    NEW_EMPLOYEE = "New Employee"
    FINANCE = "Finance Manager"
    SALES = "Sales Manager"
    CPO = "CPO"
