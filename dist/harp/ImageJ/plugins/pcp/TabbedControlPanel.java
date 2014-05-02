// TODO
// code to get each page in a scroll pane
//
import java.awt.*;
import java.awt.event.*;
import java.util.*;
import java.io.*;
import ij.*;
import ij.plugin.frame.PlugInFrame;
import ij.text.TextWindow;
import cw.notebook.*;


/**
 * TabbedControlPanel.java
 * 
 * This class allows access to classes installed in subdirectories of the main "plugin" directory, using a tabbed  panel with buttons. 
 * 
 * <OL>
 * <LI>FEATURES AND USAGE:</li>
 * 
 * <LI>The control panel is actually a "notebook" with each "page" corresponding to a plugins subdirectory. Pages are selectable using a horizontal row of tabs at the top edge of the notebook. Each tab gets its name from the subdirectory containing the plugins collection.</li>
 *
 * <LI>Right-click in the narrow space under the tab row pops up a menu for page selection (does NOT work on MacOS platforms).</li>
 * 
 * <LI>The plugin supports more than one level of directory branching. However, the control panel will display one row of tabs, regardless of the directory tree depth. </li>
 * 
 * <LI> The code has been written according to Java 1 specifications, without Swing components, so it should be possible to run it on any platform that meets the minimal requirements to run ImageJ 1.1.9</li>
 *  
 * </ol> 
 * <OL>BUGS and LIMITATIONS:
 * 
 * <LI> The subdirectory names should <b>not</b> contain ".class" string or the underscore ('_') character.</li>
 * </ol>
 *
 * Changes as of Saturday 01 September 2001
 * 
 * - changes to the cw.notebook package (see also individual file sources therein):
 *   - the notebook's popup menu is now hooked to a custom button (NBButton.java) located at the top right (right end of the tab panel); it also implements "Help" and "Version" menuitems - their action commands are casted to any ActionListeners registered with the
NoteBook instance
 *   - the tab panel is now scrollable (thanks to TabScroller.java and to two new methods in the Tab.java code: doCommand() and getTabStyle();
 * 
 * - the panel is now registering as an ActionListener to the NoteBook so that it can process the "Help" and "About" actions fired by the NoteBook's popup menu (and possibly other actions, in the future); please see showHelp() and showVersion() methods below for details; this required changes to the action command semantics in the notebook package (see "Changes" section in source files therein) and also changes to the actionPerformed() code here for conformity 
 * 
 * - the reLoad() function now creates a new instance of the TabbedControlPanel after disposing itself
 *
 *
 * Created: Sun Oct 22 22:27:04 2000, Modified on Tue Dec 5 02:32 2000.
 *
 * @see Plugins_Control_Panel
 * @author Cezar M. Tigaret, c.tigaret@ucl.ac.uk
 * @version 0.4b
 */
