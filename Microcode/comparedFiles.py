running = True
with open("received.txt", 'r') as result:
    with open("legible.txt", 'r') as source:
        result.readline()
        while running:
            res = result.readline()
            src = source.readline()
            if res != src:
                print(res)
                print(src)
                print("")
                running = False
