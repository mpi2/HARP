package cw.notebook;

import cw.notebook.PagePanel;
import cw.notebook.TabPanel;
import cw.notebook.NoteBook;

import java.awt.*;
import java.awt.event.*;
import java.util.*;

/**
 * NBButton.java
 *
 *
 * Created: Sat Sep  1 14:09:29 2001
 *
 * @author Cezar M. Tigaret
 * @version 0.1
 */


public class NBButton extends Component 
    implements ActionListener {

    /** The color palette: the background color for the "normal" tab. */
    public static final int  BACKGROUND=0;
    /** The color palette: the foreground color for the "normal" tab. */
    public static final int  FOREGROUND=1;
    /** The color palette: the background of the "active" tab. */
    public static final int  ACTIVE_BACKGROUND=2;
    /** The color palette: the foreground of the "active" tab. */
    public static final int  ACTIVE_FOREGROUND=3;
    /** The color palette: the background under the mouse cursor ("focused")*/
    public static final int  FOCUSED_BACKGROUND=4;
    /** The color palette: the foreground under the mouse cursor ("focused")*/
    public static final int  FOCUSED_FOREGROUND=5;
    /** The color palette: the color of the disabled */
    public static final int  UNAVAILABLE=6;
    /** The color palette: the color of the 3D effect highlight. */
    public static final int  HIGHLIGHT=7;
    /** The color palette: the color of the 3D effect shadow.*/
    public static final int  SHADOW=8;

    /** Default "normal" background color. */
    public Color back = SystemColor.menu;
    /** Default "normal" foreground color. */
    public Color fore = SystemColor.menuText;
    /** Default "active" background color.*/
    public Color backActive = SystemColor.activeCaption;
    /** Default "active" foreground color.*/
    public Color foreActive = SystemColor.activeCaptionText;
    /** Default "focused" background color.*/
    public Color backFocus = SystemColor.textHighlight;
    /** Default "focused" foreground color.*/
    public Color foreFocus = SystemColor.textHighlightText;
    /** Default "disabled" color. */
    public Color foreUnavailable = SystemColor.textInactiveText;
    /** Default 3D effect highlight. */
    public Color highlight3D = SystemColor.controlHighlight;
    /** Default 3D effect shadow.*/
    public Color shadow3D = SystemColor.controlShadow;

    private Color currentBack, currentFore, currentHighlight, currentShadow, tempBack, tempFore;

    private Polygon p;

    private Rectangle r;

    NoteBook nB;

    public NBButton (NoteBook nB) {
        this.nB=nB;
        compute();
        update();
        enableEvents(AWTEvent.MOUSE_EVENT_MASK);
    }

    public void compute() {
        currentBack=back;
        currentFore=fore;
        currentHighlight=highlight3D;
        currentShadow=shadow3D;
        tempFore=currentFore;
        tempBack=currentBack;
        r=new Rectangle(getMinimumSize());
        int[] xp={r.x+r.width/4,r.x+r.width*3/4,r.x+r.width/2};
        int[] yp={r.y+r.height/4,r.y+r.height/4,r.y+r.height*3/4};
        p=new Polygon(xp,yp,3);
    }
    
    public void paint(Graphics g) {
        // button's contour
        g.setColor(currentHighlight);
        g.drawLine(r.x+3,r.y,r.x+r.width,r.y);
        g.drawLine(r.x+3,r.y+1,r.x+r.width,r.y+1);
        g.drawLine(r.x,r.y+3,r.x,r.y+r.height);
        g.drawLine(r.x+1,r.y+3,r.x+1,r.y+r.height);
        g.drawLine(r.x,r.y+3,r.x+3,r.y);
        g.drawLine(r.x+1,r.y+4,r.x+4,r.y+1);
        g.setColor(currentFore);
        g.fillPolygon(p);
        int[] xp=p.xpoints;
        int[] yp=p.ypoints;
        g.setColor(currentHighlight);
        // triangle highlight
        g.drawLine(xp[0],yp[0],xp[1],yp[1]);
        g.drawLine(xp[0]-1,yp[0]-1,xp[1]+1,yp[1]-1);
        g.drawLine(xp[0]-1,yp[0]-1,xp[2],yp[2]+1);
        // baseline highilight
        g.drawLine(xp[0]+1,yp[2]+3,xp[1]-1,yp[2]+3);
        g.drawLine(xp[0]+1,yp[2]+3,xp[0]+1,yp[2]+5);
        g.setColor(currentShadow);
        // triangle shadow
        g.drawLine(xp[1],yp[1],xp[2],yp[2]);
        g.drawLine(xp[1],yp[1],xp[2],yp[2]+1);
        // baseline shadow
        g.drawLine(xp[1]-1,yp[2]+3,xp[1]-1,yp[2]+5);
        g.drawLine(xp[0]+1,yp[2]+5,xp[1]-1,yp[2]+5);
        // baseline core
        g.setColor(currentFore);
        g.drawLine(xp[0]+1,yp[2]+4,xp[1]-1,yp[2]+4);
    }

    public void update(){
        super.repaint();
    }

    /** Replaces a specific color in the color palette.
     * @param colorIndex The index of the new color in the color palette.
     * @param The new color.
     */
    public void setColor(int colorIndex, Color color){
        switch (colorIndex) {
        case BACKGROUND:
            back=color;
            break;
        case FOREGROUND:
            fore=color;
            break;
        case ACTIVE_BACKGROUND:
            backActive=color;
            break;
        case ACTIVE_FOREGROUND:
            foreActive=color;
            break;
        case FOCUSED_BACKGROUND:
            backFocus=color;
            break;
        case FOCUSED_FOREGROUND:
            foreFocus=color;
            break;
        case UNAVAILABLE:
            foreUnavailable=color;
            break;
        case HIGHLIGHT:
            highlight3D=color;
            break;
        case SHADOW:
            shadow3D=color;
            break;
        default:
            break;
        }
        compute();
        update();
    }

    public void processMouseEvent(MouseEvent e) {
        if (nB==null) return;
        switch (e.getID()) {
        case MouseEvent.MOUSE_PRESSED:
            nB.getPopUpMenu().show(this,e.getX(),e.getY());
            break;
        default:
            break;
        }
        super.processMouseEvent(e);
    }

    public Dimension getPreferredSize(){
        return getMinimumSize();
    }

    public Dimension getMinimumSize() {
        Dimension minDim=null;
        TabPanel tabPanel=nB.getTabPanel();
        if (tabPanel!=null) {
            int size=tabPanel.getPreferredSize().height-2;
            minDim=new Dimension(size,size);
        } else {
            minDim=new Dimension(20,20);
        }
        return minDim;
    }

    public void actionPerformed(ActionEvent e) {
        //String cmd=e.getActionCommand();
        //System.out.println("NBButton received command: "+cmd);
        nB.setActivePopupCheckMenuItem();
    }

}// NBButton
