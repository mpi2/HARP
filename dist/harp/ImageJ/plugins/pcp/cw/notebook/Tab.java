// todo: try to make the TabScroller thread a static member (once it's implemented as a daemon thread) so that's only one instance of this thread per TabPanel instance !?
package cw.notebook;

import cw.notebook.TabScroller;
import java.awt.*;
import java.awt.event.*;
/**
 * Tab.java
 *
 * A lightweight component.
 * 
 * The "transparent" background allows for adding several tab components to a panel such that they may be partially overlapped.
 *
 * Tabs are identified by their name, which appears as a label in the TabPanel, and also represent their default ActionCommand string. The ActionCommand string can, however, be set by calling setActionCommand(String) method.
 *
 * Changes as of Sunday 02 September 2001
 *
 * - The arrow-styled tabs call the TabScroller tab which, in conjunction with the doCommand() method provide a mechanism for tabs scrolling in the TabPanel. 
 *
 * - Added public int getTabStyle() to the Tab.java.
 * - Added public void doCommand() to fire action events from this tab by another object (i.e., a thread);
 * - Altered the event-generating code on Tab.java: arrow tabs will generate ActionEvent when MOUSE_PRESSED; all other tabs - when MOUSE_RELEASED
 * - Changed action command semantics to prefix "tab_" string to the arrow tabs command string
 * 
 * @see cw.notebook.TabPanel
 * @see cw.notebook.NoteBook
 * @see cw.notebook.TabScroller
 *
 * Created: Tue Oct 24 00:16:22 2000
 *
 * @author Cezar M. Tigaret
 * @version 0.4b
 */
public class Tab extends Component {

    /** TabScroller thread - initialized and used only when this tab style is
     *  STYLE_LEFTARROW or STYLE_RIGHTARROW. Enables repeated calls to doCommand() method on these two styles of tabs to generate a scrolling effect in the TabPanel.
     *
     *  @see TabScroller
     */
    TabScroller tS;

    protected boolean focused=false, 
        pressed=false, 
        usable=true, 
        hilite=true, 
        arrow=false, 
        isLocal;
	 
    /** The tab style constant. */
    public static final int  MASK_STYLE = 3;
    /** The local style constant. */
    public static final int  MASK_LOCAL = 16;
    /** The "normal" tab appearance. */
    public static final int  STYLE_SINGLE = 0;
    /** The "active" tab appearance; tabs sits in front of the others. */
    public static final int  STYLE_SINGLELOCAL = 16;
    /** The left arrow tab style. */
    public static final int  STYLE_LEFTARROW = 32;
    /** The right arrow tab style. */
    public static final int  STYLE_RIGHTARROW = 64;
    /** The arrow style constant. */
    public static final int  MASK_ARROW = 96;
    public static final int  MASK_TAB = 255;

    /** The Tab color palette: the background color for the "normal" tab. */
    public static final int  BACKGROUND=0;
    /** The Tab color palette: the foreground color for the "normal" tab. */
    public static final int  FOREGROUND=1;
    /** The Tab color palette: the background of the "active" tab. */
    public static final int  ACTIVE_BACKGROUND=2;
    /** The Tab color palette: the foreground of the "active" tab. */
    public static final int  ACTIVE_FOREGROUND=3;
    /** The Tab color palette: the background of the tab under the mouse cursor ("focused"); useful only when tab is created with <b>hilite</b> is true. */
    public static final int  FOCUSED_BACKGROUND=4;
    /** The Tab color palette: the foreground of the tab under the mouse cursor ("focused"); useful only when tab is created with <b>hilite</b> is true. */
    public static final int  FOCUSED_FOREGROUND=5;
    /** The Tab color palette: the color of the disabled tab. */
    public static final int  UNAVAILABLE=6;
    /** The Tab color palette: the color of the 3D effect highlight. */
    public static final int  HIGHLIGHT=7;
    /** The Tab color palette: the color of the 3D effect shadow.*/
    public static final int  SHADOW=8;

