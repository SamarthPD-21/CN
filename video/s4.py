from common import *


class S4(VScene):
    def construct(self):
        self.session_title(
            4, "nginx and the Code That Explains It", "Apache made the worker cheaper. nginx deleted it.",
            "Session four. nginx, and the code that explains it. Every design in this session was someone's answer to a constraint that may no longer exist. "
            "Knowing which constraint tells you a law from a habit.")
        self.ch_history()
        self.ch_apache_decade()
        self.ch_java()
        self.ch_2002()
        self.ch_nginx_origin()
        self.ch_process_model()
        self.ch_loop()
        self.ch_accept()
        self.ch_select_epoll()
        self.ch_stale()
        self.ch_sendfile()
        self.ch_proxy()
        self.ch_cache()
        self.ch_cache_lines()
        self.ch_location()
        self.ch_wrr()
        self.ch_try_files()
        self.ch_tree()
        self.ch_parser()
        self.ch_phases()
        self.ch_fcgi_header()
        self.ch_ladder()
        self.ch_ideas()
        self.quiz()

    # ------------------------------------------------------------------
    def ch_history(self):
        self.new_slide("History: the correction worth making", "First, a correction. The myth says: Berners-Lee wrote the first server, called Mosaic, and Mosaic became Apache. That is wrong. There were three separate programs.", C_ORANGE)
        rows = [("1990", "CERN httpd", "Berners-Lee, on a NeXT - the first web server", C_BLUE, "CERN httpd, by Tim Berners-Lee on a NeXT machine in nineteen ninety. That was the first web server."),
                ("1993", "NCSA Mosaic", "a browser (Andreessen) - inline images, the web goes mainstream", C_GREEN, "NCSA Mosaic, in nineteen ninety-three. It was a browser, not a server. It had inline images and took the web mainstream."),
                ("1993", "NCSA HTTPd", "Rob McCool - a server; invents CGI", C_PURPLE, "NCSA HTTPd, also nineteen ninety-three, by Rob McCool. That was a server, and it invented CGI."),
                ("1994", "McCool leaves", "development stalls - webmasters trade patches by mail", C_GREY, "In nineteen ninety-four McCool left, development stalled, and webmasters traded patches by mail."),
                ("1995", "Apache", "that patch set continued as a project: 'a patchy server'", C_RED, "In nineteen ninety-five that patch set continued as a project. A patchy server. Apache."),
                ("1996", "Apache #1", "passes NCSA HTTPd - number one for twenty years", C_YELLOW, "In nineteen ninety-six, Apache passed NCSA HTTPd, and stayed number one for twenty years.")]
        y = 2.0
        for yr, nm, d, c, nar in rows:
            g = VGroup(T(yr, 26, c, maxw=1.3), box(nm, c, w=2.8, h=0.62, size=22), T(d, 21, WHITE, maxw=7.2)).arrange(RIGHT, buff=0.35)
            g.move_to([0, y, 0]).shift(RIGHT * (-g.get_left()[0] - 6.4))
            with self.vo(nar):
                self.play(FadeIn(g, shift=RIGHT * 0.3), run_time=0.7)
            y -= 0.95

    def ch_apache_decade(self):
        self.new_slide("Apache spent a decade outrunning fork()", "Apache then spent a decade trying to outrun fork.", C_RED)
        cols = [("1.3 - prefork", C_RED, "Pool of processes forked at startup, not per request. Setup cost is off the request path. But one process still parks on one connection.",
                 "Apache one point three, prefork. A pool of processes forked at startup instead of per request. The setup cost leaves the request path. But one process still parks on one connection."),
                ("2.0 - worker MPM", C_ORANGE, "Processes running many threads. 8 MB shared plus a stack each. Linux pthreads in 1999 to 2002 were new and buggy.",
                 "Apache two point zero, the worker MPM. Processes running many threads, with eight megabytes shared and a stack each. Linux pthreads in nineteen ninety-nine to two thousand two were new and buggy."),
                ("2.4 - event MPM", C_GREEN, "A listener thread parks idle keep-alives on epoll and hands a worker a connection only when it has work. Default on Unix since 2.4.",
                 "Apache two point four, the event MPM. A listener thread parks idle keep-alives on epoll, and hands a worker a connection only when it has work. It is the default on Unix since two point four.")]
        gs = VGroup(*[VGroup(box(a, c, w=3.9, h=0.8, size=24), T(wrap(b, 28), 20, WHITE, maxw=3.9, line_spacing=0.9)).arrange(DOWN, buff=0.3) for a, c, b, _ in cols])
        gs.arrange(RIGHT, buff=0.3, aligned_edge=UP).shift(DOWN * 0.3)
        for g, (_, _, _, nar) in zip(gs, cols):
            with self.vo(nar):
                self.play(FadeIn(g, shift=UP * 0.2), run_time=0.9)
        t = T("Three architectures, one question: how do I make the per-connection worker cheaper?", 25, C_YELLOW, maxw=12.4).to_edge(DOWN, buff=0.5)
        with self.vo("Three architectures, one question: how do I make the per-connection worker cheaper? None of them was a different question."):
            self.play(FadeIn(t))

    def ch_java(self):
        self.new_slide("Java's answer: stop creating things", "Java's answer was different in style: stop creating things.", C_ORANGE)
        L = VGroup(T("CGI (1993) - every request:", 26, C_RED), T("fork + exec + load interpreter", 22), T("+ parse script + run + exit", 22)).arrange(DOWN, buff=0.2).move_to(LEFT * 3.4 + UP * 1.2)
        R = VGroup(T("Servlet (1997):", 26, C_GREEN), T("at startup: load the class,", 22), T("instantiate once", 22), T("per request: service(req, res)", 22, C_YELLOW), T("= a method call", 22)).arrange(DOWN, buff=0.2).move_to(RIGHT * 3.4 + UP * 1.2)
        with self.vo("CGI, from nineteen ninety-three, did all this for every request: fork, exec, load the interpreter, parse the script, run, exit."):
            self.play(FadeIn(L))
        with self.vo("The servlet, from nineteen ninety-seven, loads the class at startup and instantiates it once. Then each request is just a method call: service, request, response. The object outlives the request. That is the trick."):
            self.play(FadeIn(R))
        pts = [("J2EE (1999): a multi-layer app server - web tier, EJB tier, database", "J two E E, in nineteen ninety-nine, made this a multi-layer app server: a web tier, an E J B tier, and the database."),
               ("Connection pools do the same for the DB handshake - same move as prefork and FastCGI", "Connection pools do the same thing for the database handshake. It is the same move as prefork and FastCGI.")]
        self.bullets(pts, size=24, gap=0.35, shift=DOWN * 1.8)

    def ch_2002(self):
        self.new_slide("2002: the numbers", "Now it is two thousand two. Here are the numbers everyone was staring at.", C_YELLOW)
        nums = [("10,000", "concurrent connections - C10K, Dan Kegel, 1999", C_BLUE, "Ten thousand concurrent connections. That is C ten K, Dan Kegel, nineteen ninety-nine."),
                ("8 MB", "stack per thread -> 10k threads = 80 GB address space", C_RED, "Eight megabytes of stack per thread. Ten thousand threads is eighty gigabytes of address space."),
                ("1024", "FD_SETSIZE, hard-coded - ulimit doesn't move it", C_ORANGE, "And one thousand twenty-four, FD_SETSIZE, hard-coded. A ulimit does not move it.")]
        y = 1.4
        for big, small, c, nar in nums:
            g = VGroup(T(big, 52, c, maxw=3.6), T(small, 24, WHITE, maxw=8)).arrange(RIGHT, buff=0.6)
            g.move_to([0, y, 0])
            with self.vo(nar):
                self.play(FadeIn(g, shift=UP * 0.2), run_time=0.8)
            y -= 1.5
        t = T("Everyone is optimising the worker. Somebody is about to delete it.", 28, C_GREEN).to_edge(DOWN, buff=0.5)
        with self.vo("Everyone is optimising the worker. Somebody is about to delete it."):
            self.play(FadeIn(t))

    def ch_nginx_origin(self):
        self.new_slide("What nginx changed", "Igor Sysoev, at Rambler, the big Russian portal, in two thousand two.", C_GREEN)
        pts = [("Rambler's Apache servers were falling over under connection volume, not request volume", "Rambler's Apache servers were falling over under connection volume, not request volume."),
               ("Started 2002 to solve C10K. First public release: 4 October 2004 (Sputnik's anniversary). 1.0.0 only in April 2011", "He started nginx in two thousand two to solve C ten K. The first public release was on the fourth of October, two thousand four, the anniversary of Sputnik. Version one point zero came only in April two thousand eleven."),
               ("Goal: serve 10k mostly-idle connections from ONE process; let something else make dynamic content", "The goal: serve ten thousand mostly idle connections from one process, and let something else generate dynamic content. That is why nginx is a reverse proxy, not an app server.")]
        g = self.bullets(pts, size=25, gap=0.4, shift=UP * 0.9)
        a = T("Apache asked: how do I make the worker cheaper?", 28, C_RED, maxw=12)
        b = T("nginx asked: why is there a worker per connection at all?", 28, C_GREEN, maxw=12)
        VGroup(a, b).arrange(DOWN, buff=0.3).shift(DOWN * 1.9)
        with self.vo("Apache asked: how do I make the worker cheaper? nginx asked: why is there a worker per connection at all? "
                     "A connection needs a few hundred bytes of state, and a place in a list, until it has something to say."):
            self.play(FadeIn(a))
            self.play(FadeIn(b))

    def ch_process_model(self):
        self.new_slide("Process model", "The process model. One process per core, plus a master that never touches a connection.", C_BLUE)
        m = box("master\nbinds :80 · reads config\nforks · handles signals", C_ORANGE, w=4.6, h=1.4, size=22).move_to(UP * 1.5)
        ws = VGroup(*[box(f"worker {i}\nown epoll loop", C_GREEN, w=2.5, h=1.0, size=20) for i in range(3)], box("worker N", C_GREEN, w=2.0, h=1.0, size=20)).arrange(RIGHT, buff=0.3).shift(DOWN * 0.5)
        cm = VGroup(box("cache manager\nevicts LRU", C_PURPLE, w=2.9, h=1.0, size=20), box("cache loader\nwarms the index", C_PURPLE, w=2.9, h=1.0, size=20)).arrange(RIGHT, buff=0.3).shift(DOWN * 2.3)
        with self.vo("The master binds port eighty, reads the config, forks, and handles signals. Nothing else."):
            self.play(FadeIn(m))
        arrows = VGroup(*[Arrow(m.get_bottom(), w.get_top(), buff=0.1, color=C_GREY, stroke_width=3) for w in ws])
        with self.vo("Then there is one worker per core, each with its own event loop."):
            self.play(FadeIn(ws, lag_ratio=0.2), Create(arrows))
        with self.vo("Plus a cache manager, which evicts the least recently used entries, and a cache loader, which warms the index."):
            self.play(FadeIn(cm))
        t = T("ps -o pid,ppid,args -C nginx  ->  the count does not change under load", 22, C_YELLOW, font=MONO, maxw=12.4).to_edge(DOWN, buff=0.4)
        with self.vo("You can check this with ps. The master has parent process one, and the number of workers does not change under load, unlike a fork server, where it grows. "
                     "The code is ngx_master_process_cycle, ngx_start_worker_processes, and ngx_spawn_process."):
            self.play(FadeIn(t))

    def ch_loop(self):
        self.new_slide("All of nginx in six lines", "All of nginx, in six lines. This is ngx_process_events_and_timers.", C_GREEN)
        lines = ["timer = ngx_event_find_timer();",
                 "ngx_process_events(cycle, timer, flags);        /* epoll_wait(): 99.9% of life asleep here */",
                 "ngx_event_process_posted(cycle, &ngx_posted_accept_events);",
                 "ngx_shmtx_unlock(&ngx_accept_mutex);",
                 "ngx_event_expire_timers();",
                 "ngx_event_process_posted(cycle, &ngx_posted_events);"]
        code = self.code_block(lines, size=20, hl={"epoll_wait": C_GREEN, "timer": C_YELLOW}, pos=UP * 0.4)
        with self.vo("Find the nearest timer. Process events. Process posted accept events. Release the accept mutex. Expire timers. Process the remaining posted events. That is the whole server."):
            self.play(FadeIn(code[0]), Write(code[1], run_time=4))
        pts = [("The timer is an argument to the sleep - nginx never polls for timeouts", "Notice that the timer is an argument to the sleep. So nginx never polls for timeouts. It just sleeps exactly until the next one is due."),
               ("Handlers don't run inside the poll: they are posted, then drained after", "And handlers do not run inside the poll. They are posted, and drained afterwards.")]
        self.bullets(pts, size=26, gap=0.4, shift=DOWN * 1.9)

    def ch_accept(self):
        self.new_slide("Load balancing between workers: one line", "How do the workers share new connections? With one line.", C_ORANGE)
        code = self.code_block(["ngx_accept_disabled = ngx_cycle->connection_n / 8 - ngx_cycle->free_connection_n;"], size=19, pos=UP * 1.8, hl={"accept_disabled": C_YELLOW})
        with self.vo("ngx accept disabled equals the total connection slots divided by eight, minus the free slots."):
            self.play(FadeIn(code))
        slots = VGroup(*[Square(0.5, color=C_BLUE, fill_opacity=0.6 if i < 7 else 0.0, stroke_width=2) for i in range(8)]).arrange(RIGHT, buff=0.05).shift(UP * 0.3)
        lab = T("7/8 of the slots in use", 24, C_RED).next_to(slots, DOWN, buff=0.2)
        for i in range(7):
            slots[i].set_fill(C_RED if i >= 6 else C_BLUE, 0.6)
        with self.vo("In plain words: once I am using more than seven eighths of my connection slots, stop competing for new connections, and let my siblings take them. No coordinator and no shared counter. Each worker decides alone."):
            self.play(FadeIn(slots, lag_ratio=0.1), FadeIn(lab), run_time=2)
        pts = [("accept_mutex: off by default since 1.11.3", "The accept mutex has been off by default since version one point eleven point three."),
               ("The thundering herd (all workers woken for one connection) was real in 2004; now EPOLLEXCLUSIVE (Linux 4.5+) and SO_REUSEPORT let the kernel fan out", "The thundering herd, where all workers wake up for a single connection, was real in two thousand four. Now EPOLLEXCLUSIVE, in Linux four point five and later, and SO_REUSEPORT let the kernel fan connections out.")]
        self.bullets(pts, size=23, gap=0.35, shift=DOWN * 1.9)

    def ch_select_epoll(self):
        self.new_slide("select vs epoll: O(watched) vs O(active)", "select versus epoll, stated as: O of watched, versus O of active.", C_PURPLE)
        tbl = self.table([["", "select()", "epoll()"],
                          ["Watch list lives", "in your process, rebuilt each call", "in the kernel, edited via epoll_ctl()"],
                          ["Cost / iteration", "O(n) build + O(n) kernel + O(n) scan", "O(ready events)"],
                          ["10,000 idle, 10 active", "30,000 units of work to find 10", "10"],
                          ["Ceiling", "FD_SETSIZE 1024 (compile time)", "ulimit -n"],
                          ["What ulimit -n does", "nothing - the limit is a bitmap width", "everything"],
                          ["Portable", "everywhere since 1983", "Linux only (kqueue on BSD)"]],
                         [3.4, 4.9, 4.7], size=23, y=0.5, row_h=0.8)
        self.reveal_rows(tbl, ["Where does the watch list live? With select, in your process, rebuilt on every call. With epoll, in the kernel, edited with epoll_ctl.",
                               "The cost per iteration: select does an O of n build, an O of n kernel walk, and an O of n scan. epoll costs O of ready events.",
                               "With ten thousand idle and ten active, select does thirty thousand units of work to find ten. epoll does ten.",
                               "The ceiling: FD_SETSIZE of one thousand twenty-four, fixed at compile time, versus ulimit dash n.",
                               "And what does ulimit do? For select, nothing, because the limit is a bitmap width. For epoll, everything.",
                               "select is portable everywhere since nineteen eighty-three. epoll is Linux only, with kqueue on BSD."])
        t = T("Everything is downstream of one decision: who owns the watch list.", 26, C_YELLOW).to_edge(DOWN, buff=0.5)
        with self.vo("Everything here is downstream of one decision: who owns the watch list."):
            self.play(FadeIn(t))

    def ch_stale(self):
        self.new_slide("The stale-event bug", "Every event loop author writes this bug once. The stale event.", C_RED)
        batch = VGroup(*[box(f"event {i}", C_BLUE, w=1.5, h=0.7, size=20) for i in range(1, 8)]).arrange(RIGHT, buff=0.12).shift(UP * 1.7)
        with self.vo("epoll_wait returns a batch of events."):
            self.play(FadeIn(batch, lag_ratio=0.1), run_time=1.5)
        ar = Arrow(batch[0].get_bottom(), batch[0].get_bottom() + DOWN * 1.0, color=C_YELLOW, buff=0)
        with self.vo("Handling event one may close the connection that event seven points at."):
            self.play(GrowArrow(ar), batch[6].animate.set_color(C_RED))
        new = box("new client\non the recycled fd", C_ORANGE, w=3.2, h=1.0, size=20).shift(DOWN * 0.8 + RIGHT * 3)
        with self.vo("A new client then takes that recycled file descriptor, and event seven is delivered to the wrong connection."):
            self.play(FadeIn(new))
        code = self.code_block(["if (c->fd == -1 || rev->instance != instance) continue;"], size=20, pos=DOWN * 2.0 + LEFT * 2.5)
        with self.vo("nginx's fix is clever. Structures are aligned so the low bit of a pointer is always zero, and that bit is used as an instance flag, flipped on reuse. "
                     "One branch checks it. A free bit, no extra memory."):
            self.play(FadeIn(code))
        with self.vo("The companion repository uses an explicit generation counter instead, which is easier to read."):
            pass

    def ch_sendfile(self):
        self.new_slide("sendfile: four copies become two", "sendfile. Four copies become two.", C_BLUE)
        a_t = T("read() + write():  4 copies, 2 mode switches per chunk", 25, C_RED).shift(UP * 2.2)
        fl1, _ = self.flow(["disk", "page cache", "your buffer", "socket buffer", "NIC"], [C_GREY, C_BLUE, C_RED, C_BLUE, C_GREEN], y=1.3, w=2.2, h=0.8, size=21, gap=0.4)
        self.play(FadeIn(a_t))
        with self.vo("With read and write, data goes from disk to the page cache, to your buffer, to the socket buffer, to the network card. Four copies, and two mode switches per chunk."):
            self.play(Indicate(fl1[2], color=C_RED))
        b_t = T("sendfile():  2 copies (both DMA), 0 mode switches per chunk", 25, C_GREEN).shift(DOWN * 0.2)
        self.play(FadeIn(b_t))
        fl2, _ = self.flow(["disk", "page cache", "socket buffer", "NIC"], [C_GREY, C_BLUE, C_BLUE, C_GREEN], y=-1.1, w=2.4, h=0.8, size=21, gap=0.5)
        with self.vo("With sendfile, data goes from disk to the page cache, to the socket buffer, to the network card. Two copies, both by DMA, and no mode switches per chunk. The data never enters your process."):
            pass
        pts = [("Limit: if you must touch the bytes (gzip, TLS, templating) they have to come to user space - gzip on and sendfile on fight. That is why kTLS exists", "The limit: if you must touch the bytes, for gzip, TLS or templating, they have to come to user space. So gzip on and sendfile on fight each other. That is why kernel TLS exists."),
               ("Honest benchmark, 64 MB on loopback: read 37 ms / 2048 syscalls; mmap 23 ms / 4; sendfile 33 ms / 1 syscall - the real win is 2048 syscalls -> 1", "An honest benchmark, sixty-four megabytes over loopback: read takes thirty-seven milliseconds and two thousand forty-eight system calls. mmap takes twenty-three milliseconds and four. sendfile takes thirty-three milliseconds and one system call. "
                "On loopback there is no network card or DMA, so wall clock is about the same. The real win is two thousand forty-eight system calls down to one, and headroom under concurrency. A benchmark that does not model the bottleneck measures the wrong thing.")]
        self.bullets(pts, size=21, gap=0.3, shift=DOWN * 2.4)

    def ch_proxy(self):
        self.new_slide("Why 'reverse' proxy?", "Why is it called a reverse proxy? Because proxy was taken.", C_TEAL)
        L = VGroup(T("Forward proxy (Squid, 1996)", 28, C_BLUE), T("sits next to the CLIENTS", 23), T("caches for campus users; protects your uplink", 21),
                   T("client -> [proxy] -> internet", 22, C_YELLOW)).arrange(DOWN, buff=0.25).move_to(LEFT * 3.5 + UP * 1.0)
        R = VGroup(T("Reverse proxy (nginx)", 28, C_GREEN), T("sits next to the SERVERS", 23), T("cache, route by path/host, balance across upstreams,", 21), T("TLS termination, hold 10k slow clients", 21),
                   T("internet -> [nginx] -> app servers", 22, C_YELLOW)).arrange(DOWN, buff=0.25).move_to(RIGHT * 3.5 + UP * 1.0)
        with self.vo("A forward proxy, like Squid from nineteen ninety-six, sits next to the clients. It caches for campus users and protects your uplink."):
            self.play(FadeIn(L))
        with self.vo("A reverse proxy, like nginx, sits next to the servers. It caches, routes by path or host, distributes across upstreams, terminates TLS, and holds ten thousand slow clients. The client never configures it, and usually cannot see it."):
            self.play(FadeIn(R))
        t = T("The killer feature nobody lists: it absorbs slow clients. Your app never talks to a phone on 2G.", 25, C_ORANGE, maxw=12.4).to_edge(DOWN, buff=0.6)
        with self.vo("The killer feature nobody lists: it absorbs slow clients. Your app never has to talk to a phone on two G."):
            self.play(FadeIn(t))

    def ch_cache(self):
        self.new_slide("The cache: two structures, one on disk", "Now the features you configure. First, the cache.", C_PURPLE)
        code = self.code_block(["proxy_cache_path temp/cache levels=1:2 keys_zone=demo:10m",
                                "                 max_size=100m inactive=60s use_temp_path=off;"], size=19, pos=UP * 2.0,
                               hl={"levels": C_BLUE, "keys_zone": C_GREEN, "max_size": C_ORANGE, "inactive": C_RED})
        with self.vo("One directive defines the cache."):
            self.play(FadeIn(code))
        tbl = self.table([["Directive", "Meaning"],
                          ["keys_zone=demo:10m", "10 MB of shared memory holding the rbtree + LRU queue: the INDEX, not the data. ~8,000 keys per MB"],
                          ["levels=1:2", "two directory levels on disk, so no directory holds a million files"],
                          ["max_size=100m", "disk ceiling; the cache manager evicts from the LRU tail"],
                          ["inactive=60s", "evicted if not READ for 60 s, regardless of TTL"]],
                         [3.3, 9.4], size=21, y=-0.9, row_h=0.8)
        self.reveal_rows(tbl, ["keys zone: ten megabytes of shared memory holding the red-black tree and the LRU queue. That is the index, not the data. About eight thousand keys per megabyte.",
                               "levels one colon two: two directory levels on disk, so no directory ever holds a million files.",
                               "max size: the disk ceiling. The cache manager evicts from the tail of the LRU.",
                               "inactive: an item is evicted if it is not read for sixty seconds, regardless of its TTL."])

    def ch_cache_lines(self):
        self.new_slide("valid vs inactive", "A class question. proxy_cache_valid is ten seconds, inactive is sixty seconds. What happens?", C_PURPLE)
        tl = Line(LEFT * 5.5, RIGHT * 5.5, color=C_GREY).shift(UP * 0.8)
        ticks = [(-5.5, "0", ""), (-2.9, "10 s", "fresh until here -> revalidate / stale"), (2.5, "60 s", "no reads for 60 s -> deleted")]
        self.play(Create(tl))
        fresh = Line([-5.5, 0.8, 0], [-2.9, 0.8, 0], color=C_GREEN, stroke_width=10)
        kept = Line([-2.9, 0.8, 0], [2.5, 0.8, 0], color=C_ORANGE, stroke_width=10)
        with self.vo("The content is fresh for ten seconds. After that it is stale, so nginx revalidates. But it is kept on disk for up to sixty seconds since the last access."):
            self.play(Create(fresh))
            self.play(Create(kept))
        lbl1 = T("proxy_cache_valid = 10 s: FRESH", 22, C_GREEN).move_to([-4.2, 1.6, 0])
        lbl2 = T("kept on disk while read within 60 s (inactive)", 22, C_ORANGE).move_to([0, 0.0, 0])
        with self.vo("And if nobody reads it for sixty seconds, it is deleted, even if it would still be valid. Valid is freshness. Inactive is how long an unread item stays."):
            self.play(FadeIn(lbl1), FadeIn(lbl2))
        self.new_slide("Two lines that save you at 3 a.m.", "Two lines that save you at three in the morning.", C_RED)
        pts = [("proxy_cache_lock on;  - anti-stampede: when a popular object expires, only ONE request goes to the origin; the others wait. Off by default", "One. proxy_cache_lock on. This is anti-stampede. When a popular object expires, only one request goes to the origin and the others wait. It is off by default."),
               ("proxy_cache_use_stale error timeout updating http_500 http_502 http_503 http_504;  - serve stale rather than fail. 'updating' = one request refreshes while everyone else gets stale instantly", "Two. proxy_cache_use_stale. Serve stale content rather than fail, when the origin errors, times out, or returns five hundred, five oh two, five oh three or five oh four. "
                "The updating option means one request refreshes the item while everyone else gets the stale copy instantly. That is stale-while-revalidate."),
               ("And always: add_header X-Cache-Status $upstream_cache_status;  - so you can see MISS / HIT", "And always add an X-Cache-Status header with the upstream cache status, so you can see miss or hit.")]
        self.bullets(pts, size=23, gap=0.5)

    def ch_location(self):
        self.new_slide("location precedence - not file order", "location precedence. It is not file order.", C_YELLOW)
        tbl = self.table([["#", "Form", "Rule", "Example -> winner"],
                          ["1", "location = /exact", "exact match; wins immediately", "/exact -> 1"],
                          ["2", "location ^~ /images/", "longest prefix; suppresses the regex search", "/images/a.php -> 2 (not the regex!)"],
                          ["3", "location ~ \\.php$", "regex: FIRST match in file order (not longest)", "/other/a.php -> 3"],
                          ["4", "location /", "longest prefix, used only if no regex matched", "/anything -> 4"]],
                         [0.6, 3.5, 4.8, 3.9], size=21, y=0.8, row_h=0.95)
        self.reveal_rows(tbl, ["One: equals, exact match. It wins immediately and the search stops.",
                               "Two: caret tilde, a prefix match. It takes the longest prefix, and suppresses the regex search. So slash images slash a dot php goes to number two, not the regex. Half the room gets this wrong.",
                               "Three: a regex. The first match in file order wins, not the longest.",
                               "Four: plain slash, the longest prefix, used only if no regex matched."])
        steps = VGroup(chip("exact", C_BLUE), chip("longest prefix (remember it; ^~ stops)", C_GREEN), chip("regexes in order: first wins", C_ORANGE), chip("else the remembered prefix", C_PURPLE)).arrange(RIGHT, buff=0.2)
        steps.scale_to_fit_width(12.4) if steps.width > 12.4 else None
        steps.shift(DOWN * 2.3)
        with self.vo("So the algorithm is: exact match first, then the longest prefix, which is remembered, and if it is a caret tilde, the search stops. Then regexes in order, first match wins. Otherwise use the remembered prefix."):
            self.play(FadeIn(steps, lag_ratio=0.2), run_time=2)
        self.new_slide("Why 500 prefixes are free and 500 regexes aren't", "Why are five hundred prefixes free, while five hundred regexes are not?", C_YELLOW)
        L = VGroup(T("Prefixes", 30, C_GREEN), T("ternary search tree", 24), T("built at config-parse time", 22), T("walked per URI segment", 22), T("tree -> longest wins", 24, C_YELLOW)).arrange(DOWN, buff=0.25).move_to(LEFT * 3.5 + UP * 0.6)
        R = VGroup(T("Regexes", 30, C_RED), T("a plain array", 24), T("walked in order, every request", 22), T("array -> first wins", 24, C_YELLOW)).arrange(DOWN, buff=0.25).move_to(RIGHT * 3.5 + UP * 0.6)
        with self.vo("Prefixes are stored in a ternary search tree, built at config parse time, and walked per URI segment. Regexes are a plain array, walked in order on every request. "
                     "The data structure is the documentation: a tree means the longest wins, an array means the first wins."):
            self.play(FadeIn(L), FadeIn(R), run_time=2)
        t = T("nginx has no .htaccess - deliberately, so it never stat()s up the directory tree on every request.", 23, C_ORANGE, maxw=12.4).to_edge(DOWN, buff=0.6)
        with self.vo("And nginx has no dot htaccess, deliberately, so it never has to stat its way up the directory tree on every request."):
            self.play(FadeIn(t))

    def ch_wrr(self):
        self.new_slide("Smooth weighted round robin", "Load balancing across upstreams: smooth weighted round robin. This is the core of it.", C_BLUE)
        code = self.code_block(["peer->current_weight += peer->effective_weight;   total += peer->effective_weight;",
                                "if (best == NULL || peer->current_weight > best->current_weight) best = peer;",
                                "best->current_weight -= total;"], size=18, pos=UP * 2.0, hl={"current_weight": C_YELLOW})
        with self.vo("Each round, every peer's current weight grows by its effective weight. Pick the peer with the highest current weight. Then subtract the total from the winner."):
            self.play(FadeIn(code))
        tbl = self.table([["round", "current weights after adding (a, b)", "pick", "after subtracting total (4)"],
                          ["1", "(3, 1)", "a", "(-1, 1)"],
                          ["2", "(2, 2)", "a  (tie: first wins)", "(-2, 2)"],
                          ["3", "(1, 3)", "b", "(1, -1)"],
                          ["4", "(4, 0)", "a", "(0, 0)"]],
                         [1.4, 4.4, 3.2, 3.8], size=21, y=-0.6, row_h=0.65)
        self.reveal_rows(tbl, ["Take weights three and one, so a is three and b is one. Round one: add, and the weights are three and one. Pick a. Subtract four from a: minus one, one.",
                               "Round two: two and two. A tie, and the first peer wins, so a. Subtract: minus two, two.",
                               "Round three: one and three. Pick b. Subtract: one, minus one.",
                               "Round four: four and zero. Pick a. We are back to zero, zero."])
        t = T("Naive WRR: a a a b (bursts).  Smooth: b is interleaved - same 3:1, no bursts at the origin.", 23, C_GREEN, maxw=12.4).to_edge(DOWN, buff=0.5)
        with self.vo("The ratio is the same three to one, but compare naive weighted round robin, which sends a, a, a, then b, in bursts. The smooth version interleaves b. "
                     "The lecture writes the sequence as a b a a. Depending on how ties break, you may see a a b a. Either way, b is in the middle, not queued at the end. "
                     "Measured over twenty-four requests, six went to one upstream and eighteen to the other. Exactly three to one. The other algorithm to try is least_conn: compare the p ninety-nine with a slow upstream."):
            self.play(FadeIn(t))

    def ch_try_files(self):
        self.new_slide("Fallbacks: try_files", "Fallbacks, with try_files.", C_TEAL)
        code = self.code_block(["location / { try_files $uri $uri/ /index.html?$args; }",
                                "location /maybe/ { try_files $uri @app; }",
                                "location @app { proxy_pass http://app; }"], size=21, pos=UP * 1.3, hl={"try_files": C_YELLOW, "@app": C_ORANGE, "proxy_pass": C_GREEN})
        with self.vo("Three small blocks."):
            self.play(FadeIn(code))
        fl, _ = self.flow(["Is it a\nreal file?", "A real\ndirectory?", "No? Hand the URI\nto the app"], [C_BLUE, C_GREEN, C_ORANGE], y=-1.2, w=3.3, h=1.1, size=22, gap=0.5,
                          narrations=["Is this a real file?", "A real directory?", "No? Hand the URI to the app. The last entry is never tested. It is the fallback, not a candidate."])
        pts = [("A named location (@app) is reachable only from try_files or error_page, never from a URL", "A named location, with an at sign, is reachable only from try_files or error_page, never from a URL."),
               ("WordPress, Rails, Django, every SPA router = this directive + an app that reads REQUEST_URI", "WordPress, Rails, Django, and every single page app router are this one directive, plus an app that reads the request URI.")]
        self.bullets(pts, size=23, gap=0.35, shift=DOWN * 2.1)

    def ch_tree(self):
        self.new_slide("Walkthrough of the source", "Now a tour of the source. Line numbers drift, function names do not. Since nginx puts the return type on its own line, grep for the caret and the function name finds only the definition.", C_ORANGE)
        tbl = self.table([["Directory", "Contents"],
                          ["src/core/", "nginx's own stdlib: string, array, list, hash, rbtree, queue, palloc, buf, conf, cycle, connection"],
                          ["src/event/", "the loop; modules/ = epoll, kqueue, select, poll, devpoll, eventport (chosen at ./configure)"],
                          ["src/http/", "HTTP state machine, phase engine, upstream framework; modules/ = every directive"],
                          ["src/os/unix/", "syscall layer: sendfile per OS, spawning, shared memory, atomics"],
                          ["src/stream/", "the same architecture for raw TCP/UDP: nginx as an L4 load balancer"],
                          ["src/mail/", "the same again for IMAP, POP3, SMTP proxying"]],
                         [2.8, 10.0], size=21, y=0.1, row_h=0.8)
        self.reveal_rows(tbl, ["src core is nginx's own standard library: strings, arrays, lists, hashes, red-black trees, queues, pools, buffers.",
                               "src event holds the loop, and six ways to wait, chosen at configure time.",
                               "src http holds the HTTP state machine, the phase engine and the upstream framework.",
                               "src os unix is the syscall layer.",
                               "src stream is the same architecture for raw TCP and UDP, which makes nginx a layer four load balancer.",
                               "And src mail does the same for IMAP, POP3 and SMTP proxying."])
        pts = [("ngx_queue.h - an intrusive doubly-linked list: link pointers live inside the node, no allocation. Used by the cache LRU and posted-event queues", "Two files to read first. ngx_queue.h is an intrusive doubly linked list: the link pointers live inside the node, so there is no allocation. The cache LRU and the posted event queues use it."),
               ("ngx_palloc.h - memory pools: allocate from a pool tied to the request, destroy the whole pool at the end. No refcounting, no leak class, no free() on the hot path", "ngx_palloc.h is the memory pool. Allocate from a pool attached to the request, and destroy the whole pool at the end. No reference counting, no class of leaks, and no free on the hot path.")]
        self.bullets(pts, size=21, gap=0.3, shift=DOWN * 2.2)

    def ch_parser(self):
        self.new_slide("The HTTP parser is a resumable state machine", "The HTTP parser is a resumable state machine.", C_GREEN)
        states = ["sw_start", "sw_method", "sw_spaces_before_uri", "sw_schema", "sw_http_H", "sw_http_HT", "..."]
        fl, bx = self.flow(states, [C_BLUE] * 7, y=0.8, w=1.9, h=0.8, size=16, gap=0.25,
                           narrations=["The request line alone has twenty-seven states.", None, None, None, None, None, None])
        pts = [("No regex, no strtok, no allocation: one byte at a time", "No regex, no strtok, no allocation. It consumes one byte at a time."),
               ("Can stop between ANY two bytes: state = r->state resumes where it stopped (a request line may arrive in 3 TCP segments)", "It can stop between any two bytes. The state is saved, and parsing resumes where it stopped, because a request line may arrive in three TCP segments."),
               ("This is what non-blocking costs you: every parser must be resumable", "This is what non-blocking costs you: every parser has to be resumable.")]
        self.bullets(pts, size=24, gap=0.4, shift=DOWN * 1.8)

    def ch_phases(self):
        self.new_slide("11 phases - and return means 'suspended'", "Every request walks through eleven phases.", C_PURPLE)
        names = ["POST_READ", "SERVER_REWRITE", "FIND_CONFIG", "REWRITE", "POST_REWRITE", "PREACCESS", "ACCESS", "POST_ACCESS", "PRECONTENT", "CONTENT", "LOG"]
        cols = [C_BLUE] * 5 + [C_ORANGE] * 3 + [C_GREEN] * 2 + [C_GREY]
        row1 = VGroup(*[box(n, c, w=2.15, h=0.65, size=16) for n, c in zip(names[:6], cols[:6])]).arrange(RIGHT, buff=0.1).shift(UP * 1.5)
        row2 = VGroup(*[box(n, c, w=2.15, h=0.65, size=16) for n, c in zip(names[6:], cols[6:])]).arrange(RIGHT, buff=0.1).shift(UP * 0.6)
        with self.vo("Post read, server rewrite, find config, rewrite, post rewrite, pre-access, access, post access, pre-content, content, and log."):
            self.play(FadeIn(row1, lag_ratio=0.1), FadeIn(row2, lag_ratio=0.1), run_time=3)
        code = self.code_block(["while (ph[r->phase_handler].checker) {", "    rc = ph[r->phase_handler].checker(r, &ph[r->phase_handler]);",
                                "    if (rc == NGX_OK) return;     /* NOT done. SUSPENDED. */", "}"], size=19, pos=DOWN * 1.2, hl={"NGX_OK": C_RED})
        with self.vo("The engine loops over the phase handlers. And here is the subtle part: when a checker returns NGX_OK, it does not mean done. It means suspended. "
                     "This is a hand-rolled coroutine in C. The request resumes at the phase it left, when its event fires."):
            self.play(FadeIn(code[0]), Write(code[1], run_time=3))
        t = T("limit_req -> PREACCESS · auth_basic -> ACCESS · try_files -> PRECONTENT · proxy_pass / fastcgi_pass / static -> CONTENT", 20, C_YELLOW, maxw=12.6).to_edge(DOWN, buff=0.4)
        with self.vo("Which module runs when: limit_req in pre-access, auth_basic in access, try_files in pre-content, and proxy_pass, fastcgi_pass and static files in content."):
            self.play(FadeIn(t))

    def ch_fcgi_header(self):
        self.new_slide("FastCGI wire format", "Back to FastCGI, this time at the byte level.", C_GREEN)
        hdr = VGroup(*[box(a, c, w=w_, h=0.9, size=18) for a, c, w_ in [("version\n1 B", C_BLUE, 1.5), ("type\n1 B", C_BLUE, 1.5), ("requestId\n2 B", C_GREEN, 1.9), ("contentLength\n2 B", C_ORANGE, 2.2),
                                                                           ("padding\n1 B", C_GREY, 1.5), ("reserved\n1 B", C_GREY, 1.5), ("contentData ...", C_PURPLE, 2.0), ("padding", C_GREY, 1.4)]]).arrange(RIGHT, buff=0.04).shift(UP * 1.6)
        with self.vo("Every record has an eight byte header: version, type, request I D in two bytes, content length in two bytes, padding length, and a reserved byte. Then the content data, then padding."):
            self.play(FadeIn(hdr, lag_ratio=0.1), run_time=2.5)
        code = self.code_block(["BEGIN_REQUEST   01 01 00 01 00 08 00 00     (version 1, type 1, request 1, length 8)",
                                "empty PARAMS    01 04 00 01 00 00 00 00     (type 4, length 0 = end of params)"], size=19, pos=DOWN * 0.1, hl={"BEGIN_REQUEST": C_GREEN, "PARAMS": C_ORANGE})
        with self.vo("A begin request header is zero one, zero one, zero zero, zero one, zero zero, zero eight, zero zero, zero zero. Those are the first eight bytes of every FastCGI connection. "
                     "And an empty params record is zero one, zero four, then the request, then length zero. That marks the end of params."):
            self.play(FadeIn(code))
        t = T("Empty record = delimiter. Forget it and the responder waits forever. Length + delimiter, at two levels.", 24, C_YELLOW, maxw=12.4).shift(DOWN * 2.0)
        with self.vo("An empty record is a delimiter. Forget it, and the responder waits forever. That is length plus delimiter, at two levels."):
            self.play(FadeIn(t))

    def ch_ladder(self):
        self.new_slide("The ladder (companion repo)", "The companion repository is a ladder of small programs, about twelve hundred lines, against nginx's two hundred thousand. The difference is error paths.", C_ORANGE)
        tbl = self.table([["Dir", "Model", "Historical match", "What you see"],
                          ["01-fork", "fork per client", "Apache 1.3, 1995", "ps shows a process per request"],
                          ["02-thread", "pthread per client", "Apache 2.0 worker, 1999", "prints its 8 MB stack"],
                          ["03-select", "one thread, select", "...and the 1024 wall", "dies at fd 1024; ulimit doesn't help"],
                          ["04-epoll", "one thread, epoll", "nginx, 2004", "5,000 connections, nothing happens"],
                          ["05-sendfile", "read vs mmap vs sendfile", "-", "2048 syscalls -> 1"],
                          ["06-fastcgi", "wire protocol, both ends", "CGI without the fork", "nginx -> your 200-line responder"],
                          ["07-nginx", "one nginx.conf, five demos", "-", "routing, cache and weights, fallbacks"]],
                         [2.0, 3.4, 3.4, 4.2], size=19, y=-0.1, row_h=0.72)
        self.reveal_rows(tbl, ["Fork per client matches Apache one point three.", "A pthread per client matches the Apache two worker, and prints its eight megabyte stack.",
                               "One thread with select dies at descriptor one thousand twenty-four, and ulimit does not help.", "One thread with epoll matches nginx. Five thousand connections, and nothing happens.",
                               "read versus mmap versus sendfile: two thousand forty-eight system calls become one.", "The FastCGI responder talks the wire protocol at both ends.", "And one nginx conf, with five demos: routing, cache and weights, and fallbacks."])

    def ch_ideas(self):
        self.new_slide("Four ideas to leave with", "Four ideas to leave with.", C_GREEN)
        pts = [("1. Ask the other question - Apache made the worker cheaper; nginx asked why there was one", "One. Ask the other question. Apache made the worker cheaper. nginx asked why there was one."),
               ("2. Check whether the constraint still exists - thread-per-connection died at 8 MB + context switches; goroutines and virtual threads brought it back", "Two. Check whether the constraint still exists. Thread per connection died at eight megabytes plus context switches. Goroutines and virtual threads brought it back."),
               ("3. The data structure is the documentation - prefixes in a tree: longest wins. Regexes in an array: first wins", "Three. The data structure is the documentation. Prefixes in a tree: longest wins. Regexes in an array: first wins."),
               ("4. Amortise the setup - prefork, pre-thread, servlets, pools, FastCGI, upstream keepalive: six names, one move", "Four. Amortise the setup. Prefork, pre-thread, servlets, connection pools, FastCGI, upstream keepalive. Six names, one move.")]
        self.bullets(pts, size=26, gap=0.5)
        with self.vo("The next question: where did all the state go? Sessions, sticky routing, TLS termination, and shared caches."):
            pass

    def quiz(self):
        self.quiz_recap(4, [
            "First server: CERN httpd (Berners-Lee, NeXT, 1990). Mosaic = a browser (1993). NCSA HTTPd (McCool) invented CGI. Apache 1995, #1 from 1996.",
            "Apache 1.3 prefork, 2.0 worker, 2.4 event (default). Servlets 1997, J2EE 1999.",
            "nginx: Igor Sysoev, Rambler, started 2002, released 4 Oct 2004, 1.0 in April 2011.",
            "Master (bind, config, fork, signals) + one worker per core + cache manager + cache loader.",
            "accept_disabled = connections/8 - free (the 7/8 rule). accept_mutex off since 1.11.3; EPOLLEXCLUSIVE and SO_REUSEPORT.",
            "Stale events: fixed with a pointer low-bit 'instance' flag. sendfile: 4 copies / 2 mode switches -> 2 DMA copies / 0; conflicts with gzip; kTLS.",
            "Forward proxy (Squid, near clients) vs reverse proxy (near servers); it absorbs slow clients.",
            "keys_zone = index in shared memory (~8k keys/MB). inactive = unread eviction. proxy_cache_valid = freshness. proxy_cache_lock = anti-stampede (off by default). use_stale + updating. X-Cache-Status.",
            "location order: = exact, then ^~ prefix, then regex ~ (first match), then longest prefix. No .htaccess.",
            "Smooth WRR 3:1 interleaves. try_files: the last argument is the fallback and is never tested; @named locations.",
            "Parser: a resumable state machine (27 states). 11 phases; returning NGX_OK = suspended. ngx_palloc memory pools. FastCGI: 8-byte header, empty record ends a stream.",
        ], "Here is what the quiz is most likely to ask from session four.", size=25, per_page=4)
        self.say("That is session four. Next up, session five: the evolution of HTTP, from nineteen ninety-six to now.")
