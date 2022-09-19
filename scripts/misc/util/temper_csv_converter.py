import sys

if __name__ == "__main__":
    name = sys.argv[1]
    file_in = sys.argv[2]

    with open(file_in, 'r') as f:
        for line in f.readlines():
            time, value = line.strip().split(",")
            print(f"{time},{name},{value}")
