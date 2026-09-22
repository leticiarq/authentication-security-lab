from decimal import Decimal

from django.db.models import Sum

from .models import FinancialAccount, Transaction


def dashboard_summary(user):
    membership = user.memberships.select_related("organization").first()
    if not membership:
        return {
            "membership": None,
            "organization": None,
            "balance": Decimal("0"),
            "income": Decimal("0"),
            "expenses": Decimal("0"),
            "recent_transactions": [],
        }
    organization = membership.organization
    accounts = FinancialAccount.objects.filter(organization=organization)
    transactions = Transaction.objects.filter(account__organization=organization)
    income = (
        transactions.filter(direction=Transaction.Direction.INCOME).aggregate(total=Sum("amount"))[
            "total"
        ]
        or Decimal("0")
    )
    expenses = (
        transactions.filter(direction=Transaction.Direction.EXPENSE).aggregate(total=Sum("amount"))[
            "total"
        ]
        or Decimal("0")
    )
    return {
        "membership": membership,
        "organization": organization,
        "balance": accounts.aggregate(total=Sum("balance"))["total"] or Decimal("0"),
        "income": income,
        "expenses": expenses,
        "recent_transactions": transactions.select_related("account")[:5],
    }
