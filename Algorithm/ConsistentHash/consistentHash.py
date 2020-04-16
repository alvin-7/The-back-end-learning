# -*- coding: utf-8 -*-
import hashlib
import collections
import bisect

"""
一致性hash算法
"""


class CConsistenHash:
    def __init__(self, nodes=None, replicas=100):
        """_replicas: 虚拟节点数"""
        self._replicas = replicas
        self._nodes = collections.defaultdict(dict) #{virNode: sRealNode}
        self._sort_nodes = [] # 排序的虚拟节点hash值列表

        # hash规则
        self._hash_rule = lambda n:int(hashlib.md5(n.encode('utf-8')).hexdigest(), 16)
        for node in nodes:
            self.add_node(node)

    def add_node(self, sNode):
        """
        添加节点并设置虚拟节点
        """
        for i in range(self._replicas):
            sVirNode = f"{sNode}#{i}"
            vir_node = self._hash_rule(sVirNode)
            if vir_node in self._nodes:
                raise Exception("err virnode: %s" % sVirNode)
            self._nodes[vir_node] = sNode
            bisect.insort_right(self._sort_nodes, vir_node)

    def remove_node(self, sNode):
        """
        移除节点及其虚拟节点
        """
        for i in range(self._replicas):
            hashval = self._hash_rule(f"{sNode}#{i}")
            del self._nodes[hashval]
            node_idx = bisect.bisect_left(self._sort_nodes, hashval)
            del self._sort_nodes[node_idx]

    def get_node(self, sKey):
        """
        根据所给的key得到对应的节点
        """
        assert self._nodes

        sortNodes = self._sort_nodes
        hashval = self._hash_rule(sKey)
        vir_index = bisect.bisect_right(sortNodes, hashval)
        if vir_index == len(sortNodes):
            vir_index = 0
        return self._nodes[sortNodes[vir_index]]


def test(replicas):
    content = """In computer science, consistent hashing is a special 
    kind of hashing such that when a hash table is resized, only 
    {\displaystyle n/m}n/m keys need to be remapped on average where 
    {\displaystyle n}n is the number of keys and {\displaystyle m}m is 
    the number of slots.
    In contrast, in most traditional hash tables, a change in the number of 
    array slots causes nearly all keys to be remapped because the mapping 
    between the keys and the slots is defined by a modular operation. 
    Consistent hashing is a particular case of rendezvous hashing, 
    which has a conceptually simpler algorithm, and was first described in 1996.
    Consistent hashing first appeared in 1997, and uses a different algorithm."""

    servers = [
        "127.0.0.1",
        "127.0.0.2",
        "127.0.0.3",
        "127.0.0.4",
        "127.0.0.5",
    ]
    hr = CConsistenHash(servers, replicas)

    myNodes = {s: [] for s in servers}
    keys = content.split()
    for skey in keys:
        myNodes[hr.get_node(skey)].append(skey)

    for node, result in myNodes.items():
        print(f"{node} = {len(result)}\nresult={result}\n")


if __name__ == '__main__':
    test(100)