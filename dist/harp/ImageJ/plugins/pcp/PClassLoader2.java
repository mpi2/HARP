import java.io.*;

/**
 * PClassLoader2.java - a custom plugins class loader for Java 1.2.x 
 *
 * Inspired from the ij.io.PluginClassLoader by Wayne Rasband
 *
 * Complies to the Java 1.2 delegation method for custom class loaders, 
 * by overriding findClass(String name) in java.lang.ClassLoader
 * Created: Sat Apr 14 13:25:11 2001
 *
 * @author Cezar M. Tigaret <c.tigaret@ucl.ac.uk>
 * @version 0.4
 */

public class PClassLoader2 extends ClassLoader {


	 /** Default path and file names for the loaded class */
	 private String path=null, ijPluginsPath=null, cName=null;

	 /** The platform-specific file separator. */
	 private static final String separator=System.getProperty("file.separator");

	 /** The default constructor. 
	  * The caller of this constructor should also invoke setPath(String) 
	  * and setPluginsPath(String) before attempting to load a class.
	  * @see #setPath(String pathName)
	  * @see #setPluginsPath(String pathName)
	  */
	 public PClassLoader2() {
		  
	 }

	 /** Construct a PClassLoader2 instance to load a
	  * class file located in path, with the top-level 
	  * user plugin directory path ijPluginsPath.
	  * @param path The path to the class to be loaded
	  * @param ijPluginsPath the path to the top-level user plugins directory
	  * @see findClass(String name)
     */
	 public PClassLoader2 (String path, String ijPluginsPath) {
		  this.path=path;
		  this.ijPluginsPath=ijPluginsPath;
	 }
	 
	 /** Overrides findClass(String) in java.lang.ClassLoader.
	  * First tries to load the class from among the system classes. 
	  * If not successful, then tries to load the class from a file relative 
	  * to the top-level user plugins directory (ijPluginsPath), useful for 
	  * plugin packages. Upon failure, it tries to load the class from 
	  * a file reachable by the specified path.
	  * @param name The filename of the java class source; the ".class" extension may be omitted.
	  * @return The resulting class object, or null if path is null.
	  * @see java.lang.ClassLoader
	  */

	 public Class findClass(String name) 
		  throws ClassNotFoundException {
		  //		  System.out.println("PClassLoader2 findClass("+name+")");
		  if (path==null || ijPluginsPath==null) return null;
		  Class c=null;
		  try {
				c=findLoadedClass(name);
				resolveClass(c);
		  } catch (Exception e0) {
				try {
					 c=findSystemClass(name);
				} catch (Exception e1) {
					 try {
						  c=loadClassData(ijPluginsPath,name);
						  resolveClass(c);
					 } catch (Exception e2) {
						  try {
								c=loadClassData(path, name);
								resolveClass(c);
						  } catch (Exception e3) {
								throw new ClassNotFoundException(name);
						  }
					 }
				}
		  }
		  return c;
	 }

	 /** Loads class bytecode from compiled java file. 
	  * 
	  * @param c the name of the '*.class" file, without leading pathname.
	  * @return The resulting Class object.
	  */
	 private Class loadClassData(String p, String c) throws ClassNotFoundException {
		  String clsName=c;
		  // convert classname to pathname and append it to path
		  if (!c.endsWith(".class")) c+=".class";
		  // needed for plugin packages 
		  if (!(c.indexOf('.')==c.lastIndexOf('.'))){
				String subPath=c.substring(0, c.lastIndexOf(".class"));
				String pack=subPath.substring(0,subPath.lastIndexOf('.'));
				pack.replace('.',separator.charAt(0));
				p+=pack;
				c=subPath.substring(subPath.lastIndexOf('.')+1)+".class";
		  }
		  p+=separator+c;
		  File f=new File(p);
		  //		  System.out.println("PClassLoader2 loadClassData("+f.getPath()+")");
		  Class cls=null;
		  try {
				InputStream in=new FileInputStream(f);
				int bufsize=(int)f.length();
				byte b[]=new byte[bufsize];
				in.read(b,0,bufsize);
				in.close();
				//				System.out.println("PClassLoader2 Class name: "+clsName);
				cls=defineClass(clsName,b,0,b.length);
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


} // PClassLoader2
