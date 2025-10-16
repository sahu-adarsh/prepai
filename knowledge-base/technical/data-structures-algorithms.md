# Data Structures and Algorithms Interview Questions

## Arrays and Strings

### Easy Level

**Q: Find the maximum element in an array**
- Expected approach: Linear scan, track maximum
- Time complexity: O(n)
- Follow-up: What if array is rotated sorted?

**Q: Reverse a string in place**
- Expected approach: Two pointers from both ends
- Time complexity: O(n)
- Follow-up: Reverse only words, not the entire string

**Q: Check if a string is a palindrome**
- Expected approach: Two pointers or compare with reversed
- Time complexity: O(n)
- Follow-up: Ignore spaces and punctuation

**Q: Find the first duplicate in an array**
- Expected approach: Hash set for O(n) or modify array for O(1) space
- Follow-up: Find all duplicates

### Medium Level

**Q: Find two numbers that sum to a target (Two Sum)**
- Expected approach: Hash map for O(n) time
- Brute force: O(n²)
- Follow-up: What if array is sorted? (Two pointers)

**Q: Longest substring without repeating characters**
- Expected approach: Sliding window with hash map
- Time complexity: O(n)
- Space complexity: O(min(m,n)) where m is charset size

**Q: Merge overlapping intervals**
- Expected approach: Sort by start time, then merge
- Time complexity: O(n log n)
- Example: [[1,3], [2,6], [8,10]] → [[1,6], [8,10]]

**Q: Product of array except self**
- Expected approach: Prefix and suffix products
- Constraint: No division allowed
- Time: O(n), Space: O(1) excluding output

**Q: Container with most water**
- Expected approach: Two pointers from both ends
- Time complexity: O(n)
- Key insight: Move pointer with smaller height

### Hard Level

**Q: Trapping rain water**
- Expected approach: Two pointers or precompute max heights
- Time complexity: O(n)
- Visualize: Given heights, how much water can be trapped?

**Q: Minimum window substring**
- Expected approach: Sliding window with character frequency map
- Time complexity: O(n + m)
- Example: Find smallest substring containing all characters of pattern

**Q: Median of two sorted arrays**
- Expected approach: Binary search
- Time complexity: O(log(min(m,n)))
- Naive: Merge and find median - O(m+n)

---

## Linked Lists

### Easy Level

**Q: Reverse a linked list**
- Expected approach: Iterative with three pointers
- Time complexity: O(n)
- Follow-up: Reverse recursively

**Q: Detect cycle in linked list**
- Expected approach: Floyd's cycle detection (slow/fast pointers)
- Time complexity: O(n)
- Space complexity: O(1)

**Q: Find middle of linked list**
- Expected approach: Slow/fast pointer
- Time complexity: O(n)
- Follow-up: Handle even length lists

### Medium Level

**Q: Merge two sorted linked lists**
- Expected approach: Two pointers, compare and merge
- Time complexity: O(n + m)
- Follow-up: Merge k sorted lists (use heap)

**Q: Remove nth node from end**
- Expected approach: Two pointers with n gap
- Time complexity: O(n)
- Edge case: Removing head

**Q: Add two numbers represented as linked lists**
- Expected approach: Traverse both, handle carry
- Time complexity: O(max(m,n))
- Example: 342 + 465 = 807 (stored as 2→4→3 + 5→6→4)

**Q: Reorder list L0→L1→…→Ln to L0→Ln→L1→Ln-1→…**
- Expected approach: Find middle, reverse second half, merge
- Time complexity: O(n)
- Space complexity: O(1)

### Hard Level

**Q: Reverse nodes in k-group**
- Expected approach: Reverse k nodes at a time
- Time complexity: O(n)
- Example: 1→2→3→4→5, k=2 → 2→1→4→3→5

---

## Trees and Graphs

### Easy Level

**Q: Maximum depth of binary tree**
- Expected approach: Recursive DFS or BFS
- Time complexity: O(n)

**Q: Invert binary tree**
- Expected approach: Recursive swap of left and right
- Time complexity: O(n)

**Q: Check if binary tree is symmetric**
- Expected approach: Recursive mirror check
- Time complexity: O(n)

**Q: Binary tree level order traversal**
- Expected approach: BFS with queue
- Time complexity: O(n)

### Medium Level

**Q: Validate binary search tree**
- Expected approach: Recursive with min/max bounds
- Time complexity: O(n)
- Common mistake: Only checking immediate children

**Q: Lowest common ancestor of BST**
- Expected approach: Leverage BST property
- Time complexity: O(h)
- Follow-up: What if it's just a binary tree?

**Q: Number of islands (2D grid)**
- Expected approach: DFS or BFS to mark connected components
- Time complexity: O(m × n)
- Follow-up: Union-Find approach

**Q: Clone graph**
- Expected approach: DFS/BFS with hash map for visited nodes
- Time complexity: O(n + e)

**Q: Course schedule (detect cycle in directed graph)**
- Expected approach: Topological sort or DFS with colors
- Time complexity: O(V + E)

### Hard Level

**Q: Binary tree maximum path sum**
- Expected approach: Recursive DFS, track global max
- Time complexity: O(n)
- Key: Path can start and end at any node

