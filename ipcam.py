import sys
import time
import subprocess
import telepot

"""
$ python3.2 ipcam.py <token> <user_id>

Use Telegram as a DDNS service, making an IP cam accessible over the internet.

Accept two commands:
/open: open a port through the router to the video stream, and send the URL
/close: close the external port

Only intended to be used by one person, indicated by the <user_id> argument
on the command-line.
"""

cs = '/home/pi/TelePi/scripts/cs'
pf = '/home/pi/TelePi/scripts/pf'
ipaddr = '/home/pi/TelePi/scripts/ipaddr'

EXTERNAL_PORT = 54321
INTERNAL_PORT = 8080  # mjpg_streamer default

def handle(msg):
    global pf, ipaddr

    content_type, chat_type, chat_id = telepot.glance(msg)

    if content_type != 'text':
        print('Invalid %s message from %d' % (content_type, chat_id))
        return

    if chat_id != USER_ID:
        print('Unauthorized user: %d' % chat_id)
        return

    command = msg['text'].strip().lower()

    if command == '/open':

        # Start streaming
        subprocess.call([cs, 'start'])

        time.sleep(1)

        # check streaming is working
        out = subprocess.check_output([cs, 'status']).strip()

        if out == b'Stopped':
            bot.message(chat_id, 'Unable to start camera stream')
            
        else:
            
            # port forward
            subprocess.call([pf, str(EXTERNAL_PORT), str(INTERNAL_PORT)])

            # extract IP addresses
            out = subprocess.check_output([ipaddr])

            # Output:
            # Internal=zzz.zzz.zzz.zzz
            # External=zzz.zzz.zzz.zzz
            # Public=zzz.zzz.zzz.zzz
            ip = dict([line.split('=') for line in out.decode('ascii').strip().split('\n')])

            reply = 'http://%s:%d/?action=stream' % (ip['External'], EXTERNAL_PORT)

            if ip['External'] != ip['Public']:
                reply += '\nmay not be accessible from outside'

            bot.sendMessage(chat_id, reply)

    elif command == '/close':
        # delete port forward
        subprocess.call([pf, 'delete', str(EXTERNAL_PORT)])

        # stop streaming
        subprocess.call([cs, 'stop'])

        bot.sendMessage(chat_id, 'Port closed and streaming stopped')
        
    elif command == '/snap':

        # check streaming is running
        out = subprocess.check_output([cs, 'status']).strip()

        if out == b'Stopped':
            # all good to take a photo

            date = subprocess.check_output(['date', '+%Y_%m_%d__%H_%M_%S']).decode().strip()

            # take the picture
            subprocess.call(['/home/pi/bin/takepic', date])

            # tell the user something is happening
            bot.sendChatAction(chat_id, 'upload_photo')

            # send the photo
            bot.sendPhoto(chat_id, open(('/home/pi/Pictures/' + date + '.jpg'), 'rb'))

        else:
            bot.sendMessage(chat_id, 'Cannot take a picture whilst streaming')
            
    elif command == '/ping':
        bot.sendMessage(chat_id, 'pong')

    elif command == '/ssh':
        
        # port forward
        subprocess.call([pf, str(54322), str(22)])

        # extract IP addresses
        out = subprocess.check_output([ipaddr])

        # Output:
        # Internal=zzz.zzz.zzz.zzz
        # External=zzz.zzz.zzz.zzz
        # Public=zzz.zzz.zzz.zzz
        ip = dict([line.split('=') for line in out.decode('ascii').strip().split('\n')])

        reply = 'ssh://%s:%d' % (ip['External'], 54322)

        if ip['External'] != ip['Public']:
            reply += '\nmay not be accessible from outside'

        bot.sendMessage(chat_id, reply)

    elif command == '/sshclose':
        # delete port forward
        subprocess.call([pf, 'delete', str(54322)])

        bot.sendMessage(chat_id, 'Port closed')
        
    else:
        bot.sendMessage(chat_id, "I don't understand")


TOKEN = sys.argv[1]
USER_ID = int(sys.argv[2])  # only one user is allowed

## Start streaming
#subprocess.call([cs, 'start'])

bot = telepot.Bot(TOKEN)
bot.message_loop(handle)
print('Listening ...')

while 1:
    time.sleep(10)
