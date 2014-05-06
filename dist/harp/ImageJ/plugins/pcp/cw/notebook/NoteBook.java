package cw.notebook;

import cw.notebook.PagePanel;
import cw.notebook.TabPanel;
import cw.notebook.NBButton;

import java.awt.*;
import java.awt.event.*;
import java.util.*;


/**
 * NoteBook.
 * A component that contains a stack of "pages" (AWT components) accesible via a horizontal row of tabs.
 *
 * NoteBook presents the user with a stack of pages (AWT Components) "linked" to each tab located in a row above the stack. The tab row is scrollable, giving access to tabs hidden from the user's view when the row is longer than the width of the notebook.
 *
 * Typical usage of NoteBook is to add it to an AWT Container (e.g., AWT Frame). It implements ActionListener interface so it can be hooked to menus and other event casting AWT components.
 * 
 * Changes as of Sunday 02 September 2001
 * - removed the MouseAdapter code calling the popup menu
 * - the popup menu is now handled by the NBButton
 * - added NBButton.java to handle the popup menu
 * - the popup menu now also contains a "Help" and a "Version" menuitem
 * - what exactly these two menuitems do is up to the ActionListener that is registered with this NoteBook instance; their actionCommand strings are "nb_help" and "nb_about", respectively
 * - added TabScroller.java that implements a scrolling thread on the TabPanel
 * - replaced setActiveItem() with setActivePopupCheckMeunItem() - updates the active (i.e., selected) checkbox menu item in the popup menu
 * 
 *  - modified the action command semantics as follows:
 *    - all action command strings issued by NoteBook class and pertaining to its functionality (page flipping, tabs scrolling, popup menu updating) are prefixed with "nb_"; the same applies to the action commands with a more general scope, that are meant for listeners external to the NoteBook package (see "nb_help" and "nb_about" above)
 *    - all action command strings issued by TabPanel class are prefixed with "tabpnl_"
 *    - all action command strings issued by a Tab are prefixed with "tab_"
 *    - all action command strings issued by NoteBook's popup menu are prefixed with "popup_"
 *   
 * - Plugin groups are now included in a submenu of the primary popup menu
 *
 * Created: Tue Oct 24 00:10:18 2000
 *
 * @author Cezar M. Tigaret
 * @version 0.4b
 * @see cw.notebook.PagePanel
 * @see cw.notebook.TabPanel
 * @see cw.notebook.Tab
 */
