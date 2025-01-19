from ply import lex, yacc  # type: ignore

# Liste des tokens
tokens = (
    'TABLE', 'IDENTIFIER', 'COLON', 'DASH',
    'LPAREN', 'RPAREN', 'COMMA', 'PROPERTY', 'INDEX', 'ON', 'REFERENCE', 'PRIMARY', 'UNIQUE', 'DOT'
)

# Règles pour les tokens
t_TABLE = r'table'
t_IDENTIFIER = r'[a-zA-Z_][a-zA-Z0-9_]*'
t_COLON = r':'
t_DASH = r'-'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_COMMA = r','
t_INDEX = r'INDEX'
t_ON = r'ON'
t_PROPERTY = r'(entier|texte|date|clé primaire|auto|requis|unique|par défaut:.+|référence:[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*)'
t_PRIMARY = r'clé primaire'
t_UNIQUE = r'unique'
t_REFERENCE = r'référence'
t_DOT = r'\.'  # Définir le token pour le point

# Ignorer les espaces et les nouvelles lignes
t_ignore = ' \t'
t_ignore_NEWLINE = r'\n+'

# Gestion des erreurs lexicales
def t_error(t):
    print(f"Caractère illégal '{t.value[0]}'")
    t.lexer.skip(1)

# Construire le lexer
lexer = lex.lex()

# Grammaire BNF avec PLY
def p_database(p):
    '''database : table_def
                | table_def database'''
    pass

def p_table_def(p):
    '''table_def : TABLE IDENTIFIER COLON column_defs'''
    pass

def p_column_defs(p):
    '''column_defs : column_def
                   | column_def column_defs'''
    pass

def p_column_def(p):
    '''column_def : DASH IDENTIFIER LPAREN properties RPAREN'''
    pass

def p_properties(p):
    '''properties : PROPERTY
                  | PROPERTY COMMA properties
                  | PRIMARY
                  | UNIQUE
                  | REFERENCE IDENTIFIER DOT IDENTIFIER'''
    pass

# La règle d'index a été supprimée car non utilisée
# def p_index_def(p):
#     '''index_def : INDEX IDENTIFIER ON IDENTIFIER LPAREN IDENTIFIER column_list RPAREN'''

# Supprimer les règles inutilisées
# def p_column_list(p):
#     '''column_list : COMMA IDENTIFIER column_list
#                    | empty'''

# def p_empty(p):
#     '''empty :'''
#     pass

# Gestion des erreurs syntaxiques
def p_error(p):
    if p:
        print(f"Erreur de syntaxe à '{p.value}'")
    else:
        print("Erreur de syntaxe à EOF")

# Construire le parser
parser = yacc.yacc()

# Exemple d'utilisation
if __name__ == "__main__":
    data = """
    table utilisateurs:
    - id (entier, clé primaire, auto)
    - nom (texte, requis, unique)
    - email (texte, unique)
    - age (entier)
    INDEX idx_nom ON utilisateurs (nom)
    table commandes:
    - id (entier, clé primaire, auto)
    - utilisateur_id (entier, référence: utilisateurs.id)
    - date_commande (date)
    """

    lexer.input(data)
    for token in lexer:
        print(token)

    result = parser.parse(data)
    print("Parsing terminé.")
