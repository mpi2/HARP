import java.awt.*;
import java.awt.event.*;
import java.io.*;
import java.awt.datatransfer.DataFlavor;
import java.awt.datatransfer.Transferable;
import java.awt.dnd.DnDConstants;
import java.awt.dnd.DropTarget;
import java.awt.dnd.DropTargetDragEvent;
import java.awt.dnd.DropTargetDropEvent;
import java.awt.dnd.DropTargetEvent;
import java.awt.dnd.DropTargetListener;
import java.util.Iterator;
import java.util.List;	

import ij.*;
import ij.plugin.PlugIn;	
import ij.gui.GenericDialog;

/** Drag and Drop images onto the ImageJ main frame. Requires Java 2, v1.3.1.
 *
 *  @author keesh <keesh@ieee.org> (orig example author Greg Merrill)
 *
 *  keesh created 05/01/2002 
 *  Known Issues
 *      .Currently opens tiff, bmp, dicom, fits, pgm, gif or jpeg images
 		 and ROI, LUT, text and Java source files.
 *      .Does not traverse image "directories".
 *      .May not detach drag and drop support when ImageJ exits. 
 *      Under JDK v1.3.1 need to drop near ImageJ menubar or titlebar.
 */
public class Drag_And_Drop implements PlugIn {
 
    protected static ImageJ ij = null;  // the "ImageJ" frame
    private static boolean enableDND = true;
    private static String vers;
    
	public Drag_And_Drop() {
	    vers = System.getProperty("java.version");
	    if (vers.compareTo("1.3.1") < 0) {
		    IJ.error ("This plugin will only run using Java 2, v1.3.1 or higher");
		    return;
		}
	    ij = IJ.getInstance();
	}  // ctor
	
	public void run(String arg) {
		if (arg.equals("about"))
			{showAbout(); return;}
		
		if (vers.compareTo("1.3.1") < 0) {
		    return;
		}
		
		// getClass should be OK for public members
		String title = "Setup " + getClass().getName() ;
		GenericDialog gd = new GenericDialog(title);	
		gd.addCheckbox("Enable Drag and Drop", enableDND);
        gd.showDialog();
        if (gd.wasCanceled())
            return;
	    enableDND = gd.getNextBoolean();
		
		// we really would like to detach the drop target
		// when the application is exiting too
	    if(ij != null) { 
		    ij.setDropTarget(null);
		}
		if(enableDND) {
		    if(ij != null) {
	        // We would like to add a DropHandler when the main image frame is created.
	        DropTarget dropTarget = new DropTarget( 
	            ij, 
	            new DropHandler(ij));
		    }   
		}
	
	    // register class to prevent garbage collect
        IJ.register(Drag_And_Drop.class);  
	}  // run
	    
	void showAbout() {
		String title = "About " + getClass().getName() + "...";
		IJ.showMessage(title,
			"This plugin hooks into ImageJ in order to\n" +
			"support drag and drop of images to the ImageJ frame." 
		);
	}	    
	
	
 /**
  * Modified class to handle drag'n'drop events for ImageJ's ImageJ.
  *
  * @author keesh<keesh@ieee.org> (orig example author Greg Merrill)
  *
  * Planned Enhancements
  *  .handle image directories.
  *  .handle more image types via 'opener'
  */	
/*
 * Credits:
 * Example from JEdit:  <a href="http://www.jedit.org"> JEdit home </a>
 * DragAndDropPlugin.java - Drag-and-Drop plugin
 * Copyright (C) 2000 Greg Merrill
 * Other contributors: Denis Lambot
 *                     Carmine Lucarelli
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 */
    static class DropHandler implements DropTargetListener
    {
	    protected ImageJ mainFrame;
	    protected DataFlavor dFlavor;

	    /**
		    * @param mainFrame  The main imaging frame we're handling
		    */
	    DropHandler(ImageJ mainFrame)
	    {
		    this.mainFrame = mainFrame;
	    }

        public void drop(DropTargetDropEvent dtde)
	    {
		    dtde.acceptDrop(DnDConstants.ACTION_COPY);
		    try
		    {
			    Transferable t = dtde.getTransferable();
			    if(t.isDataFlavorSupported(DataFlavor.javaFileListFlavor))
			    {
				    // file object(s) have been dropped
				    Object data = t.getTransferData(DataFlavor.javaFileListFlavor);
				    Iterator iterator = ((List)data).iterator();
				    while(iterator.hasNext())
				    {
					    File file = (File)iterator.next();
					    if( !file.isDirectory() )  // don't handle directories for now
					        handleDroppedFile(file.getAbsolutePath());
				    }
			    }
		    }
		    catch(Exception e)
		    {
			    e.printStackTrace();
			    IJ.error( "Error in drop() method. Reason: " + e.getMessage() );
			    dtde.dropComplete(false);
			    return;
		    }

		    dtde.dropComplete(true);
	    }  // drop

	    public void dragEnter(DropTargetDragEvent dtde)
	    {
		    // check if there is at least one File Type in the list
		    DataFlavor[] flavors = dtde.getCurrentDataFlavors();
		    for(int i = 0; i < flavors.length; i++)
		    {
			    String mimeType = flavors[i].getMimeType();
			    //System.out.println(flavors[i].toString());
			    // mimeType= application/x-java-file-list
			    if(flavors[i].isFlavorJavaFileListType())
			    {
				    dtde.acceptDrag(DnDConstants.ACTION_COPY);
				    return;
			    }
		    }
		    dtde.rejectDrag();
	    }

	    public void dragOver(DropTargetDragEvent e)
	    {
	    }

	    public void dragExit(DropTargetEvent e)
	    {
	    }

	    public void dropActionChanged(DropTargetDragEvent e)
	    {
	    }

	    private void handleDroppedFile(String path)
	    {
		    // quick & dirty method to open/display an image 
		    // tiff, bmp, dicom, fits, pgm, gif or jpeg image
		    if( !Macro.open(path) ) {
		        IJ.write("Could not open image from: " + path);
		    }
	    }
    }  // class DropHandler    
	    	    
}  // Drag_And_Drop



