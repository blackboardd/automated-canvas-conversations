from crontab import CronTab
from colored import fg
from dataclasses import dataclass
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
parser.add_argument(
    "selection",
    choices=[
        "send",
        "compose",
        "add",
        "list",
        "remove",
        "schedule",
        "sched",
        "run", # this argument is used by acc.sh
    ],
)
parser.add_argument("-t", "--type", choices=["jobs"], choices=["ids"],
        default="ids")
parser.add_argument("--msgs", nargs="+") # this argument is used by acc.sh
parser.add_argument("--ids", nargs="+") # this argument is used by acc.sh
args = parser.parse_args()

con = sqlite3.connect("acc.db")
cur = con.cursor()

cronroot = CronTab(user=True)

try:
    token = os.environ["CANVAS_HEADER_AUTH_TOKEN"]
except KeyError:
    print(
        """Missing Canvas token. use %sCANVAS_HEADER_AUTH_TOKEN="[YOUR \
TOKEN]"; export CANVAS_HEADER_AUTH_TOKEN%s in your ~/.bashrc file

Don't know where your token is? Follow this guide to get it:
Student: https://bit.ly/3jdtpXw
Admin:   https://bit.ly/3yiq3qw"""
        % (fg("yellow"), fg("white"))
    )
    exit()

@dataclass
class Url:
    base = "https://canvas.instructure.com/api/v1"
    convo = "conversations"
    course = "courses"
    addMsg = "add_message"
    scope = "?scope"
    scopeDict = dict(sent="sent")

    def addMsg(id, body):
        return "{}/{}?body={}".format(id[0], addMsg, body)

url = Url

# colors

sendColor = "magenta"

auth = {"Authorization": "Bearer {}".format(token)}

sendStr = "%sSent a message to %s{} %susing %s{}%s".format(id[0], msg) \
        % (fg("white"), fg(sendColor), fg("white"), fg(sendColor), fg("white"))
integrityErr = "%sIntegrity Error. %sA duplicate ID was found; \
                cannot add %s{}%s with %s{}".format(
                    id[0], id[1]
                ) \
                % (
                    fg("red"),
                    fg("white"),
                    fg("cyan"),
                    fg("white"),
                    fg("cyan"),
                )

def noFolders(f):
    if not f:
        print("No .txt files in current directory.")
        return true
    return false

def noIds(ids):
    if not ids:
        print("No IDs in database.")
        return true
    return false

def noSent(c):
    if not c:
        print("No existing sent conversations.")
        return true
    return false


def noDays(days):
    if not days:
        print("No day selected. Will run every day.")
        return true
    return false


def noHours(hours):
    if not hours:
        print("No hour selected. Will run every hour.")
        return true
    return false


def noSelected(sids):
    if not sids:
        print("None selected.")
        return true
    return false


def noCrons(crons):
    if not crons:
        print("No jobs in database.")
        return true
    return false


def createMsgPrompt(f):
    return [
        inquirer.List(
            "Messages",
            message="Select a file that contains your \
            message (enter to continue)",
            choices=f,
        ),
    ]


def createIdPrompt(zip, msg, title):
    return [
        inquirer.Checkbox(
            title,
            message=msg,
            choices=list(zip),
        ),
    ]


def createSendIdPrompt(ids, lms):
    return [
        inquirer.Checkbox(
        ),
    ]

def createCcPrompt(ccs, ids):
    ccPrompt = [
        inquirer.Checkbox(
            "Courses",
            message="Select a course to compose \
            a message for (use spacebar to select)",
            choices=list(zip(ccs, ids)),
        ),
    ]

def createCronDayPrompt(weekdays):
    return [
        inquirer.Checkbox(
            "Weekdays",
            message="Select day(s) to repeat on (use spacebar to select)",
            choices=weekdays,
        ),
    ]


def createCronHourPrompt(hours, ampm):
    return [
        inquirer.Checkbox(
            "Hours",
            message="Select hour(s) to repeat on (use spacebar to select)",
            choices=zip(list(ampm), hours),
        ),
    ]

def createCronPrompt(crons):
    return [
            inquirer.Checkbox(
            "Cron jobs",
            message="Select a job to remove (use spacebar to select)",
            choices=crons,
        ),
    ]

def insertId(id):
    try:
        cur.execute("INSERT INTO ids (id) VALUES (?)", (id[0],))
        print(
            "%sAdded %s{}%s with %s{}".format(id[0], id[1])
            % (fg("white"), fg("cyan"), fg("white"), fg("cyan"))
        )
    except sqlite3.IntegrityError:
        print(integrityErr)

def insertCron(job):
    cur.execute("INSERT INTO cron (cronline) VALUES (?)", (encode(job),))
    print(
        "%sAdded cron job %s{}%s".format(job) % (fg("white"), \
            fg("cyan"), fg("white"))
    )

def fetchCrons():
    cur.execute("SELECT * FROM cron")
    cur.fetchall()

def fetchIds():
    cur.execute("SELECT * FROM ids")
    cur.fetchall()

def checkPrompt(prompt, name):
    try:
        return inquirer.prompt(prompt)[name]
    except TypeError:
        exit()
        return

def decode(str):
    return base64.b64decode(str.encode("ascii")).decode("ascii")

def encode(str):
    return base64.b64encode(str(str).encode("ascii")).decode("ascii")

def post(u, h):
    return requests.post(u, headers=h)

def get(u, h):
    return requests.get(u, headers=h).json()

