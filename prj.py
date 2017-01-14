#!/bin/python

# Project management script to use in ~/Documents/projects
# Harry Poulter
# 14/01/17 - created prj.py
#          - added new, stat, list, update and delete functions
#          - now v1.0

import sys
import os
from shutil import rmtree
import subprocess
import argparse
import yaml

from time import strftime

statDict = {'p': "proposed",
            'a': "active",
            'i': "inactive",
            'c': "complete"
}

defaultDescription = "My Exciting Project!"
defaultStatus = 'a'

def main():
  """
  Main script
  """
  # Parse arguments
  parser = makeParser()
  args = parser.parse_args()

  command = args.cmd[0]

  # Remove trailing slashes from project names
  args.project = args.project.strip('/')

  if (command == "new"):
    return prj_new(args)
  elif (command == "stat"):
    return prj_stat(args)
  elif (command == "list"):
    return prj_list(args)
  elif (command == "update"):
    return prj_update(args)
  elif (command == "delete"):
    return prj_delete(args)

  return -1

### Methods ###

def prj_new(args):
  """Create new project and initialise .prj file"""
  projectName = args.project
  projectDir = "./{0}".format(projectName)

  if (projectName == "all"):
    printError("Project cannot have name {0!r}. "
      "{0!r} is a reserved keyword.", projectName)
    return 2

  # Create project directory
  try:
    print "Creating project '{0}'...".format(projectName)
    os.mkdir(projectDir)

  except OSError, e:
    printError("{0!r} already has project directory!", projectName)
    return 2

  # Initialise .prj file in directory
  return makeNewPrjFile(args)


def prj_stat(args):
  """Return the status of different projects"""
  projectName = args.project
  project = getProjectInfo(projectName)

  if (project == None):
    printError("Project {0!r} does not exist.", projectName)
    return 3

  print "{0!r} is currently {1}".format(projectName, project["status"])

  return 0


def prj_list(args):
  """Return descriptions of different projects"""
  projectName = args.project

  # List all tracked projects
  if (projectName == "all"):
    print "All tracked projects in {0}:".format(os.getcwd())

    for projectDir in os.listdir('.'):
      project = getProjectInfo(projectDir)

      if (project == None):
        continue

      printProjectInfo(project, "short")

  # List detail on selected project
  else:
    project = getProjectInfo(projectName)
    if (project == None):
      printError("Project {0!r} does not exist.", projectName)
      return 4

    printProjectInfo(project, "long")

  return 0

def prj_update(args):
  """Update project details"""
  projectName = args.project
  project = None

  try:
    projectDescription = args.descr[0]
  except TypeError, e:
    projectDescription = None

  try:
    projectStatus = statDict[args.stat[0]]
  except TypeError, e:
    projectStatus = None

  # Create a .prj file if there isn't one already
  while project is None:
    project = getProjectInfo(projectName)

    stat = 0
    if project is None:
      stat = makeNewPrjFile(args)

    if (stat == -1):
      printError("Project {0!r} does not exist.", projectName)
      return 7

  # Description has been updated
  if projectDescription is not None:
    project["description"] = projectDescription

  # Status has been updated
  if projectStatus is not None:
    project["status"] = projectStatus

    # Do date things again
    if (projectStatus == "proposed"):
      project["start_date"] = ''

    if (projectStatus == "active"):
      project["start_date"] = strftime("%d/%m/%Y")

    if (projectStatus == "complete"):
      project["end_date"] = strftime("%d/%m/%Y")
    else:
      project["end_date"] = ''

  # Write project object back to .prj file
  return setProjectInfo(project)

def prj_delete(args):
  """Delete projects"""
  projectName = args.project

  confirm = raw_input("Are you sure you want to delete {0!r} and all of its associated files? (y/N) ".format(projectName))

  if (confirm.lower() == "y"):
    projectPath = "{0}/{1}".format(os.getcwd(), projectName)
    try:
      rmtree(projectPath)

    except OSError, e:
      printError("{0!r} cannot be deleted as it is not a project", projectName)
      return 6

    else:
      print "Deleting {0!r}...".format(projectPath)

  return 0



