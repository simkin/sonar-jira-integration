#!/usr/bin/env python

#
#        ███████╗ ██████╗      ██╗██╗██╗
#        ██╔════╝██╔═══██╗     ██║██║██║
#        ███████╗██║   ██║     ██║██║██║
#        ╚════██║██║   ██║██   ██║██║██║
#        ███████║╚██████╔╝╚█████╔╝██║██║
#        ╚══════╝ ╚═════╝  ╚════╝ ╚═╝╚═╝
#          Sonar - Jira Integration 


"""
    Autor: Leonardo Molina
    Script: Script de integração de issues do Sonar com Jira
"""

import requests
import yaml
import base64
import sys
import logger
from jira import JIRA

try:
    yaml_params = yaml.load(open('.\\config.yaml', 'r', encoding="utf-8"), Loader=yaml.SafeLoader)
    sonar_user = yaml_params['sonar_user']
    sonar_pass = yaml_params['sonar_pass']
    sonar_base_url = yaml_params['sonar_base_url']
    jira_base_url = yaml_params['jira_base_url']
    sonar_issue_type = yaml_params['sonar_issue_type']
    jira_user = yaml_params['jira_user']
    jira_pass = yaml_params['jira_pass']
    jira_project = yaml_params['jira_project']

except Exception as e:
    logger.error(e)

debug_mode = False


def main():
    global debug_mode

    for arg in sys.argv[1:]:
        if arg == '-d':
            debug_mode = True

    issues = get_sonar_issues()

    for issue in issues:
        try:
            if create_jira_issue(issue):
                assign_sonar_issue(issue['key'])
            pass

        except Exception as e:
            logger.error(e)


def get_sonar_issues():
    issues = []

    try:
        response = requests.get( sonar_base_url + '/api/issues/search?types=' + sonar_issue_type + '&statuses=OPEN,REOPENED,CONFIRMED&assigned=false' )
        data_json = response.json()
        
    except Exception as e:
        logger.error(e)

    for issue in data_json['issues']:

        if debug_mode:
            print('===========================================\nIssue ' + issue['key'] + ':\n')

            for key, val in issue.items():
                try:
                    print(key + ' : ' + val)

                except Exception as e:
                    print(key + ':')
                    print(val)
                    pass

        issues.append(issue)

    return issues


def assign_sonar_issue(issue):
    try:
        credentials = str(base64.b64encode(bytes(sonar_user + ":"  + sonar_pass, 'utf-8'))).replace('b\'','').replace('\'','')
        headers = { "Authorization": ('Basic ' + credentials) }
        response = requests.post( sonar_base_url + '/api/issues/assign?issue='+issue+'&assignee='+sonar_user, headers=headers )

        print('Codigo de assign da issue no Sonar: ' + str(response.status_code))
        
    except Exception as e:
        logger(e)


def create_jira_issue(issue):
    try:
        jira = JIRA(server=jira_base_url, basic_auth=(jira_user, jira_pass))

        labels = issue['tags']
        labels.extend([issue['project']])

        message = "Vulnerabilidade: " + issue['message'] + "\nLink: """ + sonar_base_url + '/issues?issues=' + issue['key']
    
        if 'project' in issue.keys():
            message += "\nProjeto: " + issue['project']

        if 'component' in issue.keys():
            message += "\nComponente: " + issue['component']

        if 'line' in issue.keys():
            message += "\nLinha: """ + str(issue['line'])

        if 'author' in issue.keys():
            message += "\nAutor: """ + issue['author']    

        print('\n==================================\nCriando issue do sonar ' + issue['key'] + ' no Jira')

        issue_dict = {
            "project": {'key': jira_project},
            "summary": "[Sonar] - " + issue['message'],
            "description": message,
            "issuetype": {'name': 'Vulnerabilidade'},
            "priority" :  { 'value': get_prioridade(issue['severity']) },
            "labels": labels
        }

        print(issue_dict) if debug_mode else 0
        new_issue = jira.create_issue(fields=issue_dict)
        print(u'Issue ' + str(new_issue) + ' criada no Jira')
            
        return True

    except Exception as e:
        logger.error('Exception on create_jira_issue: '+ str(e) + '\nEssa issue não foi criada')
        return False


def get_prioridade(severidade):
    if severidade == 'MINOR':
        return 'Trivial'

    elif severidade == 'MAJOR':
        return 'Major'
        
    if severidade == 'CRITICAL':
        return 'Critical'

    if severidade == 'BLOCKER':
        return 'Blocker'

    else:
        return 'Minor'


if __name__ == '__main__':
    main()