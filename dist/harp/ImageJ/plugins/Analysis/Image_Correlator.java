import java.awt.*;
import java.io.*;
import ij.*;
import ij.gui.*;
import ij.process.*;
import ij.text.*;
import ij.plugin.PlugIn;

public class Image_Correlator implements PlugIn {

    private static int index1;
    private static int index2;
    private static boolean displayCounts;
    private ImagePlus imp1, imp2;
            
    public void run(String arg) {
        if (showDialog())
            correlate(imp1, imp2);
    }
    
    public boolean showDialog() {
        int[] wList = WindowManager.getIDList();
        if (wList==null) {
            IJ.noImage();
            return false;
        }
        String[] titles = new String[wList.length];
        for (int i=0; i<wList.length; i++) {
            ImagePlus imp = WindowManager.getImage(wList[i]);
            if (imp!=null)
                titles[i] = imp.getTitle();
            else
                titles[i] = "";
        }
        if (index1>=titles.length)index1 = 0;
        if (index2>=titles.length)index2 = 0;
        GenericDialog gd = new GenericDialog("Image Correlator");
        gd.addChoice("Image #1: ", titles, titles[index1]);
        gd.addChoice("Image #2: ", titles, titles[index2]);
        gd.addCheckbox("Display Counts: ", displayCounts);
        gd.showDialog();
        if (gd.wasCanceled())
            return false;
        index1 = gd.getNextChoiceIndex();
        index2 = gd.getNextChoiceIndex();
        displayCounts = gd.getNextBoolean();
        String title1 = titles[index1];
        String title2 = titles[index2];
        imp1 = WindowManager.getImage(wList[index1]);
        imp2 = WindowManager.getImage(wList[index2]);
        if (imp1.getType()!=imp1.GRAY8 || imp2.getType()!=imp1.GRAY8) {
            IJ.showMessage("Image Correlator", "Both images must be 8-bit grayscale.");
            return false;
        }
        return true;
   }
    
    public void correlate(ImagePlus imp1, ImagePlus imp2) {
        ImageProcessor ip1 = imp1.getProcessor();
        ImageProcessor ip2 = imp2.getProcessor();
        boolean unsigned = true;
        ImageProcessor plot = new ShortProcessor(256, 256);
        int width = imp1.getWidth();
        int height = imp1.getHeight();
        int z1, z2, count;
        for (int y=0; y<height; y++) {
            for (int x=0; x<width; x++) {
                z1 = ip1.getPixel(x,y); // z-value of pixel (x,y)in image #1
                z2 = 255-ip2.getPixel(x,y); // z-value of pixel (x,y)in image #2
                count = plot.getPixel(z1, z2);
                if (count<65535) count++;
                plot.putPixel(z1, z2, count);
            }
        }
        plot.invertLut();
        plot.resetMinAndMax();
        new ImagePlus("Correlation Plot", plot).show();
        if (displayCounts)
            displayCounts(plot);
    }

    void displayCounts(ImageProcessor plot) {
        StringBuffer sb = new StringBuffer();
        int count;
        for (int x=0; x<256; x++)
            for (int y=255; y>=0; y--) {
                count = plot.getPixel(x,y);
                if (count>0)
                    sb.append(x+"\t"+(255-y)+"\t"+count+"\n");
            }
       new TextWindow("Non-zero Counts", "X\tY\tCount", sb.toString(), 300, 400);
       }
 
}
