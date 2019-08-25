
##########################################################################
#
#   Fitbit
#
#   https://dev.fitbit.com/build/reference/
#
#   API Explorer: https://dev.fitbit.com/build/reference/web-api/explore/
#
##########################################################################

import datetime
import requests
import base64
import json
import numpy

'''
Example of config.json file...

{
    "access_token": "aaaaabbbbbcccccxxxxxxyyyyyyyzzzzzzz",
    "client_id": "123AB",
    "client_secret": "abcxyz",
    "code": "0123456789",
    "expires_in": "2019-07-17 17:42:51",
    "redirect_uri": "http://www.google.com",
    "refresh_token": "zyxcda",
    "scope": "sleep profile activity heartrate nutrition weight location social settings"
}
'''

##########################################################################
#
#   Functions
#
##########################################################################


def load_config( config_file='config.json' ):
    try:
        file   = open( config_file, 'r' )
        config = json.loads( file.read() )
        file.close()
        return config
    except Exception as e:
        print('[ EXCEPTION ] {}'.format(e))


def save_config( config, config_file='config.json' ):
    file = open( config_file, 'w' )
    file.write( json.dumps(config, sort_keys=True, indent=4) )
    file.close()


def fitbit_auth_get_code( config ):
    '''
        Step #1 - Prompt user to sign-in and get a "code"
        
        This needs to be ran once. The output of this func is a "code"
        which can be exchanged for an access token and refresh token.
        
        Those tokens can then be used by the rest of the code to make
        automated APIs call.
        
        Reference:
        https://dev.fitbit.com/build/reference/web-api/oauth2/#authorization-code-grant-flow
    '''
    
    req = requests.get('https://www.fitbit.com/oauth2/authorize?response_type=code&client_id={}&redirect_uri={}&scope=activity%20nutrition%20heartrate%20location%20nutrition%20profile%20settings%20sleep%20social%20weight'.format( config['client_id'], config['redirect_uri'] ))
    print('\nGo to this URL, sign-in, then get the "code":\n{}'.format( req.url ))
    response_url = input('\n\nOnce you sign-in to Fitbit, paste the response URL here:  ')
    code = response_url.split('code=')[-1].replace('#_=_','')
    return code


def fitbit_auth_get_token( config ):
    '''
        Step #2 - Get Token (using the code from step #1)
        
        Reference:
        https://dev.fitbit.com/build/reference/web-api/oauth2/#authorization-code-grant-flow
    '''
    auth_id  = base64.b64encode('{}:{}'.format( config['client_id'], config['client_secret'] ).encode('utf-8'))
    headers  = {"Content-Type":"application/x-www-form-urlencoded", "Authorization": b"Basic "+auth_id }
    code     = config['code'].replace('#_=_','')
    payload  = { "client_id":config['client_id'], "grant_type":"authorization_code", "redirect_uri":config['redirect_uri'], "code":config['code'] }
    base_url = 'https://api.fitbit.com/oauth2/token'
    
    req = requests.post( base_url, headers=headers, data=payload )
    
    if req.status_code == 200:
        json_response = json.loads(req.content)
        config['access_token']  = json_response['access_token']
        config['refresh_token'] = json_response['refresh_token']
        config['expires_in']    = (datetime.datetime.now() + datetime.timedelta(seconds=json_response['expires_in'])).strftime('%Y-%m-%d %H:%M:%S')
        config['scope']         = json_response['scope']
        return config
    else:
        print('[ WARNING ] Status Code: {}'.format( req.status_code ))


def fitbit_auth_step3_refresh_token( config ):
    '''
        Step #3 - Refresh token using the "refresh_token" (which comes from step #2)
        
        Reference:
        https://dev.fitbit.com/build/reference/web-api/oauth2/#authorization-code-grant-flow
    '''
    auth_id  = base64.b64encode('{}:{}'.format( config['client_id'], config['client_secret'] ).encode('utf-8'))
    headers  = { "Content-Type":"application/x-www-form-urlencoded", "Authorization": b"Basic "+auth_id }
    payload  = { "grant_type":"refresh_token", "refresh_token":config['refresh_token'] }
    base_url = 'https://api.fitbit.com/oauth2/token'
    
    req = requests.post( base_url, headers=headers, data=payload )
    
    if req.status_code==200:
        json_response = json.loads(req.content)
        config['access_token']  = json_response['access_token']
        config['refresh_token'] = json_response['refresh_token']
        config['expires_in']    = (datetime.datetime.now() + datetime.timedelta(seconds=json_response['expires_in'])).strftime('%Y-%m-%d %H:%M:%S')
        config['scope']         = json_response['scope']
        return config
    else:
        print('[ WARNING ] Status Code: {}'.format( req.status_code ))



