package edu.scu.engr.rsl.deca;

import com.etsy.net.UnixDomainSocketServer;

class SocketCleanup extends Thread {
	UnixDomainSocketServer server;

	public SocketCleanup( UnixDomainSocketServer server ) {
		this.server = server;
	}

	@Override
	public void run( ) {
		if (server != null) {
			System.out.println( "Cleaning up socket..." );
			server.unlink( );
		}
	}
}
