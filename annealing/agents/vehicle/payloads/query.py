# Query Payload
#
# The query payload manages the query protocol for the vehicle
#
#
import os, glob, random, string, hashlib, stat, logging, sys
from vehicle.payloads import payload, image, log

def expanduser(path):
    user = os.getenv("SUDO_USER") or os.getenv("USER")
    home = pwd.getpwnam(user).pw_dir
    return path.replace("~", home, 1)

ACTION_FETCH = 0
ACTION_QUERY = 1
ACTION_METADATA = 2
ACTION_REQTOKEN = 3 
ACTION_INFECT = 4
ACTION_PEEK = 5
ACTION_LOG = 6
ACTION_POKE = 7

action_desc = {
    ACTION_FETCH: "fetch",
    ACTION_REQTOKEN: "request",
    ACTION_QUERY: "query",
    ACTION_METADATA: "metadata",
    ACTION_INFECT: "infect",
    ACTION_PEEK: "peek",
    ACTION_POKE: "poke",
    ACTION_LOG: "log",
}

actions = action_desc.keys()


class QMsg:
    def __init__(self, action, user, parm):
        self.action = action
        self.user = user
        self.parm = parm
        
    def gen_msg(self):
        return f"{self.action}:{self.user}:{self.parm}"

    def read_msg(self, msg): # Should error catch but it'll be fine
        print('msg was ', msg)
        parms = msg.split(':')
        self.action = int(parms[0])
        self.user = parms[1]
        self.parm = ':'.join(parms[2:])
        
    def gen_msgtoken(user_name, user_secret, server_token):
        """
        Generates a message token from the user's internal secret
        and the server's token.
        """
        signature = hashlib.md5((server_token + user_secret).encode('UTF-8')).hexdigest()

        return f"{user_name}:{server_token}:{signature}"

    def __repr__(self):
        return "Action: {}({}), User: {}, Parm: {}".format(self.action, action_desc[self.action], self.user, self.parm)


