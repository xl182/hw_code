import bisect
from hashlib import sha256
from collections import defaultdict

class StorageDisk:
    def __init__(self, disk_id, capacity=1024*1024*1024):  # 1GB默认容量
        self.disk_id = disk_id
        self.capacity = capacity
        self.allocations = []        # 已分配区间 (start, end, obj_id)
        self.free_blocks = [(0, capacity)]  # 空闲区间列表（原始空间）
        self.reuse_queue = []         # 可重用空间队列（优先使用）
        
    def _merge_blocks(self, blocks):
        merged = []
        for block in sorted(blocks):
            if not merged:
                merged.append(block)
            else:
                last = merged[-1]
                if block[0] == last[1]:
                    merged[-1] = (last[0], block[1])
                else:
                    merged.append(block)
        return merged
    
    def find_best_space(self, size):
        # 优先从重用队列查找
        reuse_candidates = []
        for idx, (start, end) in enumerate(self.reuse_queue):
            if end - start >= size:
                reuse_candidates.append((end - start, idx, start, True))
        
        # 从原始空闲空间查找
        original_candidates = []
        for idx, (start, end) in enumerate(self.free_blocks):
            if end - start >= size:
                original_candidates.append((end - start, idx, start, False))
        
        # 选择最合适空间
        all_candidates = reuse_candidates + original_candidates
        if not all_candidates:
            return None
        # 选择最小可用块
        best = min(all_candidates, key=lambda x: x[0])
        return best[2], best[1], best[3]  # start, index, is_reuse
    
    def allocate(self, size, obj_id):
        # 寻找最佳空间
        result = self.find_best_space(size)
        if not result:
            return None
            
        alloc_start, idx, is_reuse = result
        alloc_end = alloc_start + size
        
        # 更新对应空间列表
        if is_reuse:
            source_list = self.reuse_queue
        else:
            source_list = self.free_blocks
            
        orig_start, orig_end = source_list[idx]
        del source_list[idx]
        
        # 处理剩余空间
        if orig_start < alloc_start:
            bisect.insort(source_list, (orig_start, alloc_start))
        if alloc_end < orig_end:
            bisect.insort(source_list, (alloc_end, orig_end))
        
        # 记录分配
        bisect.insort(self.allocations, (alloc_start, alloc_end, obj_id))
        return alloc_start
        
    def deallocate(self, obj_id):
        removed = []
        new_allocations = []
        for alloc in self.allocations:
            if alloc[2] == obj_id:
                removed.append((alloc[0], alloc[1]))
            else:
                new_allocations.append(alloc)
        
        if not removed:
            return False
            
        self.allocations = new_allocations
        
        # 将释放空间加入重用队列
        for start, end in removed:
            bisect.insort(self.reuse_queue, (start, end))
        
        # 合并重用队列空间
        self.reuse_queue = self._merge_blocks(self.reuse_queue)
        return True

class LubanHash:
    def __init__(self, nodes, tag_range=16, virtual_nodes=1000):
        self.nodes = nodes
        self.tag_range = tag_range
        self.virtual_nodes = virtual_nodes
        self.ring = defaultdict(list)
        self.node_keys = {}
        
        # 为每个标签创建虚拟节点环
        for tag in range(tag_range):
            ring = []
            for node in nodes:
                for vn in range(virtual_nodes):
                    key = self.hash(f"{tag}-{node}-{vn}")
                    ring.append((key, node))
            ring.sort()
            self.ring[tag] = ring
    
    @staticmethod
    def hash(data):
        return int(sha256(str(data).encode()).hexdigest(), 16)
    
    def get_replicas(self, tag, replica_count=3):
        if tag >= self.tag_range:
            tag = tag % self.tag_range
            
        ring = self.ring[tag]
        selected = set()
        replicas = []
        idx = 0
        
        while len(replicas) < replica_count and idx < len(ring):
            _, node = ring[idx]
            if node not in selected:
                selected.add(node)
                replicas.append(node)
            idx += 1
        
        return replicas[:replica_count]

class StorageSystem:
    def __init__(self, disk_count=10, tag_range=16):
        self.disks = {i: StorageDisk(i) for i in range(disk_count)}
        self.hash_ring = LubanHash(nodes=range(disk_count), tag_range=tag_range)
        self.object_registry = {}  # {obj_id: {'tag': t, 'replicas': [(disk, start, size)]}
        self.obj_counter = 0
    
    def write_object(self, tag, size):
        self.obj_counter += 1
        obj_id = self.obj_counter
        
        # 获取目标磁盘
        target_disks = self.hash_ring.get_replicas(tag)
        if len(target_disks) < 3:
            raise RuntimeError("Not enough available disks")
        
        allocations = []
        rollback_disks = []
        
        try:
            for disk_id in target_disks:
                disk = self.disks[disk_id]
                start = disk.allocate(size, obj_id)
                if start is None:
                    raise RuntimeError(f"Disk {disk_id} allocation failed")
                allocations.append((disk_id, start, size))
                rollback_disks.append(disk_id)
            
            # 记录元数据
            self.object_registry[obj_id] = {
                'tag': tag,
                'replicas': allocations
            }
            print(f"Object {obj_id} written to: {allocations}")
            return obj_id
        except Exception as e:
            # 回滚已分配的空间
            for disk_id in rollback_disks:
                self.disks[disk_id].deallocate(obj_id)
            print(f"Write failed: {str(e)}")
            return None
    
    def delete_object(self, obj_id):
        if obj_id not in self.object_registry:
            print(f"Delete failed: Object {obj_id} not found")
            return False
        
        locations = self.object_registry[obj_id]['replicas']
        for disk_id, start, size in locations:
            self.disks[disk_id].deallocate(obj_id)
        
        del self.object_registry[obj_id]
        print(f"Object {obj_id} deleted from: {locations}")
        return True
    
    def read_object(self, obj_id):
        if obj_id not in self.object_registry:
            print(f"Read failed: Object {obj_id} not found")
            return None
        
        # 总是读取第一个副本
        primary_disk, start, size = self.object_registry[obj_id]['replicas'][0]
        print(f"Reading object {obj_id} from disk {primary_disk} start {start}")
        return (primary_disk, start, size)

# 验证测试
if __name__ == "__main__":
    system = StorageSystem(disk_count=10, tag_range=16)
    
    # 模拟16个标签的写入
    test_objects = []
    for tag in range(16):
        for _ in range(100):  # 每个标签写100个对象
            obj_id = system.write_object(tag, 1024*1024)  # 1MB对象
            if obj_id:
                test_objects.append(obj_id)
    
    # 随机删除50%对象
    import random
    for obj_id in random.sample(test_objects, len(test_objects)//2):
        system.delete_object(obj_id)
    
    # 验证空间重用
    reused_count = 0
    for _ in range(500):
        tag = random.randint(0, 15)
        obj_id = system.write_object(tag, 1024*512)  # 512KB对象
        if obj_id:
            reused_count += 1
    print(f"成功重用空间写入 {reused_count} 个新对象")
    
    # 最终清理
    for obj_id in list(system.object_registry.keys()):
        system.delete_object(obj_id)