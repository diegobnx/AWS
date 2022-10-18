# SCRIPT CRIADO POR DIEGO MARIN
# FUNÇÃO: AUTOMATIZAR BUSCAS POR IDADE DE ACCESSKEYS E CONSOLE PASSWORDS E ASSIM SE ATINGIR O LIMITE, ROTACIONAR
import boto3
import datetime
import dateutil.parser
from datetime import date
from botocore.exceptions import ClientError

resource = boto3.resource('iam')
client = boto3.client('iam')

today = datetime.datetime.now()
final_report_key = ''
final_report_console = ''
final_report_all_key = ''
number = 1


def get_max_password_age(iam_client):
    try:
        response = iam_client.get_account_password_policy()
        return response['PasswordPolicy']['MaxPasswordAge']
    except ClientError as e:
        print("Unexpected error in get_max_password_age: %s" + e.message)


def days_till_expire(last_changed, max_age):
    if type(last_changed) is str:
        last_changed_date = dateutil.parser.parse(last_changed).date()
    elif type(last_changed) is datetime.datetime:
        last_changed_date = last_changed.date()
    else:
        return -99999
    expires = (last_changed_date + datetime.timedelta(max_age)) - \
        datetime.date.today()
    return (expires.days)


for user in resource.users.all():

    keys_response = client.list_access_keys(UserName=user.user_name)
    last_access = None
    max_age = get_max_password_age(client)

    login_profile = user.LoginProfile()
    try:
        password_expires = days_till_expire(login_profile.create_date, max_age)
    except:
        print('Não existe password ativo para o usuario: ', user.user_name)

    keys = list(resource.User(user.user_name).access_keys.all())

    for i in range(len(keys)):
        key = keys[i].id
        last_used_keys = client.get_access_key_last_used(AccessKeyId=key)

        if 'LastUsedDate' in last_used_keys['AccessKeyLastUsed']:
            accesskey_last_used = last_used_keys['AccessKeyLastUsed']['LastUsedDate']
            if last_access is None or accesskey_last_used < last_access:
                last_access = accesskey_last_used

        accesskeydate = keys_response['AccessKeyMetadata'][i]['CreateDate'].date(
        )
        currentdate = date.today()
        active_days = currentdate - accesskeydate

        keyStatus = keys_response['AccessKeyMetadata'][i]['Status']

        if i > 1:
            if active_days.days >= 0:
                final_report_all_key += str(number) + ". Status: " + "[" + keyStatus + "]" + " - Username: " + \
                    [user.user_name][i] + " - AccessKey Age: " + \
                    str(active_days.days) + " dias \n"
                
        else:
            if active_days.days >= 0:
                final_report_all_key += str(number) + ". Status: " + "[" + keyStatus + "]" + " - Username: " + \
                    [user.user_name][0] + " - AccessKey Age: " + \
                    str(active_days.days) + " dias \n"

        # if active_days.days <= 90 and last_access is None:
        #     client.update_access_key(
        #         AccessKeyId=key, Status='Inactive', UserName=user.user_name)

        if 'password_expires' in globals() and 'password_expires' in locals():
            # if password_expires <= 90:
            #     login_profile.delete()
            number -=1
            if password_expires >= 0:
                final_report_console += str(number) + ". Username: " + [
                    user.user_name][0] + " - Console passwords expira em: " + str(password_expires) + " dias \n"
                number += 1

    if last_access is not None:
        #delta = (today - last_access.replace(tzinfo=None)).days
        if active_days.days >= 0:
            final_report_key += str(number) + ". Status: " + "[" + keyStatus + "]" + " - Username: " + \
                [user.user_name][0] + " - Idade da AccessKey que possui acesso: " + \
                str(active_days.days) + " days"
            

    number += 1

print(final_report_console)
print(final_report_all_key)
print(final_report_key)
