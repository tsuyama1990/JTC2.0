from enum import StrEnum


class Phase(StrEnum):
    IDEATION = "ideation"
    CPF = "cpf"
    PSF = "psf"
    VALIDATION = "validation"
    OUTPUT = "output"
    GOVERNANCE = "governance"


class Role(StrEnum):
    NEW_EMPLOYEE = "New Employee"
    FINANCE = "Finance Manager"
    SALES = "Sales Manager"
    CPO = "CPO"
    VIRTUAL_CUSTOMER = "Virtual Customer"
    HACKER = "Hacker"
    HIPSTER = "Hipster"
    HUSTLER = "Hustler"
