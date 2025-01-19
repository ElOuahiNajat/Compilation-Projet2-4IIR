import re

# Grammaire BNF améliorée
BNF_GRAMMAR = {
    "create_database": r"CREATE TABLE (\w+) \(([\w\s,()]+)\)",
    "column_definition": r"(\w+) (\w+)( PRIMARY KEY| NOT NULL| UNIQUE| FOREIGN KEY)?",
    "identifier": r"\w+"
}

def validate_bnf(sql_query):
    """
    Valide une requête SQL en utilisant la grammaire BNF.
    """
    match = re.match(BNF_GRAMMAR["create_database"], sql_query)
    if match:
        table_name = match.group(1)
        column_definitions = match.group(2)
        print(f"Table: {table_name}")
        print(f"Colonnes: {column_definitions}")
        
        # Validation des définitions de colonnes
        columns = column_definitions.split(',')
        for column in columns:
            validate_column(column.strip())
    else:
        print("Erreur: la requête ne respecte pas la grammaire BNF.")

def validate_column(column_definition):
    """
    Valide la définition d'une colonne selon la BNF.
    """
    match = re.match(BNF_GRAMMAR["column_definition"], column_definition)
    if match:
        print(f"Colonne validée: {match.group(1)} de type {match.group(2)}")
    else:
        print(f"Erreur: la colonne '{column_definition}' n'est pas valide.")

# Exemple d'utilisation
sql_query = "CREATE TABLE students (id INT PRIMARY KEY, name VARCHAR(100) NOT NULL, age INT)"
validate_bnf(sql_query)
