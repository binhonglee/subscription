class BadIP():
    def __init__(self):
        self.bad_ip = set()
        self.bad_email = set()
        with open("bad_ip") as fp:
            for line in fp:
                ip = line.rstrip("\n")
                if len(ip) > 0:
                    self.bad_ip.add(ip)
        with open("bad_email") as fp:
            for line in fp:
                email = line.rstrip("\n")
                if len(email) > 0:
                    self.bad_email.add(email)


    def is_bad(self, email: str, ip: str):
        if email in self.bad_email:
            self.new_bad(ip)
        if ip in self.bad_ip:
            self.new_bad_email(email)
        return email in self.bad_email or ip in self.bad_ip


    def new_bad(self, ip: str):
        if ip not in self.bad_ip:
            with open("bad_ip", "a") as file:
                file.write(ip + "\n")
                file.close()
            self.bad_ip.add(ip)

    
    def new_bad_email(self, email: str):
        if email not in self.bad_email:
            with open("bad_email", "a") as file:
                file.write(email + "\n")
                file.close()
            self.bad_email.add(email)