public class TabbedControlPanel extends PlugInFrame
    implements ActionListener {

    /** The root of the plugins directory tree.
     * 
     * This should normally be the plugins subdirectory in ImageJ installation.
     */
    private String pluginsPath, title;

    /** Holds the tab names in the notebook */
    private Vector tabs;

    /** Holds the "pages" (AWT Components) of the notebook */
    private Vector comps;

    /** Maps each plugin subdirectory name (String) to a Vector of plugin class names (String) found in that subdirectory*/
    private Hashtable vv=new Hashtable();


    /** The platform-specific file separator.*/
    private static String separator=System.getProperty("file.separator"), pcpDir=null;
    private static char sep=separator.charAt(0);

    private static Plugins_Control_Panel pcp;

    private ActionListener listener;

    private NoteBook nB;

	 
    /** Inspired from the original ControlPanel code, by Wayne Rasband 
     * 
     * @see ij.plugin.frame.ControlPanel
     */
    public TabbedControlPanel(Plugins_Control_Panel pcp) {
        super("Plugins Panel");
        title="Plugins Panel";
        this.pcp=pcp;
        addActionListener(pcp);
        try {
            pluginsPath=pcp.getPluginsPath();
            //System.out.println("TCP plugins path: "+pluginsPath);
            if (pluginsPath==null) return;
            loadPlugins();
            nB=new NoteBook(0,comps,tabs);
            makeGUI();
            //pack();
            setVisible(true);
        } catch (Throwable e){
            e.printStackTrace();
            return;
        }
    }

    private void makeGUI(){
        if (nB != null) {
            nB.addActionListener(this);
            Dimension deskDim=Toolkit.getDefaultToolkit().getScreenSize();
            //nB.setDebug(true);
            setLayout(new BorderLayout());
            add(nB, "Center");
            Panel buttonPane=new Panel(new BorderLayout());
            //Panel buttonPane=new Panel(new GridLayout());
            Button reload=new Button("Reload");
            reload.addActionListener(this);
            reload.setActionCommand("reload");
            Button dismiss=new Button("Dismiss");
            dismiss.addActionListener(this);
            dismiss.setActionCommand("dismiss");
            Button help=new Button("Help");
            help.addActionListener(this);
            help.setActionCommand("help");
            buttonPane.add(reload, "West");
            buttonPane.add(dismiss, "East");
            //buttonPane.add(help, "East");
            add(buttonPane, "South");
            setBounds(deskDim.width/10,deskDim.height/10,400,200);
        }
    }

    private void loadPlugins(){
        tabs=new Vector();
        comps=new Vector();
        String pPath=pluginsPath.substring(0,pluginsPath.lastIndexOf(separator));
        recursiveSearch(new File(pPath), new Vector());
        if (vv==null || vv.isEmpty()) {
            //System.out.println("No plugins found");
            return;
        }
        String[] dirs=new String[vv.size()];
        int i=0;
        for (Enumeration e=vv.keys();e.hasMoreElements();) {
            dirs[i]=(String)e.nextElement();
            i++;
        }
        quickSSort(dirs,0,dirs.length-1);
        for (i=0;i<dirs.length;i++) {
            String id=dirs[i]; // dir path name
            //System.out.println(id);
            Vector v=(Vector)vv.get(id);
            if ((v!=null) && (v.size()>0)){
                GridLayout l=new GridLayout(0,4,0,0);
                Panel p=new Panel(l);
                for (Enumeration e1=v.elements();e1.hasMoreElements();) {
                    String s=(String)e1.nextElement(); // class file name
                    String c=s.substring(0,s.length()-6);
                    c=c.replace('_',' ');
                    Button b=new Button(c);
                    b.addActionListener(this);
                    b.setActionCommand(s);
                    p.add(b);
                }
                comps.addElement(p);
                id=id.substring(id.lastIndexOf(separator)+1,id.length());
                tabs.addElement(id);
            }
        }
    }	 

    private void reLoad(){
//         if (nB != null) {
//             tabs.removeAllElements();
//             comps.removeAllElements();
//             vv.clear();
//             loadPlugins();
//             nB.setPages(0,comps,tabs);
//         }
        setVisible(false);
        dispose();
        System.gc();
        new TabbedControlPanel(pcp);
    }

    /** The recursive directory search for compiled main plugin class files. 
     * 
     * @param dir The directory in which the search is performed
     * @param v The registry (a Vector) for the valid plugin classes found in <pre>dir</pre>.
     * 
     */
    private void recursiveSearch(File dir, Vector v){
        //System.out.println("TCP recursive in: "+dir.getPath());
        boolean hasPlugins=false;
        String [] list=dir.list();
        if (list!=null){
            if (list.length>0) quickSSort(list,0,list.length-1);
            for (int i=0; i<list.length; i++) {
                String s=list[i];
                //System.out.println("TCP list item: "+s);
                File f=new File(dir.getPath()+separator+list[i]);
                if (list[i].equals("Plugins_Control_Panel.class")) pcpDir=f.getParent();
                if (f.isDirectory()) recursiveSearch(f, new Vector());
                //System.out.println("TCP file item: "+f.getPath());
                if (register(v,s)) hasPlugins=true;
            }
            if (hasPlugins){
                vv.put(dir.getPath(),v);
            }
        }
    }

    // modified after the implementation of C. A. Hoare quick sort algorithm in Fritz Jobst, "Programmieren in Java - 2., aktualisierte und erweiterte Auflage", Carl Hanser Verlag, Munchen, Wien, [ISBN 3-446-21091-1], 1999, pp.35-36
    private void quickSSort(String[] ar, int l, int r){
        int i=l, j=r;
        String pivot;
        pivot=ar[(l+r)>>1];
        do {
            while (ar[i].compareTo(pivot)<0) i++;
            while (pivot.compareTo(ar[j])<0) j--;
            if (i<=j) {
                String tmp=ar[j];
                ar[j]=ar[i];
                ar[i]=tmp;
                i++;
                j--;
            }
        } while (i<=j);
        if (l<j) quickSSort(ar,l,j);
        if (i<r) quickSSort(ar,i,r);
    }

    /** Validates plugin class file with name s and registers it into Vector v.
     * 
     * @param v The registry (a Vector) of the class names.
     * @param s The filename of the class to be registered
     */
    private boolean register(Vector v, String s){
        boolean found=false;
        if (s.indexOf('_')>=0 && s.endsWith(".class") && s.indexOf('$')<0){
            if (!s.equals("Plugins_Control_Panel.class")){
                v.addElement(s);
                found=true;
            }
        }
        return found;
    }

    public void processEvent(ActionEvent e) {
        if (listener !=null) {
            listener.actionPerformed(e);
        }
    }

    public void addActionListener(ActionListener al) {
        listener=AWTEventMulticaster.add(listener, al);
    }

    public void removeActionListener(ActionListener al) {
        listener=AWTEventMulticaster.remove(listener, al);
    }

    /** Casts the comand to the class loader. */
    public void actionPerformed(ActionEvent ev){
        String cmd=ev.getActionCommand();
        //System.out.println("TabbedControlPanel received command: "+cmd);
        // filter-out prefixes from notebook package action command strings
        if (cmd!=null){
            if (cmd == "dismiss") {
                processWindowEvent(new WindowEvent(this,WindowEvent.WINDOW_CLOSING));
            } else if (cmd == "reload") {
                reLoad();
            } else if (cmd.startsWith("nb_")) {
                if (cmd=="nb_help") {
                    showHelp();
                } else if (cmd=="nb_about") {
                    showVersion();
                }
            } else {
                String plPath=retrievePath(cmd);
                //System.out.println("Tabbed Panel pp: "+plPath);
                cmd=plPath+separator+cmd;
                cmd=cmd.substring(0,cmd.length()-6);
                processEvent(new ActionEvent(this,ActionEvent.ACTION_PERFORMED,cmd));
            }
        }
    }

    private void showHelp() {
        if (pcpDir!=null) {
            TextWindow hWindow=new TextWindow(pcpDir+separator+"pcp_help1.txt",450,400);
            hWindow.setTitle("Plugins Control Panel Help");
        }
    }


    private void showVersion() {
        IJ.write("ImageJ Plugins Control Panel "+pcp.getVersion());
    }

    /** Returns the pathname of the compiled main plugin class file with name plName */
    private String retrievePath(String plName){
        String pp="";
        for (Enumeration e=vv.keys();e.hasMoreElements();){
            pp=(String)e.nextElement();
            Vector v=(Vector)vv.get(pp);
            for (Enumeration e1=v.elements();e1.hasMoreElements();){
                String pIn=(String)e1.nextElement();
                if (pIn.equals(plName)) return pp;
            }
        }
        return pp;
    }

    public void processWindowEvent(WindowEvent e) {
        if (e.getID()==WindowEvent.WINDOW_CLOSING) {	
            setVisible(false);
            dispose();
        }
        super.processWindowEvent(e);
    }

} // TabbedControlPanel