    protected int  txtH, txtW,
        tabH, sW, tW, txtX, txtY, 
        tabStyle, pre, scrollStep=1;
                           
    int[] xp=new int[6], yp=new int[6];
    Font f=new Font("Dialog",Font.PLAIN,10);

    /** Default "normal" tab background color. */
    public Color back = SystemColor.menu;
    /** Default "normal" tab foreground color. */
    public Color fore = SystemColor.menuText;
    /** Default "active" tab background color.*/
    public Color backActive = SystemColor.activeCaption;
    /** Default "active" tab foreground color.*/
    public Color foreActive = SystemColor.activeCaptionText;
    /** Default "focused" tab background color.*/
    public Color backFocus = SystemColor.textHighlight;
    /** Default "focused" tab foreground color.*/
    public Color foreFocus = SystemColor.textHighlightText;
    /** Default "disabled" tab color. */
    public Color foreUnavailable = SystemColor.textInactiveText;
    /** Default 3D effect highlight. */
    public Color highlight3D = SystemColor.controlHighlight;
    /** Default 3D effect shadow.*/
    public Color shadow3D = SystemColor.controlShadow;

    private Color currentBack, currentFore, currentHighlight, currentShadow, tempBack, tempFore;

    private Dimension dim;
    private String s=null,actionCommand;
    private Point[] p = new Point[15];
    private Polygon q;
    private Rectangle textRect;


    private ActionListener actionListener;

    /** Creates a tab with specified label and default appearance ("normal",appearance, enabled and highlighted by mouse hover). 
     * @param s The tab label string.
     */
    public Tab(String s){
        this(s,STYLE_SINGLE,true,true);
    }

    /** Creates a tab with specified label and style.
     * @param s The label string.
     * @param tabStyle A valid tab style constant.
     */
    public Tab(String s, int tabStyle){
        this(s,tabStyle,true,true);
    }

    /** Creates a tab with no label and with soecified style.
     * Useful for constructing arrow tabs.
     * @param tabStyle A valid tab style constant. Currently, it only makes sense to use this constructor with <b>STYLE_LEFTARROW</b> or <b>STYLE_RIGHTARROW</b> values.
     */
    public Tab(int tabStyle){
        this(null,tabStyle,true,true);
    }

    /** Creates a customized tab.
     * @param s The tab label string.
     * @param tabStyle A valid tab style constant.
     * @param usable Enables/disables the tab.
     * @param hilite Enables/diables tab highlight effect on mouse hover.
     */
    public Tab(String s, int tabStyle, boolean usable, boolean hilite) {
        this.tabStyle=tabStyle;
        this.usable=usable;
        if (s!=null) {
            this.s=s;
            actionCommand="tab_"+s;
        }
        this.hilite=hilite;
        compute();
        enableEvents(AWTEvent.MOUSE_EVENT_MASK);
        // instantiate the TabScroller only when this is an arrow-styled tab
        if (getTabStyle()==Tab.STYLE_LEFTARROW | getTabStyle()==Tab.STYLE_RIGHTARROW) tS=new TabScroller(this);
    }
	 
    // how much width is needed by the label?
    private int getLabelWidth(String s){
        FontMetrics fM=Toolkit.getDefaultToolkit().getFontMetrics(f);
        return fM.charsWidth(s.toCharArray(),0,s.length());
    }

