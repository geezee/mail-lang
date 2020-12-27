import statements

def starts_with(x, y):
    if len(y) > len(x): return False
    return x[:len(y)] == y


def is_numeral(x):
    if len(x) == 0: return False
    while len(x) > 0:
        if x[0] > '9' or x[0] < '0': return False
        x = x[1:]
    return True

def is_string(x):
    if len(x) < 2: return False
    if not x[0] == '"' or not x[-1] == '"': return False
    esc = False
    for c in x[1:-1]:
        if not esc and (c == '"'): return False
        esc = not esc and (c == '\\')
    return not esc

def is_address(x): # [0-9A-Za-z.$_-]+@[0-9A-Za-z.$_-]
    if len(x) < 3 or x[0] == '@': return False
    at = False
    for c in x:
        if c == '@' and at: return False
        if c >= '0' and c <= '9': continue
        if c >= 'A' and c <= 'Z': continue
        if c >= 'a' and c <= 'z': continue
        if not (c == '.' or c == '$' or c == '_' or c == '-' or c == '@'): return False
        at = at or c == '@'
    return (not x[-1] == '@') and at

def to_var_name(x):
    return '_v' + x.replace('_', '_0').replace('-', '_1').replace('.', '_2').replace('$', '_3')

def addr_to_var_name(addr):
    if addr.domain == "global" and addr.user == "main": return "main"
    if addr.domain == "local": return to_var_name(addr.user)
    if addr.domain == "arguments":
        if is_numeral(addr.user): return "_a_" + addr.user
        else: return "arguments[" + addr.user + "]"
    return to_var_name(addr.domain) + '_4' + to_var_name(addr.user)

def max_with_def(lst, default):
    lst = list(lst)
    if len(lst) == 0: return default
    return max(lst)

def max_arg_index_value(value):
    if isinstance(value, statements.Addr) and value.domain == "arguments" and is_numeral(value.user):
        return int(value.user)
    return -1

def max_arg_index_statement(stmt):
    if isinstance(stmt, statements.VariableSet):
        return max([max_arg_index_value(stmt.lhs), max_arg_index_value(stmt.rhs)])
    elif isinstance(stmt, statements.FunctionCall):
        aliases = max_with_def(map(max_arg_index_value, stmt.aliases), -1)
        args = max_with_def(map(max_arg_index_value, stmt.args), -1)
        return max(aliases, args, max_arg_index_value(stmt.func_name))
    else: return -1
