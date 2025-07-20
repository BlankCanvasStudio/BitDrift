from vehicle.payloads import payload
import logging

class LogPayload(payload.Payload):

    def __init__(self, lqsize, clock):
        self.clock = clock
        self.total_logged = 0 
        self.lqsize = lqsize
        self.log_buffer = []


    def fetch_logs(self, kw, maxreq):
        """
        fetch (self, kw)
        kw -- keyword, string.
        The fetch command searches through the log buffer for any
        messages matching the keyword, stores them in a response
        buffer and pushes that back to the user.
        """

        logging.debug(f'Executing fetch logs with keyword {kw} and {maxreq} requests')

        result = [x for x in self.log_buffer if kw in x]
        result = result[0:maxreq]

        logging.debug(f'Found {len(result)} results')

        return '\n'.join(result) 


    def log(self, msg):
        self.total_logged +=1 

        t = self.clock.get_time()
        lm = f'{self.total_logged:06}:{t:8.2f}:{msg}'

        if len(self.log_buffer) >= self.lqsize:
            self.log_buffer.pop(0)

        self.log_buffer.append(lm)

