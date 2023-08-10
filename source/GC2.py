import requests
import logging 
from os import getenv 
import re
Host=getenv('GitlabHost')
Token=getenv('Token')
Dryrun=bool(getenv('DryRun'))

keep_blocked=[]
All_blocked_users=[]

payload={}
headers={'Authorization':Token}

def delete_duplicates(List):
    New_list=[]
    for i in range(len(List)):
        if List[i] not in List[i + 1:]:
            New_list.append(List[i])
    return New_list

log_file='GC2.log'
log=logging.basicConfig(filename=log_file, filemode='a', format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%m-%y %H:%M:%S',level=logging.INFO)

#check that the env variables are not empty
if not Token :
    log
    logging.warning('No Token is currently available!')
    exit()
elif not Host:
    log
    logging.warning('No Host detected')
elif not Dryrun:
    log
    logging.warning('Dry run not specified. Assuming False')
    Dryrun = False

URL="https://{}/api/v4/users?blocked=true&per_page=100".format(Host)
log
logging.info('Sending a request to get all blocked users')

response = requests.request("GET", URL, headers=headers, data=payload)
total_pages=response.headers['X-Total-Pages']

log
logging.info('Sending a request to get the total number of pages')
logging.warning('that is the number of pages {total_pages}'.format(total_pages=total_pages))
logging.info('Looping through the pages')
# getting 100 users per page and loop through each user 
for x in range(1,(int(total_pages )+1)):

    params = {'page': x}
    response = requests.get(URL,
            params=params,headers=headers)
    body=response.json()
     # step 3: get the groups/projects the blocked user is part of 
    for user in body:
        All_blocked_users.append(user)
        ID=user['id']
        id=str(ID)
        url='https://{}/api/v4/users/{}/memberships'.format(Host,id)
        contr = requests.get(url,headers=headers)
        contribution=contr.json()

        if len(contribution)!=0:
         for c in contribution:
            # check if the user is part of a group 
            if (c['source_type']=='Namespace'):
                url="https://{}/api/v4/groups/{}/members".format(Host,c['source_id'])
                response = requests.request("GET", url, headers=headers)
                members=response.json()

                # check if more than one user is part of that group 
                if len(members) >1:
                    for m in members:
                        if m['state']=='active':
                            # the user blocked cannot be deleted therefore add to the keep blocked list
                            keep_blocked.append(user)
                            break
                    
                else:
                    # the group only has one member
                    pass
            elif (c['source_type']=='Project'):

                # get the members of the project 
                U="https://{}/api/v4/projects/{}/members".format(Host,c['source_id'])
                response = requests.request("GET", U, headers=headers)
                projmem=response.json()
                #check for the email of the user if staff the visibility of the project needs to be checked
                
                    
                for m in projmem:
                    if m['state']=='active':
                        #add to list of users to keep blocked
                        keep_blocked.append(user)
                        break
                
            else:
                pass
        
                
        else:
            pass

log
logging.info('Checked all blocked users memeberships as well as checked the projects members state')
#logging.info('here is the list of kept blocked uers {}'.format(keep_blocked))
# get rid of all duplicates in the keep blocked list 

KEEP_blocked=delete_duplicates(keep_blocked)
All=len(All_blocked_users)
log
logging.warning('The total number of blocked users is :{All}'.format(All=All))

#grab the list of all blocked users compare it to the to_be_kept_blocked
# compare KEEP blocked and ALL 
# for user in All if it's not in keep then delete 

Newdelete = [i for i in All_blocked_users if i not in KEEP_blocked]
dele=len(Newdelete)
log
logging.info('Getting a list of users to delete')
logging.warning('The total number of users to delete :{dele}'.format(dele=dele))
logging.info('Last check to make sure staff accounts with a public project are not deleted')
# check if the users to delete are employee 
for user in Newdelete:
    if (re.findall("@companyName.uk$", user['email'])):
        id=str(user['id'])
        #it's a staff a member check if they have a public project 
        Url='https://{}/api/v4/users/{}/projects'.format(Host,id)
        API_response = requests.get(Url, headers=headers)   
        prj=API_response.json()
        if (len(prj)>0):
            for p in prj:
                if (p['visibility']!='private'):
                    
                    # need to remove this user from the delete list 
                    Newdelete.remove(user)
                    break
                else:
                    pass
        else:
            pass

latest=len(Newdelete)
log
logging.warning('The total number of users to delete after the staff check :{latest}'.format(latest=latest))

# last step delete all users on Newdelete. 
if (len(Newdelete)!=0):
    for user in Newdelete:
        id=str(user['id'])
        un=str(user['email'])
        url='https://{}/api/v4/users/{}'.format(Host,id)
        
        log
        logging.warning('ID of user to delete {un}'.format(un=un))
        if Dryrun:
            log
            logging.info('Dry Run mode, no action will be taken')
        else:
            RESPONSE = requests.delete(url,headers=headers)
            logging.info('check if the response returns a 204 status if so the deletion was a success')
            logging.info('the response:{RESPONSE}'.format(RESPONSE=RESPONSE))
            try:
                RE=RESPONSE.json()
                
                if (RE['message'] == 'User cannot be removed while is the sole-owner of a group'):
                    url='https://{}/api/v4/users/{}?hard_delete=True'.format(Host,id)
                    DEL= requests.delete(url,headers=headers)
                    log
                    logging.info('the response {DEL}'.format(DEL=DEL))
            except:
                log
                logging.info('a soft deletion was performed')

           
       
else:
    log
    logging.info('No user to delete')

logging.info('end of script')
