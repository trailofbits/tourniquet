

# This represents a node taken from the db.
class Node:
    def __init__(self, node_type, line, col, source_info, json_blob):
        self.node_type = node_type
        self.line = line
        self.col = col
        self.source_info = source_info
        self.json_blob = json_blob

    def matches(self, match_str: str) -> bool:
        # Call extractor to do an AST match against the tree
        # Returns match text with line/col info.
        # Filter results based on line info
        # Return true if there is a match!
        return False
