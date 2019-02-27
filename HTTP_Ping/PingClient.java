import java.io.*;
import java.net.*;
import java.util.*;

/*
 * Client 
 */

public class PingClient
{
   private static final int MAX_TIMEOUT = 1000;  // milliseconds

   public static void main(String[] args) throws Exception
   {
      // Get command line argument.
      if (args.length != 2) {
         System.out.println("Required arguments: Address and port");
         return;
      }
      int port = Integer.parseInt(args[1]);
	  
	  InetAddress server;
	  server = InetAddress.getByName(args[0]);

      // Create a datagram socket for receiving and sending UDP packets
      // through the port specified on the command line.
      DatagramSocket socket = new DatagramSocket();

      // Processing loop.
	  int seq = 0;
	  int lost_count = 0;
      while (seq < 10) {
		 //sent time
		 Date now = new Date();
		 long msSend = now.getTime();
		 //send message
		 String str = "PING " + seq + " " + msSend + "CRLF \n";
		 byte[] buf = new byte[1024];
		 buf = str.getBytes();
		 
		 DatagramPacket ping = new DatagramPacket(buf, buf.length, server, port);

         socket.send(ping);   

         try {
				socket.setSoTimeout(MAX_TIMEOUT);
				DatagramPacket response = new DatagramPacket(new byte[1024], 1024);
				socket.receive(response);
				now = new Date();
				long msReceived = now.getTime();
				System.out.println("ping to " + server.toString().substring(1) + ", seq = "+ seq + ", rtt = " + (int)(msReceived - msSend) + " ms");
			} catch (IOException e) {
				// Print which packet has timed out
				System.out.println("Timeout for packet " + seq);
				lost_count ++;
			}
			seq ++;
      }
	  System.out.println("Loss Rate: " + ((float)lost_count/(float)seq));
   }

}
