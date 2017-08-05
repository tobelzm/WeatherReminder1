import urllib2, urllib, json, traceback
from collections import defaultdict
from datetime import date, datetime
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import auth
from django.core.mail import EmailMessage
from models import Reminder
from forms import AddReminderForm


def manage(request):
   user_id = None
   if request.user.is_authenticated():
       user_id = request.user.id
   else:
       return HttpResponseRedirect("/admin/login/")
   if request.method == 'POST':
       post_form = AddReminderForm(request.POST)
       if post_form.is_valid():
           zipcode = post_form.cleaned_data['zipcode']
           reminder = post_form.cleaned_data['reminder']
           Reminder.objects.create(user_id=user_id, zipcode=zipcode, warning_event=reminder)
   reminders = Reminder.objects.filter(user_id=user_id)
   form = AddReminderForm()
   return render(request, 'manage.html', {'form': form, 'reminders': reminders, 'logged_in': True})
def del_reminder(request):
   if not request.user.is_authenticated():
       return HttpResponseRedirect("/admin/login/")
   try:
       reminder_id = int(request.GET.get('id', ''))
       p = Reminder.objects.get(id=int(reminder_id))
       p.delete()
   except:
       pass
   return HttpResponseRedirect("/")

def get_weather(zipcode):
   baseurl = "https://query.yahooapis.com/v1/public/yql?"
   yql_query = "select * from weather.forecast where woeid in (select woeid from geo.places(1) where text=\"%s\")" % zipcode
   yql_url = baseurl + urllib.urlencode({'q': yql_query}) + "&format=json"
   result = urllib2.urlopen(yql_url).read()
   data = dict()
   try:
       data = json.loads(result)['query']['results']['channel']
   except:
       print(traceback.format_exc())
   return data

def generate_weather_string(data):
   return "It will be %s in %s on %s. The temperature will be %s to %s %s." % (
       data['item']['forecast'][1]['text'],
       data['location']['city'],
       data['item']['forecast'][1]['date'],
       data['item']['forecast'][1]['low'],
       data['item']['forecast'][1]['high'],
       data['units']['temperature'],
   )

def test_email(request):
   user_id = None
   if request.user.is_authenticated():
       user_id = request.user.id
   else:
       return HttpResponseRedirect("/admin/login/")
   reminders = Reminder.objects.filter(user_id=user_id)
   # De-duplicate zipcode.
   zipcodes = set()
   for reminder in reminders:
       zipcodes.add(reminder.zipcode)
   body = "Dear %s,\n\n" % request.user.username
   for zipcode in zipcodes:
       body += generate_weather_string(get_weather(zipcode)) + "\n"
   body += "\nBest,\nWeather Reminder"
   message = EmailMessage("Email Testing", body, to=[request.user.email])
   message.send()
   return HttpResponseRedirect("/")
