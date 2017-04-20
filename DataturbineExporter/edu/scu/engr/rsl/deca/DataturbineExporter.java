package edu.scu.engr.rsl.deca;

import java.io.File;

import com.rbnb.sapi.SAPIException;

import com.etsy.net.JUDS;
import com.etsy.net.UnixDomainSocketServer;

public class DataturbineExporter {
	/**
	 * Sets up the send and receive threads based on arguments passed in. Expected
	 * to be run from the command line.
	 * @param arg
	 *        An array of three Strings, containing the full path to the unix
	 *        domain socket to listen on, the dataturbine server host and port,
	 *        and the name of the robot (for setting up the dataturbine source and
	 *        sink).
	 */
	public static void main(String[] arg) throws Exception {
		try {
			File danglingSock = new File( arg[1] );
			danglingSock.delete( );
		// If this fails due to permissions error, the socket constructor will
		// raise an exception, so just gobble all exceptions here.
		} catch ( Exception error ) { }

		UnixDomainSocketServer server = new UnixDomainSocketServer( arg[1], JUDS.SOCK_STREAM );
		Runtime.getRuntime( ).addShutdownHook( new SocketCleanup( server ) );

		Sender sender;
		Receiver receiver;
		try {
			sender = new Sender( arg[0], arg[2], server.getInputStream( ) );
			receiver = new Receiver( arg[0], arg[2], server.getOutputStream( ) );
		} catch ( SAPIException error ) {
			System.out.println( "Could not connect to dataturbine." );
			return;
		}

		sender.start( );
		receiver.start( );

		sender.join( );
		receiver.join( );
	}
}
