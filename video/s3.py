from common import *


class S3(VScene):
    def construct(self):
        self.session_title(
            3, "One Process, Many Clients", "Scaling servers: select, epoll, CGI, C10K, and what Apache, HAProxy, Varnish and nginx do",
            "Session three. One process, many clients. The question for this session: how does one box hold ten thousand clients at the same time?")
        self.ch_three_ways()
        self.ch_select_server()
        self.ch_wall()
        self.ch_production()
        self.ch_timeouts()
        self.ch_cgi()
        self.ch_cgi_env()
        self.ch_fixes()
        self.ch_fastcgi()
        self.ch_servlets()
        self.ch_not_everything()
        self.ch_walls()
        self.ch_c10k()
        self.ch_memory()
        self.ch_kernel()
        self.ch_little()
        self.ch_apache()
        self.ch_haproxy_varnish()
        self.ch_nginx()
        self.ch_compare()
        self.ch_ideas()
        self.quiz()

    # ------------------------------------------------------------------
    def ch_three_ways(self):
        self.new_slide("Three ways to serve many clients", "There are three ways to serve many clients.", C_BLUE)
        cols = [("Fork per request", C_RED, ["whole process copied per client", "simple and isolated", "most expensive per connection"]),
                ("Thread per request", C_ORANGE, ["cheaper than fork", "latency drops", "every thread still costs a stack before any work"]),
                ("One loop, many sockets", C_GREEN, ["select / epoll", "one thread watches every socket", "wakes only for the ready ones", "the one that scales"])]
        nars = ["Fork per request. The whole process is copied for each client. Simple and isolated, but the most expensive per connection.",
                "Thread per request. Cheaper than fork, and latency drops. But every thread still costs a stack before any work is done.",
                "One loop with many sockets. With select or epoll, one thread watches every socket and wakes only for the ones that are ready. This is the one that scales."]
        groups = VGroup()
        for (title, c, lines), n in zip(cols, nars):
            g = VGroup(box(title, c, w=3.9, h=0.8, size=24), *[T(wrap(l, 26), 22, WHITE, maxw=3.9, line_spacing=0.9) for l in lines]).arrange(DOWN, buff=0.28)
            groups.add(g)
        groups.arrange(RIGHT, buff=0.35, aligned_edge=UP).shift(DOWN * 0.3)
        for g, n in zip(groups, nars):
            with self.vo(n):
                self.play(FadeIn(g, shift=UP * 0.2), run_time=0.9)
        with self.vo("What actually ships is a mix. Pre-fork or pre-thread a pool of workers, and let each worker run its own select or epoll loop. Isolation from the processes, concurrency from the loop."):
            self.play(Circumscribe(groups[2], color=C_YELLOW), run_time=1.5)
        with self.vo("The cost of fork is a full process image per connection: page tables, file descriptors and a scheduler entry duplicated, all paid while the user waits."):
            pass

    def ch_select_server(self):
        self.new_slide("The select() server", "Now the select server. Here is the loop.", C_GREEN)
        lines = ["listen(server_fd, 16);   int clients[FD_SETSIZE];",
                 "while (1) {",
                 "    FD_ZERO(&readfds);",
                 "    FD_SET(server_fd, &readfds);",
                 "    for each client: FD_SET(client, &readfds); track maxfd",
                 "    select(maxfd + 1, &readfds, NULL, NULL, NULL);",
                 "    if (FD_ISSET(server_fd, &readfds)) accept(...);",
                 "    for each client with FD_ISSET: n = read(...);",
                 "        if (n <= 0) { close; clients[i] = clients[--nclients]; i--; }",
                 "        else write(...);   // echo",
                 "}"]
        code = self.code_block(lines, size=20, hl={"select": C_GREEN, "accept": C_ORANGE, "read": C_BLUE, "write": C_BLUE, "close": C_RED}, pos=DOWN * 0.2)
        with self.vo("Each iteration, clear the set, add the server socket, add every client, and track the highest descriptor. Then call select with max fd plus one."):
            self.play(FadeIn(code[0]), Write(code[1], run_time=5))
        steps = [(6, "If the server socket is ready, accept a new client.", "If the server socket is marked ready, accept a new client."),
                 (7, "For every ready client, read.", "For every client marked ready, read."),
                 (8, "n <= 0: close, and delete in O(1) by swapping in the last client.", "If read returns zero or less, close the client, and delete it in constant time by swapping in the last entry. Otherwise, echo."),
                 (5, "The last NULL is the timeout: NULL means block forever.", "And note the last argument to select. That is the timeout. NULL means block forever.")]
        for idx, txt, nar in steps:
            r = SurroundingRectangle(code[1][idx], color=C_YELLOW, buff=0.05)
            n = T(txt, 22, C_YELLOW, maxw=11).next_to(code, DOWN, buff=0.25)
            with self.vo(nar):
                self.play(Create(r), FadeIn(n))
            self.play(FadeOut(r), FadeOut(n), run_time=0.3)

    def ch_wall(self):
        self.new_slide("select's ceiling: 1024", "Why does select hit a wall?", C_RED)
        bm = VGroup(*[Square(0.2, color=C_BLUE, fill_opacity=0.5, stroke_width=1) for _ in range(40)]).arrange(RIGHT, buff=0.04).shift(UP * 1.6)
        lab = T("fd_set: a fixed-width bitmap - 1024 bits on glibc", 24, C_BLUE).next_to(bm, UP, buff=0.3)
        over = Square(0.2, color=C_RED, fill_opacity=0.8).next_to(bm, RIGHT, buff=0.15)
        ol = T("fd 1024 cannot be represented", 22, C_RED).next_to(over, DOWN, buff=0.2)
        with self.vo("The fd set is a fixed-width bitmap, one thousand twenty-four bits on glibc. A descriptor numbered one thousand twenty-four simply cannot be represented."):
            self.play(FadeIn(lab), FadeIn(bm, lag_ratio=0.03), run_time=1.5)
            self.play(FadeIn(over), FadeIn(ol))
        self.new_slide("select O(n)  vs  epoll O(ready)", "The second problem: select is linear in the number of sockets, every single call.", C_RED)
        L = VGroup(T("select: O(n)", 30, C_RED), T("rebuild the set every iteration", 23), T("kernel scans every fd", 23),
                   T("10,000 idle sockets cost the same", 23), T("as 10,000 busy ones", 23)).arrange(DOWN, buff=0.2).move_to(LEFT * 3.5 + UP * 1.3)
        R = VGroup(T("epoll: O(ready)", 30, C_GREEN), T("epoll_ctl: register each fd once", 23), T("epoll_wait: returns only what fired", 23),
                   T("idle connections cost nothing", 23)).arrange(DOWN, buff=0.2).move_to(RIGHT * 3.5 + UP * 1.3)
        with self.vo("With select you rebuild the set each iteration, and the kernel scans every descriptor. Ten thousand idle sockets cost exactly as much as ten thousand busy ones."):
            self.play(FadeIn(L), run_time=1.2)
        with self.vo("With epoll, you register each descriptor once, using epoll_ctl. Then epoll_wait returns only what fired. Idle connections cost nothing."):
            self.play(FadeIn(R), run_time=1.2)
        dots = VGroup(*[Dot(radius=0.08, color=C_DIM) for _ in range(60)]).arrange_in_grid(rows=3, buff=0.25).shift(DOWN * 1.9 + LEFT * 3.5)
        dots2 = dots.copy().shift(RIGHT * 7)
        for i in (3, 17, 44):
            dots2[i].set_color(C_GREEN)
        with self.vo("Picture sixty sockets, and only three have data. select walks all sixty. epoll hands back just the three."):
            self.play(FadeIn(dots), FadeIn(dots2))
            scan = [dots[i].animate.set_color(C_RED) for i in range(0, 60, 2)]
            self.play(LaggedStart(*scan, lag_ratio=0.04), run_time=2.0)
            self.play(*[Indicate(dots2[i], color=C_GREEN, scale_factor=2) for i in (3, 17, 44)], run_time=1.0)
        t = T("One wall, three names:  FD_SETSIZE = default ulimit -n = the K in C10K = 1024", 26, C_YELLOW).to_edge(DOWN, buff=0.3)
        with self.vo("The number to remember is one thousand twenty-four. It is FD_SETSIZE, it is your default ulimit, and it is the K in C ten K. One wall, three names. "
                     "Other platforms have their own versions of epoll: kqueue on BSD and macOS, I O C P on Windows, and io_uring on modern Linux."):
            self.play(FadeIn(t))

    def ch_production(self):
        self.new_slide("In production you stack them", "In production, you stack these ideas.", C_BLUE)
        fl, _ = self.flow(["master\nforks workers\n(1 per core)", "each worker\nruns an epoll loop", "SO_REUSEPORT\nspreads connections", "crash isolation\n+ concurrency"],
                          [C_ORANGE, C_GREEN, C_BLUE, C_PURPLE], y=0.6, w=2.9, h=1.4, size=21, gap=0.35,
                          narrations=["At startup, fork or spawn a pool of workers, often one per CPU core.", "Each worker runs its own select or epoll loop.",
                                      "SO_REUSEPORT lets the kernel spread new connections across them.", "You get crash isolation from the processes, and concurrency from the loops."])
        pts = [("Apache's event MPM, nginx's master and workers, and the Go runtime", "This is Apache's event MPM, nginx's master and workers, and the Go runtime, which multiplexes goroutines onto OS threads with a scheduler on top of epoll.")]
        self.bullets(pts, size=28, below=fl)

    def ch_timeouts(self):
        self.new_slide("Timeouts: the client's half of the contract", "Timeouts are a contract, and the client has a half of it.", C_ORANGE)
        sets = VGroup(box("readfds\nnew content arrived", C_BLUE, w=4.0, h=1.3, size=21), box("writefds\nsocket allows writing", C_GREEN, w=4.0, h=1.3, size=21),
                      box("exceptfds\nconnect, close, errors", C_RED, w=4.0, h=1.3, size=21)).arrange(RIGHT, buff=0.3).shift(UP * 1.0)
        with self.vo("select waits on three sets. Read fds: new content arrived. Write fds: the socket allows writing. And except fds: sockets being connected, closed, or raising exceptions."):
            self.play(FadeIn(sets, lag_ratio=0.3), run_time=2)
        pts = [("The last argument is the timeout. NULL = block forever", "The last argument is the timeout. NULL means block forever, so one wedged client can stop the whole loop."),
               ("Client side: set a deadline, then retry with backoff", "On the client side, always set a deadline, and then retry with backoff. We will come back to that in session seven.")]
        self.bullets(pts, size=28, below=sets)

    def ch_cgi(self):
        self.new_slide("CGI: every request forks your program", "Now, how does the server run your code? The oldest answer is CGI, the Common Gateway Interface.", C_PURPLE)
        ap = box("Apache", C_BLUE, w=2.4, h=1.0, size=26).move_to(LEFT * 4.8 + UP * 0.6)
        cg = box("CGI process\n(new, per request)", C_PURPLE, w=3.2, h=1.3, size=22).move_to(RIGHT * 3.6 + UP * 0.6)
        with self.vo("For every request, Apache creates a brand new CGI process, with environment variables and three pipes."):
            self.play(FadeIn(ap), FadeIn(cg))
        ar = [Arrow(ap.get_right() + UP * 0.55, cg.get_left() + UP * 0.55, color=C_GREEN, buff=0.1), Arrow(cg.get_left(), ap.get_right(), color=C_BLUE, buff=0.1),
              Arrow(cg.get_left() + DOWN * 0.55, ap.get_right() + DOWN * 0.55, color=C_RED, buff=0.1)]
        lb = [T("stdin pipe: request body", 20, C_GREEN).next_to(ar[0], UP, buff=0.05), T("stdout: response", 20, C_BLUE).next_to(ar[1], UP, buff=0.04),
              T("stderr: Apache error log", 20, C_RED).next_to(ar[2], DOWN, buff=0.05)]
        with self.vo("The request body goes to the program's standard in. Whatever it prints on standard out becomes the response. And standard error goes to Apache's error log."):
            self.play(*[GrowArrow(a) for a in ar], *[FadeIn(l) for l in lb], run_time=2)
        pts = [("Real code: mod_cgi.c, run_cgi_child() - a timeout on each pipe so a hung script can't hold the worker", "In the real source, mod underscore cgi dot c, the function run_cgi_child creates the child and attaches the three pipes, with a timeout on each, so a hung script cannot hold the worker forever."),
               ("Cost: a whole program image is created, run once, and discarded - per hit", "The cost is that a whole program image is created, run once, and thrown away, on every single hit.")]
        self.bullets(pts, size=24, gap=0.4, shift=DOWN * 1.9)

    def ch_cgi_env(self):
        self.new_slide("HTTP headers become environment variables", "How does your program see the request? HTTP headers become environment variables.", C_PURPLE)
        tbl = self.table([["HTTP", "CGI environment variable"],
                          ["method GET / POST", "REQUEST_METHOD"],
                          ["everything after ?", "QUERY_STRING"],
                          ["User-Agent: curl", "HTTP_USER_AGENT=curl"],
                          ["protocol", "SERVER_PROTOCOL, GATEWAY_INTERFACE"]],
                         [5.0, 6.6], size=24, y=1.2, row_h=0.62)
        self.reveal_rows(tbl, ["The method becomes REQUEST_METHOD.", "The query string becomes QUERY_STRING.",
                               "A header like User-Agent: curl becomes HTTP_USER_AGENT equals curl. Upper-case, dashes become underscores, and an HTTP underscore prefix.",
                               "Plus GATEWAY_INTERFACE and SERVER_PROTOCOL. The code is ap_add_cgi_vars in util_script.c."])
        code = self.code_block(["read REQUEST_METHOD", "POST -> read stdin     GET -> parse QUERY_STRING", "print \"Content-Type: text/html\"", "print \"\"        <- the blank line is the delimiter",
                                "print body"], size=20, pos=DOWN * 2.15)
        with self.vo("The CGI program itself just prints. Read the method. For POST, read standard in. For GET, parse the query string. Print a Content-Type header, then a blank line, which is the delimiter, then the body. "
                     "Any language that can read environment variables and print can serve HTTP. That is why the early web ran on Perl and shell."):
            self.play(FadeIn(code))

    def ch_fixes(self):
        self.new_slide("Two fixes", "Two fixes for the cost of CGI.", C_ORANGE)
        a = VGroup(box("1. Compile it into the server", C_RED, w=5.6, h=0.9, size=24),
                   T("mod_php, mod_perl", 24), T("no new process per request", 22), T("but the app shares an address space with the web server", 22, C_RED),
                   T("one segfault takes both down", 22, C_RED, maxw=5.6)).arrange(DOWN, buff=0.22).move_to(LEFT * 3.5 + UP * 0.3)
        b = VGroup(box("2. FastCGI - the fix that won", C_GREEN, w=5.6, h=0.9, size=24),
                   T("a long-lived pool of processes", 22), T("talk over a Unix or TCP socket", 22), T("a reduced vocabulary", 22),
                   T("setup paid once, at startup", 22, C_GREEN)).arrange(DOWN, buff=0.22).move_to(RIGHT * 3.5 + UP * 0.3)
        with self.vo("One fix is to compile the language into the server, as mod PHP or mod Perl do. No new process per request, but the app now shares an address space with the web server, so one segfault takes both down."):
            self.play(FadeIn(a), run_time=1.5)
        with self.vo("The fix that won is FastCGI. Keep a long-lived pool of processes and talk to it over a Unix or TCP socket using a reduced vocabulary. The setup cost is taken off the request path and paid once at startup, the same trick as pre-forking."):
            self.play(FadeIn(b), run_time=1.5)

    def ch_fastcgi(self):
        self.new_slide("FastCGI architecture", "Here is the architecture.", C_GREEN)
        fl, _ = self.flow(["thousands of\nclients\n(many slow)", "nginx / httpd\nTLS, buffering,\nslow clients", "FastCGI\nupstream", "php-fpm\nfixed pool of\nlong-lived workers"],
                          [C_BLUE, C_ORANGE, C_PURPLE, C_GREEN], y=1.0, w=2.9, h=1.5, size=20, gap=0.4,
                          narrations=["Thousands of clients, many of them slow.", "They talk to nginx or httpd, which is user-facing: it absorbs the slow connections, handles TLS, and buffers.",
                                      "Behind it, you define an upstream, speaking FastCGI.", "To php-fpm: a fixed pool of long-lived workers."])
        with self.vo("FastCGI is a modified HTTP with less vocabulary. It carries the same information, method, headers, query and body, but it is binary, typed and multiplexed."):
            pass
        self.new_slide("The FastCGI record stream", "Let us look at the actual records.", C_GREEN)
        ll = self.lifelines("nginx", "php-fpm", x=3.2)
        self.msg(ll, "r", "BEGIN_REQUEST", C_YELLOW, dy=0.7, size=19, narration="A request begins with FCGI_BEGIN_REQUEST.")
        self.msg(ll, "r", "PARAMS  REQUEST_METHOD=POST ...", C_BLUE, dy=0.7, size=17, narration="Then FCGI_PARAMS carries the variables: REQUEST_METHOD equals POST, SCRIPT_FILENAME, QUERY_STRING, CONTENT_LENGTH, HTTP_HOST.")
        self.msg(ll, "r", "PARAMS (empty)", C_GREY, dy=0.7, size=19, narration="An empty PARAMS record means the params are finished.")
        self.msg(ll, "r", "STDIN  name=alice&age=20", C_GREEN, dy=0.7, size=19, narration="Then FCGI_STDIN carries the body: name equals alice and age equals twenty. Seventeen bytes.")
        self.msg(ll, "r", "STDIN (empty)", C_GREY, dy=0.7, size=19, narration="And an empty STDIN record means stdin is finished.")
        self.msg(ll, "l", "STDOUT  headers, blank, body", C_GREEN, dy=0.7, size=17, narration="The response comes back as FCGI_STDOUT: headers, a blank line, and the body, then an empty STDOUT.")
        self.msg(ll, "l", "STDERR + END_REQUEST", C_RED, dy=0.7, size=19, narration="STDERR goes to the log, in its own record type so debug output can never corrupt the page. Then END_REQUEST.")
        with self.vo("The framing is both. Every record header carries its content length, and an empty, length zero record is the delimiter that says a stream has finished."):
            pass

    def ch_servlets(self):
        self.new_slide("Servlets: the same idea in a JVM", "The same idea shows up in the Java world, as servlets.", C_ORANGE)
        pts = [("Jetty / Tomcat are the web server - the JVM is already running your code", "Jetty and Tomcat are the web server, and the JVM is already running your code."),
               ("Pre-threading: a thread pool created at startup", "A thread pool is created at startup. That is pre-threading."),
               ("Isolation by class loader and thread, not by process", "Isolation is by class loader and thread, not by process. That is cheaper than fork, but a runaway servlet can hurt its neighbours.")]
        g = self.bullets(pts, size=28, gap=0.5, shift=UP * 0.4)
        t = T("CGI, FastCGI, servlets: how do we run user code per request without creating the world each time?", 24, C_YELLOW, maxw=12).to_edge(DOWN, buff=0.6)
        with self.vo("CGI, FastCGI, servlets, and every modern framework answer one question: how do we run user code for each request without creating the world each time?"):
            self.play(FadeIn(t))

    def ch_not_everything(self):
        self.new_slide("Isn't everything a web server?", "Is everything a web server? Not quite.", C_TEAL)
        tbl = self.table([["Speaks HTTP", "Own protocol"],
                          ["router admin page, most Node apps", "Redis (RESP)"],
                          ["Firestore, CouchDB (REST)", "MySQL (binary wire protocol)"],
                          ["Kafka with a REST proxy", "MQTT brokers (IoT), messengers, Kafka natively"]],
                         [6.0, 6.4], size=26, y=1.2, row_h=0.8)
        self.reveal_rows(tbl, ["Plenty of things speak HTTP: a router's admin page, most Node apps.", "Firestore and CouchDB over REST.",
                               "But Redis speaks RESP, MySQL has its own binary wire protocol, and MQTT brokers, messaging backends, and Kafka natively do too."][:3])
        self.new_slide("Stateless vs persistent", None, C_TEAL)
        pts = [("HTTP is stateless -> any box can answer any request -> horizontal scaling is nearly free", "HTTP is stateless. Any box can answer any request, a load balancer can send the next request anywhere, so horizontal scaling is nearly free."),
               ("A database wants to stay connected: connect + handshake + auth + session setup is expensive", "A database wants to stay connected, because the TCP connect, handshake, authentication and session setup are expensive."),
               ("So the question is how many persistent connections one box can hold - not requests per second", "So the question becomes: how many persistent connections can one box hold, not how many requests per second.")]
        self.bullets(pts, size=28, gap=0.6)

    def ch_walls(self):
        self.new_slide("Four walls", "Every server hits four walls.", C_RED)
        walls = [("1  File descriptors", "a connection is a descriptor - default 1024", C_BLUE, "First, file descriptors. A connection is a descriptor, and the default limit is one thousand twenty-four."),
                 ("2  Memory", "a stack per thread, a buffer per connection - paid before any work", C_GREEN, "Second, memory. A stack per thread and a buffer per connection, paid before any work."),
                 ("3  Context switches", "every read, write and syscall crosses the kernel boundary", C_ORANGE, "Third, context switches. Every read, write and system call crosses the kernel boundary."),
                 ("4  The queue", "latency and throughput are not independent - being slow costs memory", C_RED, "And fourth, the queue. Latency and throughput are not independent. Being slow costs memory.")]
        y = 1.6
        for t1, t2, c, nar in walls:
            b = box(t1, c, w=4.3, h=0.8, size=24).move_to([-4.2, y, 0])
            d = T(t2, 22, WHITE, maxw=7.2).next_to(b, RIGHT, buff=0.4)
            with self.vo(nar):
                self.play(FadeIn(b), FadeIn(d), run_time=0.8)
            y -= 1.2

    def ch_c10k(self):
        self.new_slide("C10K to C10M", "The history of this problem is two acronyms.", C_YELLOW)
        line = Line(LEFT * 5.5, RIGHT * 5.5, color=C_GREY).shift(DOWN * 0.2)
        marks = [(-4.5, "1999", "C10K", "Dan Kegel:\ncan one box hold\n10,000 connections?\nThen: no.", C_BLUE,
                  "In nineteen ninety-nine, Dan Kegel asked: can one box hold ten thousand simultaneous connections? At the time, the answer was no."),
                 (0.0, "2013", "C10M", "Robert Graham:\nthe kernel is the problem.\nBypass it for\n10,000,000.", C_ORANGE,
                  "In twenty thirteen, Robert Graham argued the kernel itself is the problem, and that you should bypass it to reach ten million."),
                 (4.5, "today", "2 - 3 million", "demonstrated on one server.\nDefault ulimit -n\nis still 1024.", C_GREEN,
                  "Today, two to three million connections have been demonstrated on one server. And the default ulimit is still one thousand twenty-four.")]
        self.play(Create(line))
        for x, yr, nm, desc, c, nar in marks:
            d = Dot([x, -0.2, 0], color=c, radius=0.13)
            y_ = T(yr, 28, c).move_to([x, 0.4, 0])
            n_ = T(nm, 30, WHITE).move_to([x, 1.1, 0])
            ds = T(desc, 22, WHITE, maxw=4.2, line_spacing=0.9).move_to([x, -1.8, 0])
            with self.vo(nar):
                self.play(FadeIn(d), FadeIn(y_), FadeIn(n_), FadeIn(ds), run_time=1.0)

    def ch_memory(self):
        self.new_slide("Memory per connection", "Memory is the second wall. Compare an OS thread with a goroutine.", C_GREEN)
        a = Rectangle(width=9.0, height=0.7, color=C_RED, fill_opacity=0.4).move_to([-1.6, 1.4, 0])
        at = T("OS thread: 8 MB default stack, reserved up front", 24, WHITE, maxw=8.8).move_to(a)
        eq = T("10,000 threads  =  80 GB of address space", 30, C_RED).move_to([0, 0.4, 0])
        with self.vo("An OS thread reserves an eight megabyte stack up front. Ten thousand threads is about eighty gigabytes of address space."):
            self.play(FadeIn(a), FadeIn(at))
            self.play(FadeIn(eq))
        b = Rectangle(width=0.03, height=0.7, color=C_GREEN, fill_opacity=0.8).move_to([-6.1, -0.9, 0])
        bt = T("Goroutine: 2 KB initial stack, grown on demand - 4000x smaller", 24, C_GREEN, maxw=9).move_to([0.5, -1.5, 0])
        with self.vo("A goroutine starts with a two kilobyte stack, grown on demand. That is four thousand times smaller."):
            self.play(FadeIn(b), FadeIn(bt))
        pts = [("The Go runtime multiplexes goroutines onto a few OS threads using a netpoller built on epoll: you write blocking reads, the runtime parks you on a poll", "The Go runtime multiplexes goroutines onto a few OS threads with a netpoller built on epoll. You write simple blocking reads, and the runtime parks you on a poll.")]
        self.bullets(pts, size=22, shift=DOWN * 2.3)

    def ch_kernel(self):
        self.new_slide("The kernel boundary tax", "The third wall is the kernel boundary.", C_ORANGE)
        fl, _ = self.flow(["save state", "switch page\ntables", "validate", "copy", "return"], [C_BLUE, C_PURPLE, C_ORANGE, C_RED, C_GREEN], y=1.3, w=2.2, h=1.0, size=22, gap=0.4,
                          narrations=["Each trip from user mode into the kernel and back saves state,", "switches page tables,", "validates arguments,", "copies data,", "and returns."])
        with self.vo("Each one costs hundreds of nanoseconds, and the Spectre and Meltdown mitigations made it worse."):
            pass
        L = VGroup(T("Bypass the kernel", 28, C_RED), T("user-space TCP", 22), T("DPDK, netmap, mTCP, Seastar", 22), T("lose all your tools,", 22), T("get the packets", 22)).arrange(DOWN, buff=0.2).move_to(LEFT * 3.4 + DOWN * 1.3)
        R = VGroup(T("Make fewer calls", 28, C_GREEN), T("sendfile(): file -> socket,", 22), T("no user-space copy", 22), T("io_uring: batches of requests", 22), T("through a shared ring", 22)).arrange(DOWN, buff=0.2).move_to(RIGHT * 3.4 + DOWN * 1.3)
        with self.vo("Two responses. Bypass the kernel entirely with user-space TCP: DPDK, netmap, mTCP, Seastar. You lose all your usual tools, but you get the raw packets."):
            self.play(FadeIn(L))
        with self.vo("Or make fewer calls. sendfile moves a file to a socket without a user-space copy, and io_uring submits batches of operations through a shared ring."):
            self.play(FadeIn(R))

    def ch_little(self):
        self.new_slide("Little's Law", "Little's Law ties it all together. Concurrency equals throughput times latency.", C_YELLOW)
        eq = T("connections in flight  =  requests per second  ×  seconds per request", 30, C_YELLOW).shift(UP * 2.0)
        with self.vo("Connections in flight equals requests per second, times seconds per request."):
            self.play(Write(eq))
        a = Rectangle(width=1.0, height=0.7, color=C_GREEN, fill_opacity=0.6).move_to([-5.5 + 0.5, 0.6, 0])
        at = T("10,000 req/s  ×  100 ms  =  1,000 in flight", 24, WHITE).move_to([2.2, 0.6, 0])
        with self.vo("At ten thousand requests per second, with a latency of one hundred milliseconds, you hold one thousand connections."):
            self.play(FadeIn(a), FadeIn(at))
        b = Rectangle(width=10.0, height=0.7, color=C_RED, fill_opacity=0.6).move_to([-5.5 + 5.0, -0.7, 0])
        bt = T("10,000 req/s  ×  1 s  =  10,000 in flight", 24, WHITE).move_to(b)
        with self.vo("Same traffic, but with a latency of one second, and you hold ten thousand."):
            self.play(FadeIn(b), FadeIn(bt))
        t = T("Slowness is a memory bug.  Move slow work off the request path (async).", 28, C_ORANGE, maxw=12).shift(DOWN * 2.3)
        with self.vo("Slowness is a memory bug. Only getting faster reduces what you hold, so take high-latency work off the request path, and do it asynchronously."):
            self.play(FadeIn(t))

    def ch_apache(self):
        self.new_slide("Apache: prefork, worker, event", "Now the servers you actually use. Apache first. Its concurrency model is called an MPM, a Multi-Processing Module, and it evolved through three.", C_BLUE)
        cols = [("prefork", C_RED, "pool of processes,\none connection each.\nBulletproof; works with\nnon-thread-safe modules;\nmost expensive",
                 "Prefork: a pool of processes, one connection each. Bulletproof, works with non-thread-safe modules, and the most expensive."),
                ("worker", C_ORANGE, "processes running\nmany threads.\nCheaper; but a thread is pinned\nto a connection even\nwhile idle on keep-alive",
                 "Worker: processes each running many threads. Cheaper, but a thread is pinned to a connection even while it sits idle on keep-alive."),
                ("event", C_GREEN, "a listener thread parks\nidle keep-alive sockets\non epoll; workers only get\nsockets with work.\nDefault on Unix today",
                 "Event: a listener thread per process parks idle keep-alive sockets on epoll, and hands workers only the sockets with work. It arrived around twenty twelve, and is the default on Unix today.")]
        groups = VGroup(*[VGroup(box(a, c, w=3.8, h=0.8, size=26), T(b, 21, WHITE, maxw=3.9, line_spacing=0.9)).arrange(DOWN, buff=0.3) for a, c, b, _ in cols])
        groups.arrange(RIGHT, buff=0.35, aligned_edge=UP).shift(DOWN * 0.4)
        for g, (_, _, _, nar) in zip(groups, cols):
            with self.vo(nar):
                self.play(FadeIn(g, shift=UP * 0.2), run_time=0.9)

    def ch_haproxy_varnish(self):
        self.new_slide("HAProxy (2001) and Varnish (2006)", "HAProxy arrived in two thousand one.", C_PURPLE)
        pts = [("Largely select at first - epoll landed in Linux 2.5.44 in late 2002; multi-threaded only since 1.8 (2017)", "It was largely select at first. Epoll landed in Linux two point five point forty-four in late two thousand two, and HAProxy became multi-threaded only in version one point eight, in twenty seventeen."),
               ("Introduced the load balancer as a tier in front of the app servers", "Its big idea was to make the load balancer a tier of its own, sitting in front of the app servers and choosing between them."),
               ("A single event-driven process could saturate a NIC; it absorbs connection churn with a pool of persistent upstream connections", "A single event-driven process could saturate a network card, and it absorbs connection churn by keeping a pool of persistent connections to the upstreams.")]
        self.bullets(pts, size=25, gap=0.45)
        self.new_slide("Varnish (2006): the caching reverse proxy", "Varnish, from two thousand six, was the first popular caching reverse proxy.", C_PURPLE)
        a = VGroup(box("Squid", C_GREY, w=2.4, h=0.8, size=26), T("forward proxy, near the users\ncaches for the client - 'way out'", 22, WHITE, maxw=5.5, line_spacing=0.9)).arrange(DOWN, buff=0.3).move_to(LEFT * 3.5 + UP * 0.9)
        b = VGroup(box("Varnish", C_PURPLE, w=2.4, h=0.8, size=26), T("in front of the origin\nsame mechanism, opposite direction - 'way in'", 22, WHITE, maxw=5.8, line_spacing=0.9)).arrange(DOWN, buff=0.3).move_to(RIGHT * 3.5 + UP * 0.9)
        with self.vo("Squid cached for the client. It was a forward proxy near the users, on the way out. Varnish put the same mechanism in front of the origin, on the way in."):
            self.play(FadeIn(a), FadeIn(b), run_time=1.5)
        pts = [("An acceptor thread per listening point; a worker thread per active connection (pools default min 100, max 5000)", "Internally, an acceptor thread per listening point, and a worker thread per active connection, with pools that default to a minimum of one hundred and a maximum of five thousand."),
               ("Idle descriptors are handed to a waiter: epoll on Linux, kqueue on BSD - threads for work, a loop for waiting", "Idle descriptors are handed to a waiter, using epoll on Linux and kqueue on BSD. Threads for work, a loop for waiting."),
               ("Fastly's edge is built on Varnish and VCL", "Fastly's edge is built on Varnish, and VCL, the Varnish Configuration Language, is how you configure that two thousand six program even today.")]
        self.bullets(pts, size=22, gap=0.35, shift=DOWN * 1.7)

    def ch_nginx(self):
        self.new_slide("nginx (2004): epoll + sendfile", "And nginx, from two thousand four, built on epoll and sendfile.", C_GREEN)
        L = VGroup(T("read() + write()", 28, C_RED), T("disk -> kernel -> your buffer", 22), T("-> kernel -> socket", 22), T("two copies; you touch the bytes", 22, C_RED)).arrange(DOWN, buff=0.2).move_to(LEFT * 3.5 + UP * 1.2)
        R = VGroup(T("sendfile(sock, file, NULL, n)", 28, C_GREEN), T("kernel -> socket", 22), T("you never touch the bytes", 22), T("zero-copy", 22, C_GREEN)).arrange(DOWN, buff=0.2).move_to(RIGHT * 3.5 + UP * 1.2)
        with self.vo("With read and write, bytes go from disk, to the kernel, to your buffer, back into the kernel, and out to the socket. With sendfile, the kernel moves them straight from the file to the socket. You never touch the bytes. That is zero copy."):
            self.play(FadeIn(L), FadeIn(R), run_time=2)
        pts = [("One master + one single-threaded worker per CPU core; each runs an epoll loop over thousands of connections", "nginx runs one master process and one single-threaded worker per CPU core. Each worker runs one epoll loop over thousands of connections."),
               ("First a reverse proxy, then 'abused' for caching, load balancing, TLS termination, rate limiting: the default shape of an edge", "It started as a reverse proxy, and was then abused for caching, load balancing, TLS termination and rate limiting. It became the default shape of an edge."),
               ("Thread pool since 1.7.11 for disk reads: a page fault on a cache miss would otherwise stall every connection on that worker", "Since version one point seven point eleven, it has a thread pool for disk reads, because a page fault on a cache miss would otherwise stall every connection on that worker.")]
        self.bullets(pts, size=22, gap=0.35, shift=DOWN * 1.5)

    def ch_compare(self):
        self.new_slide("Side by side", "Side by side.", C_YELLOW)
        tbl = self.table([["Server", "Concurrency model", "Born", "Idea popularised"],
                          ["Apache", "prefork > worker > event", "1995", "modules; CGI"],
                          ["HAProxy", "select > epoll; MT since 1.8", "2001", "load balancer as a tier"],
                          ["Varnish", "thread per conn + epoll waiter", "2006", "caching reverse proxy"],
                          ["nginx", "master + worker per core", "2004", "sendfile; answer to C10K"]],
                         [1.9, 4.4, 1.1, 4.4], size=23, y=0.8, row_h=0.85)
        self.reveal_rows(tbl, ["Apache, nineteen ninety-five: prefork, worker, event. It popularised modules and CGI to run anyone's code. Akamai started here.",
                               "HAProxy, two thousand one: select then epoll. The load balancer as its own tier.",
                               "Varnish, two thousand six: a thread per active connection with an epoll waiter. The caching reverse proxy, now Fastly's edge.",
                               "nginx, two thousand four: a master plus one worker per core. Sendfile, and the answer to C ten K."])
        t = T("All four ended up with an event loop + a small pool of workers.", 28, C_GREEN).shift(DOWN * 2.3)
        with self.vo("All four ended up in the same place: an event loop, and a small pool of workers."):
            self.play(FadeIn(t))

    def ch_ideas(self):
        self.new_slide("The four ideas", "Four ideas to keep from this session.", C_GREEN)
        pts = [("1. Amortise the setup: pre-fork, pre-thread, FastCGI, pools, servlets", "One. Amortise the setup. Pre-fork, pre-thread, FastCGI, pools, servlets."),
               ("2. Nothing is free per connection: descriptor, stack, buffer, scheduler entry, times 10,000", "Two. Nothing is free per connection. A descriptor, a stack, a buffer and a scheduler entry, times ten thousand."),
               ("3. Framing is still length or delimiter: FastCGI uses a length in each record plus an empty record", "Three. Framing is still length or delimiter. FastCGI uses a length in each record, plus an empty record."),
               ("4. Concurrency = throughput x latency: only getting faster reduces what you hold", "Four. Concurrency equals throughput times latency. Only getting faster reduces what you hold.")]
        self.bullets(pts, size=28, gap=0.55)

    def quiz(self):
        self.quiz_recap(3, [
            "fork vs thread vs event loop. Production: pre-fork pool + a loop per worker + SO_REUSEPORT.",
            "FD_SETSIZE = 1024 bitmap. select O(n), epoll O(ready) via epoll_ctl / epoll_wait. kqueue, IOCP, io_uring.",
            "select args: nfds = maxfd + 1, readfds, writefds, exceptfds, timeout (NULL = block forever).",
            "CGI: fork + exec per request; env vars REQUEST_METHOD, QUERY_STRING, HTTP_USER_AGENT; stdin / stdout / stderr pipes.",
            "mod_php / mod_perl run in-process: one segfault kills the server. FastCGI: persistent pool (php-fpm), binary records, empty record = end of stream.",
            "Servlets: Tomcat / Jetty, pre-threaded, class-loader isolation. HTTP is stateless; databases want persistent connections.",
            "C10K Dan Kegel 1999; C10M Robert Graham 2013; 2-3 million today. Thread stack 8 MB vs goroutine 2 KB; 10k threads ~ 80 GB.",
            "Kernel bypass: DPDK, netmap, mTCP, Seastar. sendfile = zero copy. io_uring = batched syscalls. Little's Law: in flight = RPS x latency.",
            "Apache prefork / worker / event. HAProxy 2001, epoll in Linux 2.5.44, MT in 1.8. Varnish 2006, Fastly. nginx 2004, master + worker per core, thread pool since 1.7.11.",
        ], "Here is what the quiz is most likely to ask from session three.", size=26, per_page=5)
        self.say("That is session three. Next up, session four: nginx and the code that explains it.")
