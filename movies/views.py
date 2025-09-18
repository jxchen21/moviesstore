from django.shortcuts import render, redirect, get_object_or_404
from .models import Movie, Review, MovieRequest, MoviePetition, PetitionVote
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
# Create your views here.
movies = []
def index(request):
    search_term = request.GET.get('search')
    if search_term:
        movies = Movie.objects.filter(name__icontains=search_term)
    else:
        movies = Movie.objects.all()
    template_data = {}
    template_data['title'] = 'Movies'
    template_data['movies'] = movies
    return render(request, 'movies/index.html',
                  {'template_data': template_data})
def show(request, id):
    movie = Movie.objects.get(id=id)
    reviews = Review.objects.filter(movie=movie)
    template_data = {}
    template_data['title'] = movie.name
    template_data['movie'] = movie
    template_data['reviews'] = reviews
    return render(request, 'movies/show.html',
                  {'template_data': template_data})
@login_required
def create_review(request, id):
    if request.method == 'POST' and request.POST['comment'] != '':
        movie = Movie.objects.get(id=id)
        review = Review()
        review.comment = request.POST['comment']
        review.movie = movie
        review.user = request.user
        review.save()
        return redirect('movies.show', id=id)
    else:
        return redirect('movies.show', id=id)
@login_required
def edit_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id)
    if request.user != review.user:
        return redirect('movies.show', id=id)
    if request.method == 'GET':
        template_data = {}
        template_data['title'] = 'Edit Review'
        template_data['review'] = review
        return render(request, 'movies/edit_review.html',
            {'template_data': template_data})
    elif request.method == 'POST' and request.POST['comment'] != '':
        review = Review.objects.get(id=review_id)
        review.comment = request.POST['comment']
        review.save()
        return redirect('movies.show', id=id)
    else:
        return redirect('movies.show', id=id)
@login_required
def delete_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id,
        user=request.user)
    review.delete()
    return redirect('movies.show', id=id)

@login_required
def movie_requests(request):
    template_data = {}
    template_data['title'] = 'Movie Requests'

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()

        if name and description:
            movie_request = MovieRequest()
            movie_request.name = name
            movie_request.description = description
            movie_request.user = request.user
            movie_request.save()
            return redirect('movies.movie_requests')
        else:
            template_data['error'] = 'Both movie name and description are required.'

    template_data['movie_requests'] = MovieRequest.objects.filter(user=request.user).order_by('-date')
    return render(request, 'movies/movie_requests.html', {'template_data': template_data})

@login_required
def delete_movie_request(request, request_id):
    movie_request = get_object_or_404(MovieRequest, id=request_id, user=request.user)
    movie_request.delete()
    return redirect('movies.movie_requests')

# Petition views
def petition_list(request):
    template_data = {}
    template_data['title'] = 'Movie Petitions'

    # Get sorting parameter
    sort_by = request.GET.get('sort', 'newest')

    petitions = MoviePetition.objects.all()

    if sort_by == 'popular':
        petitions = petitions.order_by('-upvotes', '-created_at')
    elif sort_by == 'controversial':
        petitions = petitions.order_by('-downvotes', '-created_at')
    else:  # newest
        petitions = petitions.order_by('-created_at')

    # Add user vote information for each petition
    if request.user.is_authenticated:
        user_votes = PetitionVote.objects.filter(user=request.user, petition__in=petitions)
        user_vote_dict = {vote.petition_id: vote.vote_type for vote in user_votes}

        for petition in petitions:
            petition.user_vote = user_vote_dict.get(petition.id)
    else:
        for petition in petitions:
            petition.user_vote = None

    template_data['petitions'] = petitions
    template_data['sort_by'] = sort_by

    return render(request, 'movies/petition_list.html', {'template_data': template_data})

@login_required
def create_petition(request):
    template_data = {}
    template_data['title'] = 'Create Movie Petition'

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        movie_title = request.POST.get('movie_title', '').strip()
        movie_year = request.POST.get('movie_year', '').strip()
        movie_director = request.POST.get('movie_director', '').strip()

        if title and description and movie_title:
            petition = MoviePetition()
            petition.title = title
            petition.description = description
            petition.movie_title = movie_title
            petition.creator = request.user

            if movie_year:
                try:
                    petition.movie_year = int(movie_year)
                except ValueError:
                    template_data['error'] = 'Please enter a valid year.'
                    return render(request, 'movies/create_petition.html', {'template_data': template_data})

            if movie_director:
                petition.movie_director = movie_director

            petition.save()
            messages.success(request, 'Petition created successfully!')
            return redirect('movies.petition_list')
        else:
            template_data['error'] = 'Title, description, and movie title are required.'

    return render(request, 'movies/create_petition.html', {'template_data': template_data})

@login_required
def vote_petition(request, petition_id):
    if request.method == 'POST':
        petition = get_object_or_404(MoviePetition, id=petition_id)
        vote_type = request.POST.get('vote_type')

        if vote_type not in ['up', 'down']:
            return JsonResponse({'error': 'Invalid vote type'}, status=400)

        # Check if user already voted
        existing_vote = PetitionVote.objects.filter(petition=petition, user=request.user).first()

        if existing_vote:
            # User already voted, update their vote
            if existing_vote.vote_type == vote_type:
                # Same vote, remove it
                existing_vote.delete()
                if vote_type == 'up':
                    petition.upvotes = max(0, petition.upvotes - 1)
                else:
                    petition.downvotes = max(0, petition.downvotes - 1)
            else:
                # Different vote, update it
                old_vote_type = existing_vote.vote_type
                existing_vote.vote_type = vote_type
                existing_vote.save()

                # Update petition counts
                if old_vote_type == 'up':
                    petition.upvotes = max(0, petition.upvotes - 1)
                    petition.downvotes += 1
                else:
                    petition.downvotes = max(0, petition.downvotes - 1)
                    petition.upvotes += 1
        else:
            # New vote
            PetitionVote.objects.create(
                petition=petition,
                user=request.user,
                vote_type=vote_type
            )

            if vote_type == 'up':
                petition.upvotes += 1
            else:
                petition.downvotes += 1

        petition.save()

        return JsonResponse({
            'success': True,
            'upvotes': petition.upvotes,
            'downvotes': petition.downvotes,
            'net_votes': petition.net_votes
        })

    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def petition_detail(request, petition_id):
    petition = get_object_or_404(MoviePetition, id=petition_id)

    # Check if user has voted
    user_vote = None
    if request.user.is_authenticated:
        try:
            user_vote = PetitionVote.objects.get(petition=petition, user=request.user)
        except PetitionVote.DoesNotExist:
            pass

    template_data = {
        'title': petition.title,
        'petition': petition,
        'user_vote': user_vote
    }

    return render(request, 'movies/petition_detail.html', {'template_data': template_data})