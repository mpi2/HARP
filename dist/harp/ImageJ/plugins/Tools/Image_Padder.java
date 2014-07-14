// Image_Padder.java

// Version 1.1, 2013-MAY-24 (F.V. Hessman <hessman@astro.physik.uni-goettingen.de>)
//	Added underscores to field labels so that Image_Padder can be used in macros.

import java.awt.*;

import ij.*;
import ij.gui.*;
import ij.plugin.filter.*;
import ij.process.*;

public class Image_Padder implements PlugInFilter
	{
	ImagePlus img;
	int padTop, padLeft, padRight, padBottom;

	public int setup(String arg, ImagePlus imp)
		{
		img = imp;
		return DOES_16 | DOES_32 | DOES_8C | DOES_8G | DOES_RGB;
		}

	public void run(ImageProcessor ip)
		{
		if (img == null | ip == null) return;

		int w = img.getWidth();
		int h = img.getHeight();

		GenericDialog gd = new GenericDialog ("Image Padder");
		gd.addMessage ("Current width: "+w);
		gd.addMessage ("Current height: "+h);
		gd.addNumericField ("Pad_top:",0,0);
		gd.addNumericField ("Pad_left:",0,0);
		gd.addNumericField ("Pad_right:",0,0);
		gd.addNumericField ("Pad_bottom: ",0,0);
		gd.addMessage ("(padding can also be negative)");
		gd.showDialog();
		if (gd.wasCanceled()) return;

		padTop = (int)gd.getNextNumber();
		padLeft = (int)gd.getNextNumber();
		padRight = (int)gd.getNextNumber();
		padBottom = (int)gd.getNextNumber();
System.err.println ("top,left,right,bottom="+padTop+","+padLeft+","+padRight+","+padBottom);

		w += padLeft+padRight;
		h += padTop+padBottom;
		if (h <= 0 || w <= 0)
			{
			IJ.error ("Resulting image would have w="+w+", h="+h);
			return;
			}

		int d = img.getBitDepth();
		if (d == 32)
			padFloat ((FloatProcessor)ip);
		else
			pad (ip);
		}

	protected void padFloat (FloatProcessor ip)
		{
		int oldh = ip.getHeight();
		int oldw = ip.getWidth();
		int neww = oldw+padLeft+padRight;
		int newh = oldh+padTop+padBottom;

		float[][] padded = new float[neww][newh];
		float[][] orig = ip.getFloatArray();

		for (int j=0; j < oldh; j++)
			{
			int jj = j+padTop;
			if (jj >= 0 && jj < newh)
				{
				for (int i=0; i < oldw; i++)
					{
					int ii = i+padLeft;
					if (ii >= 0 && ii <= neww)
						padded[ii][jj] = orig[i][j];
					}
				}
			}
		FloatProcessor p = new FloatProcessor (padded);		ImagePlus im = new ImagePlus ("Padded "+img.getShortTitle(), p);
		im.show();
		}

	protected void pad (ImageProcessor ip)
		{
		int oldw = ip.getWidth();
		int oldh = ip.getHeight();
		int neww = oldw+padLeft+padRight;
		int newh = oldh+padTop+padBottom;

		ImageProcessor p;
		if (ip instanceof ShortProcessor)
			p = new ShortProcessor (neww, newh);
		else if (ip instanceof ByteProcessor)
			p = new ByteProcessor (neww, newh);
		else
			p = new ColorProcessor (neww, newh);

		for (int j=0; j < oldh; j++)
			{
			int jj = j+padTop;
			if (jj >= 0 && jj < newh)
				{
				for (int i=0; i < oldw; i++)
					{
					int ii = i+padLeft;
					if (ii >= 0 && ii <= neww)
						p.putPixel (ii,jj,ip.getPixel(i,j));
					}
				}
			}	
		ImagePlus im = new ImagePlus ("Padded "+img.getShortTitle(), p);
		im.show();
		}

	}
