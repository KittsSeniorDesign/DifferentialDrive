package edu.scu.engr.rsl.deca;

import java.util.HashMap;
import java.io.IOException;
import java.io.InputStream;

import com.rbnb.sapi.Source;
import com.rbnb.sapi.ChannelMap;
import com.rbnb.sapi.SAPIException;

public class Sender extends Thread {
	// private int channel;
	private HashMap<String, Integer> chanMap;
	private Source internalSource;
	private ChannelMap outputChannels;
	private InputStream client;

	public Sender( String dataTurbine, String botName, InputStream in ) throws Exception {
		internalSource = new Source( );
		outputChannels = new ChannelMap( );
		chanMap = new HashMap<String, Integer>( );
		chanMap.put( "states", outputChannels.Add( "states" ) );
		internalSource.OpenRBNBConnection( dataTurbine, botName+"-source" );
		client = in;
	}

	@Override
	public void run ( ) {
		while ( true ) {
			byte[] message = new byte[512];
			try {
				int bytesRead;
				try {
					bytesRead = client.read( message );
				} catch ( IllegalStateException error ) {
					// this occurs if the rbnb server shuts down while we are waiting for
					// a client read.
					System.out.println( "Dataturbine has vanished." );
					break;
				}
				if ( bytesRead < 0 ) {
					System.out.println( "client disconnected." );
					break;
				} else if ( bytesRead > 0 ) {
					String packet = new String( message, 0, bytesRead );
					try {
						outputChannels.PutDataAsString( chanMap.get( "states" ), packet );
						internalSource.Flush( outputChannels, true );
					} catch ( SAPIException error ) {
						System.out.println( "barf: " + error.getMessage( ) );
						break;
					}
				}
			} catch ( IOException error ) {
				System.out.println( "dang" + error.getMessage( ) );
				break;
			}
		}
		System.exit( 1 );
	}
}
