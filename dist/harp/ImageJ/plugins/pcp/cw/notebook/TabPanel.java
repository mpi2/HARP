package cw.notebook;

import java.awt.*;
import java.awt.event.*;
import java.util.*;

/**
 * TabPanel.java
 *
 *
 * Changes as of Sunday 02 September 2001
 * 
 * - modified (quick'n dirty) the actionPerformed() code to conform to the new action command semantics (see "Changes" section in NoteBook.java for details)
 *
 * Created: Tue Oct 24 00:15:06 2000
 *
 * @author Cezar M. Tigaret
 * @version 0.4b
 */
public class TabPanel extends Container
    implements ActionListener {
    private boolean debug=false;
    private int leftTab, localTab, rightTab;
    private String[] tabs;
    private String actionCommand;
    private Image hidden;
    private Color tabPanelBackground;

    /** Holds all tabs except the left and right arrow (panel scrolling) tabs). */
    private Vector tabsVector=new Vector(10,10);

    private ActionListener actionListener;

    private static final Tab tabLeftArrow=new Tab(Tab.STYLE_LEFTARROW),
        tabRightArrow=new Tab(Tab.STYLE_RIGHTARROW);


	 
    /** Creates a TabPanel using an array of tab names and sets up the first tab from the left to be local, by default.
     * 
     *  @param tabs The string array holding the names for each tab.
     *                        Each string gives the tab's label and its internal 
     *                        name. The order of the strings in the array gives the
     *                        order in which tabs will appear in the panel. The array should have the same size as the array of components in PagePanel; this is typically taken care of by NoteBook class.
     * @see cw.notebook.NoteBook
     * @see cw.notebook.PagePanel
     *
     */
    public TabPanel(String[] tabs){
        this(tabs,0,0);
    }
	 
    /** Creates a TabPanel using an array of tab names and sets up the local tab with the index given by <pre>localTab</pre>.
     * 
     *  @param tabs The string array holding the names for each tab.
     *                        Each string gives the tab's label and its internal 
     *                        name. The order of the strings in the array gives the
     *                        order in which tabs will appear in the panel. The array should have the same size as the array of components in PagePanel; this is typically taken care of by NoteBook class.
     *
     *  @param localTab The index of the local (active) tab. 
     * @see cw.notebook.NoteBook
     * @see cw.notebook.PagePanel
     */
    public TabPanel(String[] tabs, int localTab){
        this(tabs,localTab,localTab);
    }

    /** Creates a TabPanel using an array of tab names and sets up
     *  the local tab and the leftmost tab to be shown.
     * 
     *  @param tabs  The string array holding the names for each tab.
     *                        Each string gives the tab's label and its internal 
     *                        name. The order of the strings in the array gives the
     *                        order in which tabs will appear in the panel. The array should have the same size as the array of components in PagePanel; this is typically taken care of by NoteBook class.
     * 
     *  @param localTab   The index of the local (active) tab.
     * 
     *  @param leftTab    The index of the tab to be shown in the leftmost position. All tabs before this one are accessible using the arrow tabs in the tab panel.
     * @see cw.notebook.NoteBook
     * @see cw.notebook.PagePanel
     */
    public TabPanel(String[] tabs, int localTab, int leftTab) {
        this.tabs=tabs;  
        this.localTab=localTab;
        this.leftTab=leftTab;
        registerTabs();
        setLocalTab();
        layoutPanel();
        setVisible(true);
        tabLeftArrow.addActionListener(this);
        tabRightArrow.addActionListener(this);
        // rearranges panel layout when its parent container has beed resized
        addComponentListener(new ComponentAdapter(){
                public void componentResized(ComponentEvent e){
                    setSize(getPreferredSize());
                    layoutPanel();
                }
            });
        enableEvents(AWTEvent.ACTION_EVENT_MASK);
    }


    /** Creates the tabs and sets the local style for the given tab's position.
     * 
     * Initializes the tabs and calculates the bounds (physical position) of tabs within the panel.
     * 
     */
    private void registerTabs(){
        for (int i=0; i<tabs.length; i++) {
            Tab tab=new Tab(tabs[i]);
            //tab.setActionCommand("tab_"+tabs[i]);
            tab.addActionListener(this);
            if (i>(tabsVector.size()-1)){
                tabsVector.addElement(tab);
            } else {
                tabsVector.setElementAt(tab,i);
            }
        }
        //System.out.println(tabLeftArrow.getTabStyle());
        //System.out.println(tabRightArrow.getTabStyle());
    }

    /** Lays out the tabs in the panel, including the arrow tabs, if needed. */
    void layoutPanel(){
        removeAll();
        if (leftTab<=0) leftTab=0;
        if (leftTab>(tabsVector.size()-1)) leftTab=tabsVector.size()-1;
        setTabsBounds();
        if (needsLeftArrow()) add("tabLeftArrow",tabLeftArrow); // sits on top of everything
        if (needsRightArrow()) add("tabRightArrow",tabRightArrow);
        if (localTab>=leftTab) {
            add(tabs[localTab],(Tab)tabsVector.elementAt(localTab));
            for (int i=leftTab; i<localTab; i++) {
                add(tabs[i],(Tab)tabsVector.elementAt(i));
            }
            for (int i=(localTab+1); i<tabsVector.size(); i++) {
                add(tabs[i],(Tab)tabsVector.elementAt(i));
            }
        } else {
            for (int i=leftTab; i<tabs.length; i++) {
                add(tabs[i],(Tab)tabsVector.elementAt(i));
            }
        }
        super.setSize(getPreferredSize());
        super.repaint(); // repaint the widget tree
        validate();
    }

    /** Ensures that localTab value is never out of bounds an that the tab painting reflects it is local */
    void setLocalTab(){
        if (localTab<0) localTab=0;
        if (localTab>(tabsVector.size()-1)) localTab=tabsVector.size()-1;
        for (int i=0;i<tabsVector.size();i++){
            Tab t=(Tab)tabsVector.elementAt(i);
            if (i==localTab){
                t.setLocal();
            } else {
                t.setDefaultStyle();
            }
            tabsVector.setElementAt(t,i);
        }
    }

    private boolean needsLeftArrow(){
        boolean needs=false;
        if (leftTab>0) needs=true; // don't show left arrow if leftmost tab active
        return needs;
    }

    private boolean needsRightArrow(){
        boolean needs=false;
        int w=0;
        //if (leftTab<=0) leftTab=0;
        w+=getTabsWidth(leftTab);
        if (needsLeftArrow()) w+=tabLeftArrow.getWidth()-tabLeftArrow.getHeight()*Math.tan(30*Math.PI/180);
        if (w>super.getSize().width) needs=true;
        return needs;
    }

    private void setTabsBounds(){
        int xOffset=0;
        if (needsLeftArrow() && tabLeftArrow!=null) {
            // LEFT ARROW goes to x=0
            tabLeftArrow.setBounds(0,2,tabLeftArrow.getWidth(),tabLeftArrow.getHeight());
            xOffset+=tabLeftArrow.getWidth()-tabLeftArrow.getHeight()*Math.tan(30*Math.PI/180);
        }
        if (needsRightArrow() && tabRightArrow!=null) tabRightArrow.setBounds(getWidth()-tabRightArrow.getWidth(),2,tabRightArrow.getWidth(),tabRightArrow.getHeight());
        if (leftTab>0){
            Tab t=(Tab)tabsVector.elementAt(leftTab);
            t.setBounds(xOffset,2,t.getWidth(),t.getHeight());
            tabsVector.setElementAt(t,leftTab);
            xOffset+=t.getWidth()-t.getHeight()*Math.tan(30*Math.PI/180);
            int negOffset=0;
            for (int i=(leftTab-1);i>-1;i--){
                t=(Tab)tabsVector.elementAt(i);
                negOffset-=t.getWidth();
                t.setBounds(negOffset,2,t.getWidth(),t.getHeight());
                tabsVector.setElementAt(t,i);
            }
            for (int i=(leftTab+1);i<tabsVector.size();i++){
                t=(Tab)tabsVector.elementAt(i);
                t.setBounds(xOffset,2,t.getWidth(),t.getHeight());
                xOffset+=t.getWidth()-t.getHeight()*Math.tan(30*Math.PI/180);
                tabsVector.setElementAt(t,i);
            }
				
        } else {
            for (Enumeration e=tabsVector.elements();e.hasMoreElements();){
                Tab t=(Tab)e.nextElement();
                int ndx=tabsVector.indexOf(t);
                t.setBounds(xOffset,2,t.getWidth(),t.getHeight());
                tabsVector.setElementAt(t,ndx);
                xOffset+=t.getWidth()-t.getHeight()*Math.tan(30*Math.PI/180);
            }
        }
    }


    /** Insert a tab with the specified name, at the specified position (index) */
    public void addTab(String name, int pos){
        String[] newTabs=new String[tabs.length+1];
        // if specified index is greated than the length of the array, append the tab to the end
        if (pos>tabsVector.size()) pos=tabsVector.size();
        if (pos<0) pos=0;
        for (int i=0; i<pos; i++) newTabs[i]=tabs[i];
        newTabs[pos]=name;
        for (int i=pos+1; i<newTabs.length; i++) newTabs[i]=tabs[i-1];
        tabs=newTabs;
        registerTabs();
        layoutPanel();
    }

    /** Remove the tab from the specified position (index) */
    public void removeTab(int pos){
        if (pos<0) pos=0;
        if (pos>(tabs.length-1)) pos=tabs.length-1;
        String[] newTabs=new String[tabs.length-1];
        for (int i=0; i<pos; i++) {
            newTabs[i]=tabs[i];
        }
        for (int i=pos+1; i<tabs.length; i++) {
            newTabs[i-1]=tabs[i];
        }
        tabs=newTabs;
        registerTabs();
        layoutPanel();
    }

    /** Register an ActionListener with this tab panel.
     * @param listener An ActionListener object.
     */
    public void addActionListener(ActionListener listener){
        actionListener=AWTEventMulticaster.add(actionListener, listener);
        enableEvents(AWTEvent.ACTION_EVENT_MASK);
    }
    /** Deregisters the ActionListener from this tab panel.
     * @param listener An ActinListener object.
     */
    public void removeActionListener(ActionListener listener){
        actionListener=AWTEventMulticaster.remove(actionListener, listener);
    }

    /** Assigns an ActionCommand string to this tab panel.
     * @param actionCommand The ActionCommand string.
     */
    public void setActionCommand(String actionCommand){
        this.actionCommand=actionCommand;
    }

    /** Gets the ActionCommand string assigned to this tab panel.
     * @return The ActionCommand string.
     */
    public String getActionCommand(){
        return actionCommand;
    }

    /** Casts an ActionEvent to registered ActionListener objects.
     * @param e The ActionEvent
     */
    public void processEvent(ActionEvent e){
        if (actionListener!=null) {
            actionListener.actionPerformed(e);
        }
        super.processEvent(e);
    }

    /** Makes the next tab local and active; 
     * layoutPanel() _MUST_ be called after this method in order to propagate the changes to the GUI 
     */
    void stepNext(boolean flip){
        localTab++;
        if (flip) {
            if (localTab>(tabsVector.size()-1)) localTab=0; //circular flip
        }
        setLocalTab();
        if(localTab<leftTab) leftTab=localTab;
        leftTab=localTab;
    }

    /** Makes the previous tab local and active; 
     * layoutPanel() _MUST_ be called after this method in order to propagate the changes to the GUI
     */
    void stepPrev(boolean flip) {
        localTab--;
        if (flip) {
            if (localTab<0) localTab=tabsVector.size()-1; //circular flip
        }
        setLocalTab();
        if(localTab<leftTab) leftTab=localTab;
        leftTab=localTab;
    }

    /** Makes the first tab local and active; 
     * layoutPanel() _MUST_ be called after this method in order to propagate the changes to the GUI 
     */
    void jumpFirst() {
        localTab=0;
        setLocalTab();
        if(localTab<leftTab) leftTab=localTab;
        leftTab=localTab;
    }

    /** Makes the last tab local and active; 
     * layoutPanel() _MUST_ be called after this method in order to propagate the changes to the GUI 
     */
    void jumpLast() {
        localTab=tabsVector.size()-1;
        setLocalTab();
        if(localTab<leftTab) leftTab=localTab;
        leftTab=localTab;
    }

    /** Makes the tab with the specified index, local and active; 
     * layoutPanel() _MUST_ be called after this method in order to propagate the changes to the GUI 
     */
    void jumpSpecified(int t) {
        localTab=t;
        setLocalTab();
        // if localTab is beyond the left end of the tabs row:
        if(localTab<leftTab) leftTab=localTab;
        // if localTab is beyond the right end of the tabs row:
        if (getLocalRightEnd()>super.getSize().width){
            leftTab=localTab;
        }
    }

    /** Scrolls the tabs one to the right - normally triggered by the LEFT_ARROW tab; 
     * does _NOT_ change the localTab value;
     * issues a tab command to trigger page flipping if neccessary; 
     * layoutPanel() _MUST_ be called after this method in order to propagate the changes to the GUI 
     */
    void pushRight() {
        leftTab--;
        if (leftTab<0) leftTab=0;
        // localTab is beyond the right end of the tabs row
        if (getLocalRightEnd()>super.getSize().width){
            //System.out.println("TabPanel reached right end");
            localTab--;
            setLocalTab();
            processEvent(new ActionEvent(this,ActionEvent.ACTION_PERFORMED,"tabpnl_"+tabs[localTab]));
        }
    }

    /** Scrolls the tabs one to the left - normally triggered by the RIGHT_ARROW tab; 
     * does _NOT_ change the localTab value;
     * issues a tab command to trigger page flipping if neccessary; 
     * layoutPanel() _MUST_ be called after this method in order to propagate the changes to the GUI 
     */
    void pushLeft() {
            leftTab++;
            if (leftTab>(tabs.length-1)) leftTab=tabs.length-1;
			if (localTab<leftTab){
                //System.out.println("TabPanel reached left end");
                localTab=leftTab;
                setLocalTab();
                processEvent(new ActionEvent(this,ActionEvent.ACTION_PERFORMED,"tabpnl_"+tabs[localTab]));
			}
    }

    public void activateTabCommand(String cmd) {
        //System.out.println("TabPanel activating: "+cmd);
        for (int i=0; i<tabs.length; i++) {
            if (cmd.equals("tab_"+tabs[i])) {
                localTab=i;
                setLocalTab();
                cmd=cmd.substring(4);
                processEvent(new ActionEvent(this,ActionEvent.ACTION_PERFORMED,"tabpnl_"+cmd));
                continue;
            }
        }
    }

    public void actionPerformed(ActionEvent e){
        String cmd=e.getActionCommand();
        //System.out.println("TabPanel received command: "+cmd);
        // here we process commands received from page panel (i.e. issued when a popup menuitem is clicked)
        if (cmd.equals("popup_first")) {
            jumpFirst();
        }
        if (cmd.equals("popup_next")) {
            stepNext(true);
        }
        if (cmd.equals("popup_prev")) {
            stepPrev(true);
        } 
        if (cmd.equals("popup_last")) {
            jumpLast();
        } 
        // all action commands from tabs are prefixed with "tab_"
        if (cmd.startsWith("tab_")) {
            if (cmd=="tab_scroll_left") {
                pushRight();
            } else if (cmd=="tab_scroll_right") {
                pushLeft();
            } else {
                activateTabCommand(cmd);
            }
        }
		layoutPanel();
    }


    /** Gets the location of the localTab's right end. */
    private int getLocalRightEnd(){
        int xOffset=0;
        // when localTab<leftTab this means that we're activating a tab that's 
        // actually beyond the left end of the tabs row
        if (!(localTab<leftTab)){
            Tab t=(Tab)tabsVector.elementAt(localTab);
            for (int i=leftTab;i<localTab;i++){
                if (needsLeftArrow()) xOffset+=tabLeftArrow.getWidth()-tabLeftArrow.getHeight()*Math.tan(30*Math.PI/180);
                Tab tt=(Tab)tabsVector.elementAt(i);
                xOffset+=tt.getWidth()-tt.getHeight()*Math.tan(30*Math.PI/180);
            }
            xOffset+=t.getWidth();
        } else {
            for (int i=leftTab-1;i>localTab-1;i--){
                Tab t=(Tab)tabsVector.elementAt(i);
                xOffset-=t.getWidth();
					 
            }
        }
        return xOffset;
    }

    // ********* dimensions

    public Dimension getMinimumSize(){
        return getPreferredSize();
    }

    public Dimension getMaximumSize(){
        return new Dimension(getTabsWidth(0),getTabsHeight());
    }

    public Dimension getPreferredSize(){
        return new Dimension(super.getSize().width,getTabsHeight()+4);
    }

    public void setSize(Dimension dim){
        super.setSize(dim);
    }

    /** Gets the current width of this tab panel.
     * @return The current width of the tab panel.
     */
	public int getWidth(){
        return getPreferredSize().width;
	}

    /** Gets the current height of this tab panel.
     * @return The height of the tab panel.
     */
	public int getHeight(){
        return getPreferredSize().height;
	}

    private int getTabsWidth(int left){
        int w=0;
        if (tabsVector!=null){
            for (int i=left;i<tabsVector.size();i++){
                Tab t=(Tab)tabsVector.elementAt(i);
                if (i==(tabsVector.size()-1)){
                    w+=t.getWidth();
                } else {
                    w+=t.getWidth()-t.getHeight()*Math.tan(30*Math.PI/180);
                }
            }
        } 
        return w;
    }

    private int getTabsHeight(){
        int h=0;
        if (tabsVector!=null){
            for (Enumeration e=tabsVector.elements();e.hasMoreElements();){
                Tab t=(Tab)e.nextElement();
                h=Math.max(h,t.getHeight());
            }
            if (tabLeftArrow!=null) h=Math.max(h,tabLeftArrow.getHeight());
            if (tabRightArrow!=null) h=Math.max(h,tabRightArrow.getHeight());
        }
        return h;
    }

    // ********** debugging and peeking

    /** Enables output of messages to the system console. */

    public void setDebug(boolean dbg){
        debug=dbg;
    }

    /** Gets the Vector of registered Tab objects.
     * @see cw.notebook.Tab
     * @return The Vector of Tab objects.
     */
    public Vector getTabs(){
        return tabsVector;
    }

    // ********  Graphic rendering stuff

    /** Sets the background color of the tab panel.
     * @param background The new background color of the panel.
     */
    public void setBackground(Color background){
        this.tabPanelBackground=background;
        super.repaint();
    }

    /** Replaces the color palette for all tabs.
     * @param colors The new Tab color palette
     * @see cw.notebook.Tab
     */
    public void setTabsColors(Color[] colors){
        for (Enumeration e=tabsVector.elements(); e.hasMoreElements(); ) {
            Tab tab=(Tab)e.nextElement();
            tab.setColors(colors);
		}
		if (tabLeftArrow!=null) tabLeftArrow.setColors(colors);
		if (tabRightArrow!=null) tabRightArrow.setColors(colors);
        super.repaint();
    }

    /** Replaces a color in the color palette for all tabs.
     * @param colorIndex The index of the new color in the Tab color palette.
     * @param color The new color.
     * @see cw.notebook.Tab
     */
    public void setTabsColor(int colorIndex, Color color){
        for (Enumeration e=tabsVector.elements(); e.hasMoreElements(); ) {
            Tab tab=(Tab)e.nextElement();
            tab.setColor(colorIndex,color);
        }
		if (tabLeftArrow!=null) tabLeftArrow.setColor(colorIndex,color);
		if (tabRightArrow!=null) tabRightArrow.setColor(colorIndex,color);
        super.repaint();
    }

    /** Replaces the color palette for a specific tab.
     * @param tabIndex The index of the specified tab.
     * @param colors The new color palette.
     * @see cw.notebook.Tab
     */
    public void setTabColors(int tabIndex, Color[] colors){
        if (tabIndex<tabsVector.size()) {
            Tab tab=(Tab)tabsVector.elementAt(tabIndex);
            tab.setColors(colors);
        }
		super.repaint();
    }

    /** Replaces the color palette for the left arrow tab.
     * @param colors The new color palette.
     * @see cw.notebook.Tab
     */
    public void setLeftArrowColors(Color[] colors){
        if (tabLeftArrow!=null) tabLeftArrow.setColors(colors);
    }

    /** Replaces a specific color in the color palette for the left arrow tab.
     * @param colorIndex The index of the new color in the color palette.
     * @param color The new color
     * @see cw.notebook.Tab
     */
    public void setLeftArrowColor(int colorIndex, Color color){
        if (tabLeftArrow!=null) tabLeftArrow.setColor(colorIndex,color);
    }

    /** Replaces the color palette for the right arrow tab.
     * @param colors The new color palette.
     * @see cw.notebook.Tab
     */
    public void setRightArrowColors(Color[] colors){
        if (tabRightArrow!=null) tabRightArrow.setColors(colors);
    }

    /** Replaces a specific color in the color palette for the right arrow tab.
     * @param colorIndex The index of the new color in the color palette.
     * @param color The new color
     * @see cw.notebook.Tab
     */
    public void setRightArrowColor(int colorIndex, Color color){
        if (tabRightArrow!=null) tabRightArrow.setColor(colorIndex, color);
    }

    /** Replaces the color palette for the arrow tabs.
     * @param colors The new color palette.
     * @see cw.notebook.Tab
     */
    public void setArrowsColors(Color[] colors){
        if (tabLeftArrow!=null) tabLeftArrow.setColors(colors);
        if (tabRightArrow!=null) tabRightArrow.setColors(colors);
    }

    /** Replaces a specific color in the color palette for the arrow tabs.
     * @param colorIndex The index of the new color in the color palette.
     * @param color The new color
     * @see cw.notebook.Tab
     */
    public void setArrowsColor(int colorIndex, Color color){
        if (tabLeftArrow!=null) tabLeftArrow.setColor(colorIndex,color);
        if (tabRightArrow!=null) tabRightArrow.setColor(colorIndex, color);
    }

    /** Replaces a color in the color palette for a specific tab.
     * @param tabIndex The index of the specific tab.
     * @param colorIndex The index opf the new color in the palette. 
     * @param color The new color.
     * @see cw.notebook.Tab
     */
    public void setTabColor(int tabIndex, int colorIndex, Color color){
        if (tabIndex<tabsVector.size()) {
            Tab tab=(Tab)tabsVector.elementAt(tabIndex);
            tab.setColor(colorIndex, color);
            super.repaint();
        }
    }

    public void paint(Graphics g){
        if (tabPanelBackground!=null) {
            g.setColor(tabPanelBackground);
            g.fillRect(0,0,super.getSize().width,super.getSize().height);
        }
        super.paint(g);
    }

    public void update(Graphics g){
        if (hidden==null) hidden=createImage(super.getSize().width,super.getSize().height);
        Graphics hg=hidden.getGraphics();
        hg.setClip(0,0,super.getSize().width,super.getSize().height);
        super.paint(hg);
        g.drawImage(hidden,0,0,null);
        hg.dispose();
        paint(g);
    }

    public void update(){
        paint(this.getGraphics());
    }

    public void invalidate(){
        super.invalidate();
        hidden=null;
    }

} // TabPanel