    // performs the actual tab structure composition
    private void compute(){
        isLocal=((tabStyle & MASK_LOCAL)==16);
        if ((tabStyle & MASK_ARROW)==STYLE_LEFTARROW) {
            arrow=true;
			txtW=10;
            actionCommand="tab_scroll_left";
        } else if ((tabStyle & MASK_ARROW)==STYLE_RIGHTARROW) {
            arrow=true;
            txtW=10;
            actionCommand="tab_scroll_right";
        } else {
            txtW=getLabelWidth(s);
		}
        currentBack=back;
        currentFore=fore;
        if (isLocal) {
            currentBack=backActive;
            currentFore=foreActive;
        } else {
            if (!usable) currentFore=foreUnavailable;
        }
        currentHighlight=highlight3D;
        currentShadow=shadow3D;
        tempFore=currentFore;
        tempBack=currentBack;
        txtH=getFontMetrics(this.f).getHeight();
        if (s!=null) {txtW=getFontMetrics(this.f).stringWidth(s);}
        tabH=txtH+10;
        sW=(int)(tabH*Math.tan(30*Math.PI/180));
        tW=txtW+6;
        pre=sW;
        dim=new Dimension(2*sW+tW,tabH);
        txtX=dim.width/2-txtW/2;
        txtY=dim.height/2+txtH/3;
        p[0]=new Point(0,tabH);
        p[1]=new Point(sW,0);
        p[2]=new Point(sW+tW,0);
        p[3]=new Point(2*sW+tW,tabH);
        xp[0]=p[0].x; xp[1]=p[1].x; xp[2]=p[2].x; xp[3]=p[3].x; 
        yp[0]=p[0].y; yp[1]=p[1].y; yp[2]=p[2].y; yp[3]=p[3].y;
        q=new Polygon(xp,yp,4);
        textRect=new Rectangle(pre,1,tW-1,tabH-2);
    }

    /** Registers an ActionListener object with this tab.
     * @param listener The ActionListener object. 
     */
    public void addActionListener(ActionListener listener){
        actionListener=AWTEventMulticaster.add(actionListener, listener);
        enableEvents(AWTEvent.MOUSE_EVENT_MASK);
    }


    /** Deregisters an ActionListener from this tab. 
     * @param listener The ActionListener object.
     */
    public void removeActionListener(ActionListener listener){
        actionListener=AWTEventMulticaster.remove(actionListener, listener);
    }

    /** Handles mouse events on this tab and 
     *  casts the appropriate ActionEvent on registered listeners.
     *  Arrow-styled tabs call TabScroller instance for repeated action firing upon MouseEvent.MOUSE_PRESSED;
     *  regular tabs fire actions upon MouseEvent.MOUSE_RELEASED.
     */
    public void processMouseEvent(MouseEvent e){
        //if (tS!=null && tS.isAlive()) tS.stop();
        if (usable) {
            switch (e.getID()) {
            case MouseEvent.MOUSE_ENTERED:
                if (hilite) {
                    focused=true;
                    pressed=false;
                    currentFore=foreFocus;
                    currentBack=backFocus;
                } 
                update();
                break;
            case MouseEvent.MOUSE_EXITED:
                if (hilite) {
                    focused=false;
                    pressed=false;
                    currentFore=tempFore;
                    currentBack=tempBack;
                } 
                update();
                if (getTabStyle()==Tab.STYLE_LEFTARROW | getTabStyle()==Tab.STYLE_RIGHTARROW) {
                    if (tS!=null && tS.isAlive()) tS.stop();
                }
                break;
            case MouseEvent.MOUSE_PRESSED:
                if (e.getModifiers()==InputEvent.BUTTON1_MASK) {
                    if (hilite) {
                        focused=true;
                        pressed=true;
                        currentFore=foreFocus;
                    }
                    update();
                    if ((getTabStyle()==Tab.STYLE_LEFTARROW)|(getTabStyle()==Tab.STYLE_RIGHTARROW)) {
                        if (tS!=null && !tS.isAlive()) tS.start();
                    }
                }
                break;
            case MouseEvent.MOUSE_RELEASED:
                if (e.getModifiers()==InputEvent.BUTTON1_MASK) {
                    if (hilite) {
                        focused=true;
                        pressed=false;
                        if (!isLocal) {
                            currentFore=foreActive;
                        } else {
                            currentFore=fore;
                        }
                    }
                    update();
                    if ((getTabStyle()!=Tab.STYLE_LEFTARROW)&(getTabStyle()!=Tab.STYLE_RIGHTARROW))  doCommand();                 
                    else if (getTabStyle()==Tab.STYLE_LEFTARROW | getTabStyle()==Tab.STYLE_RIGHTARROW) {
                        if (tS!=null && tS.isAlive()) tS.stop();
                    } 
                } 
                break;
            } 
            super.processMouseEvent(e);
        } 
    }

