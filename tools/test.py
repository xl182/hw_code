import inspect

def main():
    frame = inspect.currentframe()

    def current_line_number():
        # 获取当前栈帧
        # 返回当前执行行的行号
        return frame.f_lineno
    return current_line_number()

print(f"当前行号是: {main()}")
print(f"当前行号是: {main()}")
