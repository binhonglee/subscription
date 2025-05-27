import datetime
import uuid


class Secret():
    def __init__(self):
        self.previous_valid = ""
        try:
            with open("previous_uuid", "r") as puid:
                self.previous_valid = puid.read().rstrip("\n")
        except Exception:
            self.previous_valid = str(uuid.uuid4())

        self.valid_gen_time = datetime.datetime.now()
        print(self.valid_gen_time)
        self.current_valid = str(uuid.uuid4())
        with open("previous_uuid", "w") as puid:
            puid.write(self.current_valid)


    def get_secret(self) -> str:
        return self.current_valid

    
    def is_valid(self, provided: str) -> bool:
        return provided == self.previous_valid or provided == self.current_valid


    def new_secret(self):
        if abs(datetime.datetime.now() - self.valid_gen_time) > datetime.timedelta(minutes=30):
            self.previous_valid = self.current_valid
            self.valid_gen_time = datetime.datetime.now()
            self.current_valid = str(uuid.uuid4())
            with open("previous_uuid", "w") as puid:
                puid.write(self.current_valid)

