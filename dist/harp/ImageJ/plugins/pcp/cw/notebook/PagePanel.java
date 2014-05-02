//TODO code to add/insert/remove pages
package cw.notebook;

import cw.notebook.*;

import java.awt.*;
import java.awt.event.*;
import java.util.*;

// TODO clean up the messy code checking for activeComp validity in the constructor


/**
 * PagePanel.
 *
 * component based on CardLayout, holding a stack of AWT components.
 *
 *
 * Changes as of Sunday 02 September 2001
 * 
 * - modified the actionPerformed() code to repsect the new action command semantics (see Changes to the NoteBook.java)
 *
 * Created: Tue Oct 24 00:15:46 2000
 *
 * @author Cezar M. Tigaret
 * @version 0.4
 * 
 * @see cw.notebook.NoteBook
 */
public class PagePanel extends Container
    implements ActionListener {
	 
    private boolean debug=false;
    private int shown;
    private String[] names;
    private String shownPage;
    private Vector pageVect=new Vector(10,10);

    /**
     * Constructs a PagePanel with an array of components and their names.
     * 
     * @param activeComp The component ("page") that is first shown on top of the stack.
     * @param comps The component array that represent PagePanel "pages".
     * @param names An array of string identifiers for each component page in the PagePanel. It must have the same size as <pre>comps</pre>. Typically, this falls in the responsibility of the NoteBook class.
     */
    public PagePanel(int activeComp, Component[] comps, String[] names) {
        this.names=names;
        if (activeComp>comps.length){
            //System.out.println("Active page number out of range");
            System.exit(0);
        }
        if (comps.length!=names.length){
            //System.out.println("comps array and names array differ in size!");
            System.exit(0);
        }
        shown=activeComp;
        setLayout(new CardLayout());
        buildPages(comps);
        ((CardLayout)getLayout()).show(this,names[activeComp]);
    }

    private void buildPages(Component[] comps){
        for (int i=0; i<comps.length; i++) {
            comps[i].setSize(super.getSize());
            ScrollPane scrP=new ScrollPane();
            scrP.add(comps[i]);
            //add(comps[i],names[i]);
            add(scrP,names[i]);
            pageVect.addElement(names[i]);
        }
    }

    public void actionPerformed(ActionEvent aev){
        String cmd=aev.getActionCommand();
        //System.out.println("PagePanel received command: "+cmd);
        if (cmd=="popup_first") {
            ((CardLayout)getLayout()).first(this);
            shown=0;
            shownPage=names[shown];
        } else if ((cmd=="popup_prev")) {
            ((CardLayout)getLayout()).previous(this);
            shown--;
            if (shown<0) shown=names.length-1;;
            shownPage=names[shown];
        } else if ((cmd=="popup_next")) {
            ((CardLayout)getLayout()).next(this);
            shown++;
            if (shown>(names.length-1)) shown=0;
            shownPage=names[shown];
        } else if (cmd=="popup_last") {
            ((CardLayout)getLayout()).last(this);
            shown=names.length-1;
            shownPage=names[shown];
        } else if (cmd.startsWith("popup_")){
            cmd=cmd.substring(6);
            ((CardLayout)getLayout()).show(this,cmd);
            shown=pageVect.indexOf(cmd);
            shownPage=cmd;
        } else if (cmd.startsWith("tabpnl_")) {
            cmd=cmd.substring(7);
            ((CardLayout)getLayout()).show(this,cmd);
            shown=pageVect.indexOf(cmd);
            shownPage=cmd;
        }
    }

    /** Gets the identifier of the "page" currently at the top of the stack.
     * 
     * @return The identifier of the page at the top of the stack.
     */
    public String getActivePageName(){
        return shownPage;
    }
	 
    public Dimension getMinimumSize(){
        //if (debug) System.out.println("PagePanel.getMinimumSize() called");
        return super.getMinimumSize();
    }

    public Dimension getMaximumSize(){
        //if (debug) System.out.println("PagePanel.getMaximumSize() called");
        return super.getMaximumSize();
    }

    public Dimension getPreferredSize(){
        //if (debug) System.out.println("PagePanel.getPreferredSize() called");
        return super.getPreferredSize();
    }

    /** Enables output of debugging messages to the console.*/
    public void setDebug(boolean dbg){
        debug=dbg;
    }

} // PagePanel
