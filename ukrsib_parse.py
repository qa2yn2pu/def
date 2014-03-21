from pyquery import PyQuery
import sys
import sqlite3
import re
import configparser
import os
import smtplib
from email.mime.text import MIMEText

batch_mode = False
if '-b' in sys.argv:
    batch_mode = True

cfg=configparser.RawConfigParser()
cfg.read(os.path.expanduser('~/secured/myukrsib.cfg'))
smtp_host = cfg.get('default','smtp_host')
smtp_user = cfg.get('default','smtp_user')
smtp_secret = cfg.get('default','smtp_secret')



#fname = sys.argv[len(sys.argv)-1]
#f = open(fname,'rb')
q = PyQuery(sys.stdin.read())

tbls = PyQuery(q('form#cardAccountInfoForm').children('table'))
t = tbls.eq(0)('td').eq(1).text().split(':')
available_amount = t[2]
global_own_amount = t[1].split()[0]
t = tbls.eq(2)('td').eq(0).text().split(':')
overdraft = t[1]
t = tbls.eq(2)('td').eq(1).text().split(':')
replenishment = t[1]
t = tbls.eq(2)('td').eq(4).text().split(':')
own_amount = t[1]
t = tbls.eq(2)('td').eq(5).text().split(':')
withdrawal = t[1]

account_ops = []
card_ops = []
holds = []

def parse_row(idx, node):
    row = []
    PyQuery(node)('td').each(lambda i: row.append(PyQuery(this).text()))
    return(row)

jid = re.search('(j_id_jsp_[0-9]+_)', q.html()).group(1)

q('cardAccountInfoForm\\:'+jid+'106\\:tbody_element tr').each(lambda i,n: account_ops.append(parse_row(i,n)))
q("tbody#cardAccountInfoForm\\:"+jid+"133\\:0\\:"+jid+"136\\:tbody_element tr").each(lambda i,n: card_ops.append(parse_row(i,n)))
q("tbody#cardAccountInfoForm\\:"+jid+"172\\:0\\:"+jid+"175\\:tbody_element tr").each(lambda i,n: holds.append(parse_row(i,n)))

#print("account_ope")
#print(account_ops)
#print("card_ope")
#print(card_ops)
#print("holds")
#print(holds)
#print(q('table.opersTable'))


conn = sqlite3.connect(os.path.expanduser("~/secured/sc.db"))

c = conn.cursor()

c.execute("CREATE TABLE IF NOT EXISTS operation (auth_code text, op_date text NOT NULL, calc_date text, description text, currency text, currency_amount text, amount text);")
c.execute("CREATE TABLE IF NOT EXISTS snapshot (ts text, overdraft text, own_amount text, available_amount text, replenishment text, withdrawal text)")

def handle_account_ops(c, ops):
    sops = []
    for op in ops:
        c.execute("SELECT op_date,calc_date,description,currency,currency_amount,amount FROM operation WHERE auth_code IS NULL AND op_date=? AND calc_date=? AND description=? AND currency=? AND currency_amount=? AND amount=? LIMIT 1", op)
        row = c.fetchone()
        if row:
            sops.append(list(row))
    nops = [ i for i in ops if not i in sops or sops.remove(i)]
    if len(nops) > 0:
#        print("new ops:")
        print(nops)
        c.executemany("INSERT INTO operation (op_date,calc_date,description,currency,currency_amount,amount) VALUES(?,?,?,?,?,?)",nops)
        return nops
    return []

def handle_card_ops(c, ops):
    sops = []
    for op in ops:
        c.execute("SELECT op_date,calc_date,auth_code,description,currency,currency_amount,amount FROM operation WHERE op_date=? AND calc_date=? AND auth_code=? AND description=? AND currency=? AND currency_amount=? AND amount=? LIMIT 1", op)
        row = c.fetchone()
        if row:
            sops.append(list(row))
    nops = [ i for i in ops if not i in sops or sops.remove(i)]
    if len(nops) > 0:
#        print("new ops:")
        print(nops)
        c.executemany("INSERT INTO operation (op_date,calc_date,auth_code,description,currency,currency_amount,amount) VALUES(?,?,?,?,?,?,?)",nops)
        return nops
    return []

def handle_holds(c, ops):
    sops = []
    for op in ops:
        c.execute("SELECT auth_code,op_date,description,currency,currency_amount,amount FROM operation WHERE auth_code=? AND op_date=? AND description=? AND currency=? AND currency_amount=? AND amount=? LIMIT 1", op)
        row = c.fetchone()
        print(row)
        if row:
            sops.append(list(row))
    nops = [ i for i in ops if not i in sops or sops.remove(i)]
    if len(nops) > 0:
#        print("new ops:")
        print(nops)
        c.executemany("INSERT INTO operation (auth_code,op_date,description,currency,currency_amount,amount) VALUES(?,?,?,?,?,?)", nops)
        return nops
    return []

newao = handle_account_ops(c, account_ops)
newco = handle_card_ops(c, card_ops)
newh = handle_holds(c, holds)

conn.commit()
conn.close()

msg = ''

if len(newao) > 0:
    msg += str(newao)
    msg += '\n'

if len(newco) > 0:
    msg += str(newco)
    msg += '\n'

if len(newh) > 0:
    msg += str(newh)
    msg += '\n'
print (msg)
if len(msg) > 0:
    smtp = smtplib.SMTP(smtp_host,587)
    smtp.set_debuglevel(1)
    smtp.ehlo()
    smtp.starttls()
    smtp.login(smtp_user, smtp_secret)
    msg = MIMEText(msg.encode('utf-8'),'plain','utf-8')
    msg['Subject'] = 'Ukrsib notification'
    msg['From'] = smtp_user
    msg['To'] = smtp_user
    smtp.sendmail(smtp_user, smtp_user, str(msg))
    smtp.quit()
