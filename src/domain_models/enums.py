from enum import StrEnum


class EnhancedEnum(StrEnum):
    """Base enum with metadata support."""
    display_name: str
    description: str

    def __new__(cls, value: str, display_name: str, description: str) -> "EnhancedEnum":
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.display_name = display_name
        obj.description = description
        return obj


class Phase(EnhancedEnum):
    IDEATION = ("ideation", "Ideation", "Generating new startup ideas.")
    VERIFICATION = ("verification", "Verification", "Validating the core problem.")
    SOLUTION = ("solution", "Solution", "Designing the MVP.")
    PMF = ("pmf", "Product-Market Fit", "Testing market fit.")
    GOVERNANCE = ("governance", "Governance", "Final review and approval.")


class Role(EnhancedEnum):
    NEW_EMPLOYEE = ("New Employee", "New Employee", "The enthusiastic proposer.")
    FINANCE = ("Finance Manager", "Finance Manager", "The budget guardian.")
    SALES = ("Sales Manager", "Sales Manager", "The market skeptic.")
    CPO = ("CPO", "Chief Product Officer", "The product mentor.")
