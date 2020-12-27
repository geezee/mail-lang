from util import *


class Integer:
    def __init__(self, value): self.value = value
    def repr(self): return "((value) { integer, (void*) %d })" % self.value
    def __eq__(self, other): return other.value == self.value
    def __hash__(self): return self.value

class String:
    def __init__(self, value): self.value = value
    def repr(self): return "((value) { string, %s })" % self.value
    def __eq__(self, other): return other.value == self.value
    def __hash__(self): return hash(self.value)

class Addr:
    def __init__(self, user, domain):
        self.user = user
        self.domain = domain
    def repr(self): return addr_to_var_name(self)
    def __eq__(self, other): return other.user == self.user and other.domain == self.domain
    def __hash__(self): return hash(self.user) + hash(self.domain)



def to_value(x):
    if is_numeral(x): return Integer(int(x))
    elif is_string(x): return String(x)
    elif is_address(x): return Addr(*x.split('@'))
    else: raise Exception("What do you mean by '" + x + "'?")



class VariableSet:
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

class FunctionCall:
    def __init__(self, func_name, args):
        self.func_name = func_name # Addr
        self.args = args # [ Value ]
        self.aliases = [] # [ Addr ]

    def add_alias(self, alias):
        self.aliases.append(alias)



class FunctionInvocation:
    def __init__(self, name, domain):
        self.name = name
        self.domain = domain
        self.statements = []
        self._sbj2call = {} # every email (id by subject) gets a function call object

    def treat_email(self, email): # email looks like last_mail
        to, subject, body = email['to'], email['subject'], email['body']
        statement = None
        if starts_with(subject.lower(), "re:"):
            oldsbj = subject[3:].strip()
            if not oldsbj in self._sbj2call:
                raise Exception("The email you're replying to '" + oldsbj + "' does not exist")
            if len(body) != 1 or not isinstance(body[0], Addr):
                raise Exception("A response email must have a body made of an address")
            self._sbj2call[oldsbj].add_alias(body[0])
        elif to.domain == "local":
            if len(body) != 1:
                raise Exception("Assigning a value to " + to + " requires you give me one value")
            statement = VariableSet(to, body[0])
        else:
            if subject in self._sbj2call:
                raise Exception("The email with subject " + subject + " already exists")
            statement = FunctionCall(to, body)
            self._sbj2call.update({subject.strip(): statement})
        if not statement is None:
            self.statements.append(statement)
