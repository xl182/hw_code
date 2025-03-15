import matplotlib.pyplot as plt

def assign_files_to_folders(file_sizes, num_folders, folder_capacity):
    folders = [0] * num_folders
    assignments = {i: [] for i in range(len(file_sizes))}
    
    sorted_files = sorted(enumerate(file_sizes), key=lambda x: -x[1])
    
    for idx, size in sorted_files:
        used_folders = []
        for _ in range(3):
            min_folder = min(enumerate(folders), key=lambda x: x[1])[0]
            if folders[min_folder] + size <= folder_capacity:
                folders[min_folder] += size
                used_folders.append(min_folder)
            else:
                for f in range(num_folders):
                    if folders[f] + size <= folder_capacity and f not in used_folders:
                        folders[f] += size
                        used_folders.append(f)
                        break
                if f not in used_folders and folders[f] + size > folder_capacity:
                    print("无法放置文件{}的备份，现有文件夹容量不足".format(idx))
                    return None, None
        assignments[idx] = used_folders
    
    return folders, assignments

file_sizes = [1067,
 799,
 1585,
 836,
 944,
 502,
 1399,
 783,
 494,
 712,
 631,
 1138,
 434,
 1107,
 545,
 1489]
num_folders = 10
folder_size = 5792

folders_usage, assignments = assign_files_to_folders(file_sizes, num_folders, folder_size)

if folders_usage is not None and assignments is not None:
    print("成功分配文件")
    # 绘制每个文件夹的使用情况
    plt.figure(figsize=(10, 6))
    plt.bar(range(num_folders), folders_usage, color='skyblue')
    plt.title('文件夹使用情况')
    plt.xlabel('文件夹编号')
    plt.ylabel('已使用容量')
    plt.xticks(range(num_folders))
    plt.ylim(0, folder_size)
    plt.show()
    
    # 绘制每个文件的分配情况
    plt.figure(figsize=(12, 6))
    for i in range(len(file_sizes)):
        if len(assignments[i]) == 3:
            plt.text(assignments[i][0], i, '★', color='red', ha='center', va='center')
            plt.text(assignments[i][1], i, '★', color='green', ha='center', va='center')
            plt.text(assignments[i][2], i, '★', color='blue', ha='center', va='center')
        plt.text(-1, i, str(file_sizes[i]), ha='right', va='center')
    
    plt.title('文件分配情况')
    plt.xlabel('文件夹编号')
    plt.ylabel('文件索引')
    plt.xlim(-2, num_folders)
    plt.ylim(-1, len(file_sizes))
    plt.yticks(range(len(file_sizes)), [f'文件 {i}' for i in range(len(file_sizes))])
    plt.show()
else:
    print("文件分配失败，请检查文件大小和文件夹容量")
print(assignments)