from .models import NewUploadMultiple, SponsoredUploadMultiple, AllianceList
from django.contrib.auth.models import User
from itertools import chain
from random import random, randint

def adsmanager(single_query, userinstance):
    pass
    assesment = {
        'sum_one': None,    #Date
        'sum_two': None,    #followers
        'sum_three': None,  #comments
        'sum_four': None,   #likes
        'query_instance': None,   
    }
def ads_to_display(query_set, sponsored_post):
    total_ads = sponsored_post.count()
    l1 = [0,1,2]
    l2 = [0,1,2,3]
    l3 = [0,1,2,3,4]
    level = {
        'level_1': l1,
        'level_2': l2,
        'level_3': l3
    }
    if total_ads == 0:
        return None
    if total_ads == 1:
        return 1
    if total_ads <=2 :
        return random.choice(l1)
    if total_ads <=3:
        return random.choice(l2)
    if total_ads <=4:
        return random.choice(l3)
    if total_ads <=5:
        return random.choice(random.choice(list(level.items())))
    else:
        return (total_ads/random.choice(l3))/2

def display_media(query_set, sponsored_post):
    include_ads = [1,2,3,4]
    random_choice_ads = [0,1,2]
    level = {
        'level_1': 2,
        'level_2': 3,
        'level_3': 4
    }
    r = 0
    ads_list = ads_to_display(query_set, sponsored_post)
    new_query_set = []
    sponsored_post.count()
    if query_set.count() == 0:
        new_query_set = sponsored_post[:1]
        return new_query_set
        
    if query_set.count() <= 10:
        ads_amount = random.choice(random_choice_ads)
        for qs in query_set:
            new_query_set.append(qs.id)
        
    if query_set.count() <= 2:
        add_ads_list = []
        for ads_a in ads_list:
            ads = randint(1,query_set.count())
            while ads in add_ads_list:
                ads = randint(1,query_set.count())
            add_ads_list.append(ads)
        for qs in query_set:
            new_query_set.append(qs.id)
            r += 1
            if r in add_ads_list:
                for qs_sponsor in sponsored_post[:1]:
                    new_query_set.append(qs_sponsor.id)
        return NewUploadMultiple.objects.filter(id__in=new_query_set)

    if query_set.count() <= 4:
        for qs in query_set:
            new_query_set.append(qs.id)
            r += 1
            if r in add_ads_list:
                for qs_sponsor in sponsored_post[:1]:
                    new_query_set.append(qs_sponsor.id)
        return NewUploadMultiple.objects.filter(id__in=new_query_set)

    if query_set.count() <= 8:
        for qs in query_set:
            new_query_set.append(qs.id)
            r += 1
            if r in add_ads_list:
                for qs_sponsor in sponsored_post[:1]:
                    new_query_set.append(qs_sponsor.id)
        return NewUploadMultiple.objects.filter(id__in=new_query_set)

    if query_set.count() <= 12:
        for qs in query_set:
            new_query_set.append(qs.id)
            r += 1
            if r in add_ads_list:
                for qs_sponsor in sponsored_post[:1]:
                    new_query_set.append(qs_sponsor.id)
        return NewUploadMultiple.objects.filter(id__in=new_query_set)

    else:
        new_query_set = query_set | sponsored_post[:2]
        return new_query_set.order_by('-created_by')




