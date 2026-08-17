"""CKA Exam Prep Learning Platform - backend application package."""

__version__ = "1.0.0"

# The demo accounts required by the spec live on `demo.local`, and
# email-validator rejects RFC 6762 special-use domains by default. Allowing
# `.local` keeps EmailStr validation everywhere else intact while letting the
# seeded demo logins work out of the box.
import email_validator as _email_validator

_email_validator.SPECIAL_USE_DOMAIN_NAMES = [
    name for name in _email_validator.SPECIAL_USE_DOMAIN_NAMES if name != "local"
]