    /** Sets the ActionCommand string for this tab
     * @param actionCommand The ActionCommand string
     */
    public void setActionCommand(String actionCommand){
        this.actionCommand=actionCommand;
    }

    /** Gets the ActionCommand string assigned to this tab
     * @return The ActionCommand string.
     */
    public String getActionCommand(){
        return actionCommand;
    }

    /** Assigns a label to this tab.
     * @param s The tab label.
     */
    public void setLabel(String s){
        this.s=s;
        update();
    }

    /** Gets the tab label.
     * @return The label string.
     */
    public String getLabel(){
        return s;
    }


    /** Assigns a specifc style to this tab.
     * @param A valid tab style constant.
     */
    public void setStyle(int tabStyle){
        this.tabStyle=tabStyle;
        compute();
        update();
    }

    /** Assigns this tab an "active" appearance. */
    public void setLocal(){
        tabStyle=STYLE_SINGLELOCAL;
        compute();
        update();
    }

    /** Assigns the default ("normal") appearance to this tab. */
    public void setDefaultStyle(){
        tabStyle=STYLE_SINGLE;
        compute();
        update();
    }

    /** Gets the current style of the tab.
     * @return The tab style.
     */
    public int getStyle(){
        return tabStyle;
    }

    public String getStyleDescription(){
        String descr="";
        switch(tabStyle) {
        case 0:
            descr="SINGLE";
            break;
        case 16:
            descr="SINGLELOCAL";
            break;
        case 32:
            descr="LEFTARROW";
            break;
        case 64:
            descr="RIGHTARROW";
            break;
        }
        return descr;
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

    /** Replaces the color palette for this tab.
     * @param colors The new color palette. The array should contain at least nine colors.
     */
    public void setColors(Color[] colors){
        for (int i=0; i<colors.length; i++) {
            setColor(i,colors[i]);
        }
    }

    /** Gets a specific color from the current palette.
     * @param colorIndex The index within the palette color.
     * @return Teh color at the specified index.
     */
    public Color getColor(int colorIndex){
        Color color=null;
        switch (colorIndex) {
        case BACKGROUND:
            color=back;
            break;
        case FOREGROUND:
            color=fore;
            break;
        case ACTIVE_BACKGROUND:
            color=backActive;
            break;
        case ACTIVE_FOREGROUND:
            color=foreActive;
            break;
        case FOCUSED_BACKGROUND:
            color=backFocus;
            break;
        case FOCUSED_FOREGROUND:
            color=foreFocus;
            break;
        case UNAVAILABLE:
            color=foreUnavailable;
            break;
        case HIGHLIGHT:
            color=highlight3D;
            break;
        case SHADOW:
            color=shadow3D;
            break;
        default:
            break;
        }
        return color;
    }

    /** Gets the current color palette.
     * @return The color palette.
     */
    public Color[] getColors(){
        Color[] colors=new Color[9];
        for (int i=0; i<colors.length; i++) {
            colors[i]=getColor(i);
        }
        return colors;
    }

    /** Enables/disables this tab.*/
    public void setEnabled(boolean usable){
        this.usable=usable;
        compute();
        update();
    }

    /** Gets the enabled state of this tab.
     * @return <b>true</b> if tab is enabled.
     */
    public boolean isEnabled(){
        return usable;
    }

    /** Enables/disables mouse hover effect.*/
    public void setHighlight(boolean hilite){
        this.hilite=hilite;
        update();
    }

    /** Gets the status of mouse hover effect.
     * @return <b>true</b> if mouse hover effect is enabled.
     */
    public boolean getHighlight(){
        return hilite;
    }

    public Dimension getDimension(){
        return dim;
    }


    public void paint(Graphics g){
        if(!isVisible()){
            focused=false;
            pressed=false;
        }
        g.setColor(currentBack);
        g.fillPolygon(q);
        g.setColor(currentHighlight);
        g.drawLine(q.xpoints[0],q.ypoints[0],q.xpoints[1],q.ypoints[1]);
        g.drawLine(q.xpoints[0]+1,q.ypoints[0],q.xpoints[1]+1,q.ypoints[1]-1);
        g.drawLine(q.xpoints[1],q.ypoints[1],q.xpoints[2],q.ypoints[2]);
        g.drawLine(q.xpoints[1]+1,q.ypoints[1]-1,q.xpoints[2]-1,q.ypoints[2]-1);
        g.setColor(currentShadow);
        g.drawLine(q.xpoints[2],q.ypoints[2],q.xpoints[3],q.ypoints[3]);
        g.drawLine(q.xpoints[2]-1,q.ypoints[2]-1,q.xpoints[3]-1,q.ypoints[3]);
        if (arrow) {
            g.setColor(backActive);
            if ((tabStyle & MASK_ARROW)==STYLE_LEFTARROW) {
                int[] arrowX={pre,pre+tW-2,pre+tW-2};
                int[] arrowY={tabH/2,tabH/2-txtY/2,txtY};
                g.fillPolygon(arrowX,arrowY,3);
                if (pressed) {
                    g.setColor(currentShadow);
                } else {
                    g.setColor(currentHighlight);
                }
                g.drawLine(pre,tabH/2,pre+tW-2,tabH/2-txtY/2);
                if (pressed) {
                    g.setColor(currentHighlight);
                } else {
                    g.setColor(currentShadow);
                }
                g.drawLine(pre+tW-2,tabH/2-txtY/2,pre+tW-2,txtY);
                g.drawLine(pre+tW-2,txtY,pre,tabH/2);
            } else {
                int[] arrowX={pre+2,pre+2,pre+tW};
                int[] arrowY={txtY,tabH/2-txtY/2,tabH/2};
                g.fillPolygon(arrowX,arrowY,3);
                if (pressed) {
                    g.setColor(currentShadow);
                } else {
                    g.setColor(currentHighlight);
                }
                g.drawLine(pre+2,txtY,pre+2,tabH/2-txtY/2);
                g.drawLine(pre+2,tabH/2-txtY/2,pre+tW,tabH/2);
                if (pressed) {
                    g.setColor(currentHighlight);
                } else {
                    g.setColor(currentShadow);
                }
                g.drawLine(pre+tW,tabH/2,pre+2,txtY);
            }
        } else {
            g.setColor(currentHighlight);
            g.drawLine(q.xpoints[0],q.ypoints[0],q.xpoints[1],q.ypoints[1]);
            if (!isLocal) {
                g.drawLine(q.xpoints[0],q.ypoints[0]-1,q.xpoints[3],q.ypoints[3]-1);
            }
            g.setColor(currentBack);
            if (focused) g.fill3DRect(textRect.x,textRect.y,textRect.width,textRect.height,!pressed);
            if (s!=null & !arrow) {
                g.setColor(currentFore);
                g.setFont(f);
                g.drawString(s,txtX,txtY);
            }
        }
    }

    public void update(){
        super.repaint();
    }

    /** Gets the name (label) of this tab.
     * @return The name string.
     */
    public String getName(){
        return s;
    }


    public Dimension getMinimumSize(){
        return dim;
    }

    public Dimension getPreferredSize(){
        return getMinimumSize();
    }

    /** Gets the width of this tab.
     * @return The tab width.
     */
    public int getWidth(){
        return getPreferredSize().width;
    }

    /** Gets the height of this tab.
     * @return The tab height.
     */
    public int getHeight(){
        return getPreferredSize().height;
    }

    public int getTabStyle(){
        return tabStyle;
    }

    public void doCommand() {
        if (actionListener!=null) {
            //System.out.println("Tab:"+actionCommand);
            actionListener.actionPerformed(new ActionEvent(this,ActionEvent.ACTION_PERFORMED,actionCommand));                                  
        }
    }

    public boolean isPressed(){
        return pressed;
    }

} // Tab
