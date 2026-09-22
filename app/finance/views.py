from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_POST
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import dashboard_summary


@login_required
def notifications(request):
    return render(
        request,
        "finance/notifications.html",
        {"notifications": request.user.notifications.all()},
    )


@require_POST
@login_required
def mark_notifications_read(request):
    request.user.notifications.filter(read_at__isnull=True).update(read_at=timezone.now())
    return render(
        request,
        "finance/notifications.html",
        {"notifications": request.user.notifications.all()},
    )


class DashboardSummaryAPI(APIView):
    def get(self, request):
        summary = dashboard_summary(request.user)
        return Response(
            {
                "organization": summary["organization"].name if summary["organization"] else None,
                "balance": f"{summary['balance']:.2f}",
                "income": f"{summary['income']:.2f}",
                "expenses": f"{summary['expenses']:.2f}",
            }
        )
