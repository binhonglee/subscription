class BadIP():
    def __init__(self):
        self.bad_ip = set()
        with open("bad_ip") as fp:
            for line in fp:
                ip = line.rstrip("\n")
                if len(ip) > 0:
                    self.bad_ip.add(ip)


    def is_bad(self, ip: str):
        print("is bad", ip)
        return ip in self.bad_ip


    def new_bad(self, ip: str):
        print("new bad", ip)
        if ip not in self.bad_ip:
            with open("bad_ip", "a") as file:
                file.write(ip + "\n")
                file.close()
            self.bad_ip.add(ip)
