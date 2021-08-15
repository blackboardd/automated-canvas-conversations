from crontab import CronTab
from colored import fg
import argparse
import requests
import inquirer
import datetime
import sqlite3
import base64
import glob
import json
import sys
import os
import re

parser = argparse.ArgumentParser(description="Work with Canvas conversations.")
parser.add_argument("selection", choices=["send", "add", "list", "remove", "schedule", "sched", "run", "token"])
parser.add_argument("-t", "--type", choices=["job"])
parser.add_argument("--msgs", nargs="+")
parser.add_argument("--ids", nargs="+")
args = parser.parse_args()

con = sqlite3.connect('acc.db')
cur = con.cursor()

cronroot = CronTab(user="root")

try:
    token = os.environ["CANVAS_HEADER_AUTH_TOKEN"]
except KeyError:
    print(
"""Missing Canvas token. use %s$ env CANVAS_HEADER_AUTH_TOKEN=[YOUR TOKEN]%s

Don't know where your token is? Follow this guide to get it:
Student: https://community.canvaslms.com/t5/Student-Guide/How-do-I-manage-API-access-tokens-as-a-student/ta-p/273
Admin:   https://community.canvaslms.com/t5/Admin-Guide/How-do-I-manage-API-access-tokens-as-an-admin/ta-p/89""" \
                     % (fg("yellow"), fg("white")))
    exit()

baseURL = "https://canvas.instructure.com"
conversationsURL ="api/v1/conversations"
reqURL = baseURL + "/" + conversationsURL

headers = {"Authorization": token}

def send(shouldPost=True):
    folders = glob.glob("./*.txt")
    returnTuple = []
    
    if (not folders):
        print("No .txt files in current directory.")
        return;

    msgPrompt = [
        inquirer.List("Messages",
                      message="Select a file that contains your message (enter to continue)",
                      choices=folders),
    ]

    try:
        msg = inquirer.prompt(msgPrompt)["Messages"]
    except TypeError:
        exit()

    cur.execute("SELECT * FROM ids")
    ids = cur.fetchall()
    lams = []

    for id in ids:
        lams.append(get_lam_by_id(id))
    
    if (ids):
        idPrompt = [
            inquirer.Checkbox('Conversations',
                              message="Select threads to send your message to (use spacebar to select)",
                              choices=list(zip(["{}: {}".format(id[0], lam) for id,lam in zip(ids, lams)], ids))),
        ]

        try:
            selectedIDs = inquirer.prompt(idPrompt)["Conversations"]
        except TypeError:
            exit()

        if (selectedIDs):
            for id in selectedIDs:
                if (shouldPost):
                    url = reqURL + "/{}/add_message?body={}".format(id[0], (open(msg)).read())
                    post(url, color="magenta", to=id[0], using=msg)
                returnTuple.append((msg, id[0]))
        else:
            print("None selected.")
    else:
        print("No IDs in database.")

    return returnTuple

def add(sched=False):
    url = reqURL + "?scope=sent"
    sc = requests.get(url, headers=headers).json()
    id = []
    lam = []

    for c in sc:
        idAppend = str(c["id"])
        lamAppend = c["context_name"].strip() + ": " + c["last_authored_message"][0:25] \
            .replace("\n", " ") \
            .strip() + "..."

        id.append(idAppend)
        lam.append(lamAppend)

    conversations = list(zip(id, lam))

    if (conversations):
        idPrompt = [
            inquirer.Checkbox("Conversations",
                              message="Select threads to send a message to (use spacebar to select)",
                              choices=list(zip(lam, conversations))),
        ]
        try:
            selectedIDs = inquirer.prompt(idPrompt)["Conversations"]
        except TypeError:
            exit()

        if (selectedIDs and not sched):
            for id in selectedIDs:
                try:
                    cur.execute("INSERT INTO ids (id) VALUES (?)", (id[0],))
                    print("%sAdded %s{}%s with %s{}".format(id[0], id[1]) % (fg("white"), fg("cyan"), fg("white"), fg("cyan")))
                except sqlite3.IntegrityError:
                    print("%sIntegrity Error. %sA duplicate ID was found; cannot add %s{}%s with %s{}".format(id[0], id[1]) % (fg("red"), fg("white"), fg("cyan"), fg("white"), fg("cyan"))) 
        elif (not sched):
            print("None selected.")

    else:
        print("No existing sent conversations.")

def myList():
    if (args.type == "job"):
        cur.execute("SELECT * FROM cron")
        crons = cur.fetchall()

        if (crons):
            print("Columns in cron:")
            for cron in crons:
                print(cron)
        else:
            print("No jobs in database.")
        return

    cur.execute("SELECT * FROM ids")
    ids = cur.fetchall()

    if (ids):
        print("Columns in IDs")
        for id in ids:
            print(id)
    else:
        print("No IDs in database.")

