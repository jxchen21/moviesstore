from django.contrib import admin
from .models import Movie, Review, MovieRequest, MoviePetition, PetitionVote

class MovieAdmin(admin.ModelAdmin):
    ordering = ['name']
    search_fields = ['name']
admin.site.register(Movie, MovieAdmin)
admin.site.register(Review)

class MovieRequestAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'date']
    list_filter = ['date']
    search_fields = ['name', 'user__username']
    ordering = ['-date']
admin.site.register(MovieRequest, MovieRequestAdmin)

class PetitionVoteInline(admin.TabularInline):
    model = PetitionVote
    extra = 0
    readonly_fields = ['created_at']

class MoviePetitionAdmin(admin.ModelAdmin):
    list_display = ['title', 'movie_title', 'creator', 'upvotes', 'downvotes', 'net_votes', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'created_at', 'movie_year']
    search_fields = ['title', 'movie_title', 'movie_director', 'creator__username']
    ordering = ['-created_at']
    inlines = [PetitionVoteInline]
    readonly_fields = ['upvotes', 'downvotes', 'created_at', 'updated_at']

    def net_votes(self, obj):
        return obj.net_votes
    net_votes.short_description = 'Net Votes'
    net_votes.admin_order_field = 'upvotes'

admin.site.register(MoviePetition, MoviePetitionAdmin)

class PetitionVoteAdmin(admin.ModelAdmin):
    list_display = ['user', 'petition', 'vote_type', 'created_at']
    list_filter = ['vote_type', 'created_at']
    search_fields = ['user__username', 'petition__title']
    ordering = ['-created_at']
admin.site.register(PetitionVote, PetitionVoteAdmin)