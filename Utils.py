import time

class ExceptionTracker(object):
    def __init__(self, maxRetries, errorMessage):
        self.RemainingRetries = maxRetries
        self.ErrorMessage = errorMessage
        
    def ExceptionReceived(self, exeptionObject):
        self.RemainingRetries -= 1
        if self.RemainingRetries == 0:
            print("********** " + self.ErrorMessage)
            print(exeptionObject)
            raise exeptionObject
        time.sleep(1)
