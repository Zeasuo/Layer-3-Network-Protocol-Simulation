from mininet.node import Node


class MyRouter(Node):
    def config(self, **params):
        super(MyRouter, self).config(**params)
        self.cmd('sysctl net.ipv4.ip_forward=1')

    def terminate(self):
        self.cmd('sysctl net.ipv4.ip_forward=0')
        super(MyRouter, self).terminate()
