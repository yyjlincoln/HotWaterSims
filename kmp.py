# Thanks to the tutorial at:
# https://www.youtube.com/watch?v=dgPabAsTFa8
# Code written by Lincoln

def prefix_table(pattern: [str, bytes]) -> list:
    # Start from which character. Here is the second one as the first one (len=0) must be 0.
    i = 1
    l = 0  # Length of the prefix / suffix
    prefix = []

    # The first one must be 0 as it is only length 1 and the prefix must be shorted than itself
    prefix.append(0)

    while i < len(pattern):
        # From the previous one, if you can know that the "new" number is the same one as the next number from previous comparison,
        # then the max prefix length must be increased.

        # Starting from the second one, if the last one (which is l) is the same as the first one
        if pattern[i] == pattern[l]:
            l += 1  # Increase the max length of matched pattern
            prefix.append(l)
            # Compare the next one (i.e. increase i so it's at the last letter)
            i += 1
        else:
            if l > 0:
                # It gets the max length from the last round, then it moves the pointer to that position so it avoids repeated
                # comparisons (which are the same) all the way to that position.
                # In other words, this comparison did not work out so the pointer moved back to the previous working one (which
                # have the longest same prefix and suffix) and then try to compare from there. If the comparison works, it will
                # be added to the table via the above if.
                l = prefix[l-1]
            else:
                # When there the longest possible prefix and suffix is 0, i.e. there is no more possible solution, set the prefix
                # number to 0 and compare the next one.
                prefix.append(0)
                i += 1  # Compare the next one

    return prefix


def move_prefix_table(table: list) -> list:
    for i in range(len(table)-1, 0, -1):
        # Shift everything to the right, except for the last one
        table[i] = table[i-1]

    table[0] = -1  # Set the first one to be -1
    return table


def kmp_search(pattern: [str, bytes], text: [str, bytes]):
    # Generate prefix table
    prefix = move_prefix_table(prefix_table(pattern))
    # Now try to match the string
    i = 0  # Pointer of the pattern
    j = 0  # Pointer of the text
    m = len(pattern)
    n = len(text)

    while j < n:
        if i == m-1 and text[j] == pattern[i]:
            return j-i
        if text[j] == pattern[i]:
            i += 1
            j += 1
        else:
            i = prefix[i] # Align with the prefix index, avoid repeated comparisons
            # Now, check if the thing hits -1
            if i == -1:
                i += 1
                j += 1
                # Move both i and j to the right and skip all comparisons
    return -1
