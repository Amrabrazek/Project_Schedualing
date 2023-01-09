from datetime import datetime
from datetime import date
from datetime import timedelta
import re, sys, csv
from cs50 import SQL
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

db = SQL("sqlite:///fp.db")


critical_path = []
critical_path_name = []
carrier_dic = {}
counter = 0

def main():

    projects = db.execute("select name  from sqlite_master where type='table' Order by name ")
    projects_list =[pr["name"] for pr in projects]

    if projects_list:
        print (projects_list)
    else:
        print("No projects yet")

    #start a new project or update a current one
    # checking for the user input is valid
    while True:
        #new project
        start = input("1-New project \n2-update a current project\n")
        if start == "1" or start == "New project":
            pn = input("what is the title of the projct?" )
            #function1 : which creates the project sqlite table and add activities
            New_project(pn)

            # identify the project start date
            while True:

                PS = input("when does the project start? ")

                if matches := re.search(r"([0-9]{4})-([0-9]{2})-([0-9]{2})", PS):

                    year = matches.group(1)
                    month = matches.group(2)
                    day = matches.group(3)
                    break
            project_start_date = date(int(year),int(month),int(day))

            #function2: which schedual the project and get the cretical path
            x = Schedule (pn, project_start_date)
            #function3: which creates the project baseline figure
            dates(pn, x)
            #function4: which creates the cost_bar figure
            cost_barchart(pn)

            break

        elif start == "2" or start == "update" or start == "update a current project":
            break

    if start == "2" or start == "update" or start == "update a current project":

        while True:
            pn = input("what is the project name? ")
            if pn in projects_list:
                update_project(pn)
                break


#  Function 1 which creates the project sqlite table and add activities
def New_project(pn):

    global db
    #creating new table with the project name
    db.execute(f"CREATE TABLE  {pn} (num INTEGER, ID, name TEXT , Du INTEGER, cost INTEGER, SD, ED, ASD, AED, ADu INTEGER, PRIMARY KEY(ID))")

    activity_list=[]
    #each project has a Project Start activity
    Project_Start = Activity(pn ,1 , "PS", "Project_Start" , 0, 0)

    # inputting project activities
    i = 1
    while True:
        x = (input("add activity? ")).lower()
        if x == "yes":
            ID = input("ID: ")
            name = input("name: ")
            duration = input("duration: ")
            cost = input ("cost:")
            i = i+1
            Activity(pn, i, ID, name, duration, cost)
        elif x == "no":
            break
    #each project has a Project Finish activity
    Project_Finish = Activity(pn , i+1 ,"PF", "Project_Finish" , 0, 0)


#   Function 2
def Schedule (name, project_start_date):

    global db
    activity_list = []
    relations = ["SS", "FS", "FF", "SF"]
    #set the project start date
    db.execute(f"UPDATE {name} SET SD = ? WHERE ID = 'PS' ", project_start_date)
    db.execute(f"UPDATE {name} SET ED = ? WHERE ID = 'PS' ", project_start_date)

    # Another table to track the dependency
    scheduale_table_name = name + "_scheduale"
    db.execute(f"CREATE TABLE  {scheduale_table_name} (ID TEXT, successor TEXT , Relation TEXT, Lag INTEGER)")

    #Get all the activities oredered according to the creation date
    activities  = db.execute(f"select ID  from {name} ORDER BY num")

    #Get the activites IDs in List
    for activity in activities:
        activity_list.append(activity["ID"])

    # inputting relationships between activities
    for activity in activity_list:

        if activity != "PF":
            while True:

                while True:
                    successor_ID = input(f"{activity} successor is? ")

                    if successor_ID in activity_list:
                        break
                    else:
                        print("unavilable ID ")
                while True:
                    relation = (input(f"{activity} relation with {successor_ID}? ")).upper()

                    if relation in relations:
                        break
                    else:
                        print ("invalid relations")

                while True:
                    try:
                        lag = int(input(f"is there a lag between {activity} and {successor_ID}? "))
                        break
                    except :
                        print ("lag should be an integer")

                db.execute(f"INSERT INTO {scheduale_table_name} (ID, successor, Relation, Lag) VALUES(?,?,?,?)", activity, successor_ID, relation, lag)

                count = input ("is there another successor? ")

                if not (count == "yes" or count == "YES" or count == 1):

                    break

    # gettin the paths and the cretical path of the project
    x = project_critical_path(name)

    return x

