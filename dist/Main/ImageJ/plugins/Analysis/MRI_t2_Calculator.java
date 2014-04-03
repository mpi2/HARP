import ij.*;
import ij.plugin.*;
import ij.gui.*;
import ij.process.*;
import ij.measure.Calibration;

/** This plugin does MRI t2 calculations (s2 = k/ln(s1/s2)) on two images or stacks.
 *
 *   ERK (Eric Kischell, keesh@ieee.org) changes 11/27/99 
 *       8-bit enhancement 
 *   ERK changes 04/13/02
 *       Aded option to output to a new, third image/stack, rather
 *       than overwriting the second (S2) stack.
 *  Known Issues
 *      .Currently only works with 8-bit and 16-bit grayscale images or stacks
 *      (both images must be of the same data type).
*/ 

public class MRI_t2_Calculator implements PlugIn {

    private static String title = "MRI_t2_Calculator";
    private static double k = 35.0;
    private static boolean createWindow = true;

    public void run(String arg) {
         if (arg.equals("about"))
            {showAbout(); return;}
        
        int[] wList = WindowManager.getIDList();
        if (wList==null || wList.length<2) {
            IJ.showMessage(title, "There must be at least two windows open.");
            return;
        }
        String[] titles = new String[wList.length];
        for (int i=0; i<wList.length; i++) {
            ImagePlus imp = WindowManager.getImage(wList[i]);
            if (imp!=null)
                titles[i] = imp.getTitle();
            else
                titles[i] = "";
        }
        GenericDialog gd = new GenericDialog("MRI t2 Calculator");
        gd.addChoice("S1:", titles, titles[0]);
        gd.addChoice("S2:", titles, titles[1]);
        gd.addNumericField("K:", k, 1);
        gd.addMessage("S2 = K/ln(S1/S2)");
        gd.addCheckbox("Create New Window", createWindow);
        gd.showDialog();
        if (gd.wasCanceled())
            return;
        int s1Index = gd.getNextChoiceIndex();
        int s2Index = gd.getNextChoiceIndex();
        k = gd.getNextNumber();
        createWindow = gd.getNextBoolean();
        ImagePlus s1 = WindowManager.getImage(wList[s1Index]);
        ImagePlus s2 = WindowManager.getImage(wList[s2Index]);
        
        // chk support image types 
        int s1Type = s1.getType();
        int s2Type = s2.getType();
        if (s1Type!=s1.GRAY16 || s2Type!=s1.GRAY16) {   
            if (s1Type!=s1.GRAY8 || s2Type!=s1.GRAY8) {
                IJ.showMessage(title, "Both Images must be 8-bits or 16-bits");
                return;
            }
        }
        if(s1Type != s2Type){
            IJ.showMessage(title, "Both Images must be 8-bits or 16-bits");
            return;
        }
        
        if (s1.getWidth()!=s2.getWidth() || s1.getHeight()!=s2.getHeight()) {
            IJ.showMessage(title, "Images must have the same dimensions");
            return;
        }
        
        int s1Size = s1.getStackSize();
        int s2Size = s2.getStackSize();
        if (s1Size!=s2Size) {
            IJ.showMessage(title, "Stacks must have the same number of slices");
            return;
        }
        // Create a new window/stach or replace S2?
        if (createWindow) {
            ImagePlus s3 = duplicateStack(s2);
            if (s3==null) {
                // getClass should be OK for public members
                IJ.showMessage(getClass().getName(), "Out of memory");
                return;
            }
            s3.show();
            calculate(s1, s3, s1Type, k);
        }   
        else {
            calculate(s1, s2, s1Type, k);
        }
        
        IJ.register(MRI_t2_Calculator.class);
    }
    
