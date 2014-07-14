import ij.*;
import ij.plugin.PlugIn;
import ij.process.*;
import ij.gui.*;

public class RGB_Stack_Merge implements PlugIn {

	private ImagePlus imp;

	/** Merges one, two or three 8-bit stacks into an RGB stack. */
	public void run(String arg) {
		imp = WindowManager.getCurrentImage();
		MergeStacks();
	}

	/** Combines three grayscale stacks into one RGB stack. */
	public void MergeStacks() {
		int[] wList = WindowManager.getIDList();
		if (wList==null) {
			IJ.error("No images are open.");
			return;
		}

		String[] titles = new String[wList.length+1];
		for (int i=0; i<wList.length; i++) {
			ImagePlus imp = WindowManager.getImage(wList[i]);
			titles[i] = imp!=null?imp.getTitle():"";
		}
		String none = "*None*";
		titles[wList.length] = none;

		GenericDialog gd = new GenericDialog("RGB Stack Merge");
		gd.addChoice("Red Stack:", titles, titles[0]);
		gd.addChoice("Green Stack:", titles, titles[1]);
		String title3 = titles.length>2?titles[2]:none;
		gd.addChoice("Blue Stack:", titles, title3);
		gd.addCheckbox("Keep source stacks", false);
		gd.showDialog();
		if (gd.wasCanceled())
			return;
		int[] index = new int[3];
		index[0] = gd.getNextChoiceIndex();
		index[1] = gd.getNextChoiceIndex();
		index[2] = gd.getNextChoiceIndex();
		boolean keep = gd.getNextBoolean();

		ImagePlus[] image = new ImagePlus[3];
		int stackSize = 0;
		int width = 0;
		int height = 0;
		for (int i=0; i<3; i++) {
			if (index[i]<wList.length) {
				image[i] = WindowManager.getImage(wList[index[i]]);
				width = image[i].getWidth();
				height = image[i].getHeight();
				stackSize = image[i].getStackSize();
			}
		}
		if (width==0) {
			IJ.error("There must be at least one 8-bit source stack.");
			return;
		}
		for (int i=0; i<3; i++) {
			ImagePlus img = image[i];
			if (img!=null) {
				if (img.getStackSize()!=stackSize) {
					IJ.error("The source stacks must all have the same number of slices.");
					return;
				}
				if (img.getType()!=ImagePlus.GRAY8) {
					IJ.error("The source stacks must be 8-bit grayscale.");
					return;
				}
				if (img.getWidth()!=width || image[i].getHeight()!=height) {
					IJ.error("The source stacks must have the same width and height.");
					return;
				}
			}
		}

		ImageStack red = image[0]!=null?image[0].getStack():null;
		ImageStack green = image[1]!=null?image[1].getStack():null;
		ImageStack blue = image[2]!=null?image[2].getStack():null;
		ImageStack rgb = MergeStacks(width, height, stackSize, red, green, blue, keep);
		if (!keep)
			for (int i=0; i<3; i++) {
				if (image[i]!=null) {
					image[i].changes = false;
					ImageWindow win = image[i].getWindow();
					if (win!=null)
						win.close();
				}
			}
		new ImagePlus("RGB", rgb).show();
	}
	
	public ImageStack MergeStacks(int w, int h, int d, ImageStack red, ImageStack green, ImageStack blue, boolean keep) {
		ImageStack rgb = new ImageStack(w, h);
		int inc = d/10;
		if (inc<1) inc = 1;
		ColorProcessor cp;
		int slice = 1;
		byte[] blank = new byte[w*h];
		byte[] redPixels, greenPixels, bluePixels;
	    	boolean invertedRed = red!=null?red.getProcessor(1).isInvertedLut():false;
	    	boolean invertedGreen = green!=null?green.getProcessor(1).isInvertedLut():false;
	    	boolean invertedBlue = blue!=null?blue.getProcessor(1).isInvertedLut():false;
		try {
	    	for (int i=1; i<=d; i++) {
			cp = new ColorProcessor(w, h);
	    		redPixels = red!=null?(byte[])red.getPixels(slice):blank;
	    		greenPixels = green!=null?(byte[])green.getPixels(slice):blank;
	    		bluePixels = blue!=null?(byte[])blue.getPixels(slice):blank;
	    		if (invertedRed) invert(redPixels);
	    		if (invertedGreen) invert(greenPixels);
	    		if (invertedBlue) invert(bluePixels);
	    		cp.setRGB(redPixels, greenPixels, bluePixels);
			if (keep) {
				slice++;
	    			if (invertedRed) invert(redPixels);
	    			if (invertedGreen) invert(greenPixels);
	    			if (invertedBlue) invert(bluePixels);
			} else {
	    			if (red!=null) red.deleteSlice(1);
				if (green!=null &&green!=red) green.deleteSlice(1);
				if (blue!=null&&blue!=red && blue!=green) blue.deleteSlice(1);
				//System.gc();
			}
			rgb.addSlice(null, cp);
			if ((i%inc) == 0) IJ.showProgress((double)i/d);
	    	}
		IJ.showProgress(1.0);
		} catch(OutOfMemoryError o) {
			IJ.outOfMemory("MergeStacks");
			IJ.showProgress(1.0);
		}
		return rgb;
	}
	
	void invert(byte[] pixels) {
		for (int i=0; i<pixels.length; i++)
			pixels[i] = (byte)(255-pixels[i]&255);
	}

}


