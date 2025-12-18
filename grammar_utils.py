def parse_grammar(text):
    """
    Parses raw grammar text into a dictionary.
    Returns: (grammar_dict, start_symbol, non_terminals_set)
    """
    grammar = {}
    non_terminals = set()
    start_symbol = None

    lines = text.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line: continue
        if '->' not in line: continue

        head, body = line.split('->')
        head = head.strip()

        if start_symbol is None:
            start_symbol = head

        non_terminals.add(head)

        alternatives = [alt.strip().split() for alt in body.split('|')]
        if head not in grammar:
            grammar[head] = []
        grammar[head].extend(alternatives)

    return grammar, start_symbol, non_terminals


def remove_left_recursion(grammar, non_terminals):
    """
    Removes immediate left recursion from the grammar.
    Returns: (new_grammar, updated_non_terminals)
    """
    new_grammar = {}
    updated_non_terminals = set(non_terminals)
    ordered_heads = list(grammar.keys())

    for head in ordered_heads:
        bodies = grammar[head]
        recursive = []
        non_recursive = []

        for body in bodies:
            if body[0] == head:
                recursive.append(body[1:])  # Alpha
            else:
                non_recursive.append(body)  # Beta

        if not recursive:
            new_grammar[head] = bodies
        else:
            # Create new Non-Terminal A'
            new_head = head + "'"
            updated_non_terminals.add(new_head)

            # Rule 1: A -> Beta A'
            new_grammar[head] = []
            for beta in non_recursive:
                if beta == ['ε']:
                    new_grammar[head].append([new_head])
                else:
                    new_grammar[head].append(beta + [new_head])

            # Rule 2: A' -> Alpha A' | ε
            new_grammar[new_head] = []
            for alpha in recursive:
                new_grammar[new_head].append(alpha + [new_head])
            new_grammar[new_head].append(['ε'])

    return new_grammar, updated_non_terminals


def format_grammar(grammar):
    """Converts grammar dict back to string for display."""
    res = []
    for head, bodies in grammar.items():
        bodies_str = [" ".join(b) for b in bodies]
        res.append(f"{head} -> {' | '.join(bodies_str)}")
    return "\n".join(res)