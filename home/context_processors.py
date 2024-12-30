from .models import Service, SubService

def services_and_subservices(request):
    services = Service.objects.all().prefetch_related('subservices')
    return {
        'services': services
    }
