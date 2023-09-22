start: header function*

WORD: /(?!\d)\w+/
str: /"([^"]|"")*"/ //"// This comment fixes syntax highlight
number: /-?\d+(\.\d+)?/

header: "version" /\d+/ "hash" str
function: "function" str block

block: "{" stmt* "}"
stmt: WORD "(" csep_term ")" [block]
csep_term: (term ",")* term? -> args

?term: number | str
     | "(" expr ")" -> expr
     | "{" str* "}" -> text

?expr: expr0
?expr0: expr0 /expr_missing_op/ expr1 -> binop | expr1
?expr1: expr1 /\|\|?/           expr2 -> binop | expr2
?expr2: expr2 /&&?/             expr3 -> binop | expr3
?expr3: expr3 /[!=]=|[<>]=?/    expr4 -> binop | expr4
?expr4: expr4 /[+-]/            expr5 -> binop | expr5
?expr5: expr5 /[*\/%]/          expr6 -> binop | expr6
?expr6: /[!-]/ expr6 -> prefixop | expr7
?expr7: expr_atom

?expr_atom: number | str
          | "(" expr ")"
          | WORD "[" expr "]" -> index
          | WORD "(" csep_expr ")" -> call
          | expr_atom "." WORD "[" expr "]" -> index_on
          | expr_atom "." WORD "(" csep_expr ")" -> call_on
          | "expr_missing" -> expr_missing

csep_expr: (expr ",")* expr? -> args

%ignore /[  \t\r\n]/
%ignore /\/\/.*/
