from .models import StatusMedia
from django.utils import timezone

def my_scheduled_job():
    print('Hello World')

def delete_status():
    queryset = StatusMedia.objects.all()
    for qs in  queryset:
        date_check = qs.created_on - timedelta(days=1) 
        remove_media = timezone.now() > date_check
        if remove_media:
            queryset = StatusMedia.objects.get(id=qs.id)
            queryset.visibility = False
            queryset.save()

