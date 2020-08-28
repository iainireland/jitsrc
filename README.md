# Disclaimer

This is hacky, poorly tested, and probably quite fragile. I hope it works, but I make no guarantees.

# Purpose

This is a gdb extension to automate the process of tracing backwards in rr from a jit instruction to the code that generated that instruction.

# Installation

Add "source /path/to/jitsrc.py" to your `.gdbinit` file.

# Usage
```
  (rr) x/10i $pc

  => 0x240e954ac13a:	pushq  (%rbx)

  (rr) jitsrc 0x240e954ac13a
```
# Implementation

My workflow for finding	the source of a jit instruction manually is as follows:

1. Set a watchpoint on the address of that instruction.
2. Reverse-continue to find who wrote to that address.
3. It's a memcpy! Hop up a couple of frames to find the source of the memcpy (where `new\_address = src\_of\_memcpy + (old\_address - dst\_of\_memcpy)`).
4. Repeat steps 1-3 with the new address until I find the actual origin.

This plugin uses the same approach. The most finicky part is recognizing a memcpy and figuring out how to calculate the new address.

To make it work, jitsrc.py contains an array of pattern tuples of the form `(base\_name, hops, func\_name, source\_var, dest\_var)`. For example:
```
   ("\_\_memmove\_avx\_unaligned\_erms", 1, "js::jit::X86Encoding::BaseAssembler::executableCopy", "src", "dst")

   ("mozilla::detail::VectorImpl<.&ast;>::new\_<.&ast;>", 3, "mozilla::Vector<.&ast;>::convertToHeapStorage", "beginNoCheck()", "newBuf")
```
Each tuple indicates:

  - `base\_name`: a regex matching the name of the function that implements the actual write
  - `hops`: the number of stack frames between `base\_name` and `func\_name`
  - `func\_name`: a regex matching the name of the function that calls memcpy
  - `source\_var`: an expression that can be evaluated in the frame corresponding to `func\_name` to get the source of the memcpy
  - `dest\_var`: an expression that can be evaluated in the frame corresponding to `func\_name` to get the source of the memcpy

To skip past other forms of memcpy, add new entries to the pattern array. Pull requests welcome.

# Limitations

To the extent that I've tested this at all, it was only on `--enable-debug` `--disable-optimize` builds. I expect it would be harder to automate this process for optimized builds.
