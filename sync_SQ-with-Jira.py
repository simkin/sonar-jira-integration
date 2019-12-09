#!/usr/bin/env python

import requests
from requests.auth import HTTPBasicAuth
import json
import yaml
import base64
import sys
import logger
from jira import JIRA

try:
    yaml_params = yaml.load(open('config.yaml', 'r', encoding="utf-8"), Loader=yaml.SafeLoader)
    sonar_user = yaml_params['sonar_user']
    sonar_pass = yaml_params['sonar_pass']
    sonar_base_url = yaml_params['sonar_base_url']
    sonar_project = yaml_params['sonar_project']
    sonar_branch = yaml_params['sonar_branch']
    jira_base_url = yaml_params['jira_base_url']
    sonar_issue_type = yaml_params['sonar_issue_type']
    jira_user = yaml_params['jira_user']
    jira_pass = yaml_params['jira_pass']
    jira_project = yaml_params['jira_project']

except Exception as e:
    logger.error(e)

debug_mode = True


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
        response = requests.get( sonar_base_url + '/api/issues/search?additionalFields=comments&types=' + sonar_issue_type + sonar_project + '&branch=' + sonar_branch + '&statuses=OPEN,REOPENED,CONFIRMED' )
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

        print('Response code SQ: ' + str(response.status_code))
        
    except Exception as e:
        logger(e)


def create_jira_issue(issue):
    try:
        jira = JIRA(server=jira_base_url, basic_auth=(jira_user, jira_pass))

        labels = issue['tags']
        comments = issue['comments']
        labels.extend([issue['project']])

        description = "Triggering rule:\n" + issue['message'] + "\nLink: """ + sonar_base_url + '/issues?issues=' + issue['key']

        if 'author' in issue.keys():
            description += "\nAuthor: """ + issue['author']    

        print('\n==================================\nCreating SQ issue ' + issue['key'] + ' in Jira')

        issue_dict = {
            "project": {'key': jira_project},
            "summary": "[SonarQube] - " + issue['component'],
            "description": description,
            "issuetype": {'name': 'Bug'},
            "priority" :  { 'value': get_prioridade(issue['severity']) },
            #"labels": labels
            "labels": {'SonarQube': 'static-code-analysis'},
            "customfield_12072": {"value":"Low"}
        }

        print(issue_dict) if debug_mode else 0
        new_issue = jira.create_issue(fields=issue_dict)
        print(u'Issue ' + str(new_issue) + ' created in Jira')
            
        return True

    except Exception as e:
        logger.error('Exception on create_jira_issue: '+ str(e) + '\n')
        return False


def get_prioridade(severidade):
    if severidade == 'MINOR':
        return 'Major (P2)'

    elif severidade == 'MAJOR':
        return 'Major (P2)'
        
    if severidade == 'CRITICAL':
        return 'Major (P2)'

    if severidade == 'BLOCKER':
        return 'Major (P2)'

    else:
        return 'Major (P2)'


if __name__ == '__main__':
    main()