def sche(activity,  table_name ):

    global critical_path
    global critical_path_name
    global counter
    global carrier_dic

    critical_path_name.append(activity)
    next_activities = db.execute(f"SELECT successor FROM {table_name} WHERE ID = ?", activity)
    next_activity_list = dictolist (next_activities, "successor")
    if len(next_activity_list) == 1:
        if "PF" in next_activity_list:
            critical_path_name.append("PF")
            X = critical_path_name
            critical_path.append(X)
            critical_path_name = []
        else:
            x = sche (next_activity_list[0], table_name)
    else:
        carrier_dic[counter] = critical_path_name[:]
        counter = counter + 1
        for activities in next_activity_list:
            #NOT FIRST ONE
            if activities != next_activity_list[0]:

                critical_path_name = carrier_dic[counter-1]
                x = sche (activities, table_name)
            #FIRST ACTIVITY
            else:
                x = sche (activities, table_name)
        counter = counter - 1


    return critical_path

# updating dates and getting a Gatt chart where cretical activities are in red
def dates(name, critical_path):

    global db

    project_start_date = (db.execute(f"select SD from {name} WHERE ID = ?", "PS") [0]) ["SD"]
    project_start_date = datetime.strptime(project_start_date, "%Y-%m-%d")

    activity_list = []
    duration_list = []
    activity_start_list = []
    colors = []

    scheduale_table_name = name + "_scheduale"

    activities  = db.execute(f"select ID, Du, SD from {name} ORDER BY num")
    for activity in activities:
        activity_list.append(activity["ID"])
        duration_list.append(activity["Du"])

    # updating planned dates (SD and ED)
    for activity in activity_list:

        successors = dictolist((db.execute(f"SELECT successor FROM {scheduale_table_name} WHERE ID = ?", activity)), "successor")


        #making a list of colors to identify the creditical
        if activity in critical_path:
            colors.append("red")
        else:
            colors.append("green")


        for successor in successors:
            lag = int((db.execute(f"SELECT Lag FROM {scheduale_table_name} WHERE ID = ? AND successor = ?", activity, successor) [0]) ["Lag"])
            relation = (db.execute(f"SELECT Relation FROM {scheduale_table_name} WHERE ID = ? AND successor = ?",activity , successor) [0]) ["Relation"]
            activity_end_date = (db.execute(f"SELECT ED FROM {name} WHERE ID = ?", activity) [0]) ["ED"]
            activity_start_date = (db.execute(f"SELECT SD FROM {name} WHERE ID = ?", activity) [0]) ["SD"]
            successor_duration = int((db.execute(f"SELECT Du FROM {name} WHERE ID = ?", successor)[0])["Du"])
            successor_start_date = (db.execute(f"SELECT SD FROM {name} WHERE ID = ?", successor) [0]) ["SD"]


            if relation == "FS":
                SD = ((datetime.strptime(activity_end_date, "%Y-%m-%d")) + timedelta(days=lag)).date()
            elif relation == "SS":
                SD = ((datetime.strptime(activity_start_date, "%Y-%m-%d")) + timedelta(days=lag)).date()

            if not successor_start_date:
                db.execute(f"UPDATE {name} SET SD = ? WHERE ID = ? ", SD, successor)
                ED = SD +  timedelta(days=successor_duration)
                db.execute(f"UPDATE {name} SET ED = ? WHERE ID = ? ", ED, successor)

            else:
                SSD = ((datetime.strptime(successor_start_date, "%Y-%m-%d")) + timedelta(days=lag)).date()
                if SD > SSD:
                    db.execute(f"UPDATE {name} SET SD = ? WHERE ID = ? ", SD, successor)
                    ED = SD +  timedelta(days=successor_duration)
                    db.execute(f"UPDATE {name} SET ED = ? WHERE ID = ? ", ED, successor)



    # getting the start of Each project and put it in a list
    for activity in activities:
        activity_start_dateX = (db.execute(f"SELECT SD FROM {name} WHERE ID = ?", activity["ID"]) [0]) ["SD"]
        activity_start_dateX = datetime.strptime(activity_start_dateX, "%Y-%m-%d")
        x = (activity_start_dateX - project_start_date).days
        activity_start_list.append(x)


    project_end_date = (db.execute(f"select SD from {name} WHERE ID = ?", "PF") [0]) ["SD"]
    project_end_date = datetime.strptime(project_end_date, "%Y-%m-%d")

    #getting the total project duration
    project_duration = project_durationx(name)

    xticks = np.arange(0, project_duration+1 , 3)
    xticks_labels = pd.date_range(project_start_date, project_end_date).strftime("%m-%d")
    xticks_minor = np.arange(0, project_duration+1, 1)
    fig, ax = plt.subplots(1, figsize=(10,len(activity_list)+2))

    #plotting the figure
    ax.barh(activity_list, duration_list, left = activity_start_list, color = colors)
    ax.set_axisbelow(True)
    ax.xaxis.grid(color='k', linestyle='dashed', alpha=0.4, which='both')
    ax.set_xticks(xticks)
    ax.set_xticks(xticks_minor, minor=True)
    ax.set_xticklabels(xticks_labels[::3], rotation ='vertical' )
    ax.plot("PS", marker = 'o')


    plt.xlabel("dates")
    plt.ylabel("activities")
    plt.suptitle('Project Baseline Schedule')
    plt.savefig("Project Baseline.png")

    #clearing the memory for another plot
    plt.figure().clear()
    plt.close()
    plt.cla()
   # plt.clf()
    return project_duration

