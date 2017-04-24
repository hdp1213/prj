#!/usr/bin/env python

# Project management script to use in ~/Documents/projects
# Harry Poulter
# 14/01/17 - created prj.py
#          - added new, stat, list, update and delete functions
#          - now v1.0
# 16/01/17 - renamed 'list' to 'info'
# 26/01/17 - added basic scheduler colour flag support
# 24/04/17 - added subparsers
#          - made project path specification more robust
#          - now v1.1

# TODO(harry): rip out guts and add objects

import sys
import os
from shutil import rmtree
import subprocess
import argparse
import yaml

from time import strftime

statDict = {'p': 'proposed',
            'a': 'active',
            'i': 'inactive',
            'c': 'complete'
}

defaultDescription = 'My Exciting Project!'
defaultStatus = 'a'

activeFields = ['name', 'status', 'description',
        'start_date', 'end_date', 'colour']

def main():
    """
    Main script
    """
    # Parse arguments
    parser = makeParser()
    args = parser.parse_args()

    # Make commands dictionary
    cmd = {'new': prj_new,
                'stat': prj_stat,
                'info': prj_info,
                'update': prj_update,
                'delete': prj_delete}

    # Convert project path to project name
    try:
        args.projectName = os.path.split(args.project.rstrip('/'))[1]

    except AttributeError as e:
        args.projectName = None

    return cmd[args.cmdID](args)

### Methods ###

def prj_new(args):
    """Create new project and initialise .prj file"""
    projectName = args.projectName
    projectDir = args.project

    # Create project directory
    try:
        print 'Creating project {!r}...'.format(projectName)
        os.mkdir(projectDir)

    except OSError:
        printError('{!r} already has a project directory', projectName)
        return 2

    # Initialise .prj file in directory
    return makeNewPrjFile(args)


def prj_stat(args):
    """Return the status of different projects"""
    projectName = args.projectName
    projectDir = args.project
    project = getProjectInfo(projectDir)

    if (project == None):
        printError('Project {!r} does not exist.', projectName)
        return 3

    print '{!r} is currently {}'.format(projectName, project['status'])

    return 0


def prj_info(args):
    """Return descriptions of different projects"""
    projectName = args.projectName
    projectDir = args.project

    # List all tracked projects
    if projectName is None:
        print 'All tracked projects in {}:'.format(os.getcwd())

        for projectDir in os.listdir('.'):
            project = getProjectInfo(projectDir)

            if project is None:
                continue

            printProjectInfo(project, 'short')

    # List detail on selected project
    else:
        project = getProjectInfo(projectDir)
        if (project == None):
            printError('Project {!r} does not exist.', projectName)
            return 4

        printProjectInfo(project, 'long')

    return 0

def prj_update(args):
    """Update project details"""
    projectName = args.projectName
    projectDir = args.project
    project = None

    try:
        projectDescription = args.descr[0]
    except TypeError:
        projectDescription = None

    try:
        projectStatus = statDict[args.stat[0]]
    except TypeError:
        projectStatus = None

    try:
        projectColour = args.colour[0]
    except TypeError:
        projectColour = None

    # Create a .prj file if there isn't one already
    while project is None:
        project = getProjectInfo(projectDir)

        stat = 0
        if project is None:
            stat = makeNewPrjFile(args)

        if (stat == -1):
            printError('Project {!r} does not exist.', projectName)
            return 7

    # Check that all categories exist in the project object
    # If not, set their default values
    for field in activeFields:
        try:
            test = project[field]

        # TODO(harry): make initialiseDefaults() a function
        # Be aware that makeNewPrjFile does its own thing here
        except KeyError:
            if (field == 'colour'):
                project[field] = '"-"'

    # Description has been updated
    if projectDescription is not None:
        project['description'] = projectDescription

    # Status has been updated
    if projectStatus is not None:
        project['status'] = projectStatus

        # Do date things again
        if (projectStatus == 'proposed'):
            project['start_date'] = ''

        if (projectStatus == 'active'):
            project['start_date'] = strftime('%d/%m/%Y')

        if (projectStatus == 'complete'):
            project['end_date'] = strftime('%d/%m/%Y')
        else:
            project['end_date'] = ''

    # Colour has been updated
    if projectColour is not None:
        project['colour'] = projectColour

    # Write project object back to .prj file
    return setProjectInfo(project)

def prj_delete(args):
    """Delete projects"""
    projectName = args.projectName
    projectDir = args.project

    confirm = raw_input('Are you sure you want to delete {!r} and all of its associated files? (y/N) '.format(projectName))

    if (confirm.lower() == 'y'):
        try:
            rmtree(projectDir)

        except OSError:
            printError('{!r} cannot be deleted as it is not a project', projectName)
            return 6

        else:
            print 'Deleting {!r}...'.format(projectDir)

    return 0



### Secondary methods ###

