# This file imports all models so that:
#
# 1. Alembic can discover them for auto-generating migrations
#    (alembic/env.py imports app.models, which runs this file)
#
# 2. SQLAlchemy knows about all relationships between models
#    (BankAccount.transactions relationship needs Transaction to be imported)
#
# RULE: Every new model you create MUST be added here.

from app.models.auth_user import AuthUser
from app.models.bank_account import BankAccount
from app.models.transaction import Transaction

__all__ = [
    "AuthUser",
    "BankAccount",
    "Transaction",
]