import javax.swing.*;
import javax.swing.tree.*;
import javax.swing.event.*;
import java.awt.*;
import java.awt.event.*;
import java.util.*;
import java.io.*;
import java.net.URL;
import ij.*;

/**
 * TreeControlPanel.java
 *
 * This class lays out the ImageJ user plugins in a vertical, hierarchical tree.. Plugins are launched by double-clicking on their names, in the vertical tree.
 * 
 * Advantages: uses less screen estate, and provides a realistic graphical presentation of the plugins installed in the file system.
 * 
 * Requires: ImageJ 1.20b or newer, and Java 2 Platform v 1.3 or newer.
 * NB! This plugin will NOT work with Java platform 1 even if you have the Swing components (Java Foundation Classes) installed.
 *
 *
 * Changes as of Saturday 01 September 2001
 * 
 * - Changed the help calling code (showHelp() method in TreeControlPanel.java) so that
the help file resource is loaded from the pcp's directory, whatever its name is.
* 
 * Created: Thu Nov 23 02:12:12 2000
 * @see Plugins_Control_Panel
 * @author Cezar M. Tigaret <c.tigaret@ucl.ac.uk>
 * @version 0.4b
 */

public class TreeControlPanel
    implements ActionListener {
    private String path=null;
    private static String pcpDir=null;
    private JFrame pFrame;
    private static FileFilter pFF, pFD;
    private ActionListener listener;
    private static JTree pTree;
    private DefaultMutableTreeNode root;
    private DefaultTreeModel pTreeModel;
    private static JMenuBar pMenuBar;
    private static JMenu pMenu_p, pMenu_h;
    private static JMenuItem pMenu_p_reload, pMenu_h_help, pMenu_h_about;

    // The instance of the caller
    private static Plugins_Control_Panel pcp;

    /** File filters for compiled main plugin class files (with underscore in filename) and for plugin directories; 
     * @see recurse(File dir, DefaultMutableTreeNode node)
     */
    static {
        // accept only compiled main plugin class file; 
        // reject compiled auxiliary class file and compiled inner (nested) class file; 
        // also reject the compiled Plugins_Control_Panel class file
        pFF=new FileFilter () {
                public boolean accept(File f) {
                    String s=f.getName();
                    if (s.indexOf('_') >= 0 && s.endsWith(".class") && s.indexOf('$') < 0) {
                        if (s.equals("Plugins_Control_Panel.class")) {
                            pcpDir=f.getParent();
                        } else {
                            return true;
                        }
                    }
                    return false;
                }
            };
        // accept only directories with subdirs or plugins
        pFD=new FileFilter() {
                public boolean accept(File f) {
                    if (f.isDirectory()) {
                        File[] plst=f.listFiles(pFF);
                        File[] dlst=f.listFiles(pFD);
                        if(dlst.length>0 || plst.length>0) return true;
                    }
                    return false;
                }
            };
    }

    /** New instance of this tree panel, hooked on the caller (a Plugins_ControlPanel) */
    public TreeControlPanel(Plugins_Control_Panel pcp) {
        this.pcp=pcp;
        addActionListener(pcp);
        addActionListener(this);
        // pluginsPath=pcp.getPluginsPath();
        // no plugins path in ImageJ, no game
        if (pcp.getPluginsPath()==null) return;
        pFrame=new JFrame("Plugins Panel");
        // dispose when user closes this window
        pFrame.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE);
        addActionListener(this);
        root=new DefaultMutableTreeNode("User Plugins");
        pTreeModel=new DefaultTreeModel(root);
        loadPlugins();
        pTree=new JTree(pTreeModel);
        pTree.setEditable(false);
        pTree.putClientProperty("JTree.lineStyle","Angled");
        pTree.getSelectionModel().setSelectionMode(TreeSelectionModel.SINGLE_TREE_SELECTION);
        pTree.addMouseListener(new MouseAdapter() {
                public void mouseClicked(MouseEvent e) {
                    if (e.getClickCount()==2) {
                        int selRow=pTree.getRowForLocation(e.getX(),e.getY());
                        if (selRow!=-1) toAction(pTree);
                    }
                }
            });
        JScrollPane ptView=new JScrollPane(pTree);
        // the menu bar
        pMenuBar=new JMenuBar();
        pMenu_p=new JMenu("Plugins");
        pMenu_p.getAccessibleContext().setAccessibleDescription("Manage Plugins");
        pMenu_p_reload=new JMenuItem("Reload");
        pMenu_h=new JMenu("Help");
        pMenu_h_help=new JMenuItem("Contents");
        pMenu_h_about=new JMenuItem("About");
        pMenu_p_reload.getAccessibleContext().setAccessibleDescription("Reload Plugins");
        pMenu_p_reload.addActionListener(this);
        pMenu_h_help.addActionListener(this);
        pMenu_h_about.addActionListener(this);
        //pMenu_p.add(pMenu_p_reload);
        pMenu_h.add(pMenu_h_help);
        pMenu_h.add(pMenu_h_about);
        pMenuBar.add(pMenu_p_reload);
        pMenuBar.add(pMenu_h);
        pFrame.setJMenuBar(pMenuBar);
        pFrame.getContentPane().add(ptView, BorderLayout.CENTER);
        pFrame.pack();
        pFrame.setVisible(true);
    }

    /**
     *    Recursively builds up the root of the plugins tree
     */    
    private void loadPlugins(){
        recurse(new File(pcp.getPluginsPath()), root);
        if (root.getChildCount()==0) {
            System.out.println("TreeControlPanel couldn't find any plugins");
            return;
        }
    }

    /**
     *   Reloads the plugins tree
     */
    private void reloadPlugins(){
        root.removeAllChildren();
        loadPlugins();
        pTreeModel.reload();
    }

    /** Recursive search for compiled plugin main class files through the plugins directory tree. 
     * 
     * @param dir The directory in which the search is performed
     * @param node The tree node (a DefaultMutableTreeNode) representing this <pre>dir</pre>.
     * 
     */
    private void recurse(File dir,  DefaultMutableTreeNode node){
        // dir search performs separately from file search so that
        // JTree will first show dirs under each node
        DefaultMutableTreeNode lf;
        File[] dlist=dir.listFiles(pFD);
        File[] flist=dir.listFiles(pFF);
        // deal with sub-directories
        if (dlist.length>0) {
            Arrays.sort(dlist);
            for (int i=0;i<dlist.length; i++) {
                File f=dlist[i];
                lf=new DefaultMutableTreeNode(f.getName());
                node.add(lf);
                recurse(f, lf);
            }
        }
        // deal with files in sub-directories
        if (flist.length>0) {
            Arrays.sort(flist);
            for (int i=0;i<flist.length;i++) {
                File f=flist[i];
                String plName=f.getName();
                //plName=plName.substring(0,plName.length()-6); // remove ".class"
                plName=plName.substring(0,plName.lastIndexOf(".class")); // remove ".class"
                plName=plName.replace('_',' '); // reset this at actionPerformed
                lf=new DefaultMutableTreeNode(plName);
                node.add(lf);
            }
        }
    }

    /** Fires an ActionEvent upon double-click on the plugin item (leaf node) in the JTree */
    private void toAction(JTree tree) {
        DefaultMutableTreeNode nde=(DefaultMutableTreeNode)tree.getLastSelectedPathComponent();
        // if the node has children then do nothing (return)
        if (nde.getChildCount()>0) return;
        // construct a path string to the selected plugin
        TreeNode[] nodes=nde.getPath();
        path=pcp.getPluginsPath();
        for (int i=1;i<nodes.length;i++) {
            if (i==nodes.length-1) break;
            path+=((DefaultMutableTreeNode)nodes[i]).toString();
            if (i<nodes.length-1) path+=System.getProperty("file.separator");
        }
        //System.out.println("TreeControlPanel: "+path);
        // fires up the ActionEvent; set ActionCommand as the name of the selected item; replace blanks back to underscores
        String aCmd=nde.toString().replace(' ','_');
        processEvent(new ActionEvent(this,ActionEvent.ACTION_PERFORMED,path+aCmd));
    }

    private void showHelp(){
        if (pcpDir!=null) {
            //System.out.println(pcpDir);
            JFrame helpFrame=new JFrame("Plugins Control Panel Help");
            helpFrame.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE);
            JEditorPane helpPane=new JEditorPane();
            helpPane.setEditable(false);
            //String h="file:"+pcp.getPluginsPath()+"pcp-0.4a"+System.getProperty("file.separator")+"pcp_help2.html";
            String h="file:"+pcpDir+System.getProperty("file.separator")+"pcp_help2.html";
            try {
                URL helpURL=new URL(h);
                helpPane.setPage(helpURL);
            } catch (Exception e) {
                e.printStackTrace();
            }
            JScrollPane helpScrollPane=new JScrollPane(helpPane);
            helpScrollPane.setVerticalScrollBarPolicy(JScrollPane.VERTICAL_SCROLLBAR_ALWAYS);
            helpScrollPane.setPreferredSize(new Dimension(400,300));
            helpFrame.getContentPane().add(helpScrollPane,BorderLayout.CENTER);
            helpFrame.pack();
            helpFrame.setVisible(true);
        }
    }

    public void processEvent(ActionEvent e) {
        if (listener != null) {
            listener.actionPerformed(e);
        }
    }

    public void addActionListener(ActionListener al) {
        listener=AWTEventMulticaster.add(listener, al);
    }

    public void removeActionListener(ActionListener al) {
        listener=AWTEventMulticaster.remove(listener, al);
    }

    public void actionPerformed(ActionEvent e) {
        String cmd=e.getActionCommand();
        if (cmd.equals("Reload")) {
            //System.out.println("Reload plugins");
            //MenuBar ijMnuBar=Menus.getMenuBar();
            reloadPlugins();
        }
        if (cmd.equals("Contents")){
            showHelp();
        }
        if (cmd.equals("About")){
            IJ.write("ImageJ Plugins Control Panel "+pcp.getVersion());
        }
    }

	 
} // TreeControlPanel