def cost_barchart(name):

    global db

    date_cost_dic = {}

    project_start_date = (db.execute(f"select SD from {name} WHERE ID = ?", "PS") [0]) ["SD"]
    project_start_date = datetime.strptime(project_start_date, "%Y-%m-%d")

    project_end_date = (db.execute(f"select SD from {name} WHERE ID = ?", "PF") [0]) ["SD"]
    project_end_date = datetime.strptime(project_end_date, "%Y-%m-%d")

    project_duration = project_durationx(name)

    carrier = project_start_date

    date_list = []

    for day in range(project_duration+1):
        x = carrier.strftime('%Y-%m-%d')
        date_list.append(x)
        date_cost_dic[x] = 0
        carrier = (carrier + timedelta(days=1))

    activities  = db.execute(f"select cost, Du, SD from {name} ORDER BY num")

    for activity in activities:
        if activity["Du"] != 0:
            costperday = activity["cost"] / activity["Du"]
            for day in date_cost_dic:
                if day == activity["SD"]:
                    for days in range(activity["Du"]):
                        date_cost_dic[day] = date_cost_dic[day] + costperday
                        day = (datetime.strptime(day, "%Y-%m-%d")).date()
                        day = day +timedelta(days=1)
                        day = day.strftime('%Y-%m-%d')


    cost_list = []
    for day in date_cost_dic:
        x = date_cost_dic[day]
        cost_list.append(x)

    cum_cost_list = []
    cum = 0
    for cost in cost_list:
        cum = cum +cost
        cum_cost_list.append(cum)

    width = 0.5

    m1_t = pd.DataFrame({
     'cost_list' : cost_list,
     'cum_cost_list' : cum_cost_list,
     })

    m1_t[['cost_list']].plot(kind='bar', width = width)
    plt.ylabel("cost" )

    m1_t['cum_cost_list'].plot(secondary_y=True)

    ax = plt.gca()
    plt.xlim([-width, len(m1_t['cost_list'])-width])
    xticks = np.arange(0, project_duration+1 , 3)

    xticks_labels = pd.date_range(project_start_date, project_end_date).strftime("%m-%d")

    xticks_minor = np.arange(0, project_duration+1, 1)

    ax.set_xticks(xticks)
    ax.set_xticks(xticks_minor, minor=True)
    ax.set_xticklabels(xticks_labels[::3], rotation ='vertical' )

    plt.xlabel("dates")
    plt.ylabel("Cumlative cost")
    plt.suptitle('Activity cost and Cumlative cost')
    plt.savefig("Project Cost.png")

    plt.figure().clear()
    plt.close()
    plt.cla()
    return cum_cost_list[-1]