def send(post = True):
    folders = glob.glob("./*.txt")
    if noFolders(folders): return
    lms = []
    returnTuple = []
    ids = fetchIds()
    if noIds(ids): return

    body = open(checkPrompt(createMsgPrompt(folders), "Messages")).read()

    for id in ids:
        lms.append(getLm(id))


    title = "Conversations"
    msg = "Select threads to send your message \
            to (use spacebar to select)"
    zip = zip(["{}: {}".format(id[0], lm) for id, \
            lm in zip(ids, lms)], ids)
    sIds = checkPrompt(createIdPrompt(zip, msg, title), "Conversations")
    if noSelected(sIds): return

    for id in sIds:
        _url = "{}/{}".format(url.base, url.addMsg(id, body))
        if post: r = post(_url, auth)
        print(sendStr, r, url)
        returnTuple.append((msg, id[0]))
    return returnTuple


def compose(sched=False):
    courseCodes = []
    ids = []

    for _ in get("{}/{}".format(url.base, url.course), auth):
        courseCode = _["course_code"]
        id = _["id"]
        courseCodes.append(courseCode)
        ids.append(id)

    ccs = checkPrompt(createCcPrompt(zip(courseCodes, ids)))

def add(sched=False):
    ids = []
    lms = []

    for _ in get("{}/{}={}".format(url.base, url.scope,
                            scopeDict.get("sent")), auth):
        ids.append(str(_["id"]))
        lms.append(getLm(id), _)

    convos = list(zip(ids, lms))
    if noSent(convos): return

    title = "Conversations"
    msg = "Select a thread to add (spacebar to select)"
    zip = zip(lms, convos)
    sIds = checkPrompt(createIdPrompt(zip, msg, title), title)

    if noSelected(sIds): return
    for id in sIds:
        insertId(id)


def listIds():
    ids = fetchIds()
    if noIds(ids): return
    print("Columns in IDs:")
    for id in ids: print(id)


def listJobs():
    ecrons = fetchCrons()
    if noCrons(ecrons): return
    print("Columns in cron:")
    for _ in ecrons: print(decode(str(_)))


def removeJobs():
    ecrons = fetchCrons()
    crons = {}

    if noCrons(ecrons): return
    for _ in ecrons: crons[decode(_[0])] = _[0]

    scrons = checkPrompt(createCronPrompt(crons), "Cron jobs")

    if noSelected(scrons): return
    for _ in scrons: removeCron(_, crons)


def removeIds():
    ids = fetchIds()
    lms = []

    for id in ids: lms.append(getLm(id))

    if noIds(ids): return

    title = "Conversations"
    msg = "Select threads to remove (use spacebar to select)"
    zip = zip(["{}: {}".format(id[0], lm) for id, lm in zip(ids, lms)], ids)
    sIds = checkPrompt(createIdPrompt(zip, msg, title), title)

    if noSelected(sIds): return
    for _ in sIds: removeId(_)


def removeCron(cron, crons):
    cur.execute("DELETE FROM cron WHERE cronline = ?", (crons[cron],))
    for job in cronroot:
        if str(job) == str(cron):
            cronroot.remove(job)
    cronroot.write()
    print(
        "%sRemoved %s{}%s".format(cron)
        % (fg("white"), fg("red"), fg("white"))
    )


def removeId(id):
    cur.execute("DELETE FROM ids WHERE id = ?", (id[0],))
    print(
        "%sRemoved %s{}%s".format(id[0])
        % (fg("white"), fg("red"), fg("white"))
    )


def schedule():
    ids = fetchIds()
    if noIds(ids): return

    msgIds = send(False)
    if noIds(msgIds): return

    cron_job(msgIds)

def cron_job(tasks):
    cronCmd = "cd {} && sh acc.sh --msgs {} \
    --ids {}".format(os.getcwd(), msgs, ids)
    taskRgx = r"[\[\(\)\],]"
    msgs = str(list(zip((msg[0] for msg in tasks))))
    msgs = re.sub(taskRgx, "", msgs)

    ids = str(list(zip((id[1] for id in tasks))))
    ids = re.sub(taskRgx, "", ids)

    job = cronroot.new(command=cronCmd)
    job.minute.on(0)

    weekdays = [ "Sunday", "Monday", "Tuesday", "Wednesday",
        "Thursday", "Friday", "Saturday" ]
    weekdaysList = list(zip(weekdays, range(len(weekdays))))

    sDays = checkPrompt(createCronDayPrompt(weekdaysList), "Weekdays")
    if noDays(sDays): return

    for _ in sDays: job.dow.also.on(_)

    hours = [*range(24)]
    ampm = map(lambda h: h = "{}{}".format((h + 1 if h < 12 else h + 1 - 12), \
        ("am" if h < 12 else "pm")), hours)

    sHours = checkPrompt(createCronHourPrompt(hours, ampm), "Hours")
    if noHours(sHours): return

    for _ in sHours:
        job.hour.also.on(_)

    cronroot.write()
    insertCron(job)


def cronRun():
    tasks = list(zip(args.msgs, args.ids))
    for _ in tasks:
        body = (open(_[0])).read()
        _url = "{}/{}".format(url.base, url.addMsg(id, body))
        post(_url, auth)


def getLm(id, c = get("{}/{}".format(url.base, id[0]), auth)):
    context = c["context_name"].strip()
    lm = c["last_authored_message"][0:25].replace("\n", " ").strip()
    return "{}: {}...".format(context, lm)

if arg.selection == "send": send()
if arg.selection == "add": add()
if arg.selection == "compose": compose()
if arg.selection == "list": send()
if arg.selection == "send": send()
    case "add": add()
    case "compose": compose()
    case "list":
        match args.type:
            case "jobs": listJobs()
            case "ids": listIds()
    case "remove":
        match args.type:
            case "jobs": removeJobs()
            case "ids": removeIds()
    case "schedule": schedule()
    case "sched": schedule()
    case "run": cronRun()

con.commit()
con.close()
