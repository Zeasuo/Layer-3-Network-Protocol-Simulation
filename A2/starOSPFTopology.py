from mininet.topo import Topo


class ComplexRouter(Topo):
    """
        A multi-router network topology to test basic functionality of router broadcasting and advertising
        r1 = u  s1  h1
        r2 = v  s2  h2
        r3 = w  s3  h3
        r4 = x  s4  h4
        r5 = y  s5  h5
        The ip address of hosts and interfaces in this topology is static.
    """

    def __init__(self, **params):
        Topo.__init__(self)

        # Add monitor node
        m0 = self.addHost('m0', ip="11.1.11.2/24")

        # Add hosts and switches
        # r1 network host
        r1 = self.addHost('r1', ip='10.1.0.1/24',
                          hostRoute='10.101.0.1 via 10.104.0.1')
        h1 = self.addHost('h1', ip='10.1.0.251/24')
        s1 = self.addSwitch('s1')

        # r2 network host
        r2 = self.addHost('r2', ip='10.101.0.1/24')
        h2 = self.addHost('h2', ip='10.101.0.251/24')
        s2 = self.addSwitch('s2')

        # r3 network host
        r3 = self.addHost('r3', ip='10.103.0.1/24')
        h3 = self.addHost('h3', ip="10.103.0.251/24")
        s3 = self.addSwitch('s3')

        # r4 network host
        r4 = self.addHost('r4', ip='10.104.0.1/24')
        h4 = self.addHost('h4', ip="10.104.0.251/24")
        s4 = self.addSwitch('s4')

        # r5 network host
        r5 = self.addHost('r5', ip='10.105.0.1/24')
        h5 = self.addHost('h5', ip="10.105.0.251/24")
        s5 = self.addSwitch('s5')

        # Add links based on the above diagram
        # r1 network links
        self.addLink(s1, r1, intfName2='r1-eth0', params2={'ip': '10.1.0.1/24'})
        self.addLink(h1, s1)

        # r2 network links
        self.addLink(s2, r2, intfName2='r2-eth0', params2={'ip': '10.101.0.1/24'})
        self.addLink(h2, s2)

        # r3 network links
        self.addLink(s3, r3, intfName2='r3-eth0', params2={'ip': '10.103.0.1/24'})
        self.addLink(h3, s3)

        # r4 network links
        self.addLink(s4, r4, intfName2='r4-eth0', params2={'ip': '10.104.0.1/24'})
        self.addLink(h4, s4)

        # r5 network links
        self.addLink(s5, r5, intfName2='r5-eth0', params2={'ip': '10.105.0.1/24'})
        self.addLink(h5, s5)

        # links between routers
        routers = [r1, r2, r3, r4, r5]
        start = 0
        intf = 11
        for r in routers:
            for y in range(start+1, 5):
                self.addLink(r, routers[start+1], intfName1=r + "-eth" + str(intf),
                             intftName2=routers[start+1] + "-eth" + str(intf),
                             params1={'ip': '12.' + str(start+1) + '.11.1/24'},
                             params2={'ip': '12.' + str(start+1) + '.11.2/24'})
            start += 1
            intf += 1

        # links to monitor node
        intf_ip = 1
        m_intf_num = 0
        for r in [r1, r2, r3, r4, r5]:
            self.addLink(r, m0, intfName1=r + "-eth10",
                         intftName2="m0-eth" + str(m_intf_num),
                         params1={'ip': '11.' + str(intf_ip) + '.11.1/24'},
                         params2={'ip': '11.' + str(intf_ip) + '.11.2/24'})
            m_intf_num += 1
            intf_ip += 1


topos = {'star': (lambda: ComplexRouter())}