**Q: Serialize and deserialize binary tree**
- Expected approach: BFS or DFS with markers for null
- Time complexity: O(n)

**Q: Word ladder (shortest transformation sequence)**
- Expected approach: BFS with word dictionary
- Time complexity: O(M² × N) where M is word length, N is dictionary size

---

## Dynamic Programming

### Medium Level

**Q: Climbing stairs (Fibonacci variant)**
- Expected approach: DP or recursion with memoization
- Time complexity: O(n)
- Space optimization: O(1) using two variables

**Q: House robber**
- Expected approach: DP, track max with/without robbing current
- Time complexity: O(n)
- Follow-up: Houses in a circle

**Q: Longest increasing subsequence**
- Expected approach: DP O(n²) or binary search O(n log n)
- Example: [10,9,2,5,3,7,101,18] → length 4

**Q: Coin change (minimum coins to make amount)**
- Expected approach: Bottom-up DP
- Time complexity: O(amount × coins)
- Return -1 if impossible

**Q: Unique paths in grid**
- Expected approach: DP or combinatorics
- Time complexity: O(m × n)
- Follow-up: With obstacles

### Hard Level

**Q: Edit distance (Levenshtein distance)**
- Expected approach: 2D DP
- Time complexity: O(m × n)
- Operations: Insert, delete, replace

**Q: Longest palindromic substring**
- Expected approach: Expand around center or DP
- Time complexity: O(n²)
- Advanced: Manacher's algorithm O(n)

**Q: Word break**
- Expected approach: DP with dictionary lookup
- Time complexity: O(n² × m) where m is max word length

**Q: Maximum subarray sum (Kadane's algorithm)**
- Expected approach: DP, track current and global max
- Time complexity: O(n)

---

## Searching and Sorting

### Easy Level

**Q: Binary search in sorted array**
- Expected approach: Classic binary search
- Time complexity: O(log n)
- Edge cases: Empty array, single element

**Q: First bad version**
- Expected approach: Binary search with API calls
- Time complexity: O(log n)

### Medium Level

**Q: Search in rotated sorted array**
- Expected approach: Modified binary search
- Time complexity: O(log n)
- Key: Determine which half is sorted

**Q: Find peak element**
- Expected approach: Binary search
- Time complexity: O(log n)
- Multiple peaks possible, find any

**Q: Kth largest element in array**
- Expected approach: Quickselect O(n) average or heap O(n log k)
- Follow-up: Find median

**Q: Merge intervals**
- Expected approach: Sort and merge
- Time complexity: O(n log n)

### Hard Level

**Q: Median from data stream**
- Expected approach: Two heaps (max heap for lower half, min heap for upper)
- Insert: O(log n)
- Get median: O(1)

---

## Hash Tables and Sets

### Medium Level

**Q: Group anagrams**
- Expected approach: Hash map with sorted string as key
- Time complexity: O(n × k log k) where k is max string length

**Q: Top K frequent elements**
- Expected approach: Hash map + bucket sort or heap
- Time complexity: O(n) with bucket sort

**Q: Longest consecutive sequence**
- Expected approach: Hash set for O(n)
- Time complexity: O(n)
- Example: [100,4,200,1,3,2] → 4 (sequence: 1,2,3,4)

---

## Stacks and Queues

### Easy Level

**Q: Valid parentheses**
- Expected approach: Stack
- Time complexity: O(n)
- Handle: (), {}, []

### Medium Level

**Q: Implement min stack (with O(1) min operation)**
- Expected approach: Auxiliary stack or single stack with min tracking
- All operations: O(1)

**Q: Evaluate reverse polish notation**
- Expected approach: Stack for operands
- Time complexity: O(n)

**Q: Daily temperatures (next greater element)**
- Expected approach: Monotonic stack
- Time complexity: O(n)

**Q: Sliding window maximum**
- Expected approach: Deque (monotonic queue)
- Time complexity: O(n)

---

## Complexity Analysis Guidelines

**Time Complexity Common Patterns:**
- O(1): Hash table lookup, array access
- O(log n): Binary search, balanced tree operations
- O(n): Linear scan, single loop
- O(n log n): Efficient sorting, divide and conquer
- O(n²): Nested loops, certain DP problems
- O(2ⁿ): Recursive subsets, permutations

**Space Complexity Considerations:**
- Recursion: O(h) for call stack where h is depth
- DP: Often O(n) or O(n²) for memoization
- Optimization: Can we reduce space? (Rolling array in DP)

---

## Coding Best Practices

1. **Clarify requirements** before coding
2. **Discuss approach** and time/space complexity
3. **Start with brute force** if stuck, then optimize
4. **Consider edge cases**: Empty input, single element, duplicates, negative numbers
5. **Write clean code**: Meaningful variable names, proper indentation
6. **Test with examples**: Walk through your code
7. **Explain as you code**: Interviewer wants to understand your thought process

---

## Common Pitfalls to Avoid

- Off-by-one errors in loops
- Not handling null/empty inputs
- Integer overflow (use long if needed)
- Modifying input when not allowed
- Not considering negative numbers or zeros
- Assuming sorted input when not specified
- Forgetting to return a value

---

*These questions are representative of what you might encounter in technical interviews at top tech companies. Practice explaining your approach clearly and concisely.*