def makeNewPrjFile(args):
    """Make a new .prj info file"""
    projectName = args.projectName

    # Sort out default values
    try:
        projectDescription = args.descr[0]
    except TypeError:
        projectDescription = defaultDescription

    try:
        projectStatus = statDict[args.stat[0]]
    except TypeError:
        projectStatus = statDict[defaultStatus]

    try:
        projectColour = args.colour[0]
    except TypeError:
        projectColour = '"-"'

    # Sort out dates, too
    startDate = ''
    if (projectStatus != 'proposed'):
        startDate = strftime('%d/%m/%Y')

    endDate = ''
    if (projectStatus == 'completed'):
        endDate = strftime('%d/%m/%Y')

    project = {
        'name'        : projectName,
        'status'      : projectStatus,
        'description' : projectDescription,
        'start_date'  : startDate,
        'end_date'    : endDate,
        'colour'      : projectColour
    }

    return setProjectInfo(project)


def getProjectInfo(projectPath):
    """Get project info from a .prj file as a dictionary

    TODO(harry): fix assumption about location of project directory"""
    projectFile = './{0}/.prj'.format(projectPath)
    project = {}

    try:
        with open(projectFile, 'r') as prj:
            project = yaml.load(prj)

    except IOError:
        return None

    else:
        return project


def setProjectInfo(project):
    """Set project info in a .prj file using a dictionary

    Returns an exit code of -1 if there was an IOError."""
    projectFile = './{0}/.prj'.format(project['name'])
    template = """name        : {name}
status      : {status}
description : {description}
start_date  : {start_date}
end_date    : {end_date}
colour      : {colour}"""

    try:
        with open(projectFile, 'w') as prj:
            prj.write(template.format(**project))

    except IOError:
        return -1

    else:
        return 0


def printProjectInfo(project, printType):
    if (printType == 'short'):
        info = """ - {name} ({status}) (sch: {colour})"""

    elif (printType == 'long'):

        if (project['status'] == 'proposed'):
            info = """Project {name!r}: {description}
    Currently {status}
    scheduler colour flag: {colour}"""

        elif (project['status'] == 'complete'):
            info = """Project {name!r}: {description}
    {start_date} - {end_date}
    Currently {status}
    scheduler colour flag: {colour}"""

        else: # active or inactive
            info = """Project {name!r}: {description}
    {start_date} - present
    Currently {status}
    scheduler colour flag: {colour}"""
        
    else:
        printError('Unknown print type: {!r}', printType)
        return 5

    print info.format(**project)


def makeParser():
    """Return the parser used to parse input arguments"""
    parser_main = argparse.ArgumentParser(
        description=(
            '%(prog)s, a project management program to create '
            'and update projects as they \nare needed.'),
        epilog=(
            ""),
        formatter_class=argparse.RawDescriptionHelpFormatter)

    subparsers = parser_main.add_subparsers(
        dest='cmdID')


    parser_new = subparsers.add_parser('new', help='initialise new project')

    parser_new.add_argument('project',
        type=str,
        help='path to project')

    parser_new.add_argument('-s', '--status',
        type=str,
        dest='stat',
        nargs=1,
        choices=statDict.keys(),
        metavar='STATUS',
        help='set status of project')

    parser_new.add_argument('-d', '--description',
        type=str,
        dest='descr',
        nargs=1,
        metavar='DESC',
        help='set project description')

    parser_new.add_argument('-c', '--colour',
        type=str,
        dest='colour',
        nargs=1,
        metavar='COL',
        help='set project colour (used with scheduler)')


    parser_stat = subparsers.add_parser('stat', help='query the status of a project')

    parser_stat.add_argument('project',
        type=str,
        help='path to project')


    parser_info = subparsers.add_parser('info', help='get information about a project')

    parser_info.add_argument('project',
        type=str,
        nargs='?',
        help='path to project. leave blank to list all projects in current directory')


    parser_update = subparsers.add_parser('update', help='update project information')

    parser_update.add_argument('project',
        type=str,
        help='path to project')

    parser_update.add_argument('-s', '--status',
        type=str,
        dest='stat',
        nargs=1,
        choices=statDict.keys(),
        metavar='STATUS',
        help='set status of project')

    parser_update.add_argument('-d', '--description',
        type=str,
        dest='descr',
        nargs=1,
        metavar='DESC',
        help='set project description')

    parser_update.add_argument('-c', '--colour',
        type=str,
        dest='colour',
        nargs=1,
        metavar='COL',
        help='set project colour (used with scheduler)')


    parser_delete = subparsers.add_parser('delete', help='delete a project')

    parser_delete.add_argument('project',
        type=str,
        help='path to project')


    parser_main.add_argument('-v', '--verbose',
        action='count',
        default=0,
        dest='verbosity',
        help='specify level of verbosity')

    parser_main.add_argument('--version',
        action='version',
        version='%(prog)s v1.1')

    return parser_main

def printWarn(content, *args):
    callerName = sys._getframe(1).f_code.co_name.replace('_',' ')
    print('{}: warn: {}'.format(callerName, content.format(*args)))

def printError(content, *args):
    callerName = sys._getframe(1).f_code.co_name.replace('_',' ')
    print('{}: error: {}'.format(callerName, content.format(*args)))

def printVerbose(level, verbosity, content, *args):
    if (verbosity >= level):
        callerName = sys._getframe(1).f_code.co_name
        print('{}: {}'.format(callerName, content.format(*args)))

if __name__ == '__main__':
    exit(main())
