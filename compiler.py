import sys
import os

from statements import *
from util import *

PRELUDE = '''
#include <stdio.h>
#include <stdlib.h>

#define T long
#define toT atol

#define INT_VALUE(v) (v.type == integer ? (T) (v.value) : toT(v.value))
#define STR_VALUE(v) (v.type == string ? (char*) (v.value) : )

#define _vglobal_4_vadd(a, b) ((value) { integer, INT_VALUE(a) + INT_VALUE(b) })
#define _vglobal_4_vminus(a, b) ((value) { integer, INT_VALUE(a) - INT_VALUE(b) })
#define _vglobal_4_vmult(a, b) ((value) { integer, INT_VALUE(a) * INT_VALUE(b) })
#define _vglobal_4_vdiv(a, b) ((value) { integer, INT_VALUE(a) / INT_VALUE(b) })
#define _vglobal_4_vmod(a, b) ((value) { integer, INT_VALUE(a) % INT_VALUE(b) })

#define _vglobal_4_vle(a, b) ((value) { integer, INT_VALUE(a) < INT_VALUE(b) })
#define _vglobal_4_vleq(a, b) ((value) { integer, INT_VALUE(a) <= INT_VALUE(b) })
#define _vglobal_4_vge(a, b) ((value) { integer, INT_VALUE(a) > INT_VALUE(b) })
#define _vglobal_4_vgeq(a, b) ((value) { integer, INT_VALUE(a) >= INT_VALUE(b) })

#define _vglobal_4_vstdout(v) printf((v).type == integer ? "%d" : "%s", (v).value)

#define _vglobal_4_vif_1then_1else(c,a,b) INT_VALUE(c)?(a):(b)

typedef enum __type { integer, string } type;

typedef struct __value {
    type type;
    void* value;
} value;

typedef value(*varargfunc_p)(value v, ...);

void bit64_str(long long n, char* buff) {
    int neg = n < 0;
    n = neg ? -n : n;
    int i;
    for (i=0; n>0; i++) {
        buff[i] = '0' + (n % 10);
        n = n / 10;
    }
    if (i == 0) buff[i++] = '0';
    if (neg) buff[i++] = '-';
    buff[i] = '\\0';
    int j=0;
    i--;
    for (; i>j; i--,j++) {
        char tmp = buff[i];
        buff[i] = buff[j];
        buff[j] = tmp;
    }
}

value _vglobal_4_vstdin() {
    char* line = NULL; size_t size;
    getline(&line, &size, stdin);
    return ((value) { integer, atoll(line) });
}
'''


class C_Compiler:
    def __init__(self):
        self.functions = []
        self.defined_vars = set()

    def add_function(self, function): # function : FunctionInvocation
        self.functions.append(function)

    def code(self):
        code = PRELUDE + "\n"
        funcs = []
        signatures = []
        for func in self.functions:
            self.defined_vars = set()
            is_main = func.name == "main" and func.domain == "global"
            sig,c = self._compile(func, is_main)
            funcs.append(c)
            if not is_main: signatures.append(sig)
        return code + "\n".join(signatures) + "\n" + "\n".join(funcs[::-1])

    def _compile(self, func, return_void = False):
        f_name = addr_to_var_name(Addr(func.name, func.domain))
        arg_count = max(map(max_arg_index_statement, func.statements))
        args = map(lambda n: "value " + addr_to_var_name(Addr(str(n), "arguments")), range(0, arg_count+1))
        sig = "%s %s(%s)" % ("void" if return_void else "value", f_name, ','.join(args))
        stmts = ""
        for i,stmt in enumerate(func.statements):
            stmts += "\t"
            stmt_code = ""
            if not return_void and i == len(func.statements)-1:
                stmt_code = "return "
            if isinstance(stmt, VariableSet): stmt_code += self._compile_variable_set(stmt)
            if isinstance(stmt, FunctionCall): stmt_code += self._compile_function_call(stmt)
            if starts_with(stmt_code, "return "):
                index = stmt_code.find('=')
                if index > 0: stmt_code = "return " + stmt_code[index+1:]
            stmts += stmt_code + "\n"
        ret = ""
        return (sig + ";", sig + "{\n" + stmts + ret + "}")

    def _compile_variable_set(self, var_set):
        return "%s = %s;" % (self._compile_var(var_set.lhs), var_set.rhs.repr())

    def _compile_function_call(self, func_call):
        fname = addr_to_var_name(func_call.func_name)
        if func_call.func_name.domain == "continuation":
            fname = "((varargfunc_p)%s.value)" % fname
        result = ""
        if len(func_call.aliases) > 0:
            result = self._compile_var(func_call.aliases[0]) + " = "
        needs_wrapping = fname == addr_to_var_name(Addr("if-then-else", "global"))
        needs_wrapping = needs_wrapping and any(map(lambda a: a.domain == "global", func_call.args))
        if needs_wrapping:
            result += "{ string, "
        result += fname + "("
        result += ', '.join(map(lambda x: x.repr(), func_call.args))
        result += ")" + ("}" if needs_wrapping else "") + ";"
        if len(func_call.aliases) > 2:
            prev = func_call.aliases[0]
            for alias in func_call.aliases[1:]:
                result += "\n\t%s = %s;" % (self._compile_var(alias), prev);
                prev = alias
        return result

    def _compile_var(self, addr):
        name = addr_to_var_name(addr)
        if not name in self.defined_vars:
            self.defined_vars.add(name)
            return "value " + name
        else: return name



SOURCE_CODE = sys.argv[1]
lines = open(SOURCE_CODE, "r").readlines() + [ "\n" ]


# Context of functions: func_name:string => FunctionInvocation
funcs = {}

# mail ::= from=>string, to=>string, subject=>string, body=>[value]
# value ::= int | "string" | addr:string
last_mail = { "from": None, "to": None, "subject": "", "body": [] }


for line in lines:
    line = line[:-1].strip()
    if len(line) == 0:
        frm, to = last_mail['from'], last_mail['to']
        if frm is None or to is None: continue
        if not frm in funcs:
            funcs[frm] = FunctionInvocation(frm.user, frm.domain)
        funcs[frm].treat_email(last_mail)
        last_mail = { "from": None, "to": None, "subject": "", "body": [] }
    elif starts_with(line.lower(), "from:"):
        data = line[5:].strip().lower()
        if not is_address(data):
            raise Exception("Malformed from: " + line)
        last_mail['from'] = to_value(data)
    elif starts_with(line.lower(), "to:"):
        data = line[3:].strip().lower()
        if not is_address(data):
            raise Exception("Malformed to: " + line)
        last_mail['to'] = to_value(data)
    elif starts_with(line.lower(), "subject:"):
        last_mail['subject'] = line[8:].strip().lower()
    else:
        last_mail['body'].append(to_value(line))


c = C_Compiler()
for f in funcs:
    c.add_function(funcs[f])


FILENAME = "/tmp/maillang-compiled-program.c"
open(FILENAME, "w+").write(c.code())
import subprocess
BINARY = os.path.splitext(os.path.basename(SOURCE_CODE))[0]
if BINARY == SOURCE_CODE: BINARY += ".bin"
subprocess.run(["gcc", "-Wno-int-conversion", FILENAME, "-o", BINARY])
