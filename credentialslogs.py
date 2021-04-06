#!/usr/bin/env python

import os
import subprocess
import json
import boto3
import requests
import time
import logging

jenkins_master = "localhost:8080"
LOGGER = None

class CloudwatchLogHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)

    def emit(self, record):
        pass

def BuildLog():
    log = logging.getLogger('logger')
    log.setLevel(logging.DEBUG)

    # TODO: NM/NF:  When doing the status digest,  we will need a total rework of the logger

    debugLogHandler = logging.StreamHandler()
    debugLogHandler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    debugLogHandler.setFormatter(formatter)
    log.addHandler(debugLogHandler)

    errorDB = CloudwatchLogHandler()
    errorDB.setLevel(logging.CRITICAL)
    errorDB.setFormatter(formatter)
    log.addHandler(errorDB)
    
    infoDB = CloudwatchLogHandler()
    infoDB.setLevel(logging.INFO)
    infoDB.setFormatter(formatter)
    log.addHandler(infoDB)
    
    return log

class SNSLogHandler(logging.Handler):
    def __init__(self, topic, subject):
        logging.Handler.__init__(self)
        self._SNS = SNSWrapper('us-east-1')
        self._Topic = topic
        self._Subject = subject

    def emit(self, record):
        msg = record.message
        self._SNS.SendMessage(self._Topic, self._Subject, msg)

class CloudwatchLogHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)

    def emit(self, record):
        pass

def GetAwsSecrets(key):
    """Get the credentials from secrets manager"""
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name='us-east-1'
    )

    secret_string = client.get_secret_value(SecretId=key)
    return secret_string

def GenerateCrumbandToken():
    """ Create Crumb and token for Jenkins api authentication """

    isSuccessful = False
    output = None
    while not isSuccessful:
        try:
            LOGGER.info("Calling Jenkins API")
            output = subprocess.check_output("curl http://"+jenkins_master+"/crumbIssuer/api/xml?xpath=concat\(//crumbRequestField,%22:%22,//crumb\) \
            -c cookies.txt \
            --user 'admin:admin'", shell=True,stderr= subprocess.STDOUT)

            if output:
                output=str(output.decode('utf-8'))
                LOGGER.info(output)
                isSuccessful = True
        except Exception as ex:
            LOGGER.info(ex)
            LOGGER.info("Connection Refused,  Trying again in 30 seconds")
            time.sleep(30)

    LOGGER.info("Connection Established")
    

    LOGGER.info("    Output: {}".format(output))

    crumb=output.splitlines()

    output = crumb[-1:]

    listToStr = ' '.join(map(str, output))

    cmd = "curl -H "+listToStr+" 'http://"+jenkins_master+"/user/admin/descriptorByName/jenkins.security.ApiTokenProperty/generateNewToken' \
    --data 'newTokenName=kb-token' \
    --user 'admin:admin' \
    -b cookies.txt"

    data = subprocess.check_output(cmd,shell=True)


    token = json.loads(data.decode('utf-8'))

    
    data = {'token':token['data']['tokenValue'],'crumb':listToStr}

    return data


def GenerateSecrets(data,secrets_data):
    if 'Username' in secrets_data['SecretString']:

        secretData = json.loads(secrets_data['SecretString'])

        jsonData = {"": "0","credentials": {"scope": "GLOBAL","id": secrets_data["Name"],"username": secretData["Username"],"password": secretData["Password"],"description": secrets_data["Name"],"$class": "com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl"}}

        cmd= "curl -H "+data['crumb']+" -X POST 'http://admin:"+data['token']+"@"+jenkins_master+"/credentials/store/system/domain/_/createCredentials' --data-urlencode 'json="+json.dumps(jsonData)+"'"

    elif 'Username' not in secrets_data['SecretString']:

        jsonData = {"": "0","credentials": {"scope": "GLOBAL","id": secrets_data["Name"],"secret":secrets_data['SecretString'],"description": secrets_data["Name"],"$class": "org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl"}}

        cmd= "curl -H "+data['crumb']+" -X POST 'http://admin:"+data['token']+"@"+jenkins_master+"/credentials/store/system/domain/_/createCredentials' --data-urlencode 'json="+json.dumps(jsonData)+"'"

    Secrets = subprocess.check_output(str(cmd),shell=True)



if __name__== "__main__":
    LOGGER = BuildLog()
    LOGGER.info(os.getenv("JENKINS_HOME"))
    LOGGER.info(os.listdir(os.path.join(os.getenv("JENKINS_HOME"), "secrets")))
    with open(os.path.join(os.getenv("JENKINS_HOME"), "secrets", "master.key")) as f:
        data = f.read()

    LOGGER.info(data)
    
    try:
        LOGGER.info("Starting Credentials Checkin Process")

        dictOfSecrtes = {"Jenkins-Jira":"jira-cred","slack-jenkins-secret-text":"slack-cred","Bitbucket":"bitbucket-cred"}
        data = GenerateCrumbandToken()
        for key in dictOfSecrtes:
            secrets_data = GetAwsSecrets(key)   # Getting Secrets from Secrets manager
            GenerateSecrets(data,secrets_data)  # Adding credentials in Jenkins store
            LOGGER.info("Successfully added secrets in Jenkins store:"+key+"")           
    except Exception as ex:
        print(ex)
        raise
