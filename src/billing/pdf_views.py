import os
from django.http import HttpResponse
from django.template.loader import get_template
try:
    from xhtml2pdf import pisa
except ImportError:
    pisa = None
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response

from .models import Bill

class GenerateBillPDFView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        try:
            bill = Bill.objects.get(pk=pk)
            
            # Ensure user owns the bill
            if not request.user.is_staff and bill.customer.user != request.user:
                 return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        except Bill.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        # Context for template
        context = {"bill": bill}
        
        # Determine template path (we need to create this)
        template_path = "billing/bill_pdf.html"
        
        # Create response
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="bill_{bill.pk}.pdf"'
        
        # Find template
        template = get_template(template_path)
        html = template.render(context)
        
        # Create PDF
        if pisa is None:
            return HttpResponse("PDF generation disabled", status=501)

        pisa_status = pisa.CreatePDF(html, dest=response)
        
        if pisa_status.err:
            return Response({"error": "PDF generation failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        return response