class QueryPayload(payload.Payload):
    #
    #
    # This section covers the execution actions, which implement the various
    # verbs of the vehicle -- token allocation, file capture, file metadata,
    # infection, memory requests, and log data. 
    def __init__(self, kf_n, image_payload, transfer_dir, is_vul, log, clock, memory):
        self.image = image_payload
        self.clock = clock
        self.log = log
        self.mem = memory
        self.fetch_count = 0 
        # Set to true if the system is -not- vulnerable to replay
        self.is_vul = is_vul
        # contains the names of the users and their associated private keys
        self.keydata = {}
        # The name of the file containing the above information
        self.kf_n = kf_n
        # Counts the number of times a request has been validated.
        # If the value is nonzero then a protocol which is not
        # replay-vulnerable will reject the transaction
        self.vtable = {}
        self.transfer_dir = os.path.expanduser(transfer_dir)

        if not os.path.exists(self.transfer_dir):
            os.mkdir(self.transfer_dir)

        self.load_keyfile()


    def load_keyfile(self):
        """
        load_keyfile

        Loads up a keyfile containing a bunch of private keys for
        various users.  Returns the number of users processed

        """
        if not os.path.exists(self.kf_n):
            return len(self.keydata)

        with open(self.kf_n, 'r') as kf:
            for i in kf.readlines():
                n, _, v = i[:-1].partition(',')
                self.keydata[n] = v

        return len(self.keydata) 


    def execute(self, msg):
        """
        Executes the contents of the message
        """
        result = None

        logging.info(f'Message {msg} received')
        self.log.log(f'execution: {msg}')
        print('Msg action is ', msg.action)

        if msg.action == ACTION_FETCH:
            result = self.exec_fetch(msg)
        elif msg.action == ACTION_REQTOKEN:
            result = self.exec_reqtoken(msg.user, msg.parm)
        elif msg.action == ACTION_QUERY:
            result = self.exec_query(msg)
        elif msg.action == ACTION_METADATA:
            result = self.exec_metadata(msg.user, msg.parm)
        elif msg.action == ACTION_LOG:
            result = self.exec_log(msg)
        elif msg.action == ACTION_PEEK:
            result = self.exec_peek(msg)
        else:
            logging.error('Invalid action {}'.format(msg.action))

        print('result is ', result)

        return result

    def exec_query(self, msg):
        """
        exec_query
        Verifies whether or not an image exists.
        image_name -- the image name, may contain wildcards
        token -- a verification token.  Whether the token is used is determined by the is_vul
        configuration variable in init.
        """
        # user = msg.user
        image_name = msg.parm

        qr = self.image.find_image(image_name)

        return ':'.join(qr)


    def exec_fetch(self, msg):
        logging.debug(f'Executing fetch with received message {msg}')

        token = msg.parm
        image_name = msg.user

        if not self.validate_token(token):            
            return '' # Terminate on error 

        logging.debug('Signatures match, continuing')
        sys.stdout.write('Checking image name\n')
        sys.stdout.write(f'Image name is {image_name}\n')

        image_fn = self.image.get_full_path(image_name)

        result = None
        with open(image_fn, 'r') as image_fh:
            result = image_fh.read()

        self.fetch_count += 1

        fstr = f'{self.fetch_count:08}'

        self.mem.poke('files', fstr)

        return result


    def exec_log(self, msg):
        logging.info('Filling out log request') 

        user = msg.user
        kw, ml = msg.parm.split(':')[0:2]

        result = self.log.fetch_logs(kw, int(ml))

        logging.debug(f'Log data length: {len(result)}')

        return result


    def exec_infect(self, msg):
        """
        exec_infect:
        msg -- the QMSg object in question
        infection doesn't affect anything except to flip on an 'infected' flag, which
        will then impact operations.
        """
        self.infected = True
        return 'infected'


    def exec_peek(self, msg):
        """
        exec_peek:
        msg -- the QMsg object with the peek request
        will return a block of memory starting at the address specified and going until
        the length specified.
        """
        ploc, _, plen = msg.parm.partition(':')

        logging.info(f'Executing peek with location {ploc} and length {plen}')

        result = self.mem.peek(ploc, plen)

        logging.info(f'Memory content is {result}')

        return result


    def exec_poke(self, msg):
        """
        exec_poke:
        msg -- the QMsg object with the poke request
        will change a blokc of memory.
        Returns the length of the modified block.
        """
        return
    

    def exec_metadata(self, user, image_name):
        """
        exec_medata
        returns metadata information -- file name, time of creation, file size, accesses
        """
        newmsg = QMsg('ACTION_QUERY','',image_name)

        images = self.exec_query(newmsg)
        if len(images) == 0:
            return False # Terminate on missing file

        source_image = images.split(':')[0]

        img_path = self.image.get_full_path(source_image)
        stats = os.stat(img_path)

        # Extract the file creation time (st_ctime) and file size (st_size)
        file_creation_time = stats.st_ctime
        file_size = stats.st_size
        accesses = 0 # To be added

        return f"{source_image}:{file_creation_time}:{file_size}:{accesses}"
    

    def get_user_secret(self, userid):
        if userid in self.keydata:
            return self.keydata[userid]
        else:
            return None
        

    def validate_token(self, msg):
        """
        validates a file request token; a token should consist of a
        userid:original_token:modded_token from user
        """
        userid, otoken, modtoken = msg.split(':')[0:3]
        self.log.log(f'security: validating request from user {userid}')

        user_secret = self.get_user_secret(userid)
        logging.debug(f'Validating token tuple({userid},{otoken},{modtoken})')

        #
        # We didn't find the user, we return false, indicating that the token
        # validated
        #
        if user_secret is None:
            self.log.log(f'security: unknown user {userid}')
            logging.debug(f'Could not find secret for user {userid}') 
            return False

        #
        # Check for replays
        #
        if (not self.is_vul) and (otoken in self.vtable):
            logging.debug(f'Token is a replay.')
            # In this situation we reject, because the token is present
            self.vtable[otoken] += 1 # Purely for audit purposes
            return False

        #
        # Now validate the signature proper; just because we're vulnerable to
        # replays doesn't mean we're vulnerable to total idiots.
        #
        # Note the use of the utf-8 encoding here; since we're messing
        # with python's hash librares (which want binaries) we need to pay
        # attention to the possibility that some encoding foo will bite us.
        signature = hashlib.md5((otoken + user_secret).encode('UTF-8')).hexdigest()
        logging.debug(f'Signature is {signature} vs. received token {modtoken}')

        if signature != modtoken:
            logging.debug('Signature mismatch')
            return False

        # This is our success case.
        logging.debug('Signatures match')
        return True
        
    
    def exec_reqtoken(self, userid, parm):
        """
        reqtoken
        Returns a token 
        A token is defined as a randomized 12-character string 
        """
        tlength = 12
        cstr=string.ascii_letters

        if self.get_user_secret(userid) is None:
            return None

        # Passed the 'user exists' gateway, now return the token
        return ''.join(random.choices(cstr, k = tlength))

