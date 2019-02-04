# Purpose

This is a gdb extension to automate the process of tracing backwards in rr from a jit instruction to the code that generated that instruction.

# Installation

Add "source /path/to/jitsrc.py" to your .gdbinit file.

# Implementation

My workflow for finding	the source of a jit instruction manually is as follows:

1. Set a watchpoint on the address of that instruction.
2. Reverse-continue to find who wrote to that address.
3. It's a memcpy! Hop up a couple of frames to find the source of the memcpy (where new_address = src_of_memcpy + (old_address - dst_of_memcpy)).
4. Repeat steps 1-3 with the new address until I find the actual origin.

This plugin uses the same approach. The most finicky part is recognizing a memcpy and figuring out how to calculate the new address.

To make it work, jitsrc.py contains an array of pattern tuples of the form "(base_name, hops, func_name, source_var, dest_var)". For example:

   ("__memmove_avx_unaligned_erms", 1, "js::jit::X86Encoding::BaseAssembler::executableCopy", "src", "dst"),

Each tuple indicates:
- base_name: the name of the function that implements the actual write
- hops: the number of stack frames between base_name and func_name
- func_name: the name of the function that calls memcpy
- source_var: the variable in func_name that holds the source of the memcpy
- dest_var: the variable in func_name that holds the destination of the memcpy

To skip past other forms of memcpy, add new entries to the pattern array. Pull requests welcome.

Limitations:

To the extent that I've tested this at all, it was only on --enable-debug --disable-optimize builds. I expect it would be harder to automate this process for optimized builds.