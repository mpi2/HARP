
/**
 * PluginsExecuter.java
 *
 *
 * Created: Fri Oct 27 12:34:01 2000
 *
 * @author Cezar M. Tigaret
 * @version 0.4
 */
import java.util.*;
import java.io.*;
//import Plugins_Control_Panel;

/** Calls a plugin in a separate thread */
public class PluginsExecuter implements Runnable {

	 private String command, path;
	 private Thread thread;
	 private static Plugins_Control_Panel pcp;
	 

	 public PluginsExecuter(String cPath, String pClass, Plugins_Control_Panel pcp){
		  command=pClass;
		  path=cPath;
		  this.pcp=pcp;
		  thread=new Thread(this);
		  thread.setPriority(Math.max(thread.getPriority()-2, Thread.MIN_PRIORITY));
		  thread.start();
	 }

	 public void run(){
		  if (command==null) return;
		  //System.out.println("Executer: "+command);
		  try {
				if (pcp != null ) pcp.runPlugin(path, command);
		  } catch (Throwable e) {
				e.printStackTrace();
		  }
	 }

} // PluginsExecuter
