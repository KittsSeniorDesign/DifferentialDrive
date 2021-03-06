package edu.scu.engr.rsl.deca;

import java.io.IOException;
import java.io.OutputStream;

import com.rbnb.sapi.Sink;
import com.rbnb.sapi.ChannelMap;
import com.rbnb.sapi.SAPIException;

public class Receiver extends Thread {
	private Sink internalSink;
	private OutputStream client;
	private String m_sinkName;
	private String dataTurbine;

	public Receiver( String dataTurbine, String botName , OutputStream out ) throws Exception {
		this.dataTurbine = dataTurbine;
		internalSink = new Sink( );
		m_sinkName = botName;
		internalSink.OpenRBNBConnection( dataTurbine, m_sinkName );
		ChannelMap watchList = new ChannelMap( );
		watchList.Add("Derp/" +  botName);
		watchList.Add("_UI_Source/_UI");
		internalSink.Subscribe( watchList );
		client = out;
	}

	protected void reconfigureSink(String newChannel) {
		internalSink.CloseRBNBConnection();
		ChannelMap watchList = new ChannelMap();
		internalSink = new Sink();
		System.out.println("reconfiguring sink to listen to " + newChannel);
		try {
			watchList.Add(newChannel);
			watchList.Add("_UI_Source/_UI");
			internalSink.OpenRBNBConnection( dataTurbine, m_sinkName );
			internalSink.Subscribe(watchList); 
		} catch (SAPIException e) {
			e.printStackTrace();
		} catch ( IllegalStateException error ) {
			// this occurs if the rbnb server shuts down while we are waiting for
			// a client read.
			System.out.println( "Dataturbine has vanished." );
		}
	}
	
	@Override
	public void run ( ) {
		while ( true ) {
			// The argument to Fetch is read timeout in ms. If there is no data,
			// it will eventually time out and return an empty channel map. I
			// actually have no idea what circumstances it will throw an
			// SAPIException under, because killing rbnb causes it to throw
			// java.lang.IllegalStateException.
			ChannelMap getmap;
			try {
				getmap = internalSink.Fetch( 1000 );
			} catch ( SAPIException error ) {
				System.out.println( "SAPIException: " + error.getMessage( ) );
				break;
			} catch ( IllegalStateException error ) {
				// this occurs if the rbnb server shuts down while we are waiting for
				// a client read.
				System.out.println( "Dataturbine has vanished." );
				break;
			}
			if ( getmap.NumberOfChannels( ) > 0 ) {
				for(int i = 0; i < getmap.NumberOfChannels(); i++) {
					byte[] message = getmap.GetData(i);
					if(getmap.GetName(i).equals("_UI_Source/_UI") || getmap.GetName(i).equals("_UI")) { // we may be getting asked to reconfigure our sink

						String data = "";
						for(int j = 0; j < message.length; j++) {
							data += (char)message[j];
						}
						System.out.println(data);
						// splitData[0] should be the name of the sink that is to be reconfigured (might not correspond to this controller)
						// splitData[1] should be either w or r for waypoint navigation, or reconfiguring a sink
						String[] splitData = data.split(" ");
						if(splitData[0].equals(m_sinkName)) { // need to reconfigure our sink
							if(splitData[1].equals("r")) {  // need to reconfigure our sink 
								// splitData[2] is the new channel the sink should listen to
								reconfigureSink(splitData[2]);
							} else if(splitData[1].equals("w")) {
								System.out.println("waypionting");
								travelToWaypoint(splitData[2], splitData[3]);
							}
						}
					} else {
//						String msg = "";
//						for(int j = 0; j < message.length-1; j+=2) {
//							msg += Integer.toString(((int)message[j+1])<<8 | ((int)message[j])) + ", ";
//						}
//						System.out.println(msg);
						try {
							client.write( message );
						} catch (IOException e) {
							e.printStackTrace();
						}
					}
				}
			}
		}
		System.exit( 1 );
	}

	private void travelToWaypoint(String wx, String wy) {
		byte[] message = new byte[6];
		message[0] = 0;
		message[1] = 5; // means waypoint navigation
		message[2] = (byte) (Integer.parseInt(wx) >> 8);
		message[3] = (byte) Integer.parseInt(wx);
		System.out.println(wx);
		message[4] = (byte) (Integer.parseInt(wy) >> 8);
		message[5] = (byte) Integer.parseInt(wy);
		try {
			client.write(message);
		} catch (IOException e) {
			e.printStackTrace();
		}
		
	}
}
