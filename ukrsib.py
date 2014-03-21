import requests
import re
import datetime
import sys
import configparser
import os

da = sys.argv[len(sys.argv)-1].split('-')
dt2 = datetime.date(int(da[0]),int(da[1]),int(da[2]))
dt1 = dt2 + datetime.timedelta(days=0)
dts1 = dt1.strftime("%d.%m.%Y")
dts2 = dt2.strftime("%d.%m.%Y")

cfg = configparser.RawConfigParser()
cfg.read(os.path.expanduser('~/secured/myukrsib.cfg'))

un = cfg.get('default','personal_num')
ps = cfg.get('default','secret')

pss = [int(s) for s in ps]

s = requests.Session()
r = s.get('https://secure.my.ukrsibbank.com/web_banking/protected/welcome.jsf')
m = re.search("var digitsArray = new Array\('([0-9]+)','([0-9]+)','([0-9]+)','([0-9]+)','([0-9]+)','([0-9]+)','([0-9]+)','([0-9]+)','([0-9]+)','([0-9]+)'\);", r.text)

ds = list(m.groups())

str = ''

for d in pss:
  str += ds[d-1] + '_'

pwd = '******'
pl = {'j_username':un, 'fake_password':pwd, 'j_password':str}

r2 = s.post('https://secure.my.ukrsibbank.com/web_banking/j_security_check', data=pl)

m2 = re.search('<input type="hidden" name="javax.faces.ViewState" id="javax.faces.ViewState" value="(.+)"', r2.text)

#print(r2.text)

mjid = re.search('(j_id_jsp_[0-9]+_)', r2.text)

wfjid = mjid.group(1)

maccid = re.search("\[\['accountId','(.+)'\]\]", r2.text)
accid = maccid.group(1)
pl2 = {'accountId':accid, 'javax.faces.ViewState':m2.group(1),'welcomeForm:_idcl':'welcomeForm:'+wfjid+'53:0:'+wfjid+'59','welcomeForm_SUBMIT':'1'}
r3 = s.post('https://secure.my.ukrsibbank.com/web_banking/protected/welcome.jsf',data=pl2)

#print(r3.text)

mjid = re.search('(j_id_jsp_[0-9]+_)', r3.text)

wfjid = mjid.group(1)
m3 = re.search('<input type="hidden" name="javax.faces.ViewState" id="javax.faces.ViewState" value="(.+)"', r3.text)
#'6577430',
pl3 = {'cardAccountInfoForm:reportPeriod':'0', 'accountId':accid,'cardAccountInfoForm_SUBMIT':'1', 'javax.faces.ViewState':m3.group(1),'cardAccountInfoForm:'+wfjid+'45':'OK','cardAccountInfoForm:'+wfjid+'40':dts1,'cardAccountInfoForm:'+wfjid+'42':dts2}

s.headers.update({'Referer':'https://secure.my.ukrsibbank.com/web_banking/protected/welcome.jsf'})
r4 = s.post('https://secure.my.ukrsibbank.com/web_banking/protected/reports/sap_card_account_info.jsf',data=pl3)

print(r4.text)

#print(m.group(0))
#print(m.groups())
#print(r.headers)
#print(r4.headers)
#print(r4.request.headers)
#print(pl3)
