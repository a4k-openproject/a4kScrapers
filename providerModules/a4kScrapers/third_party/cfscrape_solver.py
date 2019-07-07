import ast
import re
import operator as op

operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
             ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor,
             ast.USub: op.neg}

def eval_expr(expr):
    return eval_(ast.parse(expr, mode='eval').body)

def eval_(node):
    if isinstance(node, ast.Num):  # <number>
        return node.n
    elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
        return operators[type(node.op)](eval_(node.left), eval_(node.right))
    elif isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
        return operators[type(node.op)](eval_(node.operand))
    else:
        raise TypeError(node)

def parseJSString(s):
    offset = 1 if s[0] == '+' else 0
    val = s.replace('!+[]', '1').replace('!![]', '1').replace('[]', '0')[offset:]

    val = val.replace('(+0', '(0').replace('(+1', '(1')

    val = re.findall(r'\((?:\d|\+|\-)*\)', val)

    val = ''.join([str(eval_expr(i)) for i in val])
    return int(val)

def solve_challenge(body, domain):
    delay = int(re.compile("\}, ([\d]+)\);", re.MULTILINE).findall(body)[0]) / 1000

    init = re.findall('setTimeout\(function\(\){\s*var.*?.*:(.*?)}', body)[-1]
    builder = re.findall(r"challenge-form\'\);\s*(.*)a.v", body)[0]
    try:
        challenge_element = re.findall(r'id="cf.*?>(.*?)</', body)[0]
    except:
        challenge_element = None

    if '/' in init:
        init = init.split('/')
        decryptVal = parseJSString(init[0]) / float(parseJSString(init[1]))
    else:
        decryptVal = parseJSString(init)
    lines = builder.split(';')
    char_code_at_sep = '"("+p+")")}'

    for line in lines:
        if len(line) > 0 and '=' in line:
            sections = line.split('=')
            if len(sections) < 3:
                if '/' in sections[1]:
                    subsecs = sections[1].split('/')
                    val_1 = parseJSString(subsecs[0])
                    if char_code_at_sep in subsecs[1]:
                        subsubsecs = re.findall(r"^(.*?)(.)\(function", subsecs[1])[0]
                        operand_1 = parseJSString(subsubsecs[0] + ')')
                        operand_2 = ord(domain[parseJSString(
                            subsecs[1][subsecs[1].find(char_code_at_sep) + len(char_code_at_sep):-2])])
                        val_2 = '%.16f%s%.16f' % (float(operand_1), subsubsecs[1], float(operand_2))
                        val_2 = eval_expr(val_2)
                    else:
                        val_2 = parseJSString(subsecs[1])
                    line_val = val_1 / float(val_2)
                elif len(sections) > 2 and 'atob' in sections[2]:
                    expr = re.findall((r"id=\"%s.*?>(.*?)</" % re.findall(r"k = '(.*?)'", body)[0]), body)[0]
                    if '/' in expr:
                        expr_parts = expr.split('/')
                        val_1 = parseJSString(expr_parts[0])
                        val_2 = parseJSString(expr_parts[1])
                        line_val = val_1 / float(val_2)
                    else:
                        line_val = parseJSString(expr)
                else:
                    if 'function' in sections[1]:
                        continue
                    line_val = parseJSString(sections[1])

            elif 'Element' in sections[2]:
                subsecs = challenge_element.split('/')
                val_1 = parseJSString(subsecs[0])
                if char_code_at_sep in subsecs[1]:
                    subsubsecs = re.findall(r"^(.*?)(.)\(function", subsecs[1])[0]
                    operand_1 = parseJSString(subsubsecs[0] + ')')
                    operand_2 = ord(domain[parseJSString(
                        subsecs[1][subsecs[1].find(char_code_at_sep) + len(char_code_at_sep):-2])])
                    val_2 = '%.16f%s%.16f' % (float(operand_1), subsubsecs[1], float(operand_2))
                    val_2 = eval_expr(val_2)
                else:
                    val_2 = parseJSString(subsecs[1])
                line_val = val_1 / float(val_2)


            decryptVal = '%.16f%s%.16f' % (float(decryptVal), sections[0][-1], float(line_val))
            decryptVal = eval_expr(decryptVal)

    if '+ t.length' in body:
        decryptVal += len(domain)

    return float('%.10f' % decryptVal), delay
