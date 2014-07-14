import ij.plugin.filter.*;
import java.awt.*;
import java.awt.image.*;
import java.util.Vector;
import java.io.*;
import ij.*;
import ij.process.*;
import ij.io.*;
import ij.gui.*;
import ij.measure.*;

/** Saves evenly spaced  X-Y coordinates along the current ROI boundary. */
public class Path_Writer implements PlugInFilter {
	ImagePlus imp;
	double[] xpath;
	double[] ypath;

	public int setup(String arg, ImagePlus imp) {
		this.imp = imp;
		return DOES_ALL+ROI_REQUIRED+NO_CHANGES;
	}

	public void run(ImageProcessor ip) {
		try {
			saveXYCoordinates(imp);
		} catch (IllegalArgumentException e) {
			IJ.showMessage("Path Writer", e.getMessage());
		}
	}

	public void saveXYCoordinates(ImagePlus imp) {
		Roi roi = imp.getRoi();
		if (roi==null)
			throw new IllegalArgumentException("ROI required");
		if (!(roi instanceof PolygonRoi))
			throw new IllegalArgumentException("Irregular area or line selection required");
		
		SaveDialog sd = new SaveDialog("Save Coordinates as Text...", imp.getTitle(), ".txt");
		String name = sd.getFileName();
		if (name == null)
			return;
		String directory = sd.getDirectory();
		PrintWriter pw = null;
		try {
			FileOutputStream fos = new FileOutputStream(directory+name);
			BufferedOutputStream bos = new BufferedOutputStream(fos);
			pw = new PrintWriter(bos);
		}
		catch (IOException e) {
			IJ.showMessage("XYWriter", ""+e);
			return;
		}
		
		PolygonRoi p = (PolygonRoi)roi;
		getPath(p);
		Calibration cal = imp.getCalibration();
		String ls = System.getProperty("line.separator");
		boolean scaled = cal.scaled();
		int maxy = imp.getHeight()-1;
		for (int i=0; i<xpath.length; i++)
			pw.print(IJ.d2s((xpath[i])*cal.pixelWidth) + "\t" + IJ.d2s((maxy-ypath[i])*cal.pixelHeight) + ls);
		pw.close();
	}

	void getPath(PolygonRoi p) {
		int n = p.getNCoordinates();
		int[] x = p.getXCoordinates();
		int[] y = p.getYCoordinates();
		Rectangle r = p.getBoundingRect();
		int xbase = r.x;
		int ybase = r.y;
		double length = 0.0;
		double segmentLength;
		int xdelta, ydelta, iLength;
		double[] segmentLengths = new double[n];
		int[] dx = new int[n];
		int[] dy = new int[n];
		for (int i=0; i<(n-1); i++) {
			xdelta = x[i+1] - x[i];
			ydelta = y[i+1] - y[i];
			segmentLength = Math.sqrt(xdelta*xdelta+ydelta*ydelta);
			length += segmentLength;
			segmentLengths[i] = segmentLength;
			dx[i] = xdelta;
			dy[i] = ydelta;
		}
		//double[] values = new double[(int)length];
		xpath = new double[(int)length];
		ypath = new double[(int)length];
		double leftOver = 1.0;
		double distance = 0.0;
		int index;
		double oldx=xbase, oldy=ybase;
		for (int i=0; i<n; i++) {
			double len = segmentLengths[i];
			if (len==0.0)
				continue;
			double xinc = dx[i]/len;
			double yinc = dy[i]/len;
			double start = 1.0-leftOver;
			double rx = xbase+x[i]+start*xinc;
			double ry = ybase+y[i]+start*yinc;
			double len2 = len - start;
			int n2 = (int)len2;
			//double d=0;;
			//IJ.write("new segment: "+IJ.d2s(xinc)+" "+IJ.d2s(yinc)+" "+IJ.d2s(len)+" "+IJ.d2s(len2)+" "+IJ.d2s(n2)+" "+IJ.d2s(leftOver));
			for (int j=0; j<=n2; j++) {
				index = (int)distance+j;
				if (index<xpath.length) {
					//values[index] = ip.getInterpolatedValue(rx, ry);
					xpath[index] = rx;
					ypath[index] = ry;
				}
				//d = Math.sqrt((rx-oldx)*(rx-oldx)+(ry-oldy)*(ry-oldy));
				//IJ.write(IJ.d2s(rx)+"    "+IJ.d2s(ry)+"    "+IJ.d2s(d));
				//oldx = rx; oldy = ry;
				rx += xinc;
				ry += yinc;
			}
			distance += len;
			leftOver = len2 - n2;
		}
	}

}