def remove():
    if (args.type == "job"):
        cur.execute("SELECT * FROM cron")
        b64crons = cur.fetchall()
        crons = {}
        
        for cron in b64crons:
            b64cron = cron[0].encode("ascii")
            b64cron = base64.b64decode(b64cron)
            b64cron = b64cron.decode("ascii")
            
            crons[b64cron] = cron[0]
        
        if (crons):
            cronPrompt = [
                inquirer.Checkbox('Cron jobs',
                                  message="Select a job to remove (use spacebar to select)",
                                  choices=crons),
            ]
            try:
                cronSelections = inquirer.prompt(cronPrompt)["Cron jobs"]
            except TypeError:
                exit()

            if (cronSelections):
                for cron in cronSelections:
                    cur.execute("DELETE FROM cron WHERE cronline = ?", (crons[cron],))
                    for job in cronroot:
                        if (str(job) == str(cron)):
                            cronroot.remove(job)
                    cronroot.write()
                    print("%sRemoved %s{}%s".format(cron) % (fg("white"), fg("red"), fg("white")))
            else:
                print("None selected.")
        else:
            print("No jobs in database.")
        return
            

    cur.execute("SELECT * FROM ids")
    ids = cur.fetchall()
    lams = []

    for id in ids:
        lams.append(get_lam_by_id(id))
    
    if (ids):
        idPrompt = [
            inquirer.Checkbox('Conversations',
                              message="Select threads to remove (use spacebar to select)",
                              choices=list(zip(["{}: {}".format(id[0], lam) for id,lam in zip(ids, lams)], ids))),
        ]
        try:
            selectedIDs = inquirer.prompt(idPrompt)["Conversations"]
        except TypeError:
            exit()

        if (selectedIDs):
            for id in selectedIDs:
                cur.execute("DELETE FROM ids WHERE id = ?", (id[0],))
                print("%sRemoved %s{}%s".format(id[0]) % (fg("white"), fg("red"), fg("white")))
        else:
            print("None selected.")
    else:
        print("No IDs in database.")

def schedule():
    cur.execute("SELECT * FROM ids")
    ids = cur.fetchall()
    if (ids):
        selectedMsgID = send(shouldPost=False)

        if (selectedMsgID):
            cron_job(selectedMsgID)
        else:
            print("%sNo messages in database." % fg("white"))
    else:
        print("%sNo ids in database. Start by calling '%spython3 acc.py add%s' in order to begin sending." % (fg("white"), fg("yellow"), fg("white")))
    
def cron_job(smid):
    msgs = re.sub(r"[\[\(\)\],]", "", str(list(zip((msg[0] for msg in smid)))))
    ids = re.sub(r"[\[\(\)\],]", "", str(list(zip((id[1] for id in smid)))))
    
    job = cronroot.new(command="cd {} && sh acc.sh --msgs {} --ids {}".format(os.getcwd(), msgs, ids))

    job.minute.on(0)
    
    days = {"Sunday": 0, "Monday": 1, "Tuesday": 2, "Wednesday": 3, \
            "Thursday": 4, "Friday": 5, "Saturday": 6}

    cronDayPrompt = [
        inquirer.Checkbox("Days",
                          message="Select day(s) to repeat on (use spacebar to select)",
                          choices=days),
    ]
    try:
        promptDays = inquirer.prompt(cronDayPrompt)["Days"]
    except TypeError:
        exit()

    if (promptDays):
        for day in promptDays:
            job.dow.also.on(days[day])
    else:
        print("No day selected. Will run every day.")

    hours = {"7am": 7,  "8am": 8,  "9am": 9, "10am": 10,
            "11am": 11,"12pm": 12, "1pm": 13, "2pm": 14,
            "3pm":  15, "4pm": 16, "5pm": 17, "6pm": 18,
            "7pm":  19, "8pm": 20, "9pm": 21 }

    cronHourPrompt = [
        inquirer.Checkbox("Hours",
                          message="Select hour(s) to repeat on (use spacebar to select)",
                          choices=hours),
    ]
    try:
        promptHours = inquirer.prompt(cronHourPrompt)["Hours"]
    except TypeError:
        exit()

    if (promptHours):
        for hour in promptHours:
            job.hour.also.on(hours[hour])
    else:
        print("No hour selected. Will run every hour.")

    cronroot.write()
    
    b64job = str(job).encode("ascii")
    b64job = base64.b64encode(b64job)
    b64job = b64job.decode("ascii")

    cur.execute("INSERT INTO cron (cronline) VALUES (?)", (b64job,))
    print("%sAdded cron job %s{}%s".format(b64job) % (fg("white"), fg("cyan"), fg("white")))

def cron_run():
    smid = list(zip(args.msgs, args.ids))
    for mi in smid:
        url = reqURL + "/{}/add_message?body={}".format(mi[1], (open(mi[0])).read())
        post(url, color="green", to=mi[1], using=mi[0])


def post(url, color, to, using):
    r = requests.post(url, headers=headers)
    print("%sSent a message to %s{} %susing %s{}%s".format(to, using) % (fg("white"), fg(color), fg("white"), fg(color), fg("white")))
    print(r)
    print(url)

def get_lam_by_id(id):
    url = "{}/{}".format(reqURL, id[0])
    c = requests.get(url, headers=headers).json()
    return c["context_name"].strip() + ": " + c["last_authored_message"][0:25] \
        .replace("\n", " ") \
        .strip() + "..."

if (args.selection == "send"):
    send()

if (args.selection == "add"):
    add()

if (args.selection == "list"):
    myList()

if (args.selection == "remove"):
    remove()

if (args.selection == "schedule" or args.selection == "sched"):
    schedule()

if (args.selection == "run"):
    cron_run()

con.commit()
con.close()