#updating the actual dates for the project and getting a gantt chart comparing the planned with the actual
def update_project(name):
    global db
    print (f"updating project {name}")

    project_start_date = (db.execute(f"select SD from {name} WHERE ID = ?", "PS") [0]) ["SD"]
    project_start_date = datetime.strptime(project_start_date, "%Y-%m-%d")

    activity_list = []
    activity_duration = []
    activity_actual_duration = []
    activity_start_list =[]
    activity_actual_start_list = []
    activity_actually_started=[]

    activities  = db.execute(f"select ID, Du, SD, ADu from {name} ORDER BY num")
    for activity in activities:
        activity_list.append(activity["ID"])
        activity_duration.append(activity["Du"])
        activity_start_dateX = (db.execute(f"SELECT SD FROM {name} WHERE ID = ?", activity["ID"]) [0]) ["SD"]
        activity_start_dateX = datetime.strptime(activity_start_dateX, "%Y-%m-%d")
        x = (activity_start_dateX - project_start_date).days
        activity_start_list.append(x)


    print("project activities: ", end = "")
    print(activity_list)

    while True:
        activity_start_date = ""
        activity_end_date = ""
        x = (input("choose activity: "))
        if x in activity_list:
            while True:
                AS = input("Actual start: ")
                if matches := re.search(r"([0-9]{4})-([0-9]{2})-([0-9]{2})", AS):
                    year = matches.group(1)
                    month = matches.group(2)
                    day = matches.group(3)
                    break

            activity_start_date = date(int(year),int(month),int(day))
            db.execute(f"UPDATE {name} SET ASD = ? WHERE ID = ? ", activity_start_date , x)

            while True:
                AE = input("Actual end: ")
                if matches := re.search(r"([0-9]{4})-([0-9]{2})-([0-9]{2})", AE):
                    year = matches.group(1)
                    month = matches.group(2)
                    day = matches.group(3)
                    break

            activity_end_date = date(int(year),int(month),int(day))
            db.execute(f"UPDATE {name} SET AED = ? WHERE ID = ? ", activity_end_date , x)


            if activity_end_date != "":

                ADU = (activity_end_date - activity_start_date).days

                db.execute(f"UPDATE {name} SET ADu = ? WHERE ID = ? ", ADU , x)

                x = input("update new activity?")

                if x == "NO" or x == "no":
                    break


    for activity in activities:

        if activity["ADu"] != None:
            activity_actual_duration.append(activity["ADu"])
            activity_actually_started.append(activity["ADu"])
        else:
            activity_actual_duration.append(0)

        activity_start_datey = (db.execute(f"SELECT ASD FROM {name} WHERE ID = ?", activity["ID"]) [0]) ["ASD"]

        if activity_start_datey != None:
            activity_start_datey = datetime.strptime(activity_start_datey, "%Y-%m-%d")
            y = (activity_start_datey - project_start_date).days
            activity_actual_start_list.append(y)
        else:
            activity_actual_start_list.append(0)

    fig, ax = plt.subplots()
    ind = np.arange(len(activity_list))
    width = 0.4

    ax.barh(ind, activity_duration, height = width, left = activity_start_list, color='green', label='planned')
    ax.barh(ind + width, activity_actual_duration, height = width, left = activity_actual_start_list, color='blue', label='actual')
    ax.set(yticks = ind + (width/2), yticklabels = activity_list, ylim=[2*width - 1, len(activity_list)])

    project_end_date = (db.execute(f"select SD from {name} WHERE ID = ?", "PF") [0]) ["SD"]
    project_end_date = datetime.strptime(project_end_date, "%Y-%m-%d")
    project_duration = project_durationx(name)

    xticks = np.arange(0, project_duration+1 , 3)
    xticks_labels = pd.date_range(project_start_date, project_end_date).strftime("%m-%d")
    xticks_minor = np.arange(0, project_duration+1, 1)

    ax.set_xticks(xticks)
    ax.set_xticks(xticks_minor, minor=True)
    ax.set_xticklabels(xticks_labels[::3], rotation ='vertical' )
    ax.legend()
    plt.savefig("Actual vs planned.png")

    return activity_actually_started

