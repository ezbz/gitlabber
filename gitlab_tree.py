from anytree import Node

def make_node(self, type: str, name: str, parent: Node, url: str) -> Node:
    node = Node(name=name, parent=parent, url=url, type=type)
    node.root_path = self.root_path(node)
    return node