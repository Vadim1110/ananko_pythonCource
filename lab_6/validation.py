import re

class ValidationError(Exception):
    pass

def validate_user_full_name(user_full_name):
    if not user_full_name or not isinstance(user_full_name, str):
        raise ValidationError("User full name must be a non-empty string.")
    parts = user_full_name.strip().split()
    if len(parts) != 2:
        raise ValidationError("User full name must contain exactly 2 parts (name and surname).")
    return parts[0], parts[1]

def validate_strict_field(value, field_name, allowed_values):
    if value is None:
        return
    if value not in allowed_values:
        raise ValidationError(f"{field_name} must be one of {allowed_values}, got '{value}'.")

def validate_account_number(account_number):
    if not isinstance(account_number, str):
        raise ValidationError("Account number must be a string.")
    if not re.match(r'^[A-Za-z0-9]{8,12}$', account_number):
        raise ValidationError("Account number must be 8-12 alphanumeric characters.")
    return account_number