def fitbit_get_heartrate( config, start_date='2019-07-13' ):
    '''
        Reference:
        https://dev.fitbit.com/build/reference/web-api/heart-rate/
    '''
    headers  = { "Content-Type":"application/x-www-form-urlencoded", "Authorization": "Bearer "+config['access_token'] }
    #base_url= 'https://api.fitbit.com/1/user/-/activities/heart/date/[date]/[end-date]/[detail-level].json'
    #base_url= 'https://api.fitbit.com/1/user/-/activities/heart/date/2019-07-01/2019-07-13/1min.json'
    #base_url = 'https://api.fitbit.com/1/user/-/activities/heart/date/today/2019-07-14/1min.json'
    base_url = 'https://api.fitbit.com/1/user/-/activities/heart/date/{}/1d.json'.format(start_date) # Working
    
    req = requests.get( base_url, headers=headers )
    
    if req.status_code == 200:
        
        heartrate_json = json.loads(req.content)
        
        heartrate_list = [ record['value'] for record in heartrate_json['activities-heart-intraday']['dataset'] ]
        
        print('Max HR:    {}'.format( max(heartrate_list) ))
        print('Min HR:    {}'.format( min(heartrate_list) ))
        print('Median HR: {}'.format( round(numpy.median(heartrate_list),2) ))
        print('Avg HR:    {}'.format( round(numpy.average(heartrate_list),2) ))
        print('Std HR:    {}'.format( round(numpy.std(heartrate_list),2) ))
        
        return heartrate_list, heartrate_json
    else:
        print('[ INFO ] Status Code: {}'.format( req.status_code ))


def display_hr_hist( heartrate_list ):
    '''
        This function will generate and display
        a historgram, which graphs the heartrate
        distribution
        
        heartrate_list is a list of heartrates (i.e. [65, 66, 78, 75, 65, 62] )
    '''
    hr_hist = dict([ (i,0) for i in range(30,200) ])
    for measurement in heartrate_list:
        if measurement not in hr_hist:
            hr_hist[measurement] = 1
        else:
            hr_hist[measurement] += 1
    
    hr_hist_sorted = [ (k,hr_hist[k]) for k in sorted(hr_hist) ]
    for measurement in hr_hist_sorted:
        print('{}\t{}'.format( measurement[0], '*'*measurement[1] ))



def display_hr_hist_by_time( heartrate_json ):
    
for record in heartrate_json['activities-heart-intraday']['dataset']:
    print('{}\t{}\t{}'.format(record['time'], record['value'], int(record['value']/2)*'*'))


def detect_outliers( heartrate_json )
    
    heartrate_list = [ record['value'] for record in heartrate_json['activities-heart-intraday']['dataset'] ]
    
    std_dev    = numpy.std(heartrate_list)
    lower_band = numpy.median(heartrate_list) - 3*std_dev
    upper_band = numpy.median(heartrate_list) + 3*std_dev
    outlier_hr = [ record for record in json_response['activities-heart-intraday']['dataset'] if record['value']<lower_band or record['value']>upper_band ]
    print('[ INFO ] Showing Outliers...')
    for outlier in outlier_hr:
        print(outlier)



##########################################################################
#
#   Main
#
##########################################################################


config = load_config( config_file='config.json' )


token_valid = True if datetime.datetime.strptime(config['expires_in'], '%Y-%m-%d %H:%M:%S') > datetime.datetime.now() else False


if not token_valid:
    
    try:
        # Try to refresh token
        config = fitbit_auth_step3_refresh_token( config )
        save_config( config, config_file='config.json' )
    except:
        # If token refresh does not work, then prompt user to login and get a new token/refresh token.
        config['code'] = fitbit_auth_get_code( config )
        config = fitbit_auth_get_token( config )
        save_config( config, config_file='config.json' )
    
    token_valid = True if datetime.datetime.strptime(config['expires_in'], '%Y-%m-%d %H:%M:%S') > datetime.datetime.now() else False


if token_valid:
    
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    
    heartrate_list, heartrate_json = fitbit_get_heartrate( config, start_date=date_str )
    
    display_hr_hist( heartrate_list )





#ZEND