public class NoteBook extends Panel
    implements ActionListener, ItemListener {

    private boolean debug; 

    /** A pointer to the page currently displayed. */
    private int localPage;

    /** The instance of PagePanel embedded in this Notebook.
     * @see cw.notebook.PagePanel
     */
    private PagePanel pagePanel;

    /** The instance of TabPanel embedded in this Notebook.
     * @see cw.notebook.TabPanel
     */
    private TabPanel tabPanel;

    private PopupMenu popUp=new PopupMenu("Navigation and Help:");
    private Menu popup2=new Menu("Plugin Groups");

    private Vector compsVect,tabsVect, chkMnuVect=new Vector(10);
    //private Vector compsVect,tabsVect;
    private ActionListener actionListener;
    // private MouseAdapter mAdapt;
    private String actionCommand;
    private static final Font f=new Font("Dialog",Font.PLAIN,12);

    /** Creates a NoteBook with <b>compsVect</b> components, linked to <b>tabsVect</b> tabs and  <b>localPage</b> presented to th user (i.e., at the top of the stack).
     * @param localPage The index of the page intially displayed to the user.
     * @param compsVect The collection (a Vector) of AWT components making up the "page stack" in the notebook.
     * @param tabsVect The collection (a Vector) of Tab components making up the top tab row in the notebook.
     */
    public NoteBook(int localP, Vector compsV, Vector tabsV) {
        tabsVect=tabsV;
        compsVect=compsV;
        localPage=localP;
        String[] tabs=new String[tabsVect.size()];
        tabsVect.copyInto(tabs);
        Component[] comps=new Component[compsVect.size()];
        compsVect.copyInto(comps);
        popUp.setFont(f);
        build(localPage,comps,tabs);
        enableEvents(AWTEvent.ACTION_EVENT_MASK);
    }

    /** Registers an ActionListener with this NoteBook. 
     * 
     * @param listener An object that implements ActionListener interface.
     */
    public void addActionListener(ActionListener listener){
        actionListener=AWTEventMulticaster.add(actionListener, listener);
        enableEvents(AWTEvent.ACTION_EVENT_MASK);
    }

    /** Deregisters an ActionListener with this NoteBook. 
     * 
     * @param listener An object that implements ActionListener interface. 
     */
    public void removeActionListener(ActionListener listener){
        actionListener=AWTEventMulticaster.remove(actionListener, listener);
    }

    /** Assigns an ActionCommand string to this NoteBook. 
     * 
     * @param actionCommand The ActionCommand String.
     */
    public void setActionCommand(String actionCommand){
        this.actionCommand=actionCommand;
    }

    /** Gets the ActionCommand string from this NoteBook.
     * 
     * @return ActionCommand string.
     */
    public String getActionCommand(){
        return actionCommand;
    }

    /** Sends an ActionEvent <b>e</b> to registered ActionListener objects.
     * 
     * @param e The ActionEvent to be sent.
     */
    public void processEvent(ActionEvent e){
        if (actionListener != null){
            actionListener.actionPerformed(e);
        }
        super.processEvent(e);
    }

    private void build(int localPage, Component[] comps, String[] tabs){
        //System.out.println("tabs: "+tabsVect.size()+ "; comps: "+compsVect.size());
        if (comps==null | tabs==null){
            System.exit(0);
        }
        if (tabPanel != null) tabPanel=null;
        NBButton nbb=new NBButton(this);
        nbb.setColor(NBButton.FOREGROUND,new Color(144,144,144));
        tabPanel=new TabPanel(tabs,localPage,0);
        tabPanel.setBackground(new Color(172,170,173));
        setTabsColor(Tab.BACKGROUND,new Color(189,188,187));
        setTabsColor(Tab.FOCUSED_BACKGROUND,new Color(189,188,187));
        setTabsColor(Tab.FOCUSED_FOREGROUND,new Color(0,0,0));
        setTabsColor(Tab.ACTIVE_BACKGROUND,new Color(221,221,221));
        setTabsColor(Tab.ACTIVE_FOREGROUND, new Color(0,0,0));
        tabPanel.setArrowsColor(Tab.ACTIVE_BACKGROUND, new Color(144,144,144));
        // the following does nothing at this moment since we don't set the debug flag at initialization time
        if (debug) tabPanel.setDebug(true); 
        if (pagePanel !=null ) pagePanel=null;
        pagePanel=new PagePanel(localPage,comps,tabs);
        tabPanel.setSize(new Dimension(pagePanel.getPreferredSize().width,tabPanel.getPreferredSize().height));
        // the popup menu
        for (int i=0; i<tabs.length; i++){
            CheckboxMenuItem chkMnuItm=new CheckboxMenuItem(tabs[i]);
            //chkMnuItm.setActionCommand("tab_"+tabs[i]);
            chkMnuItm.setFont(f);
            chkMnuItm.addItemListener(this);
            //chkMnuItm.addActionListener(tabPanel);
            if (i==localPage) chkMnuItm.setState(true);
            chkMnuVect.addElement(chkMnuItm);
            popup2.add(chkMnuItm);
        }
        popUp.add(popup2);
        popUp.addSeparator();
        MenuItem nextComp=new MenuItem("Next");
        nextComp.setFont(f);
        nextComp.setActionCommand("popup_next");
        //nextComp.addActionListener(this);
        nextComp.addActionListener(tabPanel);
        nextComp.addActionListener(pagePanel);
        nextComp.addActionListener(nbb);
        MenuItem prevComp=new MenuItem("Previous");
        prevComp.setFont(f);
        prevComp.setActionCommand("popup_prev");
        //prevComp.addActionListener(this);
        prevComp.addActionListener(tabPanel);
        prevComp.addActionListener(pagePanel);
        prevComp.addActionListener(nbb);
        MenuItem lastComp=new MenuItem("Last");
        lastComp.setFont(f);
        lastComp.setActionCommand("popup_last");
        //lastComp.addActionListener(this);
        lastComp.addActionListener(tabPanel);
        lastComp.addActionListener(pagePanel);
        lastComp.addActionListener(nbb);
        MenuItem firstComp=new MenuItem("First");
        firstComp.setFont(f);
        firstComp.setActionCommand("popup_first");
        //firstComp.addActionListener(this);
        firstComp.addActionListener(tabPanel);
        firstComp.addActionListener(pagePanel);
        firstComp.addActionListener(nbb);
        MenuItem versionMnu=new MenuItem("About");
        versionMnu.setFont(f);
        versionMnu.setActionCommand("nb_about");
        versionMnu.addActionListener(this);
        //versionMnu.addActionListener(this);
        //versionMnu.addActionListener(this);
        MenuItem helpMnu=new MenuItem("Help");
        helpMnu.setFont(f);
        helpMnu.setActionCommand("nb_help");
        helpMnu.addActionListener(this);
        popUp.add(firstComp);
        popUp.add(prevComp);
        popUp.add(nextComp);
        popUp.add(lastComp);
        popUp.addSeparator();
        popUp.add(helpMnu);
        popUp.add(versionMnu);
        add(popUp);
        // register action listeners
        //tabPanel.addActionListener(this);
        //addActionListener(tabPanel);
        //addActionListener(pagePanel);
        Panel topPanel=new Panel(new BorderLayout());
        setLayout(new BorderLayout());
        setBackground(new Color(189,188,187));
        pagePanel.setBackground(new Color(221,221,221));
        topPanel.add(tabPanel,"Center");
        topPanel.add(nbb,"East");
        add(topPanel,"North");
        add(pagePanel,"Center");
        // conveys events from the popup menu
        //addActionListener(tabPanel);
        tabPanel.addActionListener(pagePanel);
        tabPanel.addActionListener(nbb);
        super.doLayout();
        super.validate();
        super.setVisible(true);
    }
	 
    /** Appends a component <b>comp</b> with the name <b>name</b> to this NoteBook instance.
     * @param comp The AWT Component to be added to the NoteBook.
     * @param name The name under which the added component is to be accessed (it will be shown on the corresponding tab).
     */
    public void addPage(Component comp, String name){
        compsVect.addElement(comp);
        tabsVect.addElement(name);
        reBuild();
    }

    /** Inserts a component <b>comp</b> with the name <b>name</b> at the specified position <b>pos</b>.
     * If indicated position is not a valid one (i.e., a negative number or a positive number larger than the size of components vector, then the component is appended at the end of the page stack (and its correspondent tab, inserted at the end of tab row).
     * @param comp The AWT Component to be added to the NoteBook.
     * @param name The identifier of the newlyadded component (it will be shown on the corresponding tab).
     * @param pos The position at which the component is to be inserted. Valid values are zero or positive and no bigger than the current number of components ("pages").
     */
    public void insertPage(Component comp, String name, int pos){
        if ((pos>(compsVect.size()-1))|(pos<0)){
            compsVect.addElement(comp);
            tabsVect.addElement(name);
        } else {
            compsVect.insertElementAt(comp,pos);
            tabsVect.insertElementAt(name,pos);
        }
        reBuild();
    }

    /** Removes the component ("page") <b>comp</b> specified by <b>name</b>.
     * @param comp The component to be removed.
     * @param name The identifier of the component to be removed.
     */
    public void removePage(Component comp, String name){
        boolean pageRemoved,tabRemoved;
        pageRemoved=compsVect.removeElement(comp);
        tabRemoved=tabsVect.removeElement(name);
        reBuild();
    }

    public void setPages(int localP, Vector compsV, Vector tabsV) {
        compsVect.removeAllElements();
        tabsVect.removeAllElements();
        tabsVect=tabsV;
        compsVect=compsV;
        localPage=localP;
        reBuild();
    }

    private void reBuild(){
        String[] tabs=new String[tabsVect.size()];
        tabsVect.copyInto(tabs);
        Component[] comps=new Component[compsVect.size()];
        compsVect.copyInto(comps);
        chkMnuVect.removeAllElements();
        remove(tabPanel);
        remove(pagePanel);
        popUp.removeAll();
        System.gc();
        build(localPage, comps, tabs);
    }

    public void actionPerformed(ActionEvent aev){
        String cmd=aev.getActionCommand();
        //System.out.println("NoteBook received command: "+cmd);
        processEvent(new ActionEvent(this,ActionEvent.ACTION_PERFORMED,(cmd)));
    }


    void setActivePopupCheckMenuItem(){
        for (int i=0;i<chkMnuVect.size();i++){
            CheckboxMenuItem chkMnu=(CheckboxMenuItem)chkMnuVect.elementAt(i);
            //System.out.println("NoteBook checkMenuItem: "+chkMnu.getLabel());
            chkMnu.setState(pagePanel.getActivePageName().equals(chkMnu.getLabel()));
        }
    }

    public void itemStateChanged(ItemEvent iev){
        CheckboxMenuItem chkMnuItm=(CheckboxMenuItem)iev.getItemSelectable();
        String selection=chkMnuItm.getLabel();
        //System.out.println(selection);
        tabPanel.activateTabCommand("tab_"+selection);
        tabPanel.layoutPanel();
        tabPanel.setLocalTab();
    }

    public Dimension getMinimumSize(){
        //if (debug) System.out.println("NoteBook.getMinimumSize() called");
        return super.getMinimumSize();
    }

    public Dimension getPreferredSize(){
        //if (debug) System.out.println("NoteBook.getPreferredSize() called");
        return super.getPreferredSize();
    }

    /** Sets one of the eight colors (specified by <b>colorIndex</b>) of a tab to the specified <b>color</b>. Affects tab at position <b>tabIndex</b>.
     * @param tabIndex The index of the tab.
     * @param colorIndex The index of the color in tab color palette.
     * @param color The specified color.
     * @see cw.notebook.Tab
     */
    public void setTabColor(int tabIndex, int colorIndex, Color color){
        tabPanel.setTabColor(tabIndex, colorIndex, color);
    }

    /** Changes the color specified by <b>colorIndex</b> to the specified <b>color</b>, for all tabs.
     * 
     * @param colorIndex Specifies the color index in the tab color palette
     * @param color The new color.
     * @see cw.notebook.Tab
     */
    public void setTabsColor(int colorIndex, Color color){
        tabPanel.setTabsColor(colorIndex, color);
    }

    /** Changes the tab color palette for a specified tab.
     * 
     * @param tabIndex The position of the tab for which colors will be set (changed).
     * @param colors The color array corresponding to the new tab color palette.
     * @see cw.notebook.Tab
     */
    public void setTabColors(int tabIndex, Color[] colors){
        tabPanel.setTabColors(tabIndex, colors);
    }

    /** Changes the tab color palette for all the tabs in the notebook.
     * 
     * @param color The color array corresponding to the new tab color palette.
     * @see cw.notebook.Tab
     */
    public void setTabsColors(Color[] colors){
        tabPanel.setTabsColors(colors);
    }

    /** Enables output of debugging messages to the console. */
    public void setDebug(boolean dbg){
        debug=dbg;
        tabPanel.setDebug(true);
        pagePanel.setDebug(true);
    }

    public PopupMenu getPopUpMenu() {
        return popUp;
    }

    public TabPanel getTabPanel() {
        return tabPanel;
    }
} // NoteBook
