import java.awt.event.*;
import java.io.*;
import java.util.*;
import java.net.*;
import ij.*;
import ij.gui.*;
import ij.io.*;
import ij.plugin.*;
import ij.plugin.filter.*;
import ij.plugin.frame.PlugInFrame;
import ij.gui.*;
import ij.util.*;

/**
 * Plugins_Control_Panel.java
 *
 *
 * Created: Tue Dec  5 00:52:15 2000
 *
 * Code was originally inspired from ij.plugin.frame.ControlPanel by Wayne Rasband, the author of ImageJ ({@link http://rsb.info.nih.gov/ij ImageJ Home Page }).
 *
 * This plugin allows the user to install other ImageJ plugins in a hierarchical subdirectory tree, i.e., under the "plugins" root directory of ImageJ installaton.
 *
 * Depending on the Java platform version you are using, the plugins will be accessible via either:
 * a) a tabbed panel with buttons (for Java 1)
 * b) a tree control panel (for Java 1.2 and later).
 * 
 * @see TabbedControlPanel
 * @see TreeControlPanel
 * @author Cezar M. Tigaret <c.tigaret@ucl.ac.uk>
 * @version 0.4b
 */
public class Plugins_Control_Panel implements PlugIn, ActionListener {

    // On MacOS folder path names often have blank spaces (not recommended, but...) therefore the code for path/filename handling must be rewritten
	 
    /** The top-level user plugins directory as registered my ij.Menus 
     * the plugins subdirectory in ImageJ installation. 
     *
     */
    private static final String pluginsPath=Menus.getPlugInsPath();

    private static final String pcpVersion="0.4b";

    /** The platform-specific file separator string.*/
    private static final String separator=System.getProperty("file.separator");

    /** The platform-specific file separator character. */
    private static final char sep=separator.charAt(0);

    /** The JVM version we're using */
    private static final String jvmversion=System.getProperty("java.version");

    /** The "major" part of the JVM version string. */
    private static final String jvmversionMajor=jvmversion.substring(0,jvmversion.lastIndexOf('.'));

    /** The instance of ImageJ application we're running */
    private static ImageJ ij=IJ.getInstance();

    /** The image class upon which the selected plugin will be run.
     * 
     */
    private ImagePlus imp;

    /** Creates an instance of the control panel flavor that 
     * is suitable for the JVM version we're running.
     */
    public Plugins_Control_Panel() {
        
        if (jvmversionMajor.compareTo("1.1")==0) new TabbedControlPanel(this);
        else new TreeControlPanel(this);
        IJ.register(Plugins_Control_Panel.class);
    }

    /** Runs the selected plugin after trying to load the main 
     * compiled plugin class using a custom class loader.
     * The custom class loader is either:
     * a) PCLassLoader2 (if jvm version is greater than 1.1.x), or
     * b) PanelClassLoader (if jvm version is 1.1.x).
     * If sucessfull, it creates a new instance of the loaded plugin class 
     * and runs it according to whether it implements the PlugIn or the
     * PlugInFilter interface.
     * In either case, the plugin is run via a generic method call i.e., 
     * does not pass any arguments to the run() method.
     * In case of failure, reports the stack trace in ImageJ main window.
     * @see PClassLoader2
     * @see PanelClassLoader
     */
    public Object runPlugin(String pName, String cName) {
        // the instance of ImagePlus
        imp=WindowManager.getCurrentImage();
        // System.out.println("PCP run: "+cName);
        // the plugin object
        Object plugIn=null;
        // the plugin class
        Class c=null;
        // the custom class loader
        ClassLoader loader;
        try {
            // if jvm is 1.1.x use PanelCLassLoader, else use PClassLoader2
            if (jvmversionMajor.compareTo("1.1")==0) {
                loader=new PanelClassLoader(pName, pluginsPath);
            } else {
                loader=new PClassLoader2(pName, pluginsPath);
            }
            // same method call for either class loader, 
            // but things happen differently there
            c=loader.loadClass(cName);
            if (c!=null) {
                if (imp!=null) imp.unlock();
                plugIn=c.newInstance();
            }
            // run the plugin instance - this is a generic call; does not pas any arguments to the plugin
            if (plugIn!=null) {
                if (plugIn instanceof PlugIn) {
                    ((PlugIn)plugIn).run("");
                } else if (plugIn instanceof PlugInFilter) {
                    ij.runFilterPlugIn(plugIn, cName, "");
                }
            }
        } catch (Throwable e) {
            IJ.showStatus("");
            IJ.showProgress(1.0);
            if (imp!=null) imp.unlock();
            if (e instanceof OutOfMemoryError){
                IJ.outOfMemory(cName);
            } else {
                CharArrayWriter cw=new CharArrayWriter();
                PrintWriter p=new PrintWriter(cw);
                e.printStackTrace(p);
                String s=cw.toString();
                if (IJ.isMacintosh()) s=Tools.fixNewLines(s);
                IJ.write(s);
                e.printStackTrace();
            }
        }
        return plugIn;
    }

    /** Inherited from ij.PlugIn interface. Currently not used. */
    public void run(String arg) {
    }
	 
    /** Returns the path to the top-level plugins directory, 
     * as registered within ImageJ and probed with Menus.getPlugInsPath().
     */
    public String getPluginsPath(){
        return pluginsPath;
    }

    public String getVersion(){
        return pcpVersion;
    }


    /** Casts the comand to a new thread via an instance of PluginsExecuter.
     * @see PluginsExecuter
     * @see PanelClassLoader
     * @see PClassLoader2
     */
    public void actionPerformed(ActionEvent e) {
        String cmd=e.getActionCommand();
        //System.out.println("PCP received command: "+cmd);
        if (cmd!=null) {
            String path=cmd.substring(0,cmd.lastIndexOf(sep)+1);
            cmd=cmd.substring(cmd.lastIndexOf(sep)+1);
            //System.out.println("PCP ActionCommand: "+cmd);
            //System.out.println("PCP Plugin Path: "+path);
            new PluginsExecuter(path,cmd,this);
        }		  
    }


} // Plugins_Control_Panel









