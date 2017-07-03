

class IpPool(object):

    def __init__(self):
        self.pool = dict()
        pass

    def add_pool(self,name,addresses):
        self.pool[name]=addresses

    def remove_pool(self,name,addresses):
        pass

    def get(self,name):
        if len(self.pool[name]) > 0 :
            return self.pool[name].pop()

        return None

    def free(self,name,address):
        self.pool[name].append(address)

    def add_ip_in_pool(self,name,ip,netmask):
        address=dict()
        address["ip"]=ip
        address["netmask"]=netmask

        if name not in self.pool:
            self.pool[name] = []

        self.pool[name].append(address)