//todo: try to implement it as a daemon thread and make it static so there's only one instance of this thread per tab panel !?

package cw.notebook;

import java.awt.event.*;
import cw.notebook.Tab;

/**
 * TabScroller.java
 *
 * A quick'n dirty code to provide a mechanism for tabs scrolling in a TabPanel,
 * by repeated firing of action events from the arrow-style tab that calls it.
 *
 * Created: Thu Aug 23 21:44:23 2001
 *
 * @author Cezar M. Tigaret <c.tigaret@ucl.ac.uk>
 * @version 0.1
 */

public class TabScroller implements Runnable {

    protected Tab tab;
    protected Thread t=null;

    public TabScroller (Tab tab) {
        this.tab=tab;
    }
    
    public void start() {
        //System.out.println("Starting");
        t=new Thread(this);
        // set minimum priority...
        t.setPriority(Math.min(t.getPriority()-2, Thread.MIN_PRIORITY));
        t.start();
    }

    public void run(){
        while(tab.isShowing() && tab.isPressed()) {
            try {
                //System.out.println(tab.getStyleDescription());
                tab.doCommand();
                // still must yield for the other threads...
                Thread.yield();
                Thread.yield();
                Thread.yield();
                Thread.sleep(100);
            } catch(Exception e) {
                //System.out.println("Exception thrown");
                stop();
                e.printStackTrace();
            }
        }
        stop();
    }

    public void stop() {
        //System.out.println("Stopping");
        t.stop();
        t=null;
    }

    public boolean isAlive() {
        if (t==null) return false;
        return t.isAlive();
    }


}// TabScroller
