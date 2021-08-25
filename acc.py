from dotenv import dotenv_values
from crontab import CronTab
from colored import fg
from pathlib import Path
import platform
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

@dataclass
class User:
    """
    A data class used to represent user data

    ...

    Attributes
    ----------
    says_str : str
        a formatted string to print out what the animal says
    name : str
        the name of the animal
    sound : str
        the sound that the animal makes
    num_legs : int
        the number of legs the animal has (default 4)

    Methods
    -------
    says(sound=None)
        Prints the animals name and what sound it makes
    """

    os = platform.system()
    
    if user.os == "Linux":
        ospath = dict(shared="~/.local/share/automated-canvas-conversations")
    else:
        ospath = dict(shared="")

    path = dict(db="acc.db", env=".env")

user = User

setup()

def no_init():
    if os.path.exists(user.path.get("shared")): return true
    return false

def setup():
    if no_init(): init()
    update()
    root_conf = dotenv_values(".env")
    user_conf = dotenv_values("{}/{}.format(user.ospath.get("shared"), \
            user.path.get("env"))

def init():
    path = Path(user.ospath.get("shared"))
    path.mkdir(parents=True, exist_ok=True)

def update():
    update_db()
    update_env()

def update_db():
    check_db_version()

def check_db_version():
    

parser = argparse.ArgumentParser(
            description="Work with Canvas conversations."
         )
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
    token = user_conf.get("TOKEN")
except KeyError:
    token()

@dataclass
class Url:
    base = "https://canvas.instructure.com/api/v1"
    convo = "conversations"
    course = "courses"
    add_msg = "add_message"
    scope = "?scope"
    scope_dict = dict(sent="sent")

    def add_msg(id, body):
        return "{}/{}?body={}".format(id[0], add_msg, body)

url = Url

# colors

send_colo = "magenta"

auth = {"Authorization": "Bearer {}".format(token)}

send_str = "%sSent a message to %s{} %susing %s{}%s".format(id[0], msg) \
        % (fg("white"), fg(send_colo), fg("white"), fg(send_colo), fg("white"))
integrity_err = "%sIntegrity Error. %sA duplicate ID was found; \
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

def no_folders(f):
    if not f:
        print("No .txt files in current directory.")
        return true
    return false

def no_ids(ids):
    if not ids:
        print("No IDs in database.")
        return true
    return false

def no_sent(c):
    if not c:
        print("No existing sent conversations.")
        return true
    return false


def no_days(days):
    if not days:
        print("No day selected. Will run every day.")
        return true
    return false


def no_hours(hours):
    if not hours:
        print("No hour selected. Will run every hour.")
        return true
    return false


def no_selected(sids):
    if not sids:
        print("None selected.")
        return true
    return false


def no_crons(crons):
    if not crons:
        print("No jobs in database.")
        return true
    return false


def create_msg_prompt(f):
    return [
        inquirer.List(
            "Messages",
            message="Select a file that contains your \
            message (enter to continue)",
            choices=f,
        ),
    ]


def create_id_prompt(zip, msg, title):
    return [
        inquirer.Checkbox(
            title,
            message=msg,
            choices=list(zip),
        ),
    ]


def create_send_id_prompt(ids, lms):
    return [
        inquirer.Checkbox(
        ),
    ]

def create_cc_prompt(ccs, ids):
    ccPrompt = [
        inquirer.Checkbox(
            "Courses",
            message="Select a course to compose \
            a message for (use spacebar to select)",
            choices=list(zip(ccs, ids)),
        ),
    ]

def create_cron_day_prompt(weekdays):
    return [
        inquirer.Checkbox(
            "Weekdays",
            message="Select day(s) to repeat on (use spacebar to select)",
            choices=weekdays,
        ),
    ]


def create_cron_hour_prompt(hours, ampm):
    return [
        inquirer.Checkbox(
            "Hours",
            message="Select hour(s) to repeat on (use spacebar to select)",
            choices=zip(list(ampm), hours),
        ),
    ]

def create_cron_prompt(crons):
    return [
            inquirer.Checkbox(
            "Cron jobs",
            message="Select a job to remove (use spacebar to select)",
            choices=crons,
        ),
    ]

def insert_id(id):
    try:
        cur.execute("INSERT INTO ids (id) VALUES (?)", (id[0],))
        print(
            "%sAdded %s{}%s with %s{}".format(id[0], id[1])
            % (fg("white"), fg("cyan"), fg("white"), fg("cyan"))
        )
    except sqlite3.IntegrityError:
        print(integrity_err)

def insert_cron(job):
    cur.execute("INSERT INTO cron (cronline) VALUES (?)", (encode(job),))
    print(
        "%sAdded cron job %s{}%s".format(job) % (fg("white"), \
            fg("cyan"), fg("white"))
    )

def fetch_crons():
    cur.execute("SELECT * FROM cron")
    cur.fetchall()

def fetch_ids():
    cur.execute("SELECT * FROM ids")
    cur.fetchall()

def check_prompt(prompt, name):
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
    if no_folders(folders): return
    lms = []
    return_tuple = []
    ids = fetch_ids()
    if no_ids(ids): return

    body = open(check_prompt(create_msg_prompt(folders), "Messages")).read()

    for id in ids:
        lms.append(getlm(id))


    title = "Conversations"
    msg = "Select threads to send your message \
            to (use spacebar to select)"
    zip = zip(["{}: {}".format(id[0], lm) for id, \
            lm in zip(ids, lms)], ids)
    s_ids = check_prompt(create_id_prompt(zip, msg, title), "Conversations")
    if no_selected(s_ids): return

    for id in s_ids:
        _url = "{}/{}".format(url.base, url.add_msg(id, body))
        if post: r = post(_url, auth)
        print(send_str, r, url)
        return_tuple.append((msg, id[0]))
    return return_tuple


def compose(sched=False):
    course_codes = []
    ids = []

    for _ in get("{}/{}".format(url.base, url.course), auth):
        course_code = _["course_code"]
        id = _["id"]
        course_codes.append(course_code)
        ids.append(id)

    ccs = check_prompt(create_cc_prompt(zip(course_codes, ids)))

def add(sched=False):
    ids = []
    lms = []

    for _ in get("{}/{}={}".format(url.base, url.scope,
                            scope_dict.get("sent")), auth):
        ids.append(str(_["id"]))
        lms.append(getlm(id), _)

    convos = list(zip(ids, lms))
    if no_sent(convos): return

    title = "Conversations"
    msg = "Select a thread to add (spacebar to select)"
    zip = zip(lms, convos)
    s_ids = check_prompt(create_id_prompt(zip, msg, title), title)

    if no_selected(s_ids): return
    for id in s_ids:
        insert_id(id)


def list_ids():
    ids = fetch_ids()
    if no_ids(ids): return
    print("Columns in IDs:")
    for id in ids: print(id)


def list_jobs():
    ecrons = fetch_crons()
    if no_crons(ecrons): return
    print("Columns in cron:")
    for _ in ecrons: print(decode(str(_)))


def remove_jobs():
    ecrons = fetch_crons()
    crons = {}

    if no_crons(ecrons): return
    for _ in ecrons: crons[decode(_[0])] = _[0]

    scrons = check_prompt(create_cron_prompt(crons), "Cron jobs")

    if no_selected(scrons): return
    for _ in scrons: remove_cron(_, crons)


def remove_ids():
    ids = fetch_ids()
    lms = []

    for id in ids: lms.append(getlm(id))

    if no_ids(ids): return

    title = "Conversations"
    msg = "Select threads to remove (use spacebar to select)"
    zip = zip(["{}: {}".format(id[0], lm) for id, lm in zip(ids, lms)], ids)
    s_ids = check_prompt(create_id_prompt(zip, msg, title), title)

    if no_selected(s_ids): return
    for _ in s_ids: remove_id(_)


def remove_cron(cron, crons):
    cur.execute("DELETE FROM cron WHERE cronline = ?", (crons[cron],))
    for job in cronroot:
        if str(job) == str(cron):
            cronroot.remove(job)
    cronroot.write()
    print(
        "%sRemoved %s{}%s".format(cron)
        % (fg("white"), fg("red"), fg("white"))
    )


def remove_id(id):
    cur.execute("DELETE FROM ids WHERE id = ?", (id[0],))
    print(
        "%sRemoved %s{}%s".format(id[0])
        % (fg("white"), fg("red"), fg("white"))
    )


def schedule():
    ids = fetch_ids()
    if no_ids(ids): return

    msg_ids = send(False)
    if no_ids(msg_ids): return

    cron_job(msg_ids)

def cron_job(tasks):
    cron_cmd = "cd {} && sh acc.sh --msgs {} \
    --ids {}".format(os.getcwd(), msgs, ids)
    task_regex = r"[\[\(\)\],]"
    msgs = str(list(zip((msg[0] for msg in tasks))))
    msgs = re.sub(task_regex, "", msgs)

    ids = str(list(zip((id[1] for id in tasks))))
    ids = re.sub(task_regex, "", ids)

    job = cronroot.new(command=cron_cmd)
    job.minute.on(0)

    weekdays = [ "Sunday", "Monday", "Tuesday", "Wednesday",
        "Thursday", "Friday", "Saturday" ]
    weekdays_list = list(zip(weekdays, range(len(weekdays))))

    s_days = check_prompt(create_cron_day_prompt(weekdays_list), "Weekdays")
    if no_days(s_days): return

    for _ in s_days: job.dow.also.on(_)

    hours = [*range(1, 25, 1)]
    ampm = map(lambda h: h = "{}{}".format((h if h < 12 \
        else h - 12), ("am" if h < 12 else "pm")), hours)

    s_hours = check_prompt(create_cron_hour_prompt(hours, ampm), "Hours")
    if no_hours(s_hours): return

    for _ in s_hours:
        job.hour.also.on(_)

    cronroot.write()
    insert_cron(job)


def cronrun():
    tasks = list(zip(args.msgs, args.ids))
    for _ in tasks:
        body = (open(_[0])).read()
        _url = "{}/{}".format(url.base, url.add_msg(id, body))
        post(_url, auth)


def getlm(id, c = get("{}/{}".format(url.base, id[0]), auth)):
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
            case "jobs": list_jobs()
            case "ids": list_ids()
    case "remove":
        match args.type:
            case "jobs": remove_jobs()
            case "ids": remove_ids()
    case "schedule": schedule()
    case "sched": schedule()
    case "run": cronrun()

con.commit()
con.close()
