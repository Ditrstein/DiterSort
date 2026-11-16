#You get random time and random sort, if sort will be within that time records will be sorted, if not they will be shuffeled and algorythm will try again


"""Sort with a random time limit and a randomly chosen method."""

import argparse
import random
import sys
from collections.abc import Sequence
from fractions import Fraction
from itertools import count
from math import ceil
from time import get_clock_info, perf_counter_ns


LONG_LIMIT_CHANCE_PERCENT = 0.0001  #Funny


def shuffle_by_removal(numbers: Sequence[int]) -> list[int]:
    """Pick one value at a time and rebuild the remaining pool on every draw."""
    remaining = list(numbers)
    shuffled = []
    while remaining:
        index = random.randrange(len(remaining))
        shuffled = shuffled + [remaining[index]]
        remaining = remaining[:index] + remaining[index + 1:]
    return shuffled


def bubble_sort(numbers: list[int]) -> None:
    # Repeat the full pass even when earlier passes have sorted the list.
    for _ in range(len(numbers)):
        for index in range(1, len(numbers)):
            if numbers[index - 1] > numbers[index]:
                numbers[index - 1], numbers[index] = numbers[index], numbers[index - 1]


def insertion_sort(numbers: list[int]) -> None:
    # Find each insertion point from the front and rebuild the whole list.
    for end in range(len(numbers)):
        value = numbers[end]
        position = 0
        while position < end and numbers[position] <= value:
            position += 1
        numbers[:] = numbers[:position] + [value] + numbers[position:end] + numbers[end + 1:]


def selection_sort(numbers: list[int]) -> None:
    # Make a fresh copy of the unsorted suffix for every selection.
    for start in range(len(numbers)):
        suffix = numbers[start:]
        smallest = 0
        for index in range(1, len(suffix)):
            if suffix[index] < suffix[smallest]:
                smallest = index
        chosen = start + smallest
        numbers[start], numbers[chosen] = numbers[chosen], numbers[start]


def merge_sort(numbers: list[int]) -> None:
    if len(numbers) < 2:
        return

    middle = len(numbers) // 2
    left = numbers[:middle]
    right = numbers[middle:]
    merge_sort(left)
    merge_sort(right)

    # Removing the first value shifts the rest of its list on every step.
    merged = []
    while left or right:
        if not right or (left and left[0] <= right[0]):
            merged = merged + [left.pop(0)]
        else:
            merged = merged + [right.pop(0)]
    numbers[:] = merged


def quick_sort(numbers: list[int]) -> None:
    pending = [numbers.copy()]
    ordered = []
    while pending:
        chunk = pending.pop()
        if len(chunk) < 2:
            ordered.extend(chunk)
            continue

        # The first pivot gives poor splits for ordered or equal values.
        pivot = chunk[0]
        rest = chunk[1:]
        smaller = []
        for value in rest:
            if value < pivot:
                smaller = smaller + [value]
        greater_or_equal = []
        for value in rest:
            if value >= pivot:
                greater_or_equal = greater_or_equal + [value]
        pending.extend((greater_or_equal, [pivot], smaller))

    numbers[:] = ordered


