from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.log import setLogLevel, info
from mininet.cli import CLI

from router import MyRouter


class SimpleTopo(Topo):
    """
    A simple topology to test simple router
                   r1
                  |  \
                 |    \
                s1    s2
              /   \   /  \
             h1   h2 h3   h4
    The ip address of hosts and interfaces in this topology is static.
    """

    def build(self, **_opts):

        # Add hosts and switches
        r1 = self.addHost('r1', cls=MyRouter, ip='10.0.0.1/24')
        h1 = self.addHost('h1', defaultRoute='via 10.0.0.1')
        h2 = self.addHost('h2', defaultRoute='via 10.0.0.1')
        h3 = self.addHost('h3', defaultRoute='via 10.100.0.1')
        h4 = self.addHost('h4', defaultRoute='via 10.100.0.1')
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')

        # Add links based on the above diagram
        self.addLink(s1, r1, intfName2='r1-eth1', params2={'ip': '10.0.0.1/24'})
        self.addLink(s2, r1, intfName2='r1-eth2', params2={'ip': '10.100.0.1/24'})

        self.addLink(h1, s1)
        self.addLink(h2, s1)

        self.addLink(h3, s2)
        self.addLink(h4, s2)



topos = {'mytopo': (lambda: SimpleTopo())}
