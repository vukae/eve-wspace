from models import WhitelistEntry
from django.contrib.auth.models import User, Group
from celery import task
from API import cache_handler as handler
import eveapi
import csv


@task()
def validate_users():
    """
    Validates all users who do not have the whitelist_exempt permission
    against the entries in the whitelistentry model and that all members
    are in the Ivy League alliance.
    """
    general_group = Group.objects.get(name="E-UNI")
    camper_group = Group.objects.get(name="Campers")
    alliance_name = u"Ivy League"
    api = eveapi.EVEAPIConnection(cacheHandler=handler)
    for user in User.objects.filter(is_active=True).all():
        if not user.is_superuser or not user.has_perm('member_whitelist.whitelist_exempt'):
            if WhitelistEntry.objects.filter(entry=user.username).count():
                if not camper_group in user.groups.all():
                    user.groups.add(camper_group)
                    user.save()
            else:
            	print("User: " + user.username + " not found in Whitelist")
                if camper_group in user.groups.all():
                    user.groups.remove(camper_group)
                    user.save()
            try:
                charid = api.eve.CharacterID(names=user.username).characters[0].characterID
                if api.eve.CharacterInfo(characterID=charid).alliance != alliance_name:
                    user.is_active = False
                    #user.set_unusable_password()
                    user.groups = []
                    user.save()
                    
                    print("User '" + user.username + "' account was de-activated, because he is no longuer in IVY League.")
            except AttributeError:
                print("User " + user.username + "account was de-activated, because he does not exist or is not in an alliance.")
                user.is_active = False
                user.groups = []
                user.save()
            except:
                print("API Exception, doing nothing")
                pass
                
            
   

def update_whitelist():
    csvfile = open('/home/evewspace/eve-wspace/evewspace/whitelist.csv', 'r')
    
    reader = csv.reader(csvfile, delimiter='\t')
    whitelist = []
    for line in reader:
        whitelist.append(line[0])
    
    for entry in WhitelistEntry.objects.all():
        if entry.entry not in whitelist:
            entry.delete()
    
    for member in whitelist:
        if not WhitelistEntry.objects.filter(entry=member).count():
            WhitelistEntry(entry=member).save()