### Secondary methods ###

def makeNewPrjFile(args):
  """Make a new .prj info file"""
  projectName = args.project

  # Sort out default values
  try:
    projectDescription = args.descr[0]
  except TypeError, e:
    projectDescription = defaultDescription

  try:
    projectStatus = statDict[args.stat[0]]
  except TypeError, e:
    projectStatus = statDict[defaultStatus]

  # Sort out dates, too
  startDate = ''
  if (projectStatus != "proposed"):
    startDate = strftime("%d/%m/%Y")

  endDate = ''
  if (projectStatus == "completed"):
    endDate = strftime("%d/%m/%Y")

  project = {
    "name"        : projectName,
    "status"      : projectStatus,
    "description" : projectDescription,
    "start_date"  : startDate,
    "end_date"    : endDate
  }

  return setProjectInfo(project)


def getProjectInfo(projectName):
  """Get project info from a .prj file as a dictionary"""
  projectFile = "./{0}/.prj".format(projectName)
  project = {}

  try:
    with open(projectFile, 'r') as prj:
      project = yaml.load(prj)

  except IOError, e:
    return None

  else:
    return project


def setProjectInfo(project):
  """Set project info in a .prj file using a dictionary"""
  projectFile = "./{0}/.prj".format(project["name"])
  template = """name        : {name}
status      : {status}
description : {description}
start_date  : {start_date}
end_date    : {end_date}"""

  try:
    with open(projectFile, 'w') as prj:
      prj.write(template.format(**project))

  except IOError, e:
    return -1

  else:
    return 0


def printProjectInfo(project, printType):
  if (printType == "short"):
    info = """ - {name} ({status})"""

  elif (printType == "long"):

    if (project["status"] == "proposed"):
      info = """Project {name!r}: {description}
  Currently {status}"""

    elif (project["status"] == "complete"):
      info = """Project {name!r}: {description}
  {start_date} - {end_date}
  Currently {status}"""

    else: # active or inactive
      info = """Project {name!r}: {description}
  {start_date} - present
  Currently {status}"""
    
  else:
    printError("Unknown print type: {0!r}", printType)
    return 5

  print info.format(**project)


def makeParser():
  """Return the parser used to parse input arguments"""
  parser = argparse.ArgumentParser(
    description=(
      "%(prog)s, a project management program to create "
      "and update projects as they \nare needed."),
    epilog=(
      ""),
    formatter_class=argparse.RawDescriptionHelpFormatter)

  parser.add_argument("cmd",
    type=str,
    nargs=1,
    choices=["new", "stat", "list", "update", "delete"],
    metavar="COMMAND",
    help="command to give prj. Select from\n"
       "\tnew,\n"
       "\tstat,\n"
       "\tlist,\n"
       "\tupdate,\n"
       "\tdelete"
       ".")

  parser.add_argument("project",
    type=str,
    help="project name")

  parser.add_argument("-s", "--status",
    type=str,
    # default=defaultStatus,
    dest="stat",
    nargs=1,
    choices=statDict.keys(),
    metavar="STATUS",
    help="set status of project (only with new\n"
      "or update)")

  parser.add_argument("-d", "--description",
    type=str,
    # default=defaultDescription,
    dest="descr",
    nargs=1,
    metavar="DESC",
    help="set project description (only with new\n"
      "or update)")

  parser.add_argument("-v", "--verbose",
    action="count",
    default=0,
    dest="verbosity",
    help="specify level of verbosity")

  parser.add_argument("--version",
    action="version",
    version="%(prog)s v1.0")

  return parser

def printWarn(content, *args):
  callerName = sys._getframe(1).f_code.co_name
  print "{0}: warn: {1}".format(callerName, content.format(*args))

def printError(content, *args):
  callerName = sys._getframe(1).f_code.co_name
  print "{0}: error: {1}".format(callerName, content.format(*args))

def printVerbose(level, verbosity, content, *args):
  if (verbosity >= level):
    callerName = sys._getframe(1).f_code.co_name
    print "{0}: {1}".format(callerName, content.format(*args))

if __name__ == '__main__':
  sys.exit(main())