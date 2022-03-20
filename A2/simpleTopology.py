from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node, Controller, RemoteController
from mininet.log import setLogLevel, info
from mininet.cli import CLI

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


def MyTopo():
    net = Mininet(controller=RemoteController)

    info('***Adding controller\n')

    c0 = net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6633)

    # Add hosts and switches
    r1 = net.addHost('r1', ip='10.1.0.1/24')
    h1 = net.addHost('h1', ip='10.1.0.1', defaultRoute='via 10.1.0.1')
    h2 = net.addHost('h2', ip='10.1.0.2', defaultRoute='via 10.1.0.1')
    h3 = net.addHost('h3', ip="10.100.0.1", defaultRoute='via 10.100.0.1')
    h4 = net.addHost('h4', ip="10.100.0.2", defaultRoute='via 10.100.0.1')
    s1 = net.addSwitch('s1')
    s2 = net.addSwitch('s2')

    # Add links based on the above diagram
    net.addLink(s1, r1, intfName2='r1-eth1', params2={'ip': '10.1.0.1/24'})
    net.addLink(s2, r1, intfName2='r1-eth2', params2={'ip': '10.100.0.1/24'})

    net.addLink(h1, s1)
    net.addLink(h2, s1)

    net.addLink(h3, s2)
    net.addLink(h4, s2)

    info('***Starting network\n')
    net.build()

    c0.start()

    s1.start([c0])

    s2.start([c0])
    info('***Running CLI\n')
    CLI(net)

    info('*** Stopping network')
    net.stop()


if __name__ == "__main__":
    setLogLevel('info')
    MyTopo()
