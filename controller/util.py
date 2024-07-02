def log(prefix="main"):
    def __(*msgs, **kwargs):
        print(f'[{prefix}]', end=": ")
        print(*msgs, **kwargs)
    return __