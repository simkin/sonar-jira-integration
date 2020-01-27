#!/usr/bin/env python

# Work in progress

import requests
from requests.auth import HTTPBasicAuth
import json
import yaml
import base64
import sys
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
    sonar_base_url = sonar_base_url.replace('//', f'//{sonar_user}:{sonar_pass}@')


def main():

    issues = get_sonar_issues()
    return


def get_jira_link_in_comments(comments):
    for comment in comments:
        if jira_base_url in comment['markdown']:
            text = comment['markdown']
            lines = text.split()
            for line in lines:
                if line.startswith(jira_base_url):
                    return line
    return False

def get_sonar_issues():
    issues = []

    try:
        credentials = str(base64.b64encode(bytes(sonar_user + ":"  + sonar_pass, 'utf-8'))).replace('b\'','').replace('\'','')
        headers = { "Authorization": ('Basic ' + credentials) }
        response = requests.get( sonar_base_url + '/api/issues/search?additionalFields=comments&types=' + sonar_issue_type + '&project=' + sonar_project + '&branch=' + sonar_branch + '&statuses=OPEN,REOPENED,CONFIRMED' )
        print("XXX")
        data_json = response.json()
    except Exception as e:
        print(e)

    for issue in data_json['issues']:
        jira_link = get_jira_link_in_comments(issue['comments'])
        print(issue['key'], jira_link if jira_link else 'to be created', issue['status'])
        if jira_link:
            # TODO / cleanup: check if the link
            pass
        else:
            # TODO/ create a ticket in JIRA
            pass
        issues.append(issue)

    return issues


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
        print('Exception on create_jira_issue: '+ str(e) + '\n')
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
