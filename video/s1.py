from common import *


class S1(VScene):
    def construct(self):
        self.session_title(
            1, "Network Programming, From the Socket Up", "A TCP server is seven system calls",
            "Session one. Network programming, from the socket up. By the end of this session, "
            "you will see that every web framework you have ever used is a thin wrapper around seven system calls.")

        self.ch_seven_calls()
        self.ch_echo_code()
        self.ch_ports()
        self.ch_skip_a_call()
        self.ch_backlog()
        self.ch_sigpipe()
        self.ch_client()
        self.ch_byte_order()
        self.ch_dns()
        self.ch_tools()
        self.ch_concurrency()
        self.ch_tls()
        self.ch_framing()
        self.ch_encodings()
        self.ch_grpc()
        self.quiz()

    # ------------------------------------------------------------------
    def ch_seven_calls(self):
        h = self.new_slide("The server's seven calls",
                           "Here is the core claim of the session. A TCP server is exactly seven system calls.")
        labels = ["socket", "bind", "listen", "accept", "read", "write", "close"]
        cols = [C_BLUE, C_BLUE, C_BLUE, C_ORANGE, C_GREEN, C_GREEN, C_RED]
        nars = [
            "First, socket. Ask the kernel for an endpoint. AF underscore INET means IPv4, and SOCK underscore STREAM means TCP, a byte stream.",
            "Bind. Attach that socket to a port number, so clients know where to find you.",
            "Listen. Tell the kernel to start accepting connections on your behalf.",
            "Accept. Block until a client connection arrives, and hand it to you as a brand new file descriptor.",
            "Read the bytes the client sent.",
            "Write bytes back.",
            "And close, when you are done.",
        ]
        grp, boxes = self.flow(labels, cols, y=0.6, w=1.5, h=0.9, size=24, gap=0.38, narrations=nars)
        srv = Brace(VGroup(*boxes[:4]), DOWN, color=C_BLUE)
        srv_t = T("only a server does these", 24, C_BLUE).next_to(srv, DOWN, buff=0.15)
        with self.vo("Bind, listen and accept are the three calls that only a server makes. "
                     "Express, Flask and Go's net slash http are all wrappers around this exact sequence."):
            self.play(GrowFromCenter(srv), FadeIn(srv_t))
        cl = VGroup(*[box(l, c, w=1.9, h=0.8, size=24) for l, c in
                      [("socket", C_BLUE), ("connect", C_PURPLE), ("read / write", C_GREEN), ("close", C_RED)]])
        cl.arrange(RIGHT, buff=0.5).shift(DOWN * 2.2)
        lab = T("A client:", 26, C_PURPLE).next_to(cl, UP, buff=0.3).align_to(cl, LEFT)
        with self.vo("A client is shorter. Socket, connect, read and write, close. "
                     "Notice what is missing. A client never calls bind, and never calls listen."):
            self.play(FadeIn(lab), FadeIn(cl, lag_ratio=0.2), run_time=1.5)
        with self.vo("Our course port for the demos is two thousand twenty-six."):
            self.wait(0.5)

    def ch_echo_code(self):
        self.new_slide("The echo server, in C", "Let us look at the whole thing. About twenty lines.")
        lines = [
            "int server_fd = socket(AF_INET, SOCK_STREAM, 0);",
            "addr.sin_family = AF_INET;",
            "addr.sin_addr.s_addr = INADDR_ANY;",
            "addr.sin_port = htons(2026);",
            "bind(server_fd, &addr, sizeof(addr));",
            "listen(server_fd, 1);",
            "while (1) {",
            "    int client_fd = accept(server_fd, NULL, NULL);",
            "    n = read(client_fd, buf, sizeof(buf));",
            "    write(client_fd, buf, n);",
            "    close(client_fd);",
            "}",
        ]
        hl = {"socket": C_BLUE, "bind": C_BLUE, "listen": C_BLUE, "accept": C_ORANGE, "read": C_GREEN,
              "write": C_GREEN, "close": C_RED}
        code = self.code_block(lines, size=22, hl=hl, pos=DOWN * 0.3)
        with self.vo("The program creates a socket, fills in an address structure, binds, and listens. "
                     "Then it loops forever: accept a client, read once, write the same bytes back, close."):
            self.play(FadeIn(code[0]), Write(code[1], run_time=5))
        notes = [
            (2, "INADDR_ANY: listen on every network interface.",
             "INADDR underscore ANY means listen on every network interface of the machine."),
            (3, "htons: host byte order to network byte order.",
             "And htons converts the port number from the host's byte order to network byte order. We will come back to that."),
            (5, "backlog = 1: accept-queue depth.",
             "The number passed to listen is the backlog, the depth of the accept queue. Also coming up."),
        ]
        for idx, txt, nar in notes:
            r = SurroundingRectangle(code[1][idx], color=C_YELLOW, buff=0.06)
            n = T(txt, 22, C_YELLOW).next_to(code, DOWN, buff=0.25)
            with self.vo(nar):
                self.play(Create(r), FadeIn(n))
            self.play(FadeOut(r), FadeOut(n), run_time=0.3)
        with self.vo("One more point. One read is not a conversation. "
                     "To make this server persistent, wrap read and write in a loop that continues while read returns more than zero. "
                     "When read returns zero, that is end of file: the client closed."):
            r = SurroundingRectangle(VGroup(code[1][8], code[1][9]), color=C_GREEN, buff=0.06)
            n = M("while ((n = read(...)) > 0) write(...);", 22, C_GREEN).next_to(code, DOWN, buff=0.25)
            self.play(Create(r), FadeIn(n))

    def ch_ports(self):
        self.new_slide("Ports", "Next, ports. The rule is simple: everything below one thousand twenty-four belongs to root.")
        tbl = self.table([
            ["Range", "Who can bind", "Examples"],
            ["< 1024", "root only", "80 HTTP · 443 HTTPS · 25 SMTP · 21 FTP · 110 POP"],
            [">= 1024", "anyone", "3000 node · 8080 alt-http · 6379 redis · 2026 ours"],
        ], [2.3, 2.8, 7.4], size=24, y=0.9)
        self.reveal_rows(tbl, [
            "Below one thousand twenty-four are the privileged, well-known ports. Only root can bind them. Port 80 is HTTP, 443 is HTTPS, 25 is SMTP, 21 is FTP, 110 is POP.",
            "Above that, anyone can bind. Three thousand for node, eighty-eighty as an alternate HTTP port, sixty-three seventy-nine for Redis, and twenty twenty-six for us.",
        ])
        a = box("front proxy\nowns 80 / 443", C_ORANGE, w=3.2, h=1.1, size=22).move_to([-3.2, -1.7, 0])
        b = box("your app\nbinds 8080\nunprivileged user", C_GREEN, w=3.4, h=1.3, size=22).move_to([3.2, -1.7, 0])
        ar = Arrow(a.get_right(), b.get_left(), color=C_YELLOW, buff=0.1)
        with self.vo("Why does this matter? If your server binds port eighty, it runs as root, "
                     "so a bug in your request parser becomes a root compromise. Real deployments flip it around. "
                     "The app binds eighty-eighty as an unprivileged user, and a small front proxy that does almost nothing owns eighty and four forty-three."):
            self.play(FadeIn(a), FadeIn(b), GrowArrow(ar), run_time=1.5)

    def ch_skip_a_call(self):
        self.new_slide("What breaks if you skip a call?",
                       "A good way to learn what each call does is to skip one. There are two classic mistakes.", C_RED)
        ll = self.lifelines("Client", "Server (kernel)", x=3.4)
        self.msg(ll, "r", "SYN", C_YELLOW, narration="Case one. You never called bind. Nobody owns the port. The client sends a SYN.")
        self.msg(ll, "l", "RST", C_RED, note="Connection refused",
                 narration="The kernel answers immediately with an R S T. The client sees connection refused. Fast, and loud.")
        self.new_slide("bind + listen, but no accept()", C_RED)
        ll = self.lifelines("Client", "Server (kernel)", x=3.4)
        self.msg(ll, "r", "SYN", C_YELLOW, narration="Case two. You bind and listen, but never call accept. The client sends a SYN.")
        self.msg(ll, "l", "SYN-ACK", C_GREEN, narration="The kernel completes the three-way handshake on your behalf.")
        self.msg(ll, "r", "ACK", C_YELLOW, narration="The connection is established, and sits in the accept queue.")
        q = box("accept queue: connection waiting", C_ORANGE, w=5.6, h=0.8, size=22).move_to([3.4, -2.2, 0])
        n = T("client waits... and waits", 26, C_RED).move_to([-3.4, -2.2, 0])
        with self.vo("But your process never picks it up. The client simply hangs until TCP times out. "
                     "This looks exactly like an overloaded server, which is why it is such a confusing bug."):
            self.play(FadeIn(q), FadeIn(n))

    def ch_backlog(self):
        self.new_slide("listen(fd, backlog)", "Let us look closer at the accept queue.")
        q = VGroup(*[Square(0.8, color=C_ORANGE, stroke_width=3) for _ in range(5)]).arrange(RIGHT, buff=0.1).shift(UP * 0.3)
        lab = T("accept queue", 26, C_ORANGE).next_to(q, UP, buff=0.3)
        with self.vo("The kernel keeps completed connections in a queue until your code calls accept."):
            self.play(FadeIn(q), FadeIn(lab))
        dots = [Dot(color=C_BLUE, radius=0.22).move_to(q[i]) for i in range(3)]
        with self.vo("By the time accept returns, the connection has already been established for a while."):
            self.play(*[FadeIn(d, scale=0.3) for d in dots], lag_ratio=0.3, run_time=1.5)
        pts = [
            ("Full-queue behaviour is not portable: refused on some systems, endless 'Trying' on others.",
             "Three facts to remember. What happens when the queue is full is not portable. Some systems refuse, others hang."),
            ("Linux caps the backlog at net.core.somaxconn.",
             "Linux caps the number at net dot core dot somaxconn, so the number in your code may not be the number in effect."),
            ("It is queue depth, not a connection limit.",
             "And the backlog is the depth of the accept queue. It is not a limit on how many connections you can have."),
        ]
        self.bullets(pts, size=24, gap=0.35, below=q)

    def ch_sigpipe(self):
        self.new_slide("Signals: SIGPIPE will kill you",
                       "Signals. Most are harmless trivia, but one of them will kill your server.", C_RED)
        tbl = self.table([
            ["Signal", "No.", "Meaning"],
            ["SIGINT", "2", "Ctrl-C"],
            ["SIGKILL", "9", "cannot be caught"],
            ["SIGPIPE", "13", "write to a socket the peer closed -> process dies"],
            ["SIGTERM", "15", "the polite kill"],
        ], [2.4, 1.0, 7.8], size=24, y=0.7)
        self.reveal_rows(tbl, [
            "SIGINT is signal two. It is what Ctrl C sends.",
            "SIGKILL is nine, and it cannot be caught.",
            "SIGPIPE is thirteen. If you write to a socket the peer has already closed, the default action is to terminate your process. No error, no exception. The process is just gone.",
            "SIGTERM is fifteen, the polite kill.",
        ])
        rect = SurroundingRectangle(tbl[3], color=C_RED, buff=0.12)
        self.play(Create(rect))
        pts = [
            ("SO_LINGER {1, 0}: abortive close, RST instead of FIN, no TIME_WAIT",
             "In the demo, the client forces a reset using SO underscore LINGER with on, and a timeout of zero. "
             "That sends an R S T instead of a FIN, tears the connection down immediately, discards unsent data, and skips TIME underscore WAIT."),
            ("Real fix: ignore SIGPIPE or MSG_NOSIGNAL, then handle EPIPE",
             "The real fix in servers is to ignore SIGPIPE, or pass MSG underscore NOSIGNAL, and handle the E PIPE error yourself."),
        ]
        self.bullets(pts, size=23, gap=0.3, below=tbl)

    def ch_client(self):
        self.new_slide("Writing the client",
                       "Now the client. It is shorter than the server, and the interesting part is what is missing.", C_PURPLE)
        lines = [
            "he = gethostbyname(\"localhost\");   // DNS!",
            "fd = socket(AF_INET, SOCK_STREAM, 0);",
            "memcpy(&addr.sin_addr, he->h_addr_list[0], he->h_length);",
            "addr.sin_port = htons(8080);",
            "connect(fd, &addr, sizeof(addr));  // 3-way handshake",
            "write(fd, \"hello\", 5);",
            "close(fd);",
        ]
        code = self.code_block(lines, size=21, hl={"gethostbyname": C_ORANGE, "socket": C_BLUE, "connect": C_PURPLE,
                                                     "write": C_GREEN, "close": C_RED}, pos=UP * 0.6)
        with self.vo("Look up the host name. Create a socket. Fill in the address and port. Connect, which triggers the three-way handshake. Write. Close."):
            self.play(FadeIn(code[0]), Write(code[1], run_time=4))
        n = T("No bind. No listen.", 34, C_YELLOW).next_to(code, DOWN, buff=0.5)
        with self.vo("No bind. No listen."):
            self.play(Write(n))
        eph = VGroup(
            T("Ephemeral ports", 28, C_ORANGE),
            T("kernel picks a random high port at connect()", 24),
            T("Linux range: 32768 - 60999", 24, C_YELLOW),
            T("TIME_WAIT holds each one ~60 s -> busy clients can run out", 24, C_RED),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.18).to_edge(DOWN, buff=0.3).to_edge(LEFT, buff=0.9)
        with self.vo("So where does the client's port come from? The kernel picks a random high port at connect time, from the ephemeral range. "
                     "On Linux that is typically thirty-two thousand seven hundred sixty-eight to sixty thousand nine hundred ninety-nine. "
                     "The server must bind a known port, because clients need a fixed address. But the client does not. "
                     "Ephemeral ports are finite, and TIME underscore WAIT holds each for about sixty seconds after close, so busy clients really can run out."):
            self.play(FadeOut(code), FadeOut(n), run_time=0.5)
            self.play(eph.animate.move_to(ORIGIN), run_time=0.8)

    def ch_byte_order(self):
        self.new_slide("Byte order: htons()",
                       "A quick but famous detail: byte order.", C_TEAL)
        big = T("port 2026  =  0x07EA", 36, C_YELLOW).shift(UP * 1.7)
        with self.vo("Port twenty twenty-six is hex zero seven E A."):
            self.play(Write(big))
        le = VGroup(box("EA", C_RED, w=1.2, h=0.9, size=34), box("07", C_RED, w=1.2, h=0.9, size=34)).arrange(RIGHT, buff=0.15)
        be = VGroup(box("07", C_GREEN, w=1.2, h=0.9, size=34), box("EA", C_GREEN, w=1.2, h=0.9, size=34)).arrange(RIGHT, buff=0.15)
        le_l = T("little-endian (x86 / ARM laptop)", 24, C_RED)
        be_l = T("network byte order = big-endian", 24, C_GREEN)
        le_g = VGroup(le_l, le).arrange(DOWN, buff=0.25).shift(LEFT * 3.4 + DOWN * 0.4)
        be_g = VGroup(be_l, be).arrange(DOWN, buff=0.25).shift(RIGHT * 3.4 + DOWN * 0.4)
        with self.vo("A little-endian machine, like your laptop, stores the low byte first: E A, then zero seven. "
                     "But the network standard is big-endian: zero seven, then E A."):
            self.play(FadeIn(le_g), FadeIn(be_g), run_time=1.5)
        key = VGroup(M("htons", 26, C_YELLOW), T("host -> network, short (2 bytes)", 24)).arrange(RIGHT, buff=0.3).shift(DOWN * 2.1)
        key2 = VGroup(M("htonl", 26, C_YELLOW), T("4 bytes", 24), M("ntohs / ntohl", 26, C_YELLOW), T("on the way back", 24)).arrange(RIGHT, buff=0.3).next_to(key, DOWN, buff=0.3)
        with self.vo("That is what htons does: host to network, short, two bytes. htonl is the four-byte version, and ntohs and ntohl convert on the way back."):
            self.play(FadeIn(key), FadeIn(key2))

    def ch_dns(self):
        self.new_slide("gethostbyname: one call, a whole protocol",
                       "One innocent function call in the client hides an entire protocol: DNS.", C_ORANGE)
        labels = ["/etc/hosts", "your resolver\n(UDP)", "root", "TLD\n(.com)", "authoritative"]
        cols = [C_GREY, C_BLUE, C_PURPLE, C_PURPLE, C_GREEN]
        nars = [
            "Step one, the file slash etc slash hosts, before any network traffic. That is why editing it overrides everything, and why a stale entry is so hard to debug.",
            "Step two, a UDP query to your resolver, which is listed in etc slash resolv dot conf.",
            "The resolver recurses on your behalf. First it asks a root server.",
            "Then the top-level domain server, for example dot com.",
            "And finally the authoritative server that actually knows the answer.",
        ]
        self.flow(labels, cols, y=0.6, w=2.2, h=1.0, size=20, gap=0.4, narrations=nars)
        pts = [
            ("Cached for the TTL", "The answer is cached for its TTL, so it is fast when warm."),
            ("Blocks the caller - cold lookups take seconds, no timeout you control",
             "But the call blocks. A cold lookup can take seconds, and you do not control the timeout."),
            ("Use getaddrinfo(): gethostbyname is IPv4-only and not thread-safe",
             "In real code, use getaddrinfo. gethostbyname is IPv4 only and not thread safe."),
        ]
        self.bullets(pts, size=26, gap=0.35, shift=DOWN * 2.0)

    def ch_tools(self):
        self.new_slide("You already have a client", "Before writing any code, you already own three clients.", C_BLUE)
        tbl = self.table([
            ["Tool", "Use for", "Example"],
            ["telnet", "any text protocol", "telnet google.com 80"],
            ["openssl s_client", "anything encrypted", "openssl s_client -connect host:443"],
            ["nc (netcat)", "everything else", "nc localhost 2026  ·  nc -l 9000"],
        ], [2.9, 3.2, 6.6], size=23, y=1.3)
        self.reveal_rows(tbl, [
            "telnet. If a protocol is text, your keyboard is an implementation of it. Type GET slash HTTP one point one, a Host header, and a blank line, and Google answers.",
            "openssl s underscore client, for anything encrypted, because telnet is useless once TLS gets in the way.",
            "And netcat for everything else. nc localhost 2026 is a client. nc dash l 9000 is a tiny server.",
        ])
        req = self.code_block(["GET / HTTP/1.1", "Host: google.com", ""], size=22, pos=DOWN * 1.6 + LEFT * 3.4)
        resp = self.code_block(["HTTP/1.1 301 Moved Permanently", "Location: http://www.google.com/",
                                "Cache-Control: public, max-age=2592000", "Content-Length: 219"], size=20,
                               pos=DOWN * 1.6 + RIGHT * 3.0)
        with self.vo("The response is a three hundred one, moved permanently, cacheable for two million five hundred ninety-two thousand seconds. That is thirty days. "
                     "CRLF line endings, and the blank line that ends the headers are mandatory."):
            self.play(FadeIn(req), FadeIn(resp))
        self.new_slide("Where we are on the OSI stack", C_YELLOW)
        rows = [("7", "Application", "our echo protocol, HTTP", C_ORANGE), ("4", "Transport", "TCP, ports, htons(2026)", C_GREEN),
                ("3", "Network", "IP, INADDR_ANY, 127.0.0.1", C_BLUE), ("2", "Data link", "Ethernet, Wi-Fi, MAC", C_PURPLE),
                ("1", "Physical", "copper, fibre, radio", C_GREY)]
        g = VGroup()
        for n, name, what, c in rows:
            b = box(f"L{n}  {name}", c, w=3.4, h=0.7, size=24)
            w = T(what, 24, WHITE)
            g.add(VGroup(b, w).arrange(RIGHT, buff=0.5))
        g.arrange(DOWN, buff=0.18, aligned_edge=LEFT).shift(DOWN * 0.3 + RIGHT * 0.5)
        with self.vo("And where are we on the OSI stack? We have been writing layer seven this whole time. Ports belong to layer four, transport. IP addresses belong to layer three."):
            self.play(FadeIn(g, lag_ratio=0.2), run_time=2.5)

    def ch_concurrency(self):
        self.new_slide("Many clients at once", "Our server handles one client at a time. How do we handle many?", C_GREEN)
        L = VGroup(T("fork() per client", 30, C_BLUE),
                   T("Simple. OS schedules.", 23), T("Crash is contained.", 23), T("Fine for hundreds,", 23),
                   T("hopeless at 10,000.", 23, C_RED)).arrange(DOWN, buff=0.22).move_to(LEFT * 3.4 + DOWN * 0.2)
        R = VGroup(T("select / epoll", 30, C_GREEN),
                   T("Ask kernel: which sockets are ready?", 23), T("No context switching.", 23),
                   T("Harder; one slow handler blocks all.", 23), T("nginx and Node do this.", 23, C_YELLOW)).arrange(DOWN, buff=0.22).move_to(RIGHT * 3.4 + DOWN * 0.2)
        div = Line(UP * 2, DOWN * 2.6, color=C_DIM)
        with self.vo("Two answers. One process per connection, with fork. Dead simple, the operating system schedules it, and a crash is contained to one child. Fine for hundreds of clients, hopeless at ten thousand."):
            self.play(FadeIn(L), Create(div))
        with self.vo("Or one process with many sockets, using select or epoll. Ask the kernel which sockets are ready, and handle only those. "
                     "No context switching, no per-client memory. Harder to write, and one slow handler blocks everything. This is what nginx and Node do."):
            self.play(FadeIn(R))
        self.new_slide("fork() returns twice", C_BLUE)
        tbl = self.table([["Returns", "You are...", "Do this"],
                          ["0", "the child", "handle this client, then exit"],
                          ["> 0", "the parent (value = child PID)", "close your copy of the fd, back to accept()"],
                          ["-1", "fork failed", "out of processes / memory (nobody checks)"]],
                         [1.6, 4.6, 6.6], size=23, y=0.9)
        self.reveal_rows(tbl, [
            "Fork returns twice. Zero means you are the child. Handle this client, then exit.",
            "A positive value means you are the parent, and the value is the child's process ID. Close your copy of the file descriptor and go back to accept.",
            "Minus one means the fork failed. Out of processes or memory. Almost nobody checks.",
        ])
        self.new_slide("select vs epoll", C_GREEN)
        tb = self.table([["vs", "select", "epoll"],
                         ["Cost", "O(n)", "O(ready)"],
                         ["Each call", "rebuild fd set; kernel walks all", "register once; kernel returns only changes"],
                         ["Limit", "FD_SETSIZE ~ 1024", "equivalents: kqueue (BSD), IOCP (Windows)"]],
                        [1.8, 5.2, 6.0], size=24, y=0.4)
        with self.vo("select versus epoll. Select is portable but O of n. You rebuild the set every call, the kernel walks all of them, and FD underscore SETSIZE caps you near one thousand twenty-four descriptors. "
                     "epoll is Linux only and O of ready. You register interest once, and the kernel returns only the descriptors that changed. "
                     "BSD and macOS have kqueue, Windows has I O C P. nginx and Node are built on this."):
            self.reveal_rows(tb)
        self.new_slide("Limits and options", C_ORANGE)
        pts = [("6 - Chrome's old per-host connection cap; requests 7-10 queue",
                "Some limits to know. Six was Chrome's old cap on connections per host. Requests seven to ten simply queue."),
               ("ulimit -n - ceiling on open file descriptors; sockets count; often 1024",
                "ulimit dash n is the hard ceiling on open file descriptors. Sockets count, and it is often one thousand twenty-four."),
               ("Connection pool: open once, reuse, skip TCP + TLS after the first",
                "A connection pool opens connections once and reuses them, skipping the TCP and TLS handshakes after the first."),
               ("SO_REUSEADDR: restart without 'address already in use' during TIME_WAIT",
                "And SO underscore REUSEADDR is the option you will actually use. Without it, restarting your server fails with address already in use, while the old socket sits in TIME underscore WAIT."),
               ("Promiscuous mode: see traffic that isn't yours - how sniffers work",
                "Promiscuous mode lets a network card see traffic that is not addressed to it. That is how sniffers work, and why plaintext protocols died.")]
        self.bullets(pts, size=24, gap=0.38)
        self.wait(0.5)
        self.new_slide("See the bytes", C_TEAL)
        c = self.code_block(["sudo tcpdump -ni any port 2026 -w 1.pcap   # capture", "tcpdump -r 1.pcap -A    # ASCII",
                             "tcpdump -r 1.pcap -X    # hex + ASCII"], size=22, pos=DOWN * 0.2)
        with self.vo("Finally, to see the actual bytes, use tcpdump or Wireshark. Capture to a file, then read it back as ASCII, or as hex and ASCII."):
            self.play(FadeIn(c))

    def ch_tls(self):
        self.new_slide("SSL / TLS secures TCP, not HTTP",
                       "TLS. The key sentence is: SSL secures TCP, not HTTP.", C_GREEN)
        stack = VGroup(box("HTTP / SMTP / DB protocol", C_ORANGE, w=5, h=0.8, size=24),
                       box("TLS", C_GREEN, w=5, h=0.8, size=28),
                       box("TCP", C_BLUE, w=5, h=0.8, size=28)).arrange(DOWN, buff=0.08).shift(UP * 1.1)
        with self.vo("TLS sits underneath the application protocol, so the same machinery protects HTTP, mail, databases, anything on a socket."):
            self.play(FadeIn(stack, lag_ratio=0.3), run_time=1.5)
        pts = [("1. Asymmetric crypto to agree a shared secret; symmetric for the data",
                "How it works. First, asymmetric cryptography agrees a shared secret. Then symmetric cryptography encrypts the data, because it is dramatically faster."),
               ("2. Certificate binds key to identity; CA chain is why you believe it",
                "Second, a certificate binds a key to an identity. The CA chain is why you believe it. And certificates expire, which is the three A M outage."),
               ("3. Pinning removes the CA: trust this exact cert",
                "Third, certificate pinning removes the CA from the trust equation. Common in mobile apps, trust this exact certificate.")]
        self.bullets(pts, size=22, gap=0.4, below=stack)

    def ch_framing(self):
        self.new_slide("Message framing", "Now protocol design. The single most important decision is framing.", C_ORANGE)
        with self.vo("TCP gives you a byte stream, not messages. When you write two messages, the receiver may read them glued together, or split in half. "
                     "So how does the receiver know where one message ends?"):
            stream = VGroup(*[Square(0.35, color=C_BLUE, fill_opacity=0.5, stroke_width=1) for _ in range(24)]).arrange(RIGHT, buff=0.02).shift(UP * 1.2)
            self.play(FadeIn(stream, lag_ratio=0.05), run_time=2.0)
        tbl = self.table([["Method", "How", "Cost"],
                          ["Fixed length", "every message exactly N bytes", "padding; N can never change"],
                          ["Delimited", "read until a sentinel (HTTP blank line)", "delimiter in data -> escaping"],
                          ["Length prefix", "send size, then bytes (Content-Length)", "robust, binary-safe"]],
                         [2.8, 5.2, 4.7], size=22, y=-1.2)
        self.reveal_rows(tbl, [
            "Option one. Fixed length. Every message is exactly N bytes. Trivial to parse, but you pay in padding, and you can never change N.",
            "Option two. Delimited. Read until a sentinel, like the blank line in HTTP. Simple, until the delimiter shows up in your data, and then you need escaping.",
            "Option three. Length prefix. Send the size, then the bytes, like Content-Length. Robust and binary safe. This is what most modern protocols do.",
        ])

    def ch_encodings(self):
        self.new_slide("Binary encodings", "Some encodings you will meet in real systems.", C_PURPLE)
        # BCD
        t = T("BCD: 4 bits per decimal digit", 28, C_YELLOW).shift(UP * 1.9)
        digits = ["9", "8", "7", "6", "5", "F"]
        nibs = ["1001", "1000", "0111", "0110", "0101", "1111"]
        g = VGroup(*[VGroup(M(d, 30, C_YELLOW), M(n, 22, C_BLUE)).arrange(DOWN, buff=0.15) for d, n in zip(digits, nibs)]).arrange(RIGHT, buff=0.5).shift(UP * 0.4)
        hexs = M("-> hex  98 76 5F", 28, C_GREEN).next_to(g, DOWN, buff=0.4)
        with self.vo("Binary coded decimal. Four bits, one nibble, per decimal digit. Ninety-eight thousand seven hundred sixty-five becomes one-zero-zero-one, one-zero-zero-zero, and so on. "
                     "In hex it reads nine eight, seven six, five F, where F pads the odd nibble. Digits just show up in hex. Half the size of ASCII, and still used in SIM cards, SMS and card transactions."):
            self.play(Write(t), FadeIn(g, lag_ratio=0.15), run_time=3)
            self.play(FadeIn(hexs))
        self.new_slide("TLV: Type - Length - Value", C_PURPLE)
        tlv = VGroup(box("T", C_ORANGE, w=1.3, h=0.9, size=30), box("L", C_BLUE, w=1.3, h=0.9, size=30),
                     box("V  (L bytes)", C_GREEN, w=4.4, h=0.9, size=26)).arrange(RIGHT, buff=0.1).shift(UP * 1.2)
        with self.vo("TLV: type, length, value. It is ASN dot one you can write on a napkin."):
            self.play(FadeIn(tlv, lag_ratio=0.3), run_time=1.5)
        pts = [("Self-describing: unknown type? Skip it using the length", "The magic is that it is self-describing. A parser that does not know a type can skip it using the length."),
               ("-> forward compatible", "So new fields do not break old readers. That is forward compatibility."),
               ("Used by TLS extensions, ISO 8583, protobuf", "TLV is used by TLS extensions, ISO eighty-five eighty-three, and protobuf.")]
        self.bullets(pts, size=27, gap=0.35, below=tlv)
        self.new_slide("ASN.1, hex and base64", C_PURPLE)
        pts = [("ASN.1 (1984): write the grammar once, the codec is generated",
                "ASN dot one, from nineteen eighty-four. Write the grammar once, and the encoder and decoder are generated. It still sits under X five oh nine certificates, LDAP, SNMP and the telecom stack."),
               ("Hex is for reading: 2 chars per byte (tcpdump -X)", "Hex is for reading. Two characters per byte, as in tcpdump dash capital X."),
               ("base64 is for transport over text-only channels", "Base sixty-four is for transport over text-only channels: basic auth, JWTs, email attachments, data URIs."),
               ("base64 costs +33%: 3 bytes become 4 characters", "It costs thirty-three percent more. Three bytes become four characters. A wrapper, not a design.")]
        self.bullets(pts, size=26, gap=0.45)

    def ch_grpc(self):
        self.new_slide("RPC and gRPC", "Finally, RPC and gRPC.", C_TEAL)
        fl, _ = self.flow(["marshal\nfunc + args", "frame + send", "network", "unmarshal\n+ run"],
                  [C_BLUE, C_ORANGE, C_RED, C_GREEN], y=0.8, w=2.7, h=1.0, size=22, gap=0.5,
                  narrations=["RPC is framing plus a function name. First, marshal: turn the function name and its arguments into bytes.",
                              "Then frame and send them.",
                              "But the network is not a function call. Calls fail halfway, time out with the work possibly done, and get retried.",
                              "Then the server unmarshals and runs the function."])
        pts = [("schema first (.proto) -> generate client/server in any language", "gRPC is RPC with protobuf underneath. You write a dot proto schema first, and generate client and server code in any language."),
               ("TLV on the wire -> new fields do not break old clients", "On the wire it is TLV, so new fields do not break old clients."),
               ("runs on HTTP/2: binary, many streams on one connection", "It runs on HTTP two, which is binary and multiplexed."),
               ("cost: you can't read it with curl", "The cost is that you cannot read it with curl. Speed bought with debuggability. Faster than JSON, easier than ASN dot one.")]
        self.bullets(pts, size=24, gap=0.35, below=fl)

    def quiz(self):
        self.quiz_recap(1, [
            "7 calls: socket, bind, listen, accept, read, write, close. Client has no bind / listen.",
            "No listener -> RST -> 'connection refused'. Listen but no accept -> handshake completes, client hangs.",
            "backlog = accept-queue depth; Linux caps at net.core.somaxconn.",
            "Ports < 1024 need root. Ephemeral 32768-60999. TIME_WAIT ~ 60 s.",
            "SIGPIPE (13) kills on write to closed peer. SO_LINGER{1,0} -> RST. SO_REUSEADDR fixes 'address in use'.",
            "htons: 2026 = 0x07EA -> wire bytes 07 EA (big-endian).",
            "gethostbyname: /etc/hosts -> UDP resolver -> root, TLD, authoritative. Prefer getaddrinfo.",
            "select O(n), FD_SETSIZE 1024; epoll O(ready). fork: 0 child, >0 parent, -1 fail.",
            "TLS: asymmetric for key agreement, symmetric for data. Framing: fixed / delimiter / length prefix.",
            "TLV is skippable -> forward compatible. base64 = +33%. BCD = 4 bits per digit.",
        ], "Here is what the quiz is most likely to ask from session one.", size=22)
        self.say("That is session one. Next up, session two: the eagle-eye view of the network stack.")