#getting the project duration
def project_durationx(name):
    project_start_date = (db.execute(f"select SD from {name} WHERE ID = ?", "PS") [0]) ["SD"]
    project_start_date = datetime.strptime(project_start_date, "%Y-%m-%d")
    project_end_date = (db.execute(f"select SD from {name} WHERE ID = ?", "PF") [0]) ["SD"]
    project_end_date = datetime.strptime(project_end_date, "%Y-%m-%d")
    project_duration = (project_end_date - project_start_date).days
    return project_duration

# getting thec cretical path of the project
def project_critical_path(name):
    scheduale_table_name = name + "_scheduale"
    x = sche ("PS" , scheduale_table_name)

    print("project paths: ", end = "")
    print(critical_path)

    path_time_dic = {}

    #going through all the paths to find out which is cretical
    for path in critical_path:

        days = 0
        path_string = ""

        #getting the whole path as a string
        for x in path:
            if x == "PF":
                path_string = path_string + "PF"
            else:
                path_string = path_string + x + "-"

        for i in range(len(path)-1):

            activity_duration = ((db.execute(f"SELECT Du FROM {name} WHERE ID = ?", path[i]))[0])["Du"]
            lag = ((db.execute(f"SELECT Lag FROM {scheduale_table_name} WHERE ID = ? AND successor = ?",path[i], path[i+1]))[0])["Lag"]
            relation = ((db.execute(f"SELECT Relation FROM {scheduale_table_name} WHERE ID = ? AND successor = ?",path[i], path[i+1]))[0])["Relation"]

            if relation == "FS":
                days = days + activity_duration + lag
            elif relation == "SS":
                days = days + lag
            elif relation == "FF":
                days = days + lag

        path_time_dic [path_string] = days

    print("path_time_dic:", end = "")
    print(path_time_dic)

    CP = 0
    for path in path_time_dic.values():

        if path > CP:
            CP = path

    key_list = list(path_time_dic.keys())
    val_list = list(path_time_dic.values())

    position = val_list.index(CP)

    x = key_list[position].split("-")
    print("Critical Path is: ", end = "" )
    print (x)
    print("Duration: ", end = "" )
    print (CP)
    return x

# converting a dictionary to a list
def dictolist (listx,  name):
    emptylist=[]
    for dic in listx:
        emptylist.append(dic[name])

    return emptylist

class Activity:
    """ creating a project activity"""
    def __init__ (self, pn, num, ID, name, du, cost):
        """ initiallizing an actiity adding id name and duration"""
        self.pn = pn
        self.num = num
        self.ID = ID
        self.name = name
        self.du = du
        self.cost = cost

        self.db = SQL("sqlite:///fp.db")

        self.db.execute(f"INSERT INTO {self.pn} (num, ID, name, Du, cost) VALUES(?,?,?,?,?)", self.num, self.ID, self.name, self.du, self.cost)

    def a_start (self, ASD ):
        """ intiallizing the activity when it actually start"""
        if matches := re.search(r"([0-9]{4})-([0-9]{2})-([0-9]{2})", ASD):
            year = matches.group(1)
            month = matches.group(2)
            day = matches.group(3)

        else:
            sys.exit("Invalid date, please use this format year-month-day for example 1999-01-01")

        self.AS = date(int(year),int(month),int(day))

        self.db.execute(f"UPDATE {self.pn} SET ASD = (?)  WHERE ID = (?)", self.AS, self.ID)

        print(self.AS)
        return self.AS

    def a_end (self, AED):
        """ ending the activity when it actually end"""
        if matches := re.search(r"([0-9]{4})-([0-9]{2})-([0-9]{2})", AED):

            year = matches.group(1)
            month = matches.group(2)
            day = matches.group(3)

        else:
            sys.exit("Invalid date, please use this format year-month-day for example 1999-01-01")

        self.AE = date(int(year),int(month),int(day))

        self.db.execute(f"UPDATE {self.pn} SET AED = (?)  WHERE ID = (?)", self.AE, self.ID)

        print(self.AE)
        return self.AE

    def a_duration (self):

        self.AD = (self.AE- self.AS).days

        self.db.execute(f"UPDATE {self.pn} SET ADu = (?)  WHERE ID = (?)", self.AD, self.ID)

        print(self.AD)
        return self.AD



if __name__ == "__main__":

    main()
