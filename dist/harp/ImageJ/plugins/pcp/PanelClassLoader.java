import java.io.*;
import ij.*;
import java.lang.reflect.*;
/**
 * PanelClassLoader.java - a custom plugins class loader for Java 1.1.x
 * 
 * Loads plugins classes installed in subdirectories of "plugins" by overriding
 * java.lang.ClassLoader.loadClass()
 * Based on the PluginCLassLoader written by Wayne Rasband. 
 *
 * Please note: if you are currently running a JVM 1.2 environment, 
 * you need to switch to a JVM 1.1 envrionment before compiling this file
 * 
 * Created: Sat Oct 28 12:05:55 2000
 *
 * @author Cezar M. Tigaret
 * @version 0.4b
 */
public class PanelClassLoader extends ClassLoader {

    /** The platform-specific file separator. */
    private String separator=System.getProperty("file.separator");

    /** The default path and file name for the class to be loaded. */
    private String path, ijPluginsPath;
	 
    /** The default constructor. 
     * The caller of this constructor should also invoke setPath(String) before attempting to load a class.
     * @see #setPath(String pathName)
     */
    public PanelClassLoader() {
    }

    /** Constructs a PanelCLassLoader object to load classes in path.
     * @param path The pathname of the directory where class files are to be loaded.
     */
    public PanelClassLoader (String path, String ijPluginsPath){
        this.path=path;
        this.ijPluginsPath=ijPluginsPath;
        //		  this.cName=cName;
    }


    /** Overrides loadClass(String,boolean) in java.lang.ClassLoader.
     * 
     * (re)Loads the class from the following locations:
     *  (a) tries to load from system classes with findSystemClass(classname);
     *  (b) if (a) unsuccessfull, loads bytecode from compiled binary data file using  loadClassData(classname);
     * @param name The name of the plugin class
     * @param resolve
     * @see java.lang.ClassLoader
     */
    protected synchronized Class loadClass(String name, boolean resolve)
        throws ClassNotFoundException {
        if (path==null || ijPluginsPath==null) return null;
        Class c=null;
        try {
            c=findSystemClass(name);
        } catch (Exception e1) {                      
            try {
                c=loadClassData(ijPluginsPath,name);
            } catch (Exception e2) {
                try {
                    c=loadClassData(path,name);
                } catch (Exception e3) {
                    throw new ClassNotFoundException(name);
                }
            }
        }                                                      
        if (c!=null && resolve){
            resolveClass(c);
        }
        return c;
    }


    /** Loads class bytecode from compiled binary data ("*.class") file. 
     * 
     * @param c the name of the '*.class" file, without leading pathname.
     * @return The resulting Class object.
     */
    private Class loadClassData(String p,String c) throws ClassNotFoundException {
        // Prepare the class file name string for file lookup:
        c=c.replace('.',separator.charAt(0)); // translate '.' into path separators
        if (!c.endsWith(".class")) c+=".class"; // add ".class" extension
        if (p.endsWith(separator)) p=p.substring(0,p.lastIndexOf(separator)); // discard path separator suffix in the pathname
        p+=separator+c; // concatenate plugin path and plugin class file name strings
        File f=new File(p);
        Class cls=null;
        c=c.substring(0,c.lastIndexOf(".class")); // strip out the ".class" extenstion
        try {
            InputStream in=new FileInputStream(f);
            int bufsize=(int)f.length();
            byte b[]=new byte[bufsize];
            in.read(b,0,bufsize);
            in.close();
            //System.out.println("defineClass("+c+")");
            cls=defineClass(c,b,0,b.length);
        } catch (Exception e) {
            throw new ClassNotFoundException(c);
        }
        return cls;
    }

    /** Sets the path to specified compiled class file
     * 
     */
    public void setPath(String pathName){
        path=pathName;
    }

    /* Sets the ImageJ plugins path
     *
     */
    public void setPluginsPath(String pathName) {
        ijPluginsPath=pathName;
    }

} // PanelClassLoader







