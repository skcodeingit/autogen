import itertools


def generate_partitions(N):
    """
    Generate all unique partitions of a set of size N (N is even)
    into two subsets of equal size, represented as binary vectors.

    The binary vector has N bits where exactly N/2 bits are 1 and
    N/2 bits are 0. To ensure uniqueness (as partitions are
    unordered), the first bit is fixed to 0.

    Parameters:
        N (int): The number of items in the set. Must be even.

    Returns:
        List[str]: A list of binary strings representing the partitions.
    """
    if N % 2 != 0:
        raise ValueError("N must be even.")

    partitions = []
    # Fix the first bit to 0 to avoid duplicate partitions.
    # Then choose (N/2) positions out of the remaining (N-1) to be 1.
    for comb in itertools.combinations(range(1, N), N // 2):
        binary_vector = ['0'] * N
        for index in comb:
            binary_vector[index] = '1'
        partitions.append("".join(binary_vector))

    return partitions


def write_partitions_to_file(partitions, filename):
    """
    Write the list of binary vector partitions to a text file,
    with each vector on a separate line.

    Parameters:
        partitions (List[str]): The partitions to be written.
        filename (str): The name of the output file.
    """
    with open(filename, "w") as file:
        for partition in partitions:
            file.write(partition + "\n")


if __name__ == "__main__":
    # Change N to any even number you wish to process.
    N = 10  # Example: N = 10
    partitions = generate_partitions(N)

    # Randomize the order of partitions, using a seed from the current time.
    import random
    import time
    random.seed(int(time.time()))
    random.shuffle(partitions)

    write_partitions_to_file(partitions, "partitions.txt")
    print(f"{len(partitions)} partitions for N = {N} have been written to partitions.txt.")
