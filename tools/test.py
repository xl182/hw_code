from collections import defaultdict
from bisect import bisect_left

class OSTNode:
    """Order Statistic Tree 节点"""
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None
        self.size = 1  # 子树大小
        self.height = 1

class OptimizedOrderedList:
    def __init__(self):
        self.root = None
        self.id_to_value = defaultdict(int)  # ID到值的映射
        self.value_to_ids = defaultdict(set) # 值到ID集合的映射

    def _get_size(self, node):
        return node.size if node else 0

    def _get_height(self, node):
        return node.height if node else 0

    def _update_size_height(self, node):
        node.size = 1 + self._get_size(node.left) + self._get_size(node.right)
        node.height = 1 + max(self._get_height(node.left), self._get_height(node.right))
        return node

    def _balance_factor(self, node):
        return self._get_height(node.left) - self._get_height(node.right)

    def _rotate_right(self, y):
        x = y.left
        T2 = x.right

        x.right = y
        y.left = T2

        self._update_size_height(y)
        self._update_size_height(x)
        return x

    def _rotate_left(self, x):
        y = x.right
        T2 = y.left

        y.left = x
        x.right = T2

        self._update_size_height(x)
        self._update_size_height(y)
        return y

    def _insert(self, node, value, pos_count):
        if not node:
            return OSTNode(value)

        if value < node.value:
            node.left = self._insert(node.left, value, pos_count)
            pos_count['count'] += 1 + self._get_size(node.right)
        else:
            node.right = self._insert(node.right, value, pos_count)

        self._update_size_height(node)

        # AVL 平衡
        balance = self._balance_factor(node)
        if balance > 1 and value < node.left.value:
            return self._rotate_right(node)
        if balance < -1 and value > node.right.value:
            return self._rotate_left(node)
        if balance > 1 and value > node.left.value:
            node.left = self._rotate_left(node.left)
            return self._rotate_right(node)
        if balance < -1 and value < node.right.value:
            node.right = self._rotate_right(node.right)
            return self._rotate_left(node)

        return node

    def _get_position(self, node, target, pos):
        if not node:
            return -1

        if target == node.value:
            return pos + self._get_size(node.left)
        elif target < node.value:
            return self._get_position(node.left, target, pos)
        else:
            return self._get_position(node.right, target, pos + 1 + self._get_size(node.left))

    def add(self, obj_id, value):
        """添加元素并返回其位置索引"""
        pos_count = {'count': 0}
        self.root = self._insert(self.root, value, pos_count)
        actual_pos = pos_count['count']

        self.id_to_value[obj_id] = value
        self.value_to_ids[value].add(obj_id)
        return actual_pos

    def remove(self, obj_id):
        """删除指定ID的元素"""
        value = self.id_to_value[obj_id]
        self.root = self._delete(self.root, value)
        self.value_to_ids[value].remove(obj_id)
        if not self.value_to_ids[value]:
            del self.value_to_ids[value]
        del self.id_to_value[obj_id]

    def _delete(self, node, value):
        if not node:
            return node

        if value < node.value:
            node.left = self._delete(node.left, value)
        elif value > node.value:
            node.right = self._delete(node.right, value)
        else:
            if not node.left or not node.right:
                temp = node.left if node.left else node.right
                node = temp
            else:
                temp = self._min_value_node(node.right)
                node.value = temp.value
                node.right = self._delete(node.right, temp.value)

        if not node:
            return node

        self._update_size_height(node)

        # AVL 平衡
        balance = self._balance_factor(node)
        if balance > 1 and self._balance_factor(node.left) >= 0:
            return self._rotate_right(node)
        if balance < -1 and self._balance_factor(node.right) <= 0:
            return self._rotate_left(node)
        if balance > 1 and self._balance_factor(node.left) < 0:
            node.left = self._rotate_left(node.left)
            return self._rotate_right(node)
        if balance < -1 and self._balance_factor(node.right) > 0:
            node.right = self._rotate_right(node.right)
            return self._rotate_left(node)

        return node

    def _min_value_node(self, node):
        current = node
        while current.left:
            current = current.left
        return current

    def get_position(self, obj_id):
        """获取元素的位置索引"""
        value = self.id_to_value[obj_id]
        return self._get_position(self.root, value, 0)

    def __iter__(self):
        """生成有序迭代器"""
        stack = []
        current = self.root
        while stack or current:
            while current:
                stack.append(current)
                current = current.left
            current = stack.pop()
            for _ in range(len(self.value_to_ids[current.value])):
                yield current.value
            current = current.right

request_data_list = [OptimizedOrderedList() for _ in range(110)]
request_data_list[0].add(1250, 10)     
request_data_list[0].add(2475, 242)
request_data_list[0].add(5025, 31)
print(list(request_data_list[0]))