def heap_sort(numbers: list[int]) -> None:
    def sift_down(root: int, size: int) -> None:
        while (child := 2 * root + 1) < size:
            if child + 1 < size and numbers[child] < numbers[child + 1]:
                child += 1
            if numbers[root] >= numbers[child]:
                break
            numbers[root], numbers[child] = numbers[child], numbers[root]
            root = child

    for end in range(len(numbers) - 1, 0, -1):
        # Rebuild the entire heap before extracting each maximum.
        size = end + 1
        for root in range(size // 2 - 1, -1, -1):
            sift_down(root, size)
        numbers[0], numbers[end] = numbers[end], numbers[0]


def shell_sort(numbers: list[int]) -> None:
    # Make a complete pass for every positive gap below the list length.
    for gap in range(len(numbers) - 1, 0, -1):
        for index in range(gap, len(numbers)):
            value = numbers[index]
            position = index
            while position >= gap and numbers[position - gap] > value:
                numbers[position] = numbers[position - gap]
                position -= gap
            numbers[position] = value


def stooge_sort(numbers: list[int]) -> None:
    def sort_range(first: int, last: int) -> None:
        if numbers[first] > numbers[last]:
            numbers[first], numbers[last] = numbers[last], numbers[first]

        length = last - first + 1
        if length > 2:
            third = length // 3
            sort_range(first, last - third)
            sort_range(first + third, last)
            sort_range(first, last - third)

    if numbers:
        sort_range(0, len(numbers) - 1)


def bogosort(numbers: list[int], deadline_ns: int) -> bool:
    """Shuffle until sorted or until the attempt runs out of time."""
    while perf_counter_ns() <= deadline_ns:
        out_of_order_pairs = 0
        for index in range(1, len(numbers)):
            if numbers[index - 1] > numbers[index]:
                out_of_order_pairs += 1
        if out_of_order_pairs == 0:
            return True
        numbers[:] = shuffle_by_removal(numbers)
    return False


SORTING_METHODS = (
    ("bubble sort", bubble_sort),
    ("insertion sort", insertion_sort),
    ("selection sort", selection_sort),
    ("merge sort", merge_sort),
    ("quicksort", quick_sort),
    ("heapsort", heap_sort),
    ("Shell sort", shell_sort),
    ("stooge sort", stooge_sort),
    ("bogosort", bogosort),
)

def draw_time_limit_ns(time_range_us: tuple[int, int] | None) -> int:
    if time_range_us is not None:
        return random.randint(*time_range_us) * 1_000
    probability = Fraction(str(LONG_LIMIT_CHANCE_PERCENT)) / 100
    if random.randrange(probability.denominator) < probability.numerator:
        return random.randint(100, 500) * 1_000
    return random.randint(1, 10)


def randomized_sort(
    numbers: Sequence[int],
    min_us: int | None = None,
    max_us: int | None = None,
    *,
    max_attempts: int | None = None,
    show_attempts: bool = False,
) -> list[int]:
    """Return a copy in ascending order from the first attempt within its limit."""
    time_range_us = None
    if min_us is not None or max_us is not None:
        min_us = 1 if min_us is None else min_us
        max_us = 40 if max_us is None else max_us
        if not 1 <= min_us <= max_us:
            raise ValueError("The time limits must satisfy 1 <= MIN <= MAX.")
        time_range_us = (min_us, max_us)
    if max_attempts is not None and max_attempts < 1:
        raise ValueError("The maximum number of attempts must be at least 1.")

    for attempt in count(1):
        limit_ns = draw_time_limit_ns(time_range_us)
        result = shuffle_by_removal(numbers)
        name, sort = random.choice(SORTING_METHODS)

        start_ns = perf_counter_ns()
        if sort is bogosort:
            finished = bogosort(result, start_ns + limit_ns)
        else:
            sort(result)
            finished = True
        # A clock that has not advanced cannot measure a sub-tick sort.
        elapsed_ns = perf_counter_ns() - start_ns
        clock_resolution_ns = ceil(get_clock_info("perf_counter").resolution * 1_000_000_000)
        elapsed_ns = max(clock_resolution_ns, elapsed_ns)

        within_limit = finished and elapsed_ns <= limit_ns
        if show_attempts:
            status = "within time limit" if within_limit else "retrying"
            if not within_limit and attempt == max_attempts:
                status = "attempt limit reached"
            print(f"Attempt {attempt} | {name} | {elapsed_ns:,} ns / {limit_ns:,} ns | {status}")

        if within_limit:
            return result
        if attempt == max_attempts:
            raise TimeoutError(f"Every attempt exceeded its time limit ({attempt} total).")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=(
            f"By default, {100 - LONG_LIMIT_CHANCE_PERCENT}% of attempts get 1 to 10 ns "
            f"and {LONG_LIMIT_CHANCE_PERCENT}% get 100 to 500 us."
        ),
    )
    parser.add_argument(
        "numbers", nargs="*", type=int,
        help="integers to sort (defaults to a sample of 60 numbers)",
    )
    parser.add_argument(
        "--limit-us", nargs=2, type=int, metavar=("MIN", "MAX"),
        help="draw every limit from a custom range in microseconds",
    )
    parser.add_argument(
        "--max-attempts", type=int, metavar="N",
        help="stop after N attempts if none meets its time limit",
    )
    args = parser.parse_args()
    numbers = args.numbers or shuffle_by_removal(range(1, 61))
    print("Input:", numbers)

    try:
        result = randomized_sort(
            numbers, *(args.limit_us or ()), max_attempts=args.max_attempts, show_attempts=True,
        )
    except ValueError as error:
        parser.error(str(error))
    except TimeoutError as error:
        print(error, file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nSorting interrupted.", file=sys.stderr)
        return 130

    print("Result:", result)
    
    while(true):{}
    return 0


if __name__ == "__main__":
    sys.exit(main())
