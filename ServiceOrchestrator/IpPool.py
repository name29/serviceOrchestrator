import logging

class IpPool(object):

    def __init__(self):
        self.pool = dict()
        pass

    def add_pool(self,name,addresses):
        logging.debug("Adding the new pool %s  with %s" % (name,addresses))
        self.pool[name]=addresses

    def remove_pool(self,name,addresses):
        logging.debug("Dummy function called %s - %s" % (name,addresses))
        #TODO
        pass

    def get(self,name):
        if len(self.pool[name]) > 0:
            ret = self.pool[name].pop()
            logging.debug("Leased from the pool %s the address %s" % (name, ret))
            return ret

        logging.warning("The pool %s is empty" % name)
        return None

    def free(self,name,address):
        logging.debug("%s is returned back in %s" % (address,name))
        self.pool[name].append(address)

    def add_ip_in_pool(self,name,ip,netmask):
        address=dict()
        address["ip"]=ip
        address["netmask"]=netmask

        logging.debug("Adding inside the pool %s the address %s" % (name, address))
        if name not in self.pool:
            logging.debug("Created the pool %s " % name)
            self.pool[name] = []

        self.pool[name].append(address)