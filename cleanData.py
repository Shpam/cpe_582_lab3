# coding: utf-8

### Possible Message Keys ###

keys = ['X-GM-THRID', 'X-Gmail-Labels', 'Delivered-To', 'Received', 'X-Received', 'Return-Path', 'Received', 
'Received-SPF', 'Authentication-Results', 'DKIM-Signature', 'DomainKey-Signature', 'Received', 'Date', 
'From', 'Reply-To', 'To', 'Message-ID', 'Subject', 'MIME-Version', 'Content-Type', 'x-mid', 'x-job', 
'Feedback-ID', 'x-rpcampaign', 'x-orgId', 'List-Unsubscribe']


### Imports ###

import mailbox
import os
import re

### Functions ###

#Downloads the messages, stops recursing when it reaches html
def showPayload(msg):
    ret = ""
    ignore = ["<html", "<div", "<!DOCT", "<head"]
    stop = False
    
    payload = msg.get_payload()
    global nones
    
    if payload is not None:              
        if msg.is_multipart():
            for subMsg in payload:
                data, stop = showPayload(subMsg)
                
                if not stop:
                    ret += data
                else:
                    break
        else:
            if any(x in payload for x in ignore): #if this is the start of html bullshit, just stop parsing the message
                ret = ""
                stop = True
            return payload, stop
    else:
        nones += 1
        
    return ret, stop


#Dict[candidate_name] -> list of email dicts with keys: Body, From, Subject, Date, Candidates party
def get_cleaned_data():

    directory = os.getcwd() + "/Takeout/Mail"
    files = os.listdir(directory)

    candidate_dict = {}

    for candidate in files:
        mbox = mailbox.mbox(directory + "/" + candidate)

        candidate_name = candidate.split("-")[1][:-5]
        candidate_party = candidate.split("-")[0]
        messages = []

        for message in mbox:
            mini_dict = {}
            body, _ = showPayload(message)

            #This is where we add keys for the messages, so if some data is missing that you want add it here.
            mini_dict["body"] = body
            mini_dict["From"] = message["From"]
            mini_dict["Subject"] = message["Subject"]
            mini_dict["Date"] = message["Date"]
            mini_dict["Party"] = candidate_party

            messages.append(mini_dict)

        candidate_dict[candidate_name] = messages
    return candidate_dict
