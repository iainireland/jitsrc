import gdb

patterns = [("__memmove_avx_unaligned_erms", 1, "js::jit::X86Encoding::BaseAssembler::executableCopy", "src", "dst"),
            ("__memmove_avx_unaligned_erms", 1, "arena_t::RallocSmallOrLarge", "aPtr", "ret")]

class JitSource(gdb.Command):
    def __init__(self):
        super(JitSource, self).__init__("jitsrc", gdb.COMMAND_RUNNING)
        self.dont_repeat()

    def disable_breakpoints(self):
        for b in gdb.breakpoints():
            b.enabled = False

    def search_stack(self, base_name, hops, name, src, dst, address):
        if gdb.newest_frame().name() != base_name:
            return None
        f = gdb.newest_frame();
        for _ in range(hops):
            f = f.older()
        if f.name() != name:
            return None
        src_val = f.read_var(src)
        dst_val = f.read_var(dst)
        return hex(src_val + int(address, 16) - dst_val)

    def next_address(self, old):
        for pattern in patterns:
            found = self.search_stack(pattern[0],
                                      pattern[1],
                                      pattern[2],
                                      pattern[3],
                                      pattern[4],
                                      old)
            if found:
                return found
        return None


    def runback(self, address):
        self.disable_breakpoints()
        b = gdb.Breakpoint("*" + address,
                           type=gdb.BP_WATCHPOINT,
                           wp_class=gdb.WP_WRITE,
                           internal=True)
        while b.hit_count == 0:
            gdb.execute('rc', to_string=True)
        b.delete()
        next = self.next_address(address)
        if next:
            self.runback(next)


    def invoke(self, arg, from_tty):
        args = gdb.string_to_argv(arg)
        address = args[0]
        self.runback(address)

# Register to the gdb runtime
JitSource()
