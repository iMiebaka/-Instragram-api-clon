from django.contrib import admin
from .models import BlockedUser, SponsoredUploadMultiple, ImageGalery, LikeImage,NewUploadMultiple, ImageComment, AllianceList, TaggedUser, SavedMedia
# Register your models here.

admin.site.register(LikeImage)
admin.site.register(ImageComment)
admin.site.register(NewUploadMultiple)
admin.site.register(AllianceList)
admin.site.register(TaggedUser)
admin.site.register(SavedMedia)
admin.site.register(BlockedUser)
admin.site.register(ImageGalery)
admin.site.register(SponsoredUploadMultiple)