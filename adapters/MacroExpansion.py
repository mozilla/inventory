from systems.models import System,KeyValue
from truth.models import Truth, KeyValue as TruthKeyValue
class MacroExpansion:
    
    def __init__(self,macro):
        self.operators = macro.split(":")
        self.output_text = ''
        if self.operators[0] == 'host':
            self.host_macro()
        if self.operators[0] == 'truth':
            self.truth_macro()


    def host_macro(self):
        try:
            host = self.operators[1]
            key = self.operators[2]
            system = System.objects.get(hostname=host)
            self.output_text = KeyValue.objects.filter(obj=system).filter(key=key)[0].value
            self.output()
        except Exception, e:
            self.output_text = 'Host/Key Combination Not Found'
            self.output()

    def truth_macro(self):
        try:
            truth_name = self.operators[1]
            key = self.operators[2]
            truth = Truth.objects.get(name=truth_name)
            self.output_text = TruthKeyValue.objects.filter(truth=truth).filter(key=key)[0].value
            self.output()
        except Exception, e:
            self.output_text = 'Truth/Key Combination Not Found'
            self.output()
        
    def output(self):
        return self.output_text