    /** Performs MRI t2 calculations (s2 = k/ln(s1/s2)) on two images or stacks. */
    public void calculate(ImagePlus s1, ImagePlus s2, int s1Type, double k) {
        int width  = s1.getWidth();
        int height = s1.getHeight();
        int slices = s1.getStackSize();
        ImageStack stack1 = s1.getStack();
        ImageStack stack2 = s2.getStack();
        double v1, v2;
    
        if(s1Type == s1.GRAY16) {

            short[] pixels1, pixels2;
            for (int n=1; n<=slices; n++) {
                pixels1 = (short[])stack1.getPixels(n);
                pixels2 = (short[])stack2.getPixels(n);
                    for (int i=0; i<width*height; i++) {
                        v1 = pixels1[i]&0xffff;
                        v2 = pixels2[i]&0xffff;
                        v2 = v2!=0.0?v1/v2:0.0;
                        v2 = v2>0.0?Math.log(v2):0.0;
                        v2 = v2!=0.0?k/v2:0.0;
                        v2 += 32768.0;  // make unsigned
                        pixels2[i] = (short)(v2);
                }           
                IJ.showProgress((double)n/slices);
            if (n==1) s2.getProcessor().resetMinAndMax();
                s2.updateAndDraw();
            }  // for n: slices
            setCalibration(s2);
        }  // short data type
        else  // 8-bit byte image
        {
            byte[] pixels1, pixels2;
            for (int n=1; n<=slices; n++) {
                pixels1 = (byte[])stack1.getPixels(n);
                pixels2 = (byte[])stack2.getPixels(n);
                for (int i=0; i<width*height; i++) {
                    v1 = pixels1[i];
                    v2 = pixels2[i];
                    // div by 0, set = 0 for now
                    v2 = (v2 != 0.0 ? v1/v2 : 0.0) ;
                    // natur log must be > 0.0
                    v2 = (v2 > 0.0 ? Math.log(v2) : 0.0) ;
                    // div by 0, set = 0 for now
                    v2 = (v2 != 0.0 ? k/v2 : 0.0) ;
                    // cheap round -#s using -0.5
                    v2 = (v2 >= 0.0 ? v2+0.5 : v2-0.5) ;     
                    // chk for satur vals
                    // should really use pre'def const for 255
                    if(v2 >= 0.0 && v2 <= 255.0){
                        pixels2[i] = (byte)(v2);
                    }
                    else if(v2 > 255.0){
                        pixels2[i] = (byte)255;
                    }
                    else{ // v2 < 0.0
                        pixels2[i] = (byte)0;
                    }
                }  // for i: pixels         
                IJ.showProgress((double)n/slices);
                s2.updateAndDraw();
              }  // for n: slices
        } // byte data type
    
    }  // calculate

    // duplicateStack copied from ImageCalculator class
    ImagePlus duplicateStack(ImagePlus img1) {
        ImageStack stack1 = img1.getStack();
        int width = stack1.getWidth();
        int height = stack1.getHeight();
        int n = stack1.getSize();
        ImageStack stack2 = img1.createEmptyStack();
        try {
            for (int i=1; i<=n; i++) {
                ImageProcessor ip1 = stack1.getProcessor(i);
                ip1.setRoi(null); 
                ImageProcessor ip2 = ip1.crop(); 
                stack2.addSlice(stack1.getSliceLabel(i), ip2);
            }
        }
        catch(OutOfMemoryError e) {
            stack2.trim();
            stack2 = null;
            return null;
        }
        return new ImagePlus("Result", stack2);
    }

    // setup a calibration function to subtract 32768
    void setCalibration(ImagePlus imp) {
        double[] coeff = new double[2];
        coeff[0] = -32768.0;
        coeff[1] = 1.0;
        imp.getCalibration().setFunction(Calibration.STRAIGHT_LINE, coeff, "MRI t2");
   }

    void showAbout() {
        String title = "About " + getClass().getName() + "...";
        IJ.showMessage(title,
            "This plugin does MRI t2 calculations (s2 = k/ln(s1/s2))\n" +
            "on two images or stacks.  It optionally outputs to a\n" + 
            "new, third image/stack, rather than overwriting the\n" + 
            "second (S2) stack."
        );
    }

}  // MRI_t2_Calculator_

